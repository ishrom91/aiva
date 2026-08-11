"""Configuration settings for Aiva AI Bot."""

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


settings = Settings()  # type: ignore[call-arg]
