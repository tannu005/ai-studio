import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://your-project.supabase.co")
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "your-anon-key")
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "your-service-role-key")
    
    # Resend API Key for Email Notifications
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    FROM_EMAIL = os.environ.get("FROM_EMAIL", "TaskHub <notifications@taskhub.dev>")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@taskhub.dev")
    
    # AI API keys (optional, fallback to local engine if empty)
    FAL_KEY = os.environ.get("FAL_KEY", "")
    REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "")
    
    # Server configuration
    PORT = int(os.environ.get("PORT", 5000))
    DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
    
    # Rate Limiting settings
    RATE_LIMIT_AI_PER_HOUR = 10
    RATE_LIMIT_API_PER_MINUTE = 100
