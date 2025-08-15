
from fastapi import APIRouter, UploadFile, File, Form
from starlette.concurrency import run_in_threadpool
from app.services.financials_data import process_financials_data

router = APIRouter()

@router.post("/uploadfinancials")
async def upload_financials(file: UploadFile = File(...), email: str = Form(...)):
     if not file:
        return {"message": "no file found"}
     else: 
         response = await run_in_threadpool(process_financials_data, file, email)
         return response