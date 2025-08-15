from fastapi import UploadFile
import pandas as pd
import io
from app.db.supabase_client import supabase

def load_data(file:UploadFile):
    filename = file.filename.lower()
    if filename.endswith('.csv'):
        content = file.file.read()
        df = pd.read_csv(io.StringIO(content.decode("utf-8")))
    elif filename.endswith(('.xls', '.xlsx')):
        content = file.file.read()
        df = pd.read_excel(io.BytesIO(content))
    else:
        raise ValueError("Unsupported file format. Use CSV or Excel.")
    return df

def save_financial_data_to_db(fianacials,email): 
    try:
        # Step 1: Fetch user ID
        response = supabase.table("users").select("user_id").eq("email", email).execute()

        if not response.data:
            return {"success": False, "message": f"No user found with email: {email}"}

        user_id = response.data[0]["user_id"]
        fianacials["user_id"] = user_id
        
        #Step 2: make all previous booking history as inactive
        response = supabase.table("financials").update({"is_active": False}).eq("user_id",user_id).execute()

        
        
        # Step 3: Convert to list of records
        records = fianacials.to_dict(orient="records")

        # Step 4: Insert into booking_history
        insert_response = supabase.table("financials").insert(records).execute()

        # Step 5: Check for insert errors
        if not insert_response.data:
            return {
                "success": False,
                "message": f"Error inserting financial data: {insert_response.error.message}"
            }
        return {
            "success": True,
            "message": "Booking history file uploaded successfully",
            "inserted_rows": len(insert_response.data)
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Something went wrong while uploading the file. Error: {str(e)}"
        }

def process_financials_data (file: UploadFile, email: str):
    fianacials = load_data(file)
    response = save_financial_data_to_db(fianacials,email )
    return response
    
    