
from fastapi import APIRouter, Form
from app.services.segments import generate_segments, get_latest_segment_profiles

router = APIRouter()
#GS: add email from ui
@router.post("/genrate-segments")
def genrate_customer_segments( email: str = Form(...)):
   #email = "thisisgurdeep@gmail.com"
   response = generate_segments(email)
   return response
   
@router.get("/get-segment-profiles")
def get_segment_profiles():
   response = get_latest_segment_profiles()
   return response