import pandas as pd 

# GS:delete later 
def read_file(file_path: str) -> pd.DataFrame:
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Use CSV or Excel.")
    return df

def drop_invalid_guest (df:pd.DataFrame) -> pd.DataFrame:
    """Removes rows where adults there are no adults present"""
    return df[df["adults"]>0]

def fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Fills key missing values with defaults."""
    df['market_segment'] = df['market_segment'].fillna('Unknown')
    df['distribution_channel'] = df['distribution_channel'].fillna('Unknown')
    return df
