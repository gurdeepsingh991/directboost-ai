
from fastapi import APIRouter, Form
from app.services.segments import genrate_segments

router = APIRouter()
#GS: add email from ui
@router.get("/genrate-segments")
def genrate_customer_segments():
   email = "thisisgurdeep@gmail.com"
   response = genrate_segments(email)