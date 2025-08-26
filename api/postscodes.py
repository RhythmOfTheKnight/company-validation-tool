import requests
import logging 
import time
from typing import Optional

logger =  logging.getLogger(__name__)

def get_admin_district(postcode):
    """Get admin district for a postcode
    
    Args:
        postcode: The UK postcode to look up 
        
    Returns: 
        The admin district as a string, otherwise None if no search results"""
    if not postcode:
        return None
    
    time.sleep(0.1)
    
    try:
        url = f"https://api.postcodes.io/postcodes/{postcode.replace(' ', '%20')}"
        response = requests.get(url, timeout = 10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("result",{}).get("admin_district")
        else:
            logger.warning(f"Postcode API returned problem status code {response.status_code} for postcode: {postcode}")
            return None
    except Exception as e:
        logger.error(f"An unexpected error occured for postcode {postcode}: {e}")
        return None    