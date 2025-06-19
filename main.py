import logging 
import sys
import argparse
import pandas as pd
from validators.batch_validator import validate_companies_batch
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from config import Columns, ExcelStyles

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler("company_validation.log", mode="a"),
            logging.StreamHandler(sys.stdout),
        ],
    )

def apply_manual_review_highlighting(output_file, sheet_name, tracking_df):
    """Apply red highlighting to rows that need manual review."""
    RED_FILL = PatternFill(start_color=ExcelStyles.RED_FILL_COLOR, 
                          end_color=ExcelStyles.RED_FILL_COLOR, 
                          fill_type="solid")
    
    wb = load_workbook(output_file)
    ws = wb[sheet_name]
    
    # Apply highlighting based on tracking data
    for i, needs_review in enumerate(tracking_df["needs_manual_review"]):
        if needs_review:
            excel_row = i + 2  # Adjust for header and 0-based indexing
            for col in range(1, ws.max_column + 1):
                ws.cell(row=excel_row, column=col).fill = RED_FILL
    
    wb.save(output_file)

def filter_empty_programmes(df, tracking_df, logger):
    """Filter out rows with empty programmes attended."""
    original_count = len(df)
    
    # Create comprehensive filter for empty/blank values
    if Columns.PROGRAMME in df.columns:
        mask = (
            df[Columns.PROGRAMME].notna() &
            (df[Columns.PROGRAMME].astype(str).str.strip() != '') &
            (df[Columns.PROGRAMME].astype(str).str.strip().str.lower() != 'nan') &
            (df[Columns.PROGRAMME].astype(str).str.strip() != 'N/A') &
            (df[Columns.PROGRAMME].astype(str).str.strip() != 'None')
        )
        df_filtered = df[mask].copy()
        tracking_df_filtered = tracking_df[mask].copy()
    else:
        logger.warning(f"Column '{Columns.PROGRAMME}' not found in data")
        df_filtered = df.copy()
        tracking_df_filtered = tracking_df.copy()
    
    filtered_count = len(df_filtered)
    logger.info(f"Original validated rows: {original_count}")
    logger.info(f"Rows after filtering empty programmes: {filtered_count}")
    logger.info(f"Removed {original_count - filtered_count} rows with empty programmes")
    
    return df_filtered, tracking_df_filtered

def log_summary_statistics(df_filtered, tracking_df_filtered, logger):
    """Log summary statistics of the validation results."""
    total = len(df_filtered)
    manual = tracking_df_filtered["needs_manual_review"].sum()
    perfect = (tracking_df_filtered["confidence_score"] == 10).sum()
    
    logger.info(f"Final processed rows (after filtering): {total}")
    logger.info(f"Rows needing manual review: {manual}")
    logger.info(f"Perfect-confidence matches: {perfect}")
    
    if Columns.CRN in df_filtered.columns:
        valid_crns = df_filtered[Columns.CRN].notna().sum()
        logger.info(f"Rows with a valid CRN in the final sheet: {valid_crns}")

def main():
    parser = argparse.ArgumentParser(description="Validate companies via CH API")
    parser.add_argument("--input", required=True, help="Path to input Excel file")
    parser.add_argument("--sheet", default="AllCompaniesData", help="Sheet name (default: AllCompaniesData)")
    parser.add_argument("--output", required=True, help="Path to output Excel file")
    parser.add_argument("--api_key", required=True, help="Companies House API key")
    parser.add_argument("--limit", type=int, default=None, help="Max rows to process")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting company validation…")

    # Run batch validation
    df, tracking_df = validate_companies_batch(
        source_file=args.input,
        api_key=args.api_key,
        sheet_name=args.sheet,
        output_file=args.output,
        limit=args.limit
    )

    # Filter out rows with empty programmes attended
    logger.info("Filtering out rows with empty programmes attended...")
    df_filtered, tracking_df_filtered = filter_empty_programmes(df, tracking_df, logger)
    
    # Write filtered results to output file
    logger.info(f"Writing filtered results to {args.output}")
    with pd.ExcelWriter(args.output, engine='openpyxl') as writer:
        df_filtered.to_excel(writer, sheet_name=args.sheet, index=False)
        tracking_df_filtered.to_excel(writer, sheet_name="report", index=False)

    # Apply highlighting for manual review
    logger.info("Applying manual review highlighting...")
    apply_manual_review_highlighting(args.output, args.sheet, tracking_df_filtered)

    # Log summary statistics
    log_summary_statistics(df_filtered, tracking_df_filtered, logger)

if __name__ == "__main__":
    main()
