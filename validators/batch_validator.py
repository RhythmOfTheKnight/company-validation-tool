import pandas as pd
import logging 
from datetime import datetime
from ..matchers.company_matcher import find_best_company_match

# Set up Logger
logger  = logging.getLogger(__name__)

def validate_companies_batch(excel_file_path, api_key, sheet_name = "main", output_file_path = None):
    """
    Process master.xlsx file and validate companies against Companies House API.
    
    Args:
        excel_file_path (str): Path to the master.xlsx file
        api_key (str): Companies House API key
        output_file_path (str): Optional path for output file
        
    Returns:
        tuple: (validated_df, validation_report)
    """
    # Load the Excel file
    try:
        df = pd.read_excel(excel_file_path, sheet_name)
        logger.info(f"Loaded {len(df)} rows from {excel_file_path} (sheet: {sheet_name})")
    except Exception as e:
        logger.error(f"Failed to load Excel file: {e}")
        return None, None
    
    # Initalize tracking columns
    df["validation_status"] = "pending"
    df["match_type"] = "none"
    df["confidence_score"] = 0
    df["needs_manual_review"] = False
    df["validation_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df["api_company_number"] = ""
    df["api_company_name"] = ""
    df["api_company_status"] = ""
    df["api_company_address"] = ""
    df["has_valid_crn"] = False

    validation_report = []
    
    # Process each company
    for idx in range(len(df)):
        row = df.iloc[idx]
        logger.info(f"Processing company {idx + 1}/{len(df)}")

        try:

            company_data, match_type, confidence= find_best_company_match(
                row,
                api_key)
            
            if company_data:
                # Update with found data
                df.at[idx, "validation_status"] = "validated"
                df.at[idx, "match_type"] = match_type
                df.at[idx, "confidence_score"] = confidence

                if isinstance(company_data, dict):
                    df.at[idx, 'api_company_name'] = company_data.get('name', '')
                    df.at[idx, 'api_company_status'] = company_data.get('status', '')
                    df.at[idx, 'api_incorporation_date'] = company_data.get('inc_date', '')
                    df.at[idx, 'api_company_number'] = company_data.get('company_number', '')
                    df.at[idx, 'api_company_address'] = company_data.get('address', {}).get('formatted', '')

                    # Flag for manual review if low confidence
                    if confidence < 7:
                        df.at[idx, "needs_manual_review"] = True
                        logger.warning(f"Low confidence match for row {idx}: {confidence}")

            else:
                # No match found :(
                df.at[idx, "validation_status"] = "no_match"
                df.at[idx, "match_type"] = "no_match"
                df.at[idx, "needs_manual_review"] = True
                logger.info(f"No match found for row {idx}")

            # Add to validation report
            validation_report.append({
                "row_index": idx,
                "company_name": df.at[idx, "Companies House name"],
                "crn": df.at[idx, "Companies Registration Number"],
                "validation_status": df.at[idx, "validation_status"],
                "match_type": df.at[idx, "match_type"],
                "confidence_score": df.at[idx, "confidence_score"],
                "needs_manual_review": df.at[idx, "needs_manual_review"],
                "api_company_number": df.at[idx, "api_company_number"],
                "api_company_name": df.at[idx, "api_company_name"],
                "api_company_status": df.at[idx, "api_company_status"],
                "api_company_address": df.at[idx, "api_company_address"]
            })          
        except Exception as e:
            logger.error(f"Error processing row {idx} : {e}")
            df.at[idx, "validation_status"] = "error"
            df.at[idx, "match_type"] = "error"
            df.at[idx, "needs_manual_review"] = True


    # Save results if output path provided
    if output_file_path:
        try:
            with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
                # Main validated data
                df.to_excel(writer, sheet_name='Validated_Companies', index=False)
                
                # Validation report
                report_df = pd.DataFrame(validation_report)
                report_df.to_excel(writer, sheet_name='Validation_Report', index=False)
                
                # Manual review items
                manual_review_df = df[df['needs_manual_review'] == True]
                manual_review_df.to_excel(writer, sheet_name='Manual_Review_Required', index=False)
                
                # Companies with valid CRNs
                valid_crn_df = df[df['has_valid_crn'] == True]
                valid_crn_df.to_excel(writer, sheet_name='Companies_With_Valid_CRN', index=False)
                
            logger.info(f"Results saved to {output_file_path}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
    
    return df, pd.DataFrame(validation_report)