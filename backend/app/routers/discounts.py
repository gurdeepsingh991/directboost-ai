
from fastapi import APIRouter, Form
from app.services.discounts import _genrate_discounts

router = APIRouter()

@router.get('/')
def genrate_discounts():
    response = _genrate_discounts()
    return response