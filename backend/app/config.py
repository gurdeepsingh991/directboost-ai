from dotenv import load_dotenv
from pathlib import Path
import os 
from datetime import datetime
from typing import Dict
from jinja2 import Template


env_path = Path(__file__).resolve().parents[1]/".env"
load_dotenv(dotenv_path= env_path)

SUPABASE_URL:str = os.getenv("SUPABASE_URL")
SUPABASE_KEY:str = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_KEY:str = os.getenv("SUPABASE_SERVICE_KEY")
BUCKET_NAME: str = os.getenv("BUCKET_NAME")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
SEG_NUMERICAL_COLUMNS = [
    "lead_time", "stays_in_weekend_nights", "stays_in_week_nights", "adults", "children", "babies",
    "is_canceled", "is_repeated_guest", "previous_cancellations", "previous_bookings_not_canceled",
    "booking_changes", "days_in_waiting_list", "adr", "required_car_parking_spaces",
    "special_request_count", "total_guests", "early_bird", "late_commer", "total_stay_length",
    "is_high_spender", "weekend_ratio"
]

AMENITY_COLUMNS = [
    'is_gym_used', 'is_spa_used', 'is_swimming_pool_used', 'is_bar_used',
    'is_gaming_room_used', 'is_kids_club_used', 'is_meeting_room_used', 'is_work_desk_used'
]

SEG_CAT_COLUMNS = [
    "meal", "market_segment", "distribution_channel", "deposit_type", "customer_type", "season"
]

N_CLUSTERS:int = 5
N_COMPONENTS = 45

MODEL_VERSION = f"v1-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

ASSET_BASE:str = os.getenv("ASSET_BASE")

ASSETS = {
    "city": {
        "rooms": {
            "standard": ASSET_BASE + "city-standard-min.jpg",
            "deluxe":   ASSET_BASE + "city-delux-min.jpg",
            "suite":    ASSET_BASE + "city-suite-min.jpg",
        },
        "amenities": {
            "gym":                ASSET_BASE + "gym-min.jpg",
            "kids_play_area":     ASSET_BASE + "kids-playing-area-min.jpg",
            "meal":               ASSET_BASE + "meal-min.jpg",
            "meeting_room":       ASSET_BASE + "meeting-room-min.jpg",
            "spa":                ASSET_BASE + "spa-min.jpg",
            "swimming_pool":      ASSET_BASE + "swimming-pool-min.jpg",
        },
        "hero": ASSET_BASE + "Hero-city-min.png", 
    },
    "resort": {
        "rooms": {
            "standard": ASSET_BASE + "resort-standard-min.png",
            "deluxe":   ASSET_BASE + "resort-delux-min.png",
            "suite":    ASSET_BASE + "resort-suite-min.png",
        },
        "amenities": {
            "gym":                ASSET_BASE + "gym-min.jpg",
            "kids_play_area":     ASSET_BASE + "kids-playing-area-min.jpg",
            "meal":               ASSET_BASE + "meal-min.jpg",
            "meeting_room":       ASSET_BASE + "meeting-room-min.jpg",
            "spa":                ASSET_BASE + "spa-min.jpg",
            "swimming_pool":      ASSET_BASE + "swimming-pool-min.jpg",
        },
        "hero": ASSET_BASE + "hero-resort-min.png",  # on-brand for resort
    },
}

AMENITY_LABELS = {
    "gym": "Gym",
    "kids_play_area": "Kids’ Play Area",
    "meal": "Dining",
    "meeting_room": "Meeting Room",
    "spa": "Spa",
    "swimming_pool": "Swimming Pool",
}


AMENITY_SLOGANS = {
    "spa": "Complimentary treatment credit",
    "gym": "Complimentary access – open late",
    "swimming_pool": "Access included – towels provided",
    "kids_play_area": "Free play sessions for kids",
    "meeting_room": "1-hour meeting room credit",
    "meal": "Breakfast included",
}

ROOM_LETTER_TIER: Dict[str, Dict[str, str]] = {
    "city": {
        "A": "standard",
        "B": "standard",
        "C": "deluxe",
        "D": "deluxe",
        "E": "suite",
        "F": "suite",
        "G": "suite",
    },
    "resort": {
        "A": "standard",
        "B": "standard",
        "C": "deluxe",
        "D": "deluxe",
        "E": "suite",
        "F": "suite",
        "G": "suite",
        "L": "suite",  
    },
}

PROMPTS: dict[str, str] = {}
TEMPLATES: dict[str, Template] = {}

def load_prompts_and_templates(supabase):
    global PROMPTS, TEMPLATES
    p_res = supabase.table("system_prompts").select("*").execute()
    for row in p_res.data or []:
        PROMPTS[row["name"]] = row["content"]

    t_res = supabase.table("email_templates").select("*").execute()
    for row in t_res.data or []:
        TEMPLATES[row["name"]] = Template(row["content"])

# ----- human-friendly naming -----
ROOM_TIER_FRIENDLY = {
    "standard": "Standard Room",
    "deluxe": "Deluxe Room",
    "suite": "Suite",
}

MEAL_FRIENDLY = {
    "RO": "Room Only",
    "BB": "Breakfast Included",
    "HB": "Half Board",
    "FB": "Full Board",
    "AI": "All Inclusive",
}


SAFE_KEYS_OFFER = [
        "hotel", "room_type", "meal", "country",
        "business_label", "target_month", "target_year",
        "discount_pct", "offer_type", "perks", "amenities_used_before"
    ]
SAFE_KEYS_HISTORY = [
        "arrival_date_year", "arrival_date_month",
        "stays_in_weekend_nights", "stays_in_week_nights",
        "total_stay_length", "adults", "children", "babies",
        "meal", "market_segment", "customer_type", "adr", "season",
        "is_high_spender", "is_family", "is_solo", "is_business",
        "is_gym_used", "is_spa_used", "is_swimming_pool_used",
        "is_bar_used", "is_kids_club_used", "is_meeting_room_used", "is_work_desk_used"
    ]

MONTH_NAME_TO_NUM = {
    "january": 1, "february": 2, "march": 3,
    "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9,
    "october": 10, "november": 11, "december": 12,
}

MONTH_NAMES = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
]


MONTH_TO_NUM = {
    m.lower(): i for i, m in enumerate(
        ["January","February","March","April","May","June","July","August","September","October","November","December"], 1
    )
}

REQUIRED_BOOKING_COLS = {
    "id","booking_segment_record_id","user_id","hotel","name","email","phone_number",
    "arrival_date_year","arrival_date_month","arrival_date_week_number","lead_time",
    "market_segment","is_repeated_guest","reserved_room_type","adr","country","meal",
    "booking_segment","cluster_id","business_label",
    "is_gym_used","is_spa_used","is_swimming_pool_used","is_bar_used",
    "is_gaming_room_used","is_kids_club_used","is_meeting_room_used","is_work_desk_used"
}

# Perk synonyms to align amenity usage + financial cost columns
PERK_COST_COLS = {
    "spa": "spa_cost",
    "gym": "gym_cost",
    "kids_club": "kids_club_cost",
    "bar_credit": "bar_credit_cost",
    "swimming_pool": "swimming_pool_cost",
    "work_desk": "work_desk_cost",
    "meeting_room": "meeting_room_cost"
}

AMENITY_USAGE_COLS = {
    "spa": "is_spa_used",
    "gym": "is_gym_used",
    "kids_club": "is_kids_club_used",
    "bar": "is_bar_used",  # not a perk name, but useful signal
    "swimming_pool": "is_swimming_pool_used",
    "work_desk": "is_work_desk_used",
    "meeting_room": "is_meeting_room_used",
    "gaming_room": "is_gaming_room_used"  # not a perk, signal only
}




