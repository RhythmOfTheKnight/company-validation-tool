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
    Search for a company by name using the Company Name in case the CRN is missing/invalid
    via the Companies House API

    Args:
    company_name (str): The company name from the dataset to search for.
    api_key (str): Your Companies House API key.
    delay (float): Delay in seconds to avoid hitting rate limits. 
        Default is 0.4 seconds, slightly beneath the 120 request per minute limit.
                
    Returns:
        dict: Comppany data if found, otherwise None.
    """
    try:
        params = {"q": company_name}
        response = requests.get(
            SEARCH_ENDPOINT,
            params = params,
            auth = HTTPBasicAuth(api_key, "")
        )

        if response.status_code == 200:
            results = response.json()
            
            # Check how many matches were found
            match_count = results.get("total_results", 0)
            logger.info(f"Found {match_count} possible matches for '{company_name}'")
            return results

            # Try to find an exact match


            return response.json()
        else:
            logger.error(f"Error searching for company {company_name}: {response.status_code} - {response.text}")
            return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None
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
        dict: Comppany data if found, otherwise None.
    """
    try:
        response = requests.get(f"{COMPANY_ENDPOINT}{company_number}",
            auth = HTTPBasicAuth(api_key, "")
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
        