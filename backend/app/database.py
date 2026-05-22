from supabase import create_client
from app.config import SUPABASE_URL, SUPABASE_KEY

# Initialize the Supabase client - The "Single Source" for the entire app
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_connection():
    try:
        supabase.table("table_user").select("id").limit(1).execute()
        print("Supabase connection successful")
        return True
    except Exception as e:
        print(f"Supabase connection failed: {e}")
        return False
