from app.db.supabase_client import supabase

async def signup(email:str) -> dict:
    try:
        response = supabase.table("users").select("user_id").eq("email", email).execute()
        
        if response.data:
            return {"message": "User already exists", "status": True, "user_id": response.data[0]["user_id"]}
        
        # Create user if not found
        insert_response = supabase.table("users").insert({"email": email}).execute()

        if insert_response.data:
            return {"message": "User created successfully", "status": True, "user_id": insert_response.data[0]["user_id"]}
        else:
            return {"message": "Failed to create user", "status": False}
    except Exception as e:
        return {"message": f"Something went wrong, error {str(e)}", "status":False}
    
async def login(email:str)-> dict:
    try:
        # Try to find user
        response = supabase.table("users").select("user_id").eq("email", email).execute()

        if response.data:
            return {"message": "Login successful", "status": True, "user_id": response.data[0]["user_id"]}
        
        # No user found, don't auto-create on login
        return {"message": "No user exists with this email. Please signup.", "status": False}

    except Exception as e:
        return {"message": f"Something went wrong: {str(e)}", "status": False}