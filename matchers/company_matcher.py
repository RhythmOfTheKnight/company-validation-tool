import logging 
import pandas as pd
from datetime import datetime, date
from api.companies_house import get_company_data, search_company_by_name
from utils.string_utils import normalize_company_name, is_match
from utils.validation_utils import extract_crn_from_row, extract_company_name_from_row, extract_fallback_company_name_from_row, is_valid_crn
from utils.company_type_utils import extract_company_fields

logger = logging.getLogger(__name__)

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
        return None, True  # No results found, return None and indicate update needed
    
    # Try exact match first
    for result in search_results.get("items", []):
        if "title" in result:
            api_company = result["title"]
            if is_match(api_company, company_name):
                logger.info(f"Exact match found for company: {company_name}")
                return result, False
          # Try case insensitive match
    for result in search_results.get("items", []):
        if "title" in result:
            api_company = result["title"]
            if is_match(api_company.lower(), company_name.lower()):
                logger.info(f"Match found for company when ignoring cases: {api_company}")
                return result, True
            # Calling the normalise function on company name
            if is_match(normalize_company_name(api_company), normalize_company_name(company_name)):
                logger.info(f"Match found for company when normalising company name in the dataset {api_company}")
                return result, True
            # Simultaneously call normalise and ignore case
            if is_match((normalize_company_name(api_company).lower()), normalize_company_name(company_name).lower()):
                logger.info(f"When normalising both company name and doing case insensitive matching, match found for: {api_company}")
                return result, True

    # No match found
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
    dataset_name = extract_company_name_from_row(dataset_row) or ""
    api_raw = search_result.get("title","")

    api_norm = normalize_company_name(api_raw).lower()
    dataset_norm = normalize_company_name(dataset_name).lower()    # Partial match - one contains the other
    if api_norm in dataset_norm or dataset_norm in api_norm:
        if len(api_norm) > 15 and len(dataset_norm) > 15:
            # 7 points to Gryffindor
            score += 7
        elif len(api_norm) > 10 and len(dataset_norm) > 10:
            # 4 points to Slytherin
            score += 4
        else:
            score += 2
    # Otherwise see if they have words in common
    else:
        # Define common terms to ignore in company names
        common_terms = {"limited", "ltd", "llp", "plc", "inc", "incorporated", 
                    "corporation", "corp", "company", "co", "group", "holdings",
                    "holding", "services", "international", "uk", "the", "and", "of"}
        
        # Filter out common terms
        api_words = set(w for w in api_norm.split() if w.lower() not in common_terms)
        dataset_words = set(w for w in dataset_norm.split() if w.lower() not in common_terms)

        if api_words and dataset_words:  # Make sure we still have words left
            common_words = api_words.intersection(dataset_words)
            # Only count meaningful words
            if len(common_words) > 0:
                match_ratio = len(common_words) / max(len(dataset_words), len(api_words))
                
                # Award up to 3 points based on similar words (non-common terms)
                word_score = round(match_ratio * 3)
                score += word_score
                logger.debug(f"Word overlap score: {word_score}, matching words: {common_words}")    # 2. Incorporation date (up to 3 points)
    if "Date Company Incorporated" in dataset_row.index and "date_of_creation" in search_result:
        from utils.data_utils import parse_date_safely
        api_date = search_result.get("date_of_creation", "")
        dataset_date = parse_date_safely(dataset_row["Date Company Incorporated"])
        if dataset_date and api_date == dataset_date:
            # 3 points to Hufflepuff 
            score += 3
    
    # Ensure minimum score of 1
    score = max(1, score)

    # Cap at 10
    score = min(10, score)

    return score



def find_best_company_match(dataset_row, api_key):
    """
    Find the best matching company from Companies House for a given dataset row.
    Attempts, in order:
      1) CRN lookup (10pt, no manual review)
      2) Fallback-name search if CRN invalid (8pt, manual review)
      3) Name search:
         • exact/name-match (10pt, no manual review)
         • best-scored match (score, manual review if <10)
    Returns:
        (company_data, match_type, match_confidence, needs_manual_review)
    """
    needs_manual_review = False
    match_type = None
    company_data = None
    confidence = 0

    # 1) CRN lookup
    crn = extract_crn_from_row(dataset_row)
    if crn:
        logger.info(f"Searching by CRN: {crn}")
        raw = get_company_data(crn, api_key)
        if raw:
            std = extract_company_fields(raw)
            logger.info(f"CRN match found: {std['name']} ({std['crn']})")
            return std, "crn_match", 10, False

    # 2) Name search (try Companies House name first, then Company Name)
    # This runs whether CRN was missing or CRN lookup failed
    name = extract_company_name_from_row(dataset_row)
    if name:
        logger.info(f"Searching by name: {name}")
        results, count = search_company_by_name(name, api_key)
        if count:
            matched, needs_update = find_match(results, name)
            if matched:
                full = get_company_data(matched["company_number"], api_key)
                if full:
                    company_data = extract_company_fields(full)
                    match_type = "name_match"
                    confidence = 10
                    needs_manual_review = False  # Perfect matches don't need manual review
                    return company_data, match_type, confidence, needs_manual_review            # Score main name search results if no exact match
            company_data, confidence, needs_manual_review = find_best_scored_match(results, dataset_row, api_key)
            if company_data:
                return company_data, "best_name_match", confidence, needs_manual_review

    # 3) Fallback to Company Name field if Companies House name search failed
    fallback_name = extract_fallback_company_name_from_row(dataset_row)
    if fallback_name and fallback_name != name:  # Only try if different from Companies House name
        logger.info(f"Searching by fallback name: {fallback_name}")
        results, count = search_company_by_name(fallback_name, api_key)
        if count:
            matched, _ = find_match(results, fallback_name)
            if matched:
                full = get_company_data(matched["company_number"], api_key)
                if full:
                    company_data = extract_company_fields(full)
                    match_type = "fallback_name_match"
                    confidence = 8
                    needs_manual_review = True
                    return company_data, match_type, confidence, needs_manual_review            # Score fallback results if no exact match
            company_data, confidence, needs_manual_review = find_best_scored_match(results, dataset_row, api_key)
            if company_data:
                return company_data, "best_fallback_match", confidence, needs_manual_review# 4) No match found
    match_type = "no_match"
    confidence = 0
    needs_manual_review = True
    return None, match_type, confidence, needs_manual_review

def find_best_scored_match(results, dataset_row, api_key):
    """
    Find the best scoring match from search results.
    
    Args:
        results (dict): API search results
        dataset_row (pd.Series): Dataset row for scoring
        api_key (str): Companies House API key
        
    Returns:
        tuple: (company_data, confidence, needs_manual_review) or (None, 0, True)
    """
    if not results:
        return None, 0, True
    
    best_score = 0
    best_items = []
    
    for item in results.get("items", []):
        score = score_company_match(item, dataset_row)
        if score > best_score:
            best_score = score
            best_items = [item]
        elif score == best_score:
            best_items.append(item)
    
    if best_items and len(best_items) == 1:
        item = best_items[0]
        full = get_company_data(item["company_number"], api_key)
        company_data = extract_company_fields(full) if full else None
        needs_manual_review = best_score < 10
        return company_data, best_score, needs_manual_review
    
    return None, 0, True
