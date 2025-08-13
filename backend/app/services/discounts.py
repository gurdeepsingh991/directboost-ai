import pandas as pd
import json
from app.db.supabase_client import supabase

# ---------------------------------
# 1. Load Manager Inputs
# ---------------------------------


def load_data():
# Segment config provided by managers (JSON file or from API)
    with open("/Users/Gurdeep/Documents/Research Project Repo/directboost-ai/backend/data/discounts.json", "r") as f:
        segment_config = json.load(f)

# Financial data (CSV from managers)
    financials = pd.read_csv("/Users/Gurdeep/Documents/Research Project Repo/directboost-ai/backend/data/hotel_financials.csv")

# Booking history from DB extract
    
    response = supabase.rpc("get_booking_segments", {"p_user_id": "6a6cc5b5-7af2-45ac-afd4-6a6321a5f9ac"}).execute()
    bookings =  pd.DataFrame(response.data)

    print(response)
# ---------------------------------
# 2. Normalise & Merge
# ---------------------------------
    financials['hotel_norm'] = financials['hotel_name'].str.lower().str.strip()
    bookings['hotel_norm'] = bookings['hotel'].str.lower().str.strip()

    bookings = bookings.merge(
        financials,
        left_on=['hotel_norm', 'arrival_date_month', 'arrival_date_year'],
        right_on=['hotel_norm', 'month', 'year'],
        how='left'
    )
    return bookings, segment_config

# ---------------------------------
# 3. Feature Engineering
# ---------------------------------

def add_features(bookings):
    amen_cols = ['is_gym_used', 'is_spa_used', 'is_kids_club_used', 'is_bar_used']
    bookings['occ_gap'] = bookings['target_booking_%'] - bookings['forecast_booking_%']
    bookings['amenity_count'] = bookings[amen_cols].sum(axis=1)
    bookings['amenity_pref_high'] = (bookings['amenity_count'] >= 2).astype(int)
    bookings['is_price_sensitive'] = bookings['market_segment'].str.lower().isin(
        ['online ta', 'offline ta/to']
    ).astype(int)
    bookings['is_last_minute'] = (bookings['lead_time'] <= 3).astype(int)
    return bookings

# Detect season from occupancy pattern
def _detect_season(row):
    occ = row['booking_%']
    if occ < 50:
        return "low"
    elif occ < 75:
        return "shoulder"
    else:
        return "high"

def detect_season(bookings):
    bookings['season_band'] = bookings.apply(_detect_season, axis=1)
    return bookings

# ---------------------------------
# 4. Perk Selection (based on cost)
# ---------------------------------
def choose_perks(row, max_cost):
    cost_map = {
        'spa': row.get('spa_cost', 0),
        'gym': row.get('gym_cost', 0),
        'kids_club': row.get('kids_club_cost', 0),
        'bar_credit': row.get('bar_credit_cost', 0)
    }
    sorted_perks = sorted(cost_map.items(), key=lambda x: x[1])
    chosen = []
    total_cost = 0
    for perk, cost in sorted_perks:
        if total_cost + cost <= max_cost:
            chosen.append(perk)
            total_cost += cost
    return chosen, total_cost

# ---------------------------------
# 5. Rule Engine
# ---------------------------------
def rule_offer(row, segment_config):
    seg_id = int(row['booking_segment'])
    seg_conf = next((seg for seg in segment_config if seg['cluster_id'] == seg_id), None)
    if not seg_conf:
        return pd.Series({'offer_type': 'None', 'discount_pct': 0, 'perks': []})

    # Baseline discount from config
    base_disc = seg_conf['baseline'].get(row['season_band'], 0)
    
    # Occupancy gap boost
    if row['occ_gap'] > 10:
        base_disc += seg_conf.get('boost_if_high_gap', 0)

    # Perk selection
    perks, perk_cost = choose_perks(row, seg_conf.get('max_perk_cost', 0))

    # Price sensitivity → bias to discount
    if row['is_price_sensitive'] and base_disc < seg_conf['baseline']['low']:
        base_disc = seg_conf['baseline']['low']

    # Loyalty preference
    if row.get('is_repeated_guest', 0) == 1 and base_disc > 0.05:
        base_disc -= 0.02  # Slightly reduce discount for loyalty, give perks instead
        if 'gym' not in perks:
            perks.append('gym')

    # ADR vs perk cost guardrail
    adr_loss = row['adr_y'] * base_disc
    if adr_loss > perk_cost * 0.8:
        # Perks instead of deep discount
        base_disc = 0.0

    return pd.Series({
        'offer_type': 'Discount' if base_disc > 0 else 'Perk',
        'discount_pct': round(base_disc * 100, 1),
        'perks': perks
    })

# ---------------------------------
# 6. Apply Rule Engine
# ---------------------------------
def apply_offers (bookings, segment_config):
    offers = bookings.apply(lambda r: rule_offer(r,segment_config), axis=1)
    bookings = pd.concat([bookings, offers], axis=1)
    return bookings

# ---------------------------------
# 7. Save Output
# ---------------------------------
def save_bookng_offers(bookings):
    bookings[['hotel','booking_segment_record_id' ,'arrival_date_month', 'arrival_date_year',
            'booking_segment', 'business_label',
            'offer_type', 'discount_pct', 'perks']].to_csv("guest_level_offers.csv", index=False)

    print("✅ Guest-level offers saved to guest_level_offers.csv")


def _genrate_discounts():
    bookings, segment_config = load_data()
    bookings = detect_season(bookings)
    bookings = add_features(bookings)
    bookings = apply_offers(bookings, segment_config)
    save_bookng_offers(bookings)
    return True
    
    
    