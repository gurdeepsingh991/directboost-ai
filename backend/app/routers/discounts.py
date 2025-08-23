
from fastapi import APIRouter, Query, Body
from app.services.discounts import genrate_personalised_discounts,save_discount_config_to_db
from starlette.concurrency import run_in_threadpool
import pandas as pd
from app.db.supabase_client import supabase
from collections import Counter
from fastapi.encoders import jsonable_encoder
import numpy as np
router = APIRouter()

@router.post('/genrate_discounts')
async def genrate_discounts(payload: dict = Body(...)):
    email = payload.get("email")
    discount_config = payload.get("config")

    if not email or not discount_config:
        return {"success": False, "message": "Email and config are required."}

    def sync_task():
        config_result = save_discount_config_to_db(email, discount_config)
        if not config_result.get("success"):
            return {"success": False, "message": "Failed to save discount configuration."}
        offers_result = genrate_personalised_discounts(email, discount_config)
        return {"success": True, "config_result": config_result, "offers_result": offers_result}

    return await run_in_threadpool(sync_task)


@router.get("/summary")
async def get_discount_summary(email: str = Query(...)):
    """
    Aggregated summary of discount offers (overall → segment → room → month)
    with robust deduplication to prevent inflated counts after joins.
    """
    try:
        # 1) Resolve user_id
        user_res = supabase.table("users").select("user_id").eq("email", email).execute()
        if not user_res.data:
            return {"success": False, "message": f"No user found with email: {email}"}
        user_id = user_res.data[0]["user_id"]

        # 2) Pull active offers
        offers_res = supabase.table("discount_offers").select("*").eq("user_id", user_id).eq("is_active", True).execute()
        if not offers_res.data:
            return {"success": False, "message": "No active discount offers found."}

        offers_raw = pd.DataFrame(offers_res.data)

        # ---- Normalize & build a stable offer key (dedupe BEFORE any merge)
        # Normalize email/hotel/room_type to reduce accidental dupes
        offers_raw["email_norm"] = offers_raw["email"].astype(str).str.strip().str.lower()
        offers_raw["hotel_norm"] = offers_raw["hotel"].astype(str).str.strip().str.lower()
        offers_raw["room_type"]  = offers_raw["room_type"].astype(str).str.strip()

        # Compose a business key; include booking_id if present
        key_cols = [
            "booking_id",           # safe if present; pandas will handle NaN→'nan'
            "email_norm",
            "hotel_norm",
            "room_type",
            "target_month",
            "target_year",
            "discount_pct",
            "offer_type",
        ]
        # Ensure all key cols exist
        for c in key_cols:
            if c not in offers_raw.columns:
                offers_raw[c] = np.nan

        offers_raw["offer_key"] = offers_raw[key_cols].astype(str).agg("|".join, axis=1)

        # Dedup to unique offers
        offers = offers_raw.drop_duplicates(subset=["offer_key"]).reset_index(drop=True)

        # 3) Fetch financials and deduplicate to a single ADR per (hotel, room, month, year)
        fin_res = supabase.table("financials").select("*").eq("user_id", user_id).execute()
        fin_df = pd.DataFrame(fin_res.data) if fin_res.data else pd.DataFrame()

        if not fin_df.empty:
            fin_df["hotel_norm"] = fin_df["hotel_name"].astype(str).str.strip().str.lower()
            fin_df["room_type"] = fin_df["room_type"].astype(str).str.strip()

            # Prefer the most recent record if created_at exists; otherwise first occurrence
            sort_cols = ["hotel_norm", "room_type", "year", "month"]
            if "created_at" in fin_df.columns:
                fin_df = fin_df.sort_values(sort_cols + ["created_at"], ascending=[True, True, True, True, False])
            else:
                fin_df = fin_df.sort_values(sort_cols, ascending=[True, True, True, True])

            fin_dedup = (
                fin_df
                .drop_duplicates(subset=["hotel_norm", "room_type", "month", "year"], keep="first")
                [["hotel_norm", "room_type", "month", "year", "adr"]]
                .rename(columns={"adr": "base_adr"})
            )
        else:
            fin_dedup = pd.DataFrame(columns=["hotel_norm", "room_type", "month", "year", "base_adr"])

        # 4) Merge ADR (this will NOT multiply rows thanks to fin_dedup)
        offers_adr = offers.merge(
            fin_dedup,
            left_on=["hotel_norm", "room_type", "target_month", "target_year"],
            right_on=["hotel_norm", "room_type", "month", "year"],
            how="left"
        )

        # 5) Compute post-discount ADR safely
        offers_adr["discount_pct"] = pd.to_numeric(offers_adr["discount_pct"], errors="coerce").fillna(0.0)
        offers_adr["base_adr"] = pd.to_numeric(offers_adr["base_adr"], errors="coerce")
        offers_adr["post_discount_adr"] = offers_adr.apply(
            lambda r: round(r["base_adr"] * (1 - r["discount_pct"] / 100.0), 2)
            if pd.notnull(r.get("base_adr")) else None,
            axis=1
        )

        # Helper for perks (ensure list type)
        def _ensure_list(x):
            if isinstance(x, list):
                return x
            if pd.isna(x):
                return []
            # Handle JSON-stringified lists or scalars
            try:
                import json
                v = json.loads(x)
                return v if isinstance(v, list) else [v]
            except Exception:
                return [x]

        if "perks" in offers_adr.columns:
            offers_adr["perks"] = offers_adr["perks"].apply(_ensure_list)
        else:
            offers_adr["perks"] = [[] for _ in range(len(offers_adr))]

        # 6) Build the summary using the DEDUPED offers_adr
        overall = {
            "total_offers": int(len(offers_adr)),  # deduped count
            "avg_discount_pct": round(float(offers_adr["discount_pct"].mean()), 2) if len(offers_adr) else 0.0,
            "avg_base_adr": round(float(offers_adr["base_adr"].mean()), 2) if offers_adr["base_adr"].notnull().any() else None,
            "avg_post_discount_adr": round(float(offers_adr["post_discount_adr"].mean()), 2) if offers_adr["post_discount_adr"].notnull().any() else None,
        }

        # Segment → Room → Month breakdowns
        segments_summary = []
        by_seg = offers_adr.groupby(["booking_segment", "business_label"], dropna=False)
        for (seg_id, seg_label), seg_df in by_seg:
            # most common perks
            flat_perks = []
            for p in seg_df["perks"]:
                flat_perks.extend(p if isinstance(p, list) else [])
            most_common_perks = [perk for perk, _ in Counter(flat_perks).most_common()]

            seg_block = {
                "segment_id": int(seg_id) if pd.notnull(seg_id) else None,
                "business_label": seg_label,
                "offers_count": int(len(seg_df)),
                "avg_discount_pct": round(float(seg_df["discount_pct"].mean()), 2) if len(seg_df) else 0.0,
                "avg_base_adr": round(float(seg_df["base_adr"].mean()), 2) if seg_df["base_adr"].notnull().any() else None,
                "avg_post_discount_adr": round(float(seg_df["post_discount_adr"].mean()), 2) if seg_df["post_discount_adr"].notnull().any() else None,
                "most_common_perks": most_common_perks,
                "rooms": []
            }

            for room_type, room_df in seg_df.groupby("room_type", dropna=False):
                room_block = {
                    "room_type": room_type,
                    "offers_count": int(len(room_df)),
                    "avg_discount_pct": round(float(room_df["discount_pct"].mean()), 2) if len(room_df) else 0.0,
                    "avg_base_adr": round(float(room_df["base_adr"].mean()), 2) if room_df["base_adr"].notnull().any() else None,
                    "avg_post_discount_adr": round(float(room_df["post_discount_adr"].mean()), 2) if room_df["post_discount_adr"].notnull().any() else None,
                    "months": []
                }

                for (month, year), month_df in room_df.groupby(["target_month", "target_year"], dropna=False):
                    month_block = {
                        "month": month,
                        "year": int(year) if pd.notnull(year) else None,
                        "offers_count": int(len(month_df)),
                        "avg_discount_pct": round(float(month_df["discount_pct"].mean()), 2) if len(month_df) else 0.0,
                        "avg_base_adr": round(float(month_df["base_adr"].mean()), 2) if month_df["base_adr"].notnull().any() else None,
                        "avg_post_discount_adr": round(float(month_df["post_discount_adr"].mean()), 2) if month_df["post_discount_adr"].notnull().any() else None
                    }
                    room_block["months"].append(month_block)

                seg_block["rooms"].append(room_block)

            segments_summary.append(seg_block)

        summary = {
            "success": True,
            "overall": overall,
            "segments": segments_summary
        }

        # JSON-safe (cast NumPy → native)
        return jsonable_encoder(
            summary,
            custom_encoder={
                np.int64: int,
                np.int32: int,
                np.float64: float,
                np.float32: float
            }
        )

    except Exception as e:
        return {"success": False, "message": f"Error generating discount summary: {str(e)}"}


