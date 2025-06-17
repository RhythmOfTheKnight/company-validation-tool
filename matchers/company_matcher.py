import logging 
import pandas as pd
from datetime import datetime
from ..api.companies_house import get_company_data, search_company_by_name
from ..utils.string_utils import normalize_company_name, is_match
from ..utils.validation_utils import extract_crn_from_row, extract_company_name_from_row, is_valid_crn

# Begin logging 
logger = logging.getLogger(__name__)

# Variables in the file
exact_matches = 0 
close_matches = 0

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
    global exact_matches
    global close_matches
    if not search_results or "items" not in search_results:
        return None, True  # No results found, return None and indicate update needed
    
    # Hopefully this works first time around
    for result in search_results.get("items", []):
        if "title" in result:
            API_company = result["title"]
            if is_match(API_company, company_name):
                logger.info(f"Exact match found for company: {company_name}")
                exact_matches += 1 
                return result, False
        
    # For efficency sake, we check other critieria in another loop 
    for result in search_results.get("items", []):
        if "title" in result:
            API_company = result["title"]
            # Compare case insensitive by using .lower()
            if is_match(API_company.lower(), company_name.lower()):
                logger.info(f"Match found for company when ignoring cases: {API_company}")
                close_matches += 1
                return result, True
            # Calling the normalise function on company name
            if is_match(API_company, normalize_company_name(company_name)):
                logger.info(f"Match found for company when normalising company name in the dataset {API_company}")
                close_matches += 1
                return result, True
            # Simultaneously call normalise and ignore case
            if is_match(API_company.lower(), normalize_company_name(company_name).lower()):
                logger.info(f"When normalising both company name and doing case insensitive matching, match found for: {API_company}")
                close_matches += 1
                return result, True

    # Otherwise RIP        
    return None, True
    
def score_company_match(search_result, dataset_row):
    """
    Score the similarity between a Companies House search result and a dataset row.
    Used when no exact match or CRN match is found.
    
    The function evaluates similarity across multiple dimensions:
    1. Name similarity (up to 7 points):
       - Partial name containment with length > 15 chars (7 points)
       - Partial name containment with length > 10 chars (4 points)
       - Other partial containment (2 points)
       - Word overlap ratio (up to 3 points)
    
    2. Incorporation date matching (up to 3 points):
       - Exact date match (3 points)
    
    3. Location matching (up to 2 points):
       - Company locality appears in headquarters location (2 points)
    
    Args:
        search_result (dict): Single company entry from Companies House search results
        dataset_row (pandas.Series): Row from dataset containing company information
        
    Returns:
        int: Similarity score from 1-10, with 10 indicating highest confidence match
    """
    score = 0

    # Get name from dataset row and companies house API search result entry
    dataset_name = ""
    if "Companies House name" in dataset_row.index and not pd.isna(dataset_row["Companies House name"]):
        dataset_name = str(dataset_row["Companies House name"]).lower()    
    api_name = search_result.get("title","").lower()

    # Normalise names
    api_name_norm = normalize_company_name(api_name).lower()
    dataset_name_norm = normalize_company_name(dataset_name).lower()
    
    # Partial match - one contains the other
    if api_name_norm in dataset_name_norm or dataset_name_norm in api_name_norm:
        if len(api_name_norm) > 15 and len(dataset_name_norm) > 15:
            # 7 points to gryffindor 
            score += 7
        elif len(api_name_norm) > 10 and len(dataset_name_norm) > 10:
            # 4 points to Hufflepuff
            score += 4
        else:
            # 2 points to Slytherin
            score += 2
    # Otherwise see if they have words in common
    else:
        # Define common terms to ignore in company names
        common_terms = {'limited', 'ltd', 'llp', 'plc', 'inc', 'incorporated', 
                    'corporation', 'corp', 'company', 'co', 'group', 'holdings',
                    'holding', 'services', 'international', 'uk', 'the', 'and', 'of'}
        
        # Filter out common terms
        api_words = set(w for w in api_name_norm.split() if w.lower() not in common_terms)
        dataset_words = set(w for w in dataset_name_norm.split() if w.lower() not in common_terms)

        if api_words and dataset_words:  # Make sure we still have words left
            common_words = api_words.intersection(dataset_words)
            # Only count meaningful words
            if len(common_words) > 0:
                match_ratio = len(common_words) / max(len(dataset_words), len(api_words))
                
                # Award up to 3 points based on similar words (non-common terms)
                word_score = round(match_ratio * 3)
                score += word_score
                logger.debug(f"Word overlap score: {word_score}, matching words: {common_words}")

    # 2. Incorporation date (up to 3 points)
    if "Date Company Incorporated" in dataset_row.index and "date_of_creation" in search_result:
        dataset_date = ""
        try:
            api_date = search_result.get("date_of_creation", "")

            # Handle potential NaN values
            if not pd.isna(dataset_row["Date Company Incorporated"]):
                dataset_date = str(dataset_row["Date Company Incorporated"])

            if api_date == dataset_date:
                score += 3
        except (ValueError, TypeError):        
            pass
    
    # 3. Location/address (up to 2 points)
    if "Headquarters location" in dataset_row.index and not pd.isna(dataset_row["Headquarters location"]):
        dataset_location = str(dataset_row['Headquarters location']).lower()

        if "registered_office_address" in search_result and "locality" in search_result["registered_office_address"]:
            locality = search_result["registered_office_address"]["locality"].lower()

            if locality and locality in dataset_location:
                score +=2
    
    # Ensure minimum score of 1
    score = max(1, score)

    # Cap at 10
    score = min(10, score)

    return score



def find_best_company_match(dataset_row, api_key):
    """
    Find the best matching company from Companies House for a given dataset row.
    This function first attempts to search by CRN, then by company name.

    Args:
        dataset_row (pandas.Series): Row from dataset containing company information
        api_key (str): Your Companies House API key

    Returns:
        tuple: (company_data, match_type, match_confidence)
    """

    company_name = ""  # Ensure company_name is always defined

    # First try CRN if avaiable
    crn = extract_crn_from_row(dataset_row)
    if crn:
        logger.info(f"Searching for company by CRN: {crn}")
        # Get company data by CRN
        company_data = get_company_data(crn, api_key)
        if company_data:
            logger.info(f"Company found by CRN: {company_data.get('company_name', 'Unknown')}")
            return company_data, "crn_match", 10
            
    # If CRN is not matched, try searching by name
    company_name = extract_company_name_from_row(dataset_row)
    if company_name:
        logger.info(f"Searching for company by name: {company_name}")
        
        # Search for companies by name
        search_results, match_count = search_company_by_name(company_name, api_key)
    
        if match_count > 0:
            matched_company, needs_update = find_match(search_results, company_name)
            if matched_company:
                full_company_data = get_company_data(matched_company["company_number"], api_key)
                company_data = extract_company_fields(full_company_data)
                logger.info(f"Company found by name: {company_data.get('name', 'Unknown')}")
                return company_data, "name_match", 10
            else:
                # if no exact match, score the best match
                best_score = 0
                best_company = []
                if search_results is not None:
                    for result in search_results.get("items", []):
                        score = score_company_match(result, dataset_row)
                        if score == best_score:
                            best_company.append(result)
                        elif score > best_score:
                            best_score = score
                            best_company = [result]
                if len(best_company) == 1:
                    logger.info(f"Best match found by name: {best_company[0].get('title', 'Unknown')} with score {best_score}")
                    full_data = get_company_data(best_company[0]["company_number"], api_key)
                    company_data = extract_company_fields(full_data) if full_data else None
                    return company_data, "best_name_match", best_score
                elif len(best_company) > 1:
                    logger.info(f"Multiple best matches found by name, return all process manually: {best_company[0].get('title', 'Unknown')}")
                    # Only process if the score is above a certain threshold to avoid false positives
                    if best_score >6:
                        company_data = []
                        for comp in best_company:
                            full_data = get_company_data(comp["company_number"], api_key)
                            if full_data:
                                company_data.append(extract_company_fields(full_data))
                        logger.info(f"Multiple best matches found with score {best_score}")
                        return company_data, "multiple_best_name_matches", best_score
                    else:
                        logger.info(f"Multiple best matches found but score is too low: {best_score}")
                        return None, "multiple_best_name_matches_low_score", best_score
    # If no CRN or name match found, log and return None
    logger.info(f"No companies found matching name: {company_name}")
    # If no matches found, return None
    return None, "no_match", 0


def extract_company_fields(company_data):
    """
    Extract fields from the companies house API response. 
    
    Args:
        company_data (dict): JSON response from Companies House API
        
    Returns:
        dict: Standardized company data with the following fields
            - "Company Name"
            - "Company Number"
            - "Incorporation Date"
            - "Company Status"
            - "Company Type"
            - "Address"
    """

    result = {
        "name" : company_data.get("company_name", ""),
        "crn" : company_data.get("company_number", ""),
        "status" : company_data.get("company_status", ""),
        "inc_date" : company_data.get("date_of_creation", ""),
        "dissolution_date" : company_data.get("date_of_dissolution", ""), 
        "type" : company_data.get("company_type", ""),
        "sic_codes" : company_data.get("sic_codes", []),
    }

    # Extract address if available 
    if "registered_office_address" in company_data:
        address = company_data["registered_office_address"]
        address_parts = []
        for field in ["address_line_1", "address_line_2", "locality", "region", "postal_code", "country"]:
            if field in address and address[field]:
                address_parts.append(address[field])

        result["address"] = ", ".join(address_parts)
        result["locality"] = address.get("locality", "")
    else:
        result["address"] = ""
        result["locality"] = ""

    return result