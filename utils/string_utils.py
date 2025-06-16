import re
import logging 


# Set up logger
logger = logging.getLogger(__name__)


def normalize_company_name(company_name):
    """
    Normalize a company name by removing all whitespace characters (newlines, tabs, etc.)
    and removing leading/trailing whitespace.
    
    Args:
        company_name (str): Company name to normalize
        
    Returns:
        str: Normalized company name with standardized whitespace
    """

    if not isinstance(company_name, str):
        return str(company_name) if company_name is not None else ""
    
    # Log unusual cases in companies name
    if "\n" in company_name or "\r" in company_name:
        logger.debug(f"Name contains newline characters: {company_name}")
    if "\t" in company_name:
        logger.debug(f"Name contains tab characters: {company_name}")
    
    # Replace all whitespaces and replace them with single space (including newline characters and tabs and whatever)
    normalized = company_name.replace("\n", "").replace("\r", "").replace("\t", "")

    return normalized.strip()

def is_match(API_company, company_name):
    """
    Check if two company names match exactly (case-sensitive).
    
    Args:
        api_company (str): Company name from Companies House API
        dataset_company (str): Company name from your dataset
        
    Returns:
        bool: True if names match exactly, False otherwise
    """

    if API_company == company_name:
        return True
    
    return False  
