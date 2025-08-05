import pandas as pd 
from fastapi import File,UploadFile
import io
from app.db.supabase_client import supabase
from app.config import AMENITY_COLUMNS
import numpy as np


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
    print("Initial record count:", df.shape)

    df["total_stay_length"] = df["stays_in_week_nights"] + df["stays_in_weekend_nights"]
    df["total_guests"] = df["adults"] + df["children"] + df["babies"]

    # 1. No adults
    df = df[df["adults"] > 0]

    # 2. Negative ADR
    df = df[df["adr"] >= 0]

    # 3. ADR too high (optional cap)
    df = df[df["adr"] <= 5000]

    # 4. Stay nights = 0 but not cancelled
    df = df[~((df["total_stay_length"] == 0) & (df["is_canceled"] == 0))]

    # 5. Booking cancelled but stay nights > 0 (force reset or drop)
    df = df[~((df["is_canceled"] == 1) & (df["total_stay_length"] > 0))]

    # 6. Total guests = 0
    df = df[df["total_guests"] > 0]

    # 7. Drop missing critical fields
    df = df.dropna(subset=["country", "children"])

    # 8. Negative lead_time
    df = df[df["lead_time"] >= 0]

    print("Cleaned record count:", df.shape)
    
    # 9. Previous bookings and repleat customer
    print("Before repeat guest cleanup:", df.shape)

    # Drop contradictory records: guest is marked new but has previous successful bookings
    df = df[~((df["is_repeated_guest"] == 0) & (df["previous_bookings_not_canceled"] > 0))]

    # Drop invalid values
    df = df[df["previous_bookings_not_canceled"] >= 0]
    df = df[df["previous_cancellations"] >= 0]

    print("After repeat guest cleanup:", df.shape)
    
    return df

def fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Fills key missing values with defaults."""
    print("🧪 Checking missing values before training:")
    df['market_segment'] = df['market_segment'].fillna('Unknown')
    df['distribution_channel'] = df['distribution_channel'].fillna('Unknown')
    return df

def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Creates total_guests and season features."""
   # df['total_guests'] = df['adults'] + df['children'] + df['babies']

    month_to_season = {
    'December': 'Winter', 'January': 'Winter', 'February': 'Winter',
    'March': 'Spring', 'April': 'Spring', 'May': 'Spring',
    'June': 'Summer', 'July': 'Summer', 'August': 'Summer',
    'September': 'Fall', 'October': 'Fall', 'November': 'Fall'
}
    df['season'] = df['arrival_date_month'].map(month_to_season)
    
    # Base engineered features
    df["total_stay_length"] = df["stays_in_week_nights"] + df["stays_in_weekend_nights"]
    df["total_guests"] = df["adults"] + df["children"] + df["babies"]
    df['early_bird'] = (df['lead_time'] >= 60).astype(int)
    df['late_commer'] = (df['lead_time'] <= 7).astype(int)
    df['is_high_spender'] = (df['adr'] > df['adr'].median()).astype(int)
    df['weekend_ratio'] = df['stays_in_weekend_nights'] / df['total_stay_length'].replace(0, 1)

    # Inferred persona flags
    df['is_family'] = ((df['children'] + df['babies']) > 0).astype(int)
    df['is_solo'] = ((df['adults'] == 1) & (df['children'] == 0)).astype(int)
    df['is_business'] = ((df['market_segment'].isin(['Corporate', 'Direct'])) & (df['lead_time'] < 7)).astype(int)
    
    print("Cleanup feature addition done")
    return df

def _generate_amenities(row):
    amenities = {
        'is_gym_used': 0, 'is_spa_used': 0, 'is_swimming_pool_used': 0,
        'is_bar_used': 0, 'is_gaming_room_used': 0, 'is_kids_club_used': 0,
        'is_meeting_room_used': 0, 'is_work_desk_used': 0
    }

    if row.get('is_family', False):
        amenities['is_swimming_pool_used'] = np.random.binomial(1, 0.8)
        amenities['is_kids_club_used'] = np.random.binomial(1, 0.7)
        amenities['is_gaming_room_used'] = np.random.binomial(1, 0.6)
        amenities['is_spa_used'] = np.random.binomial(1, 0.4)
    elif row.get('is_business', False):
        amenities['is_gym_used'] = np.random.binomial(1, 0.6)
        amenities['is_bar_used'] = np.random.binomial(1, 0.7)
        amenities['is_meeting_room_used'] = np.random.binomial(1, 0.5)
        amenities['is_work_desk_used'] = np.random.binomial(1, 0.8)
    elif row.get('is_solo', False):
        amenities['is_gym_used'] = np.random.binomial(1, 0.5)
        amenities['is_bar_used'] = np.random.binomial(1, 0.5)
    else:
        amenities['is_spa_used'] = np.random.binomial(1, 0.6)
        amenities['is_bar_used'] = np.random.binomial(1, 0.5)
        amenities['is_gym_used'] = np.random.binomial(1, 0.3)

    return pd.Series(amenities)

def assign_amenities(df: pd.DataFrame) -> pd.DataFrame:
    if not set(AMENITY_COLUMNS).issubset(df.columns):
        print("Amenity flags being assigned based on profile...")
        amenity_df = df.apply(_generate_amenities, axis=1)
        df = pd.concat([df, amenity_df], axis=1)
    else:
        print("⚠️ Amenity flags already present. Skipping assignment.")
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
    # df = assign_amenities(df)
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
        segments_counts = df_segmented['segment_cluster'].value_counts().to_dict()
        return {"success": True, "inserted": len(records), "segment_counts": segments_counts}
    
    except Exception as e:
        return {"success": False, "message": f"Segment insert failed: {e}"}