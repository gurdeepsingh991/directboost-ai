from dotenv import load_dotenv
from pathlib import Path
import os 
from datetime import datetime


env_path = Path(__file__).resolve().parents[1]/".env"
load_dotenv(dotenv_path= env_path)

SUPABASE_URL:str = os.getenv("SUPABASE_URL")
SUPABASE_KEY:str = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_KEY:str = os.getenv("SUPABASE_SERVICE_KEY")
BUCKET_NAME: str = os.getenv("BUCKET_NAME")
SEG_NUMERICAL_COLUMNS: list[str] =  [
    "lead_time",
    "stays_in_weekend_nights",
    "stays_in_week_nights",
    "adults",
    "children",
    "babies",
    "is_canceled",
    "is_repeated_guest",
    "previous_cancellations",
    "previous_bookings_not_canceled",
    "booking_changes",
    "days_in_waiting_list",
    "adr",
    "required_car_parking_spaces",
    "special_request_count",
    "total_guests",
    "early_bird",
    "late_commer",
    "total_stay_length",
    "is_high_spender",
    "weekend_ratio"
]

SEG_CAT_COLUMNS: list[str]= [
    "meal",
    "market_segment",
    "distribution_channel",
    "deposit_type",
    "customer_type",
    "season"
]

N_CLUSTERS:int = 5

MODEL_VERSION = f"v1-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"