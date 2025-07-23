from fastapi import APIRouter, File, UploadFile


router = APIRouter()

@router.post("/uploadbookingfile")
async def upload_file (file:UploadFile= File(None)):
    if not file:
        return {"message": "no file uploaded"}
    else:
        return {"uploaded file name": file.filename}
    
@router.post("uploadfinancesfile")
async def upload_finance_file (file:UploadFile= File(None)):
    if not file:
        return {"message": "no file uploaded"}
    else:
        return {"uploaded file name": file.filename}
    