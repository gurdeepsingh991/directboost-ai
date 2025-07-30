from app.db.supabase_client import supabase
from app.config import BUCKET_NAME
import joblib
from io import BytesIO

def get_pretrained_model(model_name:str):
    
    try:
        response = supabase.storage.from_(BUCKET_NAME).download(model_name)
            
        # Convert to BytesIO and load with joblib
        buffer = BytesIO(response)
        model = joblib.load(buffer)
        
        return {"success": True, "model": model}
     
    except Exception as e: 
        return {"success": False, "message": f"Unable to retrieve {model_name} model {e}"}
    
