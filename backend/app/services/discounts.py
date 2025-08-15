import pandas as pd
import json
from datetime import datetime
from app.db.supabase_client import supabase

# -------------------------
# Helpers & constants
# -------------------------
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

# -------------------------
# 1) LOAD & VALIDATE
# -------------------------
def load_inputs(email):
    
    try:
        # Step 1: Fetch user ID
        response = supabase.table("users").select("user_id").eq("email", email).execute()
        if not response.data:
            return {"success": False, "message": f"No user found with email: {email}"}

        user_id = response.data[0]["user_id"]

        
        #Step 2: make all previous booking history as inactive
        response = supabase.table("financials").select("*").eq("user_id",user_id).eq("is_active", True).execute()

        financials = pd.DataFrame(response.data)
        financials.drop(columns=["id", "user_id",'is_active', 'created_at', 'updated_at'], inplace=True)
        response = supabase.rpc("get_booking_segments", {"p_user_id": user_id}).execute()
        bookings = pd.DataFrame(response.data)
        print(response)

        # ---- Validate bookings
        missing = REQUIRED_BOOKING_COLS - set(bookings.columns)
        if missing:
            raise ValueError(f"Bookings missing columns: {sorted(missing)}")

        # ---- Normalize keys used for joins
        bookings["hotel_norm"] = bookings["hotel"].str.lower().str.strip()
        financials["hotel_norm"] = financials["hotel_name"].str.lower().str.strip()

        # Normalize room types on both sides (string, trimmed)
        bookings["reserved_room_type"] = bookings["reserved_room_type"].astype(str).str.strip()
        financials["room_type"] = financials["room_type"].astype(str).str.strip()

        # adr -> numeric
        bookings["adr"] = pd.to_numeric(bookings["adr"], errors="coerce")

        # month lower-case in bookings for logic
        bookings["arrival_date_month_lc"] = bookings["arrival_date_month"].astype(str).str.lower()
        if not bookings["arrival_date_month_lc"].isin(MONTH_TO_NUM.keys()).all():
            bad = bookings.loc[~bookings["arrival_date_month_lc"].isin(MONTH_TO_NUM.keys()), "arrival_date_month"].unique()
            raise ValueError(f"Unexpected month names in bookings: {bad.tolist()}")

        # ---- Financials soft checks (warn only)
        expected_fin_cols = {
            "hotel_name","hotel_norm","month","year","room_type",
            "target_booking_percent","forecast_booking_percent"
        }
        missing_fin = expected_fin_cols - set(financials.columns)
        if missing_fin:
            print(f"[WARN] Financials missing columns: {sorted(missing_fin)} — some features may degrade.")
        
        return bookings, financials
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Something went wrong while uploading the file. Error: {str(e)}"
        }
# -------------------------
# 2) FEATURE ENGINEERING
# -------------------------
def add_features(bookings: pd.DataFrame) -> pd.DataFrame:
    # amenity intensity
    amen_cols = ["is_gym_used","is_spa_used","is_kids_club_used","is_bar_used",
                 "is_swimming_pool_used","is_work_desk_used","is_meeting_room_used"]
    existing = [c for c in amen_cols if c in bookings.columns]
    bookings["amenity_count"] = bookings[existing].sum(axis=1)

    # price sensitivity
    bookings["is_price_sensitive"] = bookings["market_segment"].astype(str).str.lower().isin(
        ["online ta","offline ta/to","ta/to","ta","ota"]
    ).astype(int)

    # last-minute
    bookings["is_last_minute"] = (bookings["lead_time"] <= 3).astype(int)

    return bookings


def month_num(m_lc: str) -> int:
    return MONTH_TO_NUM[m_lc]


def match_customers_for_month(
    bookings: pd.DataFrame,
    hotel_norm: str,
    month_name: str,
    room_type: str,
    financials: pd.DataFrame
) -> pd.DataFrame:
    """
    Pick past guests who stayed in the same month at this hotel *and* in the same room type,
    and assign the earliest *future* month-year for that hotel+room_type from financials.
    """
    m_lc = month_name.lower()
    m_num = month_num(m_lc)

    # Financial periods available for this hotel + room_type
    avail = financials[
        (financials["hotel_norm"] == hotel_norm) &
        (financials["room_type"] == room_type)
    ][["month", "year"]].drop_duplicates()

    if avail.empty:
        return pd.DataFrame()  # no plan for this room type at this hotel

    # Attach numeric month for matching
    avail["month_num"] = avail["month"].str.lower().map(month_num)
    same_month = avail[avail["month_num"] == m_num]
    if same_month.empty:
        return pd.DataFrame()  # no plan for this month for that room type

    # Earliest available (year, then month)
    same_month = same_month.sort_values(["year", "month_num"])
    target_period = same_month.iloc[0]
    target_month, target_year = target_period["month"], int(target_period["year"])

    # Build booking helpers
    df = bookings.copy()
    df["stay_month_num"] = df["arrival_date_month_lc"].map(month_num)
    df["stay_date"] = pd.to_datetime({
        "year": df["arrival_date_year"].astype(int),
        "month": df["stay_month_num"],
        "day": 1
    })

    # Past guests at same hotel + month + same room type, before target year
    candidates = df[
        (df["hotel_norm"] == hotel_norm) &
        (df["stay_month_num"] == m_num) &
        (df["reserved_room_type"] == room_type) &
        (df["arrival_date_year"] < target_year)
    ].copy()

    if candidates.empty:
        return pd.DataFrame()

    candidates["target_month"] = target_month
    candidates["target_year"] = target_year
    return candidates



# -------------------------
# 3) SEASON BAND & OCC GAP PER FINANCIAL ROW
# -------------------------
def season_band_from_financial_row(fin_row: pd.Series) -> str:
    """
    Prefer explicit 'booking_percent' if present, else use forecast as a proxy.
    """
    if "booking_percent" in fin_row:
        val = fin_row["booking_percent"]
    elif "forecast_booking_percent" in fin_row:
        val = fin_row["forecast_booking_percent"]
    else:
        # fallback: neutral
        return "shoulder"

    try:
        val = float(val)
    except Exception:
        return "shoulder"

    if val < 50:
        return "low"
    elif val < 75:
        return "shoulder"
    else:
        return "high"


def occupancy_gap(fin_row: pd.Series) -> float:
    tgt = fin_row.get("target_booking_percent", None)
    fc = fin_row.get("forecast_booking_percent", None)
    try:
        return float(tgt) - float(fc)
    except Exception:
        return 0.0


# -------------------------
# 4) PERK SELECTION (with priority & amenity bias)
# -------------------------
def choose_perks(row: pd.Series, seg_conf: dict, fin_row: pd.Series) -> list[str]:
    # Allowed perks only from manager's list
    priority = seg_conf.get("perk_priority", [])
    if not priority:
        priority = ["bar_credit", "gym", "kids_club", "spa", "swimming_pool", "work_desk", "meeting_room"]

    # Build cost map for allowed perks only
    cost_map = {
        perk: float(fin_row.get(PERK_COST_COLS.get(perk, ""), 0) or 0)
        for perk in priority
    }

    # Identify perks guest has used before (and are in allowed list)
    used_perks = [
        perk for perk in priority
        if AMENITY_USAGE_COLS.get(perk) and int(row.get(AMENITY_USAGE_COLS[perk], 0)) == 1
    ]

    # Remaining allowed perks guest hasn’t used yet
    unused_perks = [perk for perk in priority if perk not in used_perks]

    # Final order = used perks first, then unused perks (both restricted to manager's allowed list)
    perk_order = used_perks + unused_perks

    # Add perks while staying under budget
    max_cost = float(seg_conf.get("max_perk_cost", 0) or 0)
    chosen, total = [], 0.0
    for perk in perk_order:
        c = cost_map.get(perk, 0)
        if total + c <= max_cost and c >= 0:
            chosen.append(perk)
            total += c

    return chosen



# -------------------------
# 5) OFFER RULES (baseline + boost + guards)
# -------------------------
def apply_offer_logic(row: pd.Series, seg_conf: dict, fin_row: pd.Series) -> pd.Series:
    # Baseline by season band (low/shoulder/high)
    season = row.get("season_band", "shoulder")
    baseline_map = seg_conf.get("baseline", {})
    base = float(baseline_map.get(season, 0) or 0)

    # Occupancy gap boost
    if float(row.get("occ_gap", 0) or 0) > 10:
        base += float(seg_conf.get("boost_if_high_gap", 0) or 0)

    # Floor for price sensitive segments
    if int(row.get("is_price_sensitive", 0)) == 1:
        base = max(base, float(baseline_map.get("low", base) or base))

    # Loyalty tweak: small discount reduction in favour of perk
    if int(row.get("is_repeated_guest", 0)) == 1 and base > 0.05:
        base -= 0.02

    # Perk selection
    perks = choose_perks(row, seg_conf, fin_row)

    # ADR vs perk cost guardrail (if costs provided)
    adr_val = float(row.get("adr", 0) or 0)
    perk_total = sum(float(fin_row.get(PERK_COST_COLS.get(p, ""), 0) or 0) for p in perks)
    if adr_val * base > 0.8 * perk_total and perk_total > 0:
        base = 0.0  # prefer perks only

    return pd.Series({
        "discount_pct": round(base * 100, 1),
        "offer_type": "Discount" if base > 0 else "Perk",
        "perks": perks
    })


# -------------------------
# 6) MAIN MONTHLY GENERATION LOOP
# -------------------------
def generate_targets(bookings: pd.DataFrame,
                     financials: pd.DataFrame,
                     segments: list[dict],
                     target_year: int,
                     only_critical: bool = True,
                     gap_threshold: float = 10.0) -> pd.DataFrame:

    fin = financials.copy()
    fin["occ_gap"] = fin["target_booking_percent"] - fin["forecast_booking_percent"]
    if only_critical:
        fin = fin[fin["occ_gap"] > gap_threshold]

    out_frames = []
    for _, fin_row in fin.iterrows():
        hotel_norm = fin_row["hotel_norm"]
        month_name = fin_row["month"]
        room_type = fin_row["room_type"]  # <-- use room type
        season_band = season_band_from_financial_row(fin_row)
        occ_gap_val = occupancy_gap(fin_row)

        # Only match customers whose past stay month + room type fits this financial row
        matched = match_customers_for_month(
            bookings=bookings,
            hotel_norm=hotel_norm,
            month_name=month_name,
            room_type=room_type,
            financials=financials
        )
        if matched.empty:
            continue

        # annotate month-level attrs
        matched = matched.copy()
        matched["season_band"] = season_band
        matched["occ_gap"] = occ_gap_val
        matched["target_month"] = month_name
        matched["target_year"] = int(fin_row["year"])  # month-year coming from fin row
        # Ensure the email-ready 'room_type' equals the plan's room type (and matches guest history)
        matched["room_type"] = matched["reserved_room_type"]  # they match by construction

        # attach offer per row
        def _offer(row):
            seg_conf = next((s for s in segments if int(s["cluster_id"]) == int(row["booking_segment"])), None)
            if not seg_conf:
                return pd.Series({"discount_pct": 0, "offer_type": "None", "perks": []})
            return apply_offer_logic(row, seg_conf, fin_row)

        offers = matched.apply(_offer, axis=1)
        enriched = pd.concat([matched, offers], axis=1)
        out_frames.append(enriched)

    if not out_frames:
        return pd.DataFrame()

    return pd.concat(out_frames, ignore_index=True)

def build_roomtype_preference(bookings: pd.DataFrame) -> pd.DataFrame:
    """
    For each guest (email), count how many times they stayed in each room type
    so we can prefer their most-used type when deduping.
    """
    pref = (
        bookings.groupby(["email", "reserved_room_type"], as_index=False)
        .agg(rt_freq=("id", "count"),
             last_year=("arrival_date_year", "max"),
             avg_lead_time=("lead_time", "mean"))
    )
    # Normalize for merges
    pref["reserved_room_type"] = pref["reserved_room_type"].astype(str).str.strip()
    return pref

def pick_best_month_per_customer(df: pd.DataFrame, bookings: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicate to one offer per customer (email), preferring:
      1) Larger occupancy gap (occ_gap DESC)
      2) Earlier target (year ASC, month ASC)
      3) Guest’s most-used room type historically (rt_freq DESC)
      4) As a tiny final tie-break: higher ADR (if present), else stable order
    """
    if df.empty:
        return df

    # Month to num
    month_to_num = {m: i for i, m in enumerate(
        ["January","February","March","April","May","June",
         "July","August","September","October","November","December"], 1)
    }

    d = df.copy()
    d["target_month_num"] = d["target_month"].map(month_to_num)

    # Build preference from bookings and merge on (email, room_type)
    pref = build_roomtype_preference(bookings)
    # In results, `room_type` equals the guest's `reserved_room_type` by construction.
    d = d.merge(
        pref[["email", "reserved_room_type", "rt_freq"]],
        left_on=["email", "room_type"],
        right_on=["email", "reserved_room_type"],
        how="left"
    )
    d["rt_freq"] = d["rt_freq"].fillna(0)

    # Sorting priority:
    #   occ_gap DESC → bigger gap first
    #   target_year ASC → earlier year first
    #   target_month_num ASC → earlier month first
    #   rt_freq DESC → guest’s most-used room type first
    #   adr DESC (optional micro tie-break if present)
    sort_cols = ["email", "occ_gap", "target_year", "target_month_num", "rt_freq"]
    ascending = [True, False, True, True, False]

    # If ADR exists, add it as a final tie-breaker (DESC)
    if "adr" in d.columns:
        sort_cols.append("adr")
        ascending.append(False)

    d = d.sort_values(by=sort_cols, ascending=ascending)

    # Keep first per email
    best = d.groupby("email", as_index=False).first()

    # Clean up helper columns
    drop_cols = [c for c in ["reserved_room_type_y", "target_month_num", "rt_freq"] if c in best.columns]
    return best.drop(columns=drop_cols, errors="ignore")


# -------------------------
# 7) EMAIL/NLP-READY OUTPUT
# -------------------------
def prepare_email_ready_output(df: pd.DataFrame) -> pd.DataFrame:
    # Expose reserved_room_type as room_type
    if "reserved_room_type" in df.columns and "room_type" not in df.columns:
        df = df.copy()
        df["room_type"] = df["reserved_room_type"]

    # Map amenity usage columns to human-readable names
    amenity_map = {
        "is_spa_used": "spa",
        "is_gym_used": "gym",
        "is_kids_club_used": "kids_club",
        "is_bar_used": "bar",
        "is_swimming_pool_used": "swimming_pool",
        "is_work_desk_used": "work_desk",
        "is_meeting_room_used": "meeting_room",
        "is_gaming_room_used": "gaming_room"
    }

    # Extract amenities used before for each customer
    def extract_used_amenities(row):
        return [name for col, name in amenity_map.items() if int(row.get(col, 0)) == 1]

    df["amenities_used_before"] = df.apply(extract_used_amenities, axis=1)

    
    # Columns to include in final output
    cols = [
        "id", "booking_segment_record_id",
        "name", "email", "phone_number",
        "hotel", "room_type", "meal", "country",
        "booking_segment", "business_label",
        "target_month", "target_year",
        "discount_pct", "offer_type", "perks",
        "amenities_used_before"
    ]
    
    # Validate all required columns exist
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Output is missing columns: {missing}")

    return df[cols]



# -------------------------
# 8) RUN
# -------------------------
def genrate_personalised_discounts(email, discountConfig):
    bookings, financials = load_inputs(email)
    segments = discountConfig
    bookings = add_features(bookings)

    result = generate_targets(
        bookings=bookings,
        financials=financials,
        segments=segments,
        target_year=2025,
        only_critical=False,
        gap_threshold=10.0
    )

    if result.empty:
        return {"success": False, "message": "No discount offers generated."}

    final_best = pick_best_month_per_customer(result, bookings)
    final_ready = prepare_email_ready_output(final_best)

    # Optional: save a CSV for debugging
    final_ready.to_csv("final_discount_targets2.csv", index=False)
    print(f"Saved final_discount_targets.csv with {len(final_ready)} rows.")

    offers_list = final_ready.to_dict(orient="records")

    response = save_discount_offers_to_db(email, offers_list)
    return response



def save_discount_config_to_db(email, discount_config):
    try:
        # Step 1: fetch user_id
        user_res = supabase.table("users").select("user_id").eq("email", email).limit(1).execute()
        if not user_res.data:
            return {"success": False, "message": f"No user found with email: {email}"}

        user_id = user_res.data[0]["user_id"]
        

        # Step 2: deactivate previous active rows for this user
        supabase.table("discount_config") \
            .update({"is_active": False}) \
            .eq("user_id", user_id) \
            .eq("is_active", True) \
            .execute()

        # Step 3: build rows for insert (one per segment)
        rows = []
        for seg in discount_config:
            rows.append({
                "user_id": user_id,
                "cluster_id": seg["cluster_id"],
                "business_label": seg["business_label"],
                "baseline_low": seg["baseline"]["low"],
                "baseline_shoulder": seg["baseline"]["shoulder"],
                "baseline_high": seg["baseline"]["high"],
                "boost_if_high_gap": seg["boost_if_high_gap"],
                "max_perk_cost": seg["max_perk_cost"],
                "perk_priority": seg["perk_priority"],
                "is_active": True,
            })

        # Step 4: insert new active rows
        insert_res = supabase.table("discount_config").insert(rows).execute()

        if not insert_res.data:
            return {
                "success": False,
                "message": f"Insert error: {insert_res.error.message}"
            }

        return {
            "success": True,
            "message": "Discount configuration saved.",
            "inserted_rows": len(insert_res.data),
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error saving discount configuration: {str(e)}"
        }
        
def save_discount_offers_to_db(email: str, discount_offers: list):
    try:
        # Step 1: Fetch user_id from users table
        user_res = supabase.table("users").select("user_id").eq("email", email).execute()
        if not user_res.data:
            return {"success": False, "message": f"No user found with email: {email}"}

        user_id = user_res.data[0]["user_id"]

        # Step 2: Mark existing discount offers as inactive for this user
        supabase.table("discount_offers").update({"is_active": False}).eq("user_id", user_id).execute()

        # Step 3: Prepare new records for insertion
        records = []
        for offer in discount_offers:
            records.append({
                "booking_id": offer.get("id"),
                "booking_segment_record_id": offer.get("booking_segment_record_id"),
                "user_id": user_id,
                "name": offer.get("name"),
                "email": offer.get("email"),
                "phone_number": offer.get("phone_number"),
                "hotel": offer.get("hotel"),
                "room_type": offer.get("room_type"),
                "meal": offer.get("meal"),
                "country": offer.get("country"),
                "booking_segment": offer.get("booking_segment"),
                "business_label": offer.get("business_label"),
                "target_month": offer.get("target_month"),
                "target_year": offer.get("target_year"),
                "discount_pct": offer.get("discount_pct"),
                "offer_type": offer.get("offer_type"),
                "perks": offer.get("perks"),
                "amenities_used_before": offer.get("amenities_used_before"),
                "is_active": True
            })

        # Step 4: Insert into discount_offers table
        insert_res = supabase.table("discount_offers").insert(records).execute()

        if insert_res.data:
            return {"success": True, "inserted_rows": len(insert_res.data)}
        else:
            return {"success": False, "message": f"Insert failed: {insert_res.error}"}

    except Exception as e:
        return {"success": False, "message": f"Error saving discount offers: {str(e)}"}

    

    
    
    
