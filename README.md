# Company Validation Tool

A Python-based command-line tool for validating and enriching company data against official UK sources. This tool uses the Companies House API to verify company details and the Postcodes.io API to enrich location data.

## Overview

This project is designed to clean and enhance a dataset of company information, typically from an Excel spreadsheet. It automates the process of:
1.  **Loading** a list of companies from an Excel file.
2.  **Validating** each company against the Companies House API by searching for its Company Registration Number (CRN) or name.
3.  **Updating** the dataset information, including official company names, status, incorporation dates, and more.
4.  **Updating** location data by fetching the administrative district for each company's postcode.
5.  **Saving** the enhanced data to a new, timestamped Excel file, with rows that require manual attention conveniently highlighted in red.

## Key Features

- **Dual API Integration**: Leverages both the **Companies House API** for corporate data and the **Postcodes.io API** for geographic data.
- **Intelligent Matching**: Finds companies based on their CRN first, then falls back to searching by primary and secondary company names.
- **Data Enrichment**: Updates your dataset with a wide range of fields, including official name, CRN, status, type, incorporation/dissolution dates, and SIC codes.
- **Location Enhancement**: Adds the correct administrative district (e.g., "City of Westminster") based on the company's postcode.
- **Historical Data Tracking**: Keeps a running list of previous administrative districts for a company if its location changes over time.
- **Automated Reporting**: Generates a clean Excel report where rows flagged for `needs_manual_review` are automatically highlighted.
- **Progress Bars**: Provides real-time feedback during long-running API calls using `tqdm`.

## Project Structure

The project is organized with a clear separation of concerns:

```
company_validation/
├── api/
│   ├── companies_house.py    # Client for the Companies House API
│   └── postscodes.py         # Client for the Postcodes.io API
├── datasets/
│   └── (Not included)        # Source data files
├── logs/
│   └── company_validation.log # Application log file
├── matchers/
│   └── company_matcher.py    # Core logic for finding the best company match
├── utils/
│   ├── file_utils.py         # Helpers for loading Excel files
│   └── ...
├── validators/
│   └── batch_validator.py    # Orchestrates the validation of the entire dataset
├── config.py                 # Central configuration for column names and constants
├── main.py                   # Main script and command-line interface entry point
├── requirements.txt          # Project dependencies
└── README.md                 # This file
```

## Setup and Installation

### Prerequisites
- Python 3.9+
- A Companies House API key. You can get one for free from the [Companies House developer portal](https://developer.company-information.service.gov.uk/).

### 1. Clone the Repository
```bash
git clone <repository_url>
cd company-validation-tool
```

### 2. Create and Activate a Virtual Environment
It is highly recommended to use a virtual environment to manage project dependencies.

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
Install all required packages from the `requirements.txt` file.
```bash
pip install -r requirements.txt
```

### 4. Upload Datasets and Create logs folder
Upload your source Excel file to the `datasets` directory (needs to be created) and ensure a `logs` folder exists in the project root. This is required for logging and data processing.

## How to Use

The tool is run from the command line. You must provide the path to your input file and your Companies House API key.

### Command
```bash
python main.py --input "path/to/your/data.xlsx" --sheet "SheetName" --api_key "YOUR_API_KEY_HERE"
```

### Arguments
- `--input`: (Required) The full path to the source Excel file containing your company data.
- `--sheet`: (Required) The name of the worksheet within the Excel file to process.
- `--api_key`: (Required) Your personal Companies House API key.

### Example
```bash
python main.py --input "datasets/master.xlsx" --sheet "AllCompaniesData" --api_key "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8"
```

The script will generate a new Excel file in the same directory as your input file, named `validated_<timestamp>.xlsx`.

## Data Privacy

**Note:** For privacy and security reasons, the `datasets/` directory in this repository is empty. You must provide your own source Excel file to run the application.

## API Rate Limits

Companies House API has rate limits of approximately 600 requests per 5 minutes. The validation functions include built-in delays to respect these limits.
