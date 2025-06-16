import logging 
from datetime import datetime
from ..api.companies_house import get_company_data, search_company_by_name
from ..utils.string_utils import normalize_company_name, is_match

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
        return None
    
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
    import pandas as pd
    score = 0

    # Get name from dataset row and companies house API search result entry
    dataset_name = ""
    if "Companies House Name" in dataset_row.index and not pd.isna(dataset_row["Companies House Name"]):
        dataset_name = str(dataset_row["Companies House Name"]).lower()    
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

def find_best_company_match():
    """

    Args:

    Returns: 
    
    """    
    return None


