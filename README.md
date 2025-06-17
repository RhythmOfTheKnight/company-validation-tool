# Companies House Validation Tool

A Python tool for validating and correcting company information against the UK Companies House API. The tool validates company names, registration numbers, incorporation dates, headquarters locations, and company status.

## Overview

This project helps ensure data accuracy by cross-referencing internal company datasets with official Companies House records. It identifies and corrects discrepancies in:

- Company names (handling case differences, whitespace, and newline characters)
- Company registration numbers (CRNs)
- Incorporation and dissolution dates
- Company status (active, dissolved, etc.)
- Headquarters locations
- Industry classifications (SIC codes)

## Current Structure
company_validation/
├── __init__.py
├── main.py                    # CLI entry point
├── config.py                  # Configuration settings
├── api/
│   ├── __init__.py
│   ├── companies_house.py     # API interaction functions
│   └── testing.py             # Test scripts
├── matchers/
│   ├── __init__.py
│   └── company_matcher.py     # Company matching logic
├── utils/
│   ├── __init__.py
│   ├── string_utils.py        # String processing utilities
│   └── validation_utils.py    # Validation helper functions
├── validators/
│   ├── __init__.py
│   ├── batch_validator.py     # Batch processing
│   └── field_validators.py    # Individual field validation
├── reporters/
│   ├── __init__.py
│   └── excel_reporter.py     # Excel output generation
├── DataSets/
│   └── master.xlsx           # Input data
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_matchers.py
│   └── test_validators.py
└── requirements.txt

## Features Implemented

- **Companies House API Integration**: Connect to and query the Companies House API
- **CRN Validation**: Validate company registration numbers against the API
- **Name Matching**: Compare company names with official records, handling case differences and newlines
- **Company Information Updates**: Update local data with correct information from Companies House
- **Error Reporting**: Track and report validation failures with specific error types
- **Rate Limiting**: Respect API rate limits to avoid throttling

## API Endpoints Used

- `/company/{company_number}` - Get details for a specific company by CRN
- `/search/companies` - Search for companies by name

## Example Usage

```python
# Validate a company using its CRN
from company_validation.api.companies_house import get_company_data

API_KEY = "your_api_key"
company_data = get_company_data("SC123456", API_KEY)

# Search for a company by name
from company_validation.api.companies_house import search_company_by_name

results = search_company_by_name("Example Company Ltd", API_KEY)

# Full validation of a dataset
from company_validation import validate_company_data

updated_df, validation_report, failed_companies = validate_company_data(
    df=companies_df,  # DataFrame with company data
    api_key=API_KEY,
    delay=0.4  # Adhere to API rate limits
)
```

## Next Steps

- Implement smart company name matching for better handling of partial matches
- Add validation for company status, incorporation dates, and SIC codes
- Create utilities for normalizing company names and addresses
- Build a full command-line interface for batch processing
- Add detailed reporting and visualization of validation results

## Requirements

- Python 3.8+
- pandas
- requests
- numpy
- matplotlib (for visualizations)

## API Rate Limits

Companies House API has rate limits of approximately 600 requests per 5 minutes. The validation functions include built-in delays to respect these limits.
