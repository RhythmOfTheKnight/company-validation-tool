"""
Utility functions for common data processing tasks in company validation.
"""
import pandas as pd
from datetime import datetime
from config import EMPTY_VALUES
from datetime import datetime

def is_empty_value(value):
    """
    Check if a value should be considered 'empty' based on various indicators.
    
    Args:
        value: The value to check
        
    Returns:
        bool: True if the value should be considered empty
    """
    if pd.isna(value):
        return True
    
    if not isinstance(value, str):
        value = str(value)
    
    value_clean = value.strip().lower()
    return value_clean in EMPTY_VALUES or value_clean == ""

def clean_string_value(value):
    """
    Clean and standardize string values from datasets.
    
    Args:
        value: The value to clean
        
    Returns:
        str or None: Cleaned string or None if empty
    """
    if pd.isna(value):
        return None
    
    if not isinstance(value, str):
        value = str(value)
    
    # Remove problematic whitespace characters
    cleaned = value.replace("\n", "").replace("\r", "").replace("\t", "").strip()
    
    if not cleaned or cleaned.lower() in EMPTY_VALUES:
        return None
    
    return cleaned

def safe_get_column(row, column_names, default=""):
    """
    Safely get a value from a row using multiple possible column names.
    
    Args:
        row (pd.Series): The row to extract from
        column_names (list): List of possible column names to try
        default: Default value if no column is found
        
    Returns:
        The value from the first matching column, or default
    """
    if isinstance(column_names, str):
        column_names = [column_names]
    
    for col_name in column_names:
        if col_name in row.index and not pd.isna(row[col_name]):
            value = clean_string_value(row[col_name])
            if value is not None:
                return value
    
    return default

def parse_date_safely(date_value):
    """
    Safely parse a date value that could be a string, datetime, or other format.
    
    Args:
        date_value: The date value to parse
        
    Returns:
        str or None: ISO date string (YYYY-MM-DD) or None if parsing fails
    """
    if pd.isna(date_value):
        return None
    
    try:
        if hasattr(date_value, "date"):
            return date_value.date().isoformat()
        else:
            # Try to parse as string
            parsed = datetime.strptime(str(date_value), "%Y-%m-%d")
            return parsed.date().isoformat()
    except (ValueError, TypeError):
        return None
