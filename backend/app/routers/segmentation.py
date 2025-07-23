
from fastapi import APIRouter

router = APIRouter()

@router.get("/hello")
def hello_segment():
    return {"message": "Segmentation route is working!"}