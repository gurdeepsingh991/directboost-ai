from app.db.supabase_client import supabase
from app.config import BUCKET_NAME
import joblib
from io import BytesIO

def get_pretrained_model(model_name: str):
    try:
        # Get latest version folder
        version = get_latest_model_version()
        if not version:
            raise ValueError("Unable to fetch latest model version")

        path = f"{version}/{model_name}"
        response = supabase.storage.from_(BUCKET_NAME).download(path)

        # Load the model from the downloaded bytes
        buffer = BytesIO(response)
        model = joblib.load(buffer)

        return {
            "success": True,
            "model": model,
            "model_version": version
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Unable to retrieve {model_name}: {e}"
        }
    
def get_latest_model_version():
    try:
        response = supabase.storage.from_(BUCKET_NAME).list("")

        # Filter only folders: metadata is None or empty
        folders = [
            item['name']
            for item in response
            if not item.get("metadata")  # safely excludes files like .pkl
        ]

        if not folders:
            raise ValueError("No model version folders found in bucket.")

        latest = sorted(folders, reverse=True)[0]
        return latest

    except Exception as e:
        print(f" Failed to get model version: {e}")
        return None

