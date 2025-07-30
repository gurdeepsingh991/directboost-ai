from fastapi import APIRouter, File, UploadFile,Form
from app.db.supabase_client import supabase
from starlette.concurrency import run_in_threadpool
from app.services.booking_data import process_booking_data

router = APIRouter()


@router.post("/uploadbookingfile")
async def upload_file (file: UploadFile = File(...),
    email: str = Form(...)):
    if not file:
        return {"message": "no file found"}
    else:
        response = await run_in_threadpool(process_booking_data, file, email)
        return response