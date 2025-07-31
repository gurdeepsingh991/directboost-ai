import pandas as pd 
from fastapi import File,UploadFile
import io
from app.db.supabase_client import supabase

def read_file(file: UploadFile) -> pd.DataFrame:
    filename = file.filename.lower()
    if filename.endswith('.csv'):
        content = file.file.read()
        df = pd.read_csv(io.StringIO(content.decode("utf-8")))
    elif filename.endswith(('.xls', '.xlsx')):
        content = file.file.read()
        df = pd.read_excel(io.BytesIO(content))
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
   # print("record count before invalid guest", df.shape)
   # print("record count after invalid guest", df[df["adults"]>0].shape)
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
    df['early_bird'] = (df['lead_time'] >= 60).astype(int)
    df['late_commer'] = (df['lead_time'] <= 7).astype(int)

    """Create total stay length feature"""
    df['total_stay_length'] = df['stays_in_weekend_nights'] + df['stays_in_week_nights']
    
    
    """create high spender if they spend more than the median of the all bookings"""
    df['is_high_spender'] = (df['adr'] > df['adr'].median()).astype(int)
    
    """weekend heavy"""
    df['weekend_ratio'] = df['stays_in_weekend_nights'] / df['total_stay_length'].replace(0, 1)
    
    return df

def upload_data_to_db(df: pd.DataFrame, email: str) -> dict:
    try:
        # Step 1: Fetch user ID
        response = supabase.table("users").select("user_id").eq("email", email).execute()

        if not response.data:
            return {"success": False, "message": f"No user found with email: {email}"}

        user_id = response.data[0]["user_id"]
        df["user_id"] = user_id
        
        #Step 2: make all previous booking history as inactive
        response = supabase.table("booking_history").update({"is_active": False}).eq("user_id",user_id).execute()

        # Step 3: Convert to list of records
        records = df.to_dict(orient="records")

        # Step 4: Insert into booking_history
        insert_response = supabase.table("booking_history").insert(records).execute()

        # Step 5: Check for insert errors
        if not insert_response.data:
            return {
                "success": False,
                "message": f"Error inserting records: {insert_response.error.message}"
            }

        return {
            "success": True,
            "message": "Booking history file uploaded successfully",
            "inserted_rows": len(insert_response.data)
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Something went wrong while uploading the file. Error: {str(e)}"
        }

def process_booking_data(file: UploadFile,email:str) -> pd.DataFrame:
    """
    Master function to read a raw booking file and return a cleaned DataFrame
    ready for segmentation.
    """
    df = read_file(file)
    df = drop_invalid_guests(df)
    df = fill_missing_values(df)
    df = add_derived_features(df)
    response = upload_data_to_db(df,email)
    return response


def get_booking_data_from_db(email: str): 
    try:
        # Step 1: Fetch user ID
        response = supabase.table("users").select("user_id").eq("email", email).execute()

        if not response.data:
            return {"success": False, "message": f"No user found with email: {email}"}

        user_id = response.data[0]["user_id"]
        
        response = supabase.table("booking_history").select("*").eq("user_id",user_id).eq("is_active", True).execute()
        
        if not response.data:
            return {"success": False, "message": f"Unable to fetch booking data"}
        
        df = pd.DataFrame(response.data)
        return  df 
    except Exception as e:
            return {"success": False, "message": f"Something went wrong: {e}"}
        
def insert_segment_records(df_segmented: pd.DataFrame):
    try:
        records = []
        for _, row in df_segmented.iterrows():
            records.append({
                "booking_id": row["id"],
                "segment_cluster": row["segment_cluster"],
                "model_version": row["model_version"],
                "is_active": True
            })

        response = supabase.table("booking_segments").insert(records).execute()

        return {"success": True, "inserted": len(records)}
    
    except Exception as e:
        return {"success": False, "message": f"Segment insert failed: {e}"}