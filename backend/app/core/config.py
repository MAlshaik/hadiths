import os
from typing import List

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings"""
    
    # API settings
    API_VERSION: str = os.getenv("API_VERSION", "v1")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    
    # CORS settings
    _cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    CORS_ORIGINS: List[str] = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]
    
    # Supabase settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # Data collection settings
    SUNNAH_API_KEY: str = os.getenv("SUNNAH_API_KEY", "")
    SCRAPER_DELAY: int = int(os.getenv("SCRAPER_DELAY", "3"))
    USER_AGENT: str = os.getenv("USER_AGENT", "Hadith-Similarity-Search/1.0")

# Create a single instance of Settings
settings = Settings()
