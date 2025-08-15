
from fastapi import APIRouter, Form
from backend.app.services.discounts import genrate_personalised_discounts

router = APIRouter()

@router.get('/genrate_discounts')
def genrate_discounts():
    response = genrate_personalised_discounts()
    return response

