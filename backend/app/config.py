import os
from dotenv import load_dotenv

load_dotenv()

# Groq AI
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# App
ALLOWED_ORIGINS = ["http://localhost:5173"]

# subscription message limits per month
SUBSCRIPTION_LIMITS = {
    "free": 10,
    "plus": 100,
    "pro": None,  # None means unlimited
}
