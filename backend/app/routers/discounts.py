
from fastapi import APIRouter, Query, Body
from backend.app.services.discounts import genrate_personalised_discounts,save_discount_config_to_db
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
    Fetch discount offers for a user and return aggregated summary:
    overall → segment → room → month
    """
    try:
        # 1️⃣ Get user_id
        user_res = supabase.table("users").select("user_id").eq("email", email).execute()
        if not user_res.data:
            return {"success": False, "message": f"No user found with email: {email}"}
        user_id = user_res.data[0]["user_id"]

        # 2️⃣ Fetch discount offers
        offers_res = supabase.table("discount_offers").select("*").eq("user_id", user_id).eq("is_active", True).execute()
        if not offers_res.data:
            return {"success": False, "message": "No active discount offers found."}

        offers_df = pd.DataFrame(offers_res.data)

        # 3️⃣ Fetch ADR from financials
        fin_res = supabase.table("financials").select("*").eq("user_id", user_id).execute()
        fin_df = pd.DataFrame(fin_res.data) if fin_res.data else pd.DataFrame()

        if not fin_df.empty and "room_type" in fin_df.columns:
            fin_df["hotel_norm"] = fin_df["hotel_name"].str.lower().str.strip()
            offers_df["hotel_norm"] = offers_df["hotel"].str.lower().str.strip()

            offers_df = offers_df.merge(
                fin_df[["hotel_norm", "room_type", "month", "year", "adr"]].rename(columns={"adr": "base_adr"}),
                left_on=["hotel_norm", "room_type", "target_month", "target_year"],
                right_on=["hotel_norm", "room_type", "month", "year"],
                how="left"
            )

        if "base_adr" not in offers_df.columns:
            offers_df["base_adr"] = None

        # 4️⃣ Post-discount ADR
        offers_df["discount_pct"] = pd.to_numeric(offers_df["discount_pct"], errors="coerce").fillna(0)
        offers_df["post_discount_adr"] = offers_df.apply(
            lambda row: round(row["base_adr"] * (1 - row["discount_pct"] / 100), 2)
            if pd.notnull(row["base_adr"]) else None,
            axis=1
        )

        # 5️⃣ Summary dict
        summary = {
            "success": True,
            "overall": {
                "total_offers": len(offers_df),
                "avg_discount_pct": round(offers_df["discount_pct"].mean(), 2),
                "avg_base_adr": round(offers_df["base_adr"].mean(), 2) if offers_df["base_adr"].notnull().any() else None,
                "avg_post_discount_adr": round(offers_df["post_discount_adr"].mean(), 2) if offers_df["post_discount_adr"].notnull().any() else None
            },
            "segments": []
        }

        for (seg_id, seg_label), seg_df in offers_df.groupby(["booking_segment", "business_label"]):
            seg_summary = {
                "segment_id": int(seg_id),
                "business_label": seg_label,
                "offers_count": int(len(seg_df)),
                "avg_discount_pct": round(seg_df["discount_pct"].mean(), 2),
                "avg_base_adr": round(seg_df["base_adr"].mean(), 2) if seg_df["base_adr"].notnull().any() else None,
                "avg_post_discount_adr": round(seg_df["post_discount_adr"].mean(), 2) if seg_df["post_discount_adr"].notnull().any() else None,
                "most_common_perks": [perk for perk, _ in Counter(sum(seg_df["perks"], [])).most_common()],
                "rooms": []
            }

            for room_type, room_df in seg_df.groupby("room_type"):
                room_summary = {
                    "room_type": room_type,
                    "offers_count": int(len(room_df)),
                    "avg_discount_pct": round(room_df["discount_pct"].mean(), 2),
                    "avg_base_adr": round(room_df["base_adr"].mean(), 2) if room_df["base_adr"].notnull().any() else None,
                    "avg_post_discount_adr": round(room_df["post_discount_adr"].mean(), 2) if room_df["post_discount_adr"].notnull().any() else None,
                    "months": []
                }

                for (month, year), month_df in room_df.groupby(["target_month", "target_year"]):
                    month_summary = {
                        "month": month,
                        "year": int(year),
                        "offers_count": int(len(month_df)),
                        "avg_discount_pct": round(month_df["discount_pct"].mean(), 2),
                        "avg_base_adr": round(month_df["base_adr"].mean(), 2) if month_df["base_adr"].notnull().any() else None,
                        "avg_post_discount_adr": round(month_df["post_discount_adr"].mean(), 2) if month_df["post_discount_adr"].notnull().any() else None
                    }
                    room_summary["months"].append(month_summary)

                seg_summary["rooms"].append(room_summary)

            summary["segments"].append(seg_summary)

        # ✅ Convert NumPy to native Python
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

