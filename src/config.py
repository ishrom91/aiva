"""Configuration settings for Aiva AI Bot."""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",
        case_sensitive=False,
    )

    # Required settings
    BOT_TOKEN: str
    DATABASE_URL: str
    ENCRYPTION_KEY: str
    WEBHOOK_URL: str | None = None

    # Optional settings with defaults
    ENVIRONMENT: str = "development"
    REDIS_URL: str = "redis://redis:6379/0"
    LOG_LEVEL: str = "INFO"
    CLIENT_HASH_SALT: str = ""
    DATA_COLLECTION_ENABLED: bool = True
    DATA_COLLECTION_LOG_TEXT: bool = False
    SUBSCRIPTION_CHECK_INTERVAL: int = 3600
    TELEGRAM_WEBHOOK_SECRET: str | None = None
    DATA_API_ENABLED: bool = False
    DATA_API_RATE_LIMIT_DEFAULT: int = 100
    ASSETS_BRAND_DIR: str = "assets/brand"
    ASSETS_BOT_DIR: str = "assets/bot"
    BOT_ASSET_FILE_IDS: dict = {}
    TELEGRAM_PROXY: str | None = None

    # Phase 2: AI & retention
    YANDEX_FOLDER_ID: str | None = None
    YANDEX_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    AI_FAQ_ENABLED: bool = True
    REMINDER_HOURS_BEFORE: int = 24
    WINBACK_DAYS: int = 60

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        """Fail fast on unsafe or incomplete production configuration."""
        if self.ENVIRONMENT.lower() != "production":
            return self

        errors: list[str] = []
        if not self.WEBHOOK_URL or not self.WEBHOOK_URL.startswith("https://"):
            errors.append("WEBHOOK_URL must be a full HTTPS URL")
        if not self.TELEGRAM_WEBHOOK_SECRET or len(self.TELEGRAM_WEBHOOK_SECRET) < 16:
            errors.append("TELEGRAM_WEBHOOK_SECRET must contain at least 16 characters")
        if len(self.CLIENT_HASH_SALT) < 16:
            errors.append("CLIENT_HASH_SALT must contain at least 16 characters")
        if not self.DATABASE_URL.startswith("postgresql+asyncpg://"):
            errors.append("DATABASE_URL must use postgresql+asyncpg in production")
        if not self.REDIS_URL:
            errors.append("REDIS_URL is required in production")
        if self.DATA_COLLECTION_LOG_TEXT:
            errors.append("DATA_COLLECTION_LOG_TEXT must be false in production")

        if errors:
            raise ValueError("Invalid production configuration: " + "; ".join(errors))
        return self


settings = Settings()  # type: ignore[call-arg]
