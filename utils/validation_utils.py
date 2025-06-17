import pandas as pd
import logging

# Set up logger
logger =  logging.getLogger(__name__)

def is_valid_crn(crn):
    """
    Validate a Company Registration Number (CRN) based on its length and format.
    A valid CRN is either 8 characters long or 2-3 characters followed by 6 digits.

    Args:
        crn (str): The Company Registration Number to validate.
    
    Returns:
        bool: True if the CRN is valid, False otherwise.
    """

    if pd.isna(crn):
        return False
    
    crn_str = str(crn)
    
    # Check for invalid values
    if crn_str.lower().strip() in ['n/a', 'na', 'nan', '', 'none']:
        return False
    
    # UK CRNs are typically 8 characters (numbers) or 8-9 chars with prefix (SC123456)
    if len(crn_str) == 8 and crn_str.isdigit():
        return True
    elif len(crn_str) in [8, 9] and crn_str[:2].isalpha() and crn_str[2:].isdigit():
        return True
    
    return False


def extract_crn_from_row(dataset_row):
    """Extract and validate CRN from dataset row.
    
    Args:
        dataset_row (pd.Series): A row from the dataset containing company information.
        
    Returns:
        str or None: The validated CRN in uppercase and stripped of whitespace, or None if invalid.
    """
    if "Companies Registration Number" not in dataset_row.index:
        return None
    
    crn = dataset_row["Companies Registration Number"]
    if is_valid_crn(crn):
        return str(crn).upper().strip()
    return None

def extract_company_name_from_row(dataset_row):
    """Extract company name from dataset row.
    
    Args:
        dataset_row (pd.Series): A row from the dataset containing company information.

    Returns:
        str or None: The company name as a string, or None if not found or empty.
    """
    if "Companies House name" not in dataset_row.index:
        return None
    
    name = dataset_row["Companies House name"]
    if pd.isna(name):
        return None
    
    return str(name)