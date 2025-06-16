import requests 
from requests.auth import HTTPBasicAuth
import time 
import logging


# Begin logging 
logger = logging.getLogger(__name__)

# Constants 
DEFAULT_DELAY = 0.4 # Most suitable delay for Companies House (Rate limit of 120 requests per minute)
BASE_URL = "https://api.company-information.service.gov.uk"
COMPANY_ENDPOINT  = f"{BASE_URL}/company/"
SEARCH_ENDPOINT = f"{BASE_URL}/search/companies"

def search_company_by_name(company_name, api_key, delay = DEFAULT_DELAY):
    """
    Search for companies by name via the Companies House API.
    
    Args:
        company_name (str): Company name to search for
        api_key (str): Your Companies House API key
        delay (float): Delay in seconds to avoid rate limits
        
    Returns:
        tuple: (results, match_count) where:
            - results: JSON response containing matches (or None if error)
            - match_count: Number of companies found (0 if error)
    """
    try:
        params = {"q": company_name}
        response = requests.get(
            SEARCH_ENDPOINT,
            params = params,
            auth = HTTPBasicAuth(api_key, ""),
            timeout = 15
        )

        if response.status_code == 200:
            results = response.json()
            match_count = int(results.get("total_results", 0))
            logger.info(f"Found {match_count} possible matches for '{company_name}'")
            return results, match_count
        elif response.status_code == 429:
            logger.warning("Rate limit exceeded. Please check the rate limiting factor and adhere to 600 requests per 5 minuts")
            return None, 0
        else:
            logger.error(f"Error searching for company {company_name}: {response.status_code} - {response.text}")
            return None, 0
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None, 0
    finally:
        time.sleep(delay) # Adhere to the rate limit 

def get_company_data(company_number, api_key, delay = DEFAULT_DELAY):
    """
    This function gets company details from companies house API using the CRN.

    Args:
        company_number (str): The company registration number (CRN).
        api_key (str): Your Companies House API key.
        delay (float): Delay in seconds to avoid hitting rate limits. 
                       Default is 0.4 seconds, slightly beneath the 120 request per minute limit.
                
    Returns:
        dict: Json of company data if found, otherwise None.
    """
    try:
        response = requests.get(
            f"{COMPANY_ENDPOINT}{company_number}",
            auth = HTTPBasicAuth(api_key, ""),
            timeout = 15
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            logger.warning(f"Company with number {company_number} not found.")
            return None
        else:
            logger.error(f"Error obtaining data for company {company_number}: {response.status_code} - {response.text}")
            return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None
    finally:
        time.sleep(delay) # Adhere to the rate limit 
        