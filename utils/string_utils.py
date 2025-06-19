import re
import logging 

logger = logging.getLogger(__name__)

def normalize_company_name(company_name):
    """
    Normalize a company name by removing problematic whitespace characters.
    
    Args:
        company_name (str): Company name to normalize
        
    Returns:
        str: Normalized company name with standardized whitespace
    """
    if not isinstance(company_name, str):
        return str(company_name) if company_name is not None else ""
    
    # Log unusual cases in companies name
    if any(char in company_name for char in ["\n", "\r", "\t"]):
        logger.debug(f"Name contains special whitespace characters: {company_name}")
    
    # Replace all problematic whitespaces with nothing
    normalized = company_name.replace("\n", "").replace("\r", "").replace("\t", "")
    return normalized.strip()

def is_match(api_company, company_name):
    """
    Check if two company names match exactly (case-sensitive).
    
    Args:
        api_company (str): Company name from Companies House API
        company_name (str): Company name from your dataset
        
    Returns:
        bool: True if names match exactly, False otherwise
    """
    return api_company == company_name
