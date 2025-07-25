from dotenv import load_dotenv
from pathlib import Path
import os 

env_path = Path(__file__).resolve().parents[1]/".env"
load_dotenv(dotenv_path= env_path)

SUPABASE_URL:str = os.getenv("SUPABASE_URL")
SUPABASE_KEY:str = os.getenv("SUPABASE_KEY")