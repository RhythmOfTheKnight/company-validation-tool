import pandas as pd
import logging
from config import EMPTY_VALUES, Columns

logger = logging.getLogger(__name__)

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
    
    crn_str = str(crn).strip().lower()
    
    # Check for invalid values using config constants
    if crn_str in EMPTY_VALUES:
        return False
    
    # UK CRNs are typically 8 characters (numbers) or 8-9 chars with prefix (SC123456)
    if len(crn_str) == 8 and crn_str.isdigit():
        return True
    elif (len(crn_str) == 8 and crn_str[:2].isalpha() and crn_str[2:].isdigit()) \
         or (len(crn_str) == 9 and crn_str[:3].isalpha() and crn_str[3:].isdigit()):
        return True
    return False

def extract_crn_from_row(dataset_row):
    """Extract and validate CRN from dataset row.
    
    Args:
        dataset_row (pd.Series): A row from the dataset containing company information.
        
    Returns:
        str or None: The validated CRN in uppercase and stripped of whitespace, or None if invalid.
    """
    if Columns.CRN not in dataset_row.index:
        return None
    
    raw = dataset_row[Columns.CRN]

    if pd.isna(raw):
        return None
    
    # clean before validation
    crn = str(raw).upper().strip()

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
    # Try multiple possible column names for company name
    name_columns = [
        Columns.CH_NAME,
        "Companies House name",
        "Company Name"    ]
    
    for col in name_columns:
        if col not in dataset_row.index:
            continue
        
        raw = dataset_row[col]
        if pd.isna(raw):
            continue

        name = str(raw).strip()
        if not name:
            continue

        lower = name.lower()
        
        # Check against invalid values from config
        if lower in EMPTY_VALUES:
            continue

        return name

    return None

def extract_fallback_company_name_from_row(dataset_row):
    """Extract fallback company name from "Company Name" column when CRN is invalid.
    
    Args:
        dataset_row (pd.Series): A row from the dataset containing company information.

    Returns:
        str or None: The fallback company name as a string, or None if not found or empty.
    """
    from utils.data_utils import safe_get_column
    result = safe_get_column(dataset_row, ["Company Name"], "")
    return result if result else None

