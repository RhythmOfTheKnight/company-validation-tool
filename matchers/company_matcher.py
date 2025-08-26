import logging 

from api.companies_house import get_company_data, search_company_by_name
from utils.string_utils import normalize_company_name, is_match
from utils.validation_utils import extract_crn_from_row, extract_company_name_from_row, extract_fallback_company_name_from_row, is_valid_crn

logger = logging.getLogger(__name__)

def extract_company_fields(api_data: dict) -> dict:
    """
    Parses the raw API response from Companies House and extracts the relevant fields
    into a standardized dictionary.
    """
    if not api_data or not isinstance(api_data, dict):
        return {}

    address = api_data.get("registered_office_address", {}) or {}
    
    # Format SIC codes into a single string
    sic_codes = api_data.get("sic_codes", [])
    sic_codes_formatted = ", ".join(sic_codes) if sic_codes else ""

    # Format previous names into a single string
    previous_names_list = api_data.get("previous_company_names", [])
    previous_names = ", ".join([item.get("name", "") for item in previous_names_list]) if previous_names_list else ""

    return {
        "name": api_data.get("company_name"),
        "crn": api_data.get("company_number"),
        "status": api_data.get("company_status"),
        "inc_date": api_data.get("date_of_creation"),
        "dissolution_date": api_data.get("date_of_cessation"),
        "type": api_data.get("type"),
        "locality": address.get("locality"),
        "postcode": address.get("postal_code"),
        "sic_codes_formatted": sic_codes_formatted,
        "previous_names": previous_names,
    }

def find_best_match(dataset_row, api_key):
    """
    Finds the best company match on companies house by CRN.
    First attempts a CRN match, then name lookup
    
    Inputs:
        dataset_row: A given row of the entrepreneurship dataset
        api_key: Companies house API key
        
    Returns:
        A tuple: (company_data, match_type, needs_manual_review)"""

    # 1. try to match on Company Registration Number. 
    crn = extract_crn_from_row(dataset_row)
    if crn:
        logger.info(f"Searching by CRN: {crn}")
        raw = get_company_data(crn, api_key)
        if raw:
            company_data = extract_company_fields(raw)
            logger.info(f"CRN match found: {company_data['name']} ({company_data['crn']})")
            return company_data, "crn_match", False
        
    # 2. Try to match by Company Name
    company_name = extract_company_name_from_row(dataset_row)
    if company_name:
        results, count = search_company_by_name(company_name, api_key)
        if count > 0:
            # Check 
            matched_item = find_match(results, company_name)
            if matched_item:
                raw_data = get_company_data(matched_item.get("company_numbr"), api_key)
                if raw_data:
                    company_data = extract_company_fields(raw_data)
                    return company_data,"exact_name_match" , False   

    # 3. Search on fallback name as last resort 
    fallback_name = extract_fallback_company_name_from_row(dataset_row)
    if fallback_name and fallback_name != company_name:
        results, count = search_company_by_name(company_name, api_key)
        if count > 0 and results != None:
            first_result = results['items'][0]
            raw_data = get_company_data(first_result.get("company_number"), api_key)
            if raw_data:
                company_data = extract_company_fields(raw_data)
                return company_data,"exact_name_match" , False 

    logger.warning(f"No confident match found for '{company_name}'. Manual review needed.")
    return None, "no_match", True 




def find_match(search_results, company_name):
    """
    Find a matching company in search results using multiple matching strategies.
    Tries exact match first, then case-insensitive, then normalized.
    
    Args:
        search_results (dict): API response from Companies House search
        company_name (str): Company name from your dataset
        
    Returns:
        tuple: (matched_company, needs_update) where:
            - matched_company: Company data if match found, None otherwise
            - needs_update: Boolean indicating if record needs updating
    """

    if not search_results or "items" not in search_results:
        return None

    # go thorugh match types and see if there is a match 
    for result in search_results.get("items", []):
        api_name = result.get("title")
        if "title" not in result:
            continue
            
        is_exact_match = (api_name.lower() == company_name.lower())
        is_normalized_match = (normalize_company_name(api_name).lower() == normalize_company_name(company_name).lower())

        if is_exact_match or is_normalized_match:
            logger.info(f"Found confident name match for '{company_name}'")
            return result  # Return the matched item
           
    # No match found
    return None
    
    

    


