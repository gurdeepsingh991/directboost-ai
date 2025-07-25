from app.services.user_auth import signup, login
from fastapi import APIRouter,Form

router = APIRouter()

@router.post("/signup")
async def signup_user(email: str = Form(...)):
    response = await signup(email)
    return response

@router.post("/login")
async def login_user(email: str = Form(...)):
    response = await login(email)
    return response

@router.post("/validateuser")
async def validate_user(email: str = Form(...)):
    login_response = await login(email)

    if login_response["status"]:
        return {"success": True, "message": "User exists", "user_id": login_response.get("user_id")}
    else:
        signup_response = await signup(email)
        if signup_response["status"]:
            return {"success": True, "message": "User created", "user_id": signup_response.get("user_id")}
        else:
            return {"success": False, "message": "User creation failed"}
