import pandas as pd
from config import EMPTY_VALUES, COMPANY_TYPE_INDICATORS

def extract_company_type(company_data=None, crn_value=None, company_name=None):
    """
    Extract company type from various sources (API data, CRN, or company name).
    
    Args:
        company_data (dict): Companies House API response data
        crn_value (str): Company Registration Number from dataset
        company_name (str): Company name from dataset
    
    Returns:
        str: Company type (e.g., "Limited", "PLC", "LLP", "CIC", "Sole Trader", etc.)
    """
    # First check if CRN indicates sole trader
    if crn_value is not None and not pd.isna(crn_value):
        crn_str = str(crn_value).strip().lower()
        if any(term in crn_str for term in ["sole trader", "freelancer"]):
            return "sole trader"
        elif crn_str in EMPTY_VALUES:
            return "n/a"
    
    # If we have API data, use the company_type field
    if company_data and isinstance(company_data, dict):
        api_type = company_data.get("company_type", "")
        if api_type:
            return api_type
        
    # Fallback: extract from company name
    if company_name is not None and not pd.isna(company_name):
        name_lower = company_name.lower()
        
        for company_type, indicators in COMPANY_TYPE_INDICATORS.items():
            if any(indicator in name_lower for indicator in indicators):
                return company_type

    return "Unknown"


def extract_company_fields(company_data):
    """
    Extract standardized company fields from Companies House API response.
    Enhanced version that includes company type and formatted SIC codes.
    
    Args:
        company_data (dict): Raw API response from Companies House
        
    Returns:
        dict: Standardized company data with the following fields
            - "name": Company name
            - "crn": Company number  
            - "status": Company status
            - "inc_date": Incorporation date
            - "dissolution_date": Dissolution date
            - "type": Company type (simplified)
            - "company_type_full": Full company type from API
            - "sic_codes": List of SIC codes
            - "sic_codes_formatted": Comma-separated SIC codes
            - "address": Full address
            - "locality": Address locality
    """

    result = {
        "name": company_data.get("company_name", ""),
        "previous_names": company_data.get("previous_company_names", []),
        "crn": company_data.get("company_number", ""),
        "status": company_data.get("company_status", ""),
        "inc_date": company_data.get("date_of_creation", ""),
        "dissolution_date": company_data.get("date_of_dissolution") or company_data.get("date_of_cessation", ""), 
        "company_type_full": company_data.get("company_type", ""),
        "sic_codes": company_data.get("sic_codes", []),
        "locality": company_data.get("registered_office_address", {}).get("locality", ""),
        "postcode": company_data.get("registered_office_address", {}).get("postal_code", ""),
    }
    
    # Extract simplified company type
    result["type"] = extract_company_type(
        company_data=company_data,
        company_name=result["name"]
    )
    
    # Format SIC codes as comma-separated string
    sic_codes = result["sic_codes"]
    if isinstance(sic_codes, list) and sic_codes:
        result["sic_codes_formatted"] = ", ".join(sic_codes)
    else:
        result["sic_codes_formatted"] = ""

    # Format previous names as comma-separated string
    prev = company_data.get("previous_company_names", [])
    formatted = []
    for entry in prev:
        # entry might be a dict like {'name': 'Foo Ltd', 'ceased_on': '2021-01-01'}
        if isinstance(entry, dict) and "name" in entry:
            formatted.append(entry["name"])
        elif isinstance(entry, str):
            formatted.append(entry)
    result["previous_names"] = ", ".join(formatted)


    return result
