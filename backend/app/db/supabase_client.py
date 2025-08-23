
from app.config import SUPABASE_URL, SUPABASE_SERVICE_KEY

from supabase import create_client, Client

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)    