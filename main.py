import logging 
import sys
import argparse
import pandas as pd
from company_validation.validators.batch_validator import validate_companies_batch

# Set up logging
def setup_logging():
    """Configure loggin for application."""

    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers = [
            logging.FileHandler("company_validation.log", mode='a'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main function for company validation process."""

    parser = argparse.ArgumentParser(description="Validate companies against Companies House API.")
    parser.add_argument("--input", required = True, help="Path to the input Excel file (master.xlsx)")
    parser.add_argument("--sheet", default = "sheet1", help="Sheet name in the input Excel file (default: main)")
    parser.add_argument("--output", required = True, help="Path to the output Excel file (results.xlsx)")
    parser.add_argument("--api_key", required = True, help="Companies House API key")
    
    
    args = parser.parse_args()

    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting company validation process...")

    # Call the validation function
    validated_df, report_df = validate_companies_batch(
            excel_file_path=args.input,
            api_key=args.api_key,
            sheet_name=args.sheet,
            output_file_path=args.output
        )
    
    if validated_df is not None:
        total_companies = len(validated_df)
        validated_count = len(validated_df[validated_df["validation_status"] == "validated"])
        manual_review_count = len(validated_df[validated_df["needs_manual_review"] == True])
        valid_crn_count = len(validated_df[validated_df["Companies Registration Number"].notna()])

        logger.info(f"Validation complete: {total_companies} companies processed")
        logger.info(f"Total companies: {total_companies}")
        logger.info(f"Companies with valid CRNs: {valid_crn_count}")
        logger.info(f"Successfully validated companies: {validated_count}")
        logger.info(f"Companies needing manual review: {manual_review_count}")
    else:
        logger.error("Validation failed. No data to report.")

if __name__ == "__main__":
    main()