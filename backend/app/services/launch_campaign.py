# services/launch_service.py
from uuid import uuid4
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.db.supabase_client import supabase


def launch_campaign(
    user_email: str,
    campaign: Dict[str, Any],
    scope: Dict[str, Any],
    email_campaign_ids: List[str],
    schedule: Dict[str, Any],
    compliance: Dict[str, bool],
):
    """
    Orchestrates the full launch flow:
      1. Create marketing campaign
      2. Create campaign batch
      3. Attach selected emails
      4. Queue send job
    """
    try:
        # 0. Get user_id
        user_res = supabase.table("users").select("user_id").eq("email", user_email).limit(1).execute()
        if not user_res.data:
            return {"success": False, "message": f"User not found: {user_email}"}
        user_id = user_res.data[0]["user_id"]

        # 1. Create marketing campaign
        campaign_id = str(uuid4())
        campaign_record = {
            "id": campaign_id,
            "user_id": user_id,
            "name": campaign.get("name"),
            "description": campaign.get("description"),
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        res = supabase.table("marketing_campaigns").insert(campaign_record).execute()
        if not res.data:
            return {"success": False, "message": f"Failed to create campaign: {res.error}"}

        # 2. Create batch
        batch_id = str(uuid4())
        batch_record = {
            "id": batch_id,
            "marketing_campaign_id": campaign_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        res = supabase.table("campaign_batches").insert(batch_record).execute()
        if not res.data:
            return {"success": False, "message": f"Failed to create batch: {res.error}"}

        # 3. Attach selected emails
        if email_campaign_ids:
            attach_rows = [
                {"id": str(uuid4()), "batch_id": batch_id, "email_campaign_id": cid}
                for cid in email_campaign_ids
            ]
            res = supabase.table("campaign_batch_emails").insert(attach_rows).execute()
            if not res.data:
                return {"success": False, "message": f"Failed to attach emails: {res.error}"}

            # 3b. Mark those email_campaigns as launched
            supabase.table("email_campaigns").update({"status": "launched"}).in_("id", email_campaign_ids).execute()

        # 4. Queue send job
        queue_record = {
            "id": str(uuid4()),
            "batch_id": batch_id,
            "mode": schedule.get("mode"),
            "schedule_at": schedule.get("schedule_at"),
            "timezone": schedule.get("timezone", "Europe/London"),
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "meta": {"scope": scope, "compliance": compliance},
        }
        res = supabase.table("send_queue").insert(queue_record).execute()
        if not res.data:
            return {"success": False, "message": f"Failed to queue campaign: {res.error}"}

        # 5. Update campaign status -> launched
        supabase.table("marketing_campaigns").update({"status": "launched"}).eq("id", campaign_id).execute()

        return {
            "success": True,
            "marketing_campaign_id": campaign_id,
            "batch_id": batch_id,
            "queued_count": len(email_campaign_ids),
            "message": "Campaign queued successfully",
        }

    except Exception as e:
        return {"success": False, "message": f"Launch error: {str(e)}"}


