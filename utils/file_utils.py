import pandas as pd
import logging 
import os 
from pathlib import Path 

# Set up logger
logger = logging.getLogger(__name__)

def load_excel_file(file_path, sheet_name = "main"):
    """
    Load an Excel file to return a DataFrame

    Args:
        file_path: The path to the excel file
        sheet_name: Sheet name to be loaded

    Returns:
        Dataframe with loaded data 
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        logger.info(f"Loaded {len(df)} rows from {file_path} (sheet: {sheet_name})")

        return df
    
    except ValueError as e:
        if "Worksheet" in str(e):
            logger.error(f"Sheet '{sheet_name}' not found in {file_path}")
            raise
    except Exception as e:
        logger.error(f"Failed to load Excel file: {e}")
        raise


def save_excel_file(df, file_path, sheet_name):
    """Save dataframe to excel file
    
    Args:
        df: Dataframe to be save
        file_path: location to save df
    """
    try:
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        df.to_excel(file_path, sheet_name = sheet_name, index= False)

        logger.info(f"Saved {len(df)} rows to {file_path}")

    except Exception as e:
        logger.error(f"Failed to save to Excel {e}")
        raise