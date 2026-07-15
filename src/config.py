from pydantic_settings import BaseSettings
from typing import Optional
import sys


class Settings(BaseSettings):
    # Bot settings
    BOT_TOKEN: str
    WEBHOOK_URL: Optional[str] = None
    
    # Database settings
    DATABASE_URL: str
    
    # Redis settings
    REDIS_URL: str
    
    # Encryption settings
    ENCRYPTION_KEY: str
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    # Webhook settings
    WEBHOOK_PATH: str = "/webhook"
    WEB_SERVER_HOST: str = "0.0.0.0"
    WEB_SERVER_PORT: int = 8000
    
    # Timezone settings
    TIMEZONE: str = "UTC"
    
    # Data collection settings
    CLIENT_HASH_SALT: str = "aiva_ai_secret_salt_2026_change_this_in_production"
    DATA_COLLECTION_ENABLED: bool = True
    DATA_COLLECTION_LOG_TEXT: bool = False  # Don't log actual message text
    
    # Subscription settings
    SUBSCRIPTION_CHECK_INTERVAL: int = 3600  # Check limits every hour
    
    # API settings
    API_KEY: str = "your_api_key_here"  # Will be set in environment

    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra environment variables


# Initialize settings and validate critical variables
try:
    settings = Settings()
    
    # Validate critical variables
    if not settings.BOT_TOKEN:
        print("ERROR: BOT_TOKEN is not set in environment variables!")
        sys.exit(1)
    
    if not settings.DATABASE_URL:
        print("ERROR: DATABASE_URL is not set in environment variables!")
        sys.exit(1)
    
    if not settings.ENCRYPTION_KEY:
        print("ERROR: ENCRYPTION_KEY is not set in environment variables!")
        sys.exit(1)
        
except Exception as e:
    print(f"ERROR: Failed to load configuration: {str(e)}")
    sys.exit(1)