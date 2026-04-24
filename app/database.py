from supabase import create_client
from app.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

def get_supabase():
    if not SUPABASE_URL:
        raise RuntimeError("Missing SUPABASE_URL")

    if not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY")

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
