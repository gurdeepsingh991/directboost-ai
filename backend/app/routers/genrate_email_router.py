from fastapi import APIRouter,Query,Form
from app.services.genrate_email import generate_emails ,fetch_campaign_stats,fetch_email_preview
from pydantic import BaseModel
from typing import List

router = APIRouter()

class CampaignGenerateRequest(BaseModel):
    email: str
    year: int
    months: List[int]  # list of integers
    
class GetCampaignPreview(BaseModel):
    campaign_id:str

@router.post("/generate-email")
def generate_email(req: CampaignGenerateRequest):
    email= req.email
    months = req.months
    year = req.year
    response = generate_emails(email,months,year)
    return response

@router.post("/get-email-campaigns")
def get_campaigns_and_filters( email: str = Form(...)):
    response = fetch_campaign_stats(email)
    return response

@router.post("/get-email-preview")
def get_email_preview_router(req:GetCampaignPreview):
    response = fetch_email_preview(req.campaign_id)
    return response
