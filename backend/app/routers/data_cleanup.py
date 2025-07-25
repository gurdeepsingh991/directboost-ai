from fastapi import APIRouter, File, UploadFile,Form
from app.db.supabase_client import supabase
from app.services.data_cleanup import clean_booking_data


router = APIRouter()


@router.post("/uploadbookingfile")
async def upload_file (file: UploadFile = File(...),
    email: str = Form(...)):
   # response = supabase.table("users").select("*").execute() 
   # print(response.data)
    if not file:
        return {"message": "no file found"}
    else:
        df = clean_booking_data (file,email)
        return {"uploaded file name": {file.filename}}
    
@router.post("/uploadfinancesfile")
async def upload_finance_file (file:UploadFile= File(None)):
    if not file:
        return {"message": "no file uploaded"}
    else:
        return {"uploaded file name": file.filename}
    