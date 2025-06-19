# Configuration constants for the company validation tool

# Companies House API Configuration
DEFAULT_API_DELAY = 0.4  # Rate limit compliance (120 requests/minute)
API_BASE_URL = "https://api.company-information.service.gov.uk"
API_COMPANY_ENDPOINT = f"{API_BASE_URL}/company/"
API_SEARCH_ENDPOINT = f"{API_BASE_URL}/search/companies"

# Column name constants
class Columns:
    """Standard column names used throughout the application"""
    CH_NAME = "Companies House name\n(or note Sole Trader/ Freelancer)"
    CRN = "Company Registration Number"
    STATUS = "Company Status?"
    INC_DATE = "Date Company Incorporated"
    DISSOLUTION_DATE = "Date Company Dissolved"
    SIC_CODES = "Company Industry(s)"
    TYPE = "Company Type"
    PREVIOUS_NAMES = "Previous Names"
    LOCALITY = "Registered Locality"
    POSTCODE = "Registered Postcode"
    PROGRAMME = "Programme(s) attended"
    MATCH_TYPE = "match_type"
    CONFIDENCE = "confidence_score"

# Column mapping for API data to Excel columns
COLUMN_MAP = {
    "name": Columns.CH_NAME,
    "crn": Columns.CRN,
    "status": Columns.STATUS,
    "inc_date": Columns.INC_DATE,
    "dissolution_date": Columns.DISSOLUTION_DATE,
    "sic_codes_formatted": Columns.SIC_CODES,
    "type": Columns.TYPE,
    "previous_names": Columns.PREVIOUS_NAMES,
    "locality": Columns.LOCALITY,
    "postcode": Columns.POSTCODE
}

# Empty value indicators
EMPTY_VALUES = {"n/a", "na", "nan", "", "none", "sole trader", "freelancer", "self employed"}

# Company type mappings
COMPANY_TYPE_INDICATORS = {
    "ltd": [" ltd", "limited"],
    "plc": [" plc"],
    "llp": [" llp"],
    "community-interest-company": [" cic"],
    "sole trader": ["sole trader", "freelancer"]
}

# Excel styling
class ExcelStyles:
    """Excel formatting constants"""
    RED_FILL_COLOR = "FFC7CE"
