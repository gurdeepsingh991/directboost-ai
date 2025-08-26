from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from app.services.launch_campaign import launch_campaign

router = APIRouter()

# ----- Request / Response Models -----
class CampaignMeta(BaseModel):
    name: str = Field(..., min_length=2, max_length=160)
    description: Optional[str] = None

class Scope(BaseModel):
    year: int
    months: List[int]

class Schedule(BaseModel):
    mode: Literal["now", "later", "smart"]
    schedule_at: Optional[str] = None
    timezone: str = "Europe/London"

class LaunchRequest(BaseModel):
    user_email: str
    campaign: CampaignMeta
    scope: Scope
    email_campaign_ids: List[str]
    schedule: Schedule
    compliance: Dict[str, bool] = {}

# ----- Routes -----
@router.post("/launch")
def launch(req: LaunchRequest):
    result = launch_campaign(
        user_email=req.user_email,
        campaign=req.campaign.dict(),
        scope=req.scope.dict(),
        email_campaign_ids=req.email_campaign_ids,
        schedule=req.schedule.dict(),
        compliance=req.compliance,
    )
    return result
