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

def print_missing_values(df: pd.DataFrame):
    missing = df.isnull().sum()
    missing = missing[missing > 0]  
    if missing.empty:
        print(" No missing values found.")
    else:
        print(" Missing values found:\n")
        print(missing.sort_values(ascending=False))

def drop_invalid_guests (df:pd.DataFrame) -> pd.DataFrame:
    """Removes rows where adults there are no adults present"""
    print("record count before invalid guest", df.shape)
    print("record count after invalid guest", df[df["adults"]>0].shape)
    return df[df["adults"]>0]

def fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Fills key missing values with defaults."""
    df['market_segment'] = df['market_segment'].fillna('Unknown')
    df['distribution_channel'] = df['distribution_channel'].fillna('Unknown')
    return df

def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Creates total_guests and season features."""
    df['total_guests'] = df['adults'] + df['children'] + df['babies']

    month_to_season = {
        'December': 'Winter', 'January': 'Winter', 'February': 'Winter',
        'March': 'Spring', 'April': 'Spring', 'May': 'Spring',
        'June': 'Summer', 'July': 'Summer', 'August': 'Summer',
        'September': 'Fall', 'October': 'Fall', 'November': 'Fall'
    }
    df['season'] = df['arrival_date_month'].map(month_to_season)
    
    """Create latecommer and early bird features."""
    df['Early bird'] = (df['lead_time'] >= 60).astype(int)
    df['Late Commers'] = (df['lead_time'] <= 7).astype(int)

    """Create total stay length feature"""
    df['total_stay_length'] = df['stays_in_weekend_nights'] + df['stays_in_week_nights']
    
    
    """create high spender if they spend more than the median of the all bookings"""
    df['is_high_spender'] = (df['adr'] > df['adr'].median()).astype(int)
    
    """weekend heavy"""
    df['weekend_ratio'] = df['stays_in_weekend_nights'] / df['total_stay_length'].replace(0, 1)
    
    return df

def clean_booking_data(file_path: str) -> pd.DataFrame:
    """
    Master function to read a raw booking file and return a cleaned DataFrame
    ready for segmentation.
    """
    df = read_file(file_path)
    df = drop_invalid_guests(df)
    df = fill_missing_values(df)
    df = add_derived_features(df)
    return df