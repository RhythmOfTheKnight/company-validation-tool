import pandas as pd
from matchers.company_matcher import find_best_match
from tqdm import tqdm
from config import Columns

def validate_companies_batch(df, api_key):
    """
    Validates a df of companies against companeies house api
    The function iterates through each row of input df, clls
    company matcher to find best match, and appends the results
    to new columns 

    Args:
        df: Input DataFrame with comp. data
        api_key: The API key for companies hosue

    Returns:
        The df with columns containing validation results
    
    """
    results = []

    for idx, row in tqdm(df.iterrows(), total = df.shape[0], desc= "Validating Companies"):
        api_data, match_type, needs_review = find_best_match(row, api_key)
        results.append({
            Columns.API_DATA: api_data,
            Columns.MATCH_TYPE: match_type,
            Columns.NEEDS_MANUAL_REVIEW : needs_review
        })

    results_df = pd.DataFrame(results)

    df.reset_index(drop = True, inplace = True)
    results_df.reset_index(drop= True, inplace = True)

    validated_df = pd.concat([df, results_df], axis = 1)

    return validated_df





