"""Safety checks for production configuration."""

import pytest

from src.config import Settings


def production_values() -> dict[str, str | bool]:
    return {
        "BOT_TOKEN": "000000000:TEST_TOKEN",
        "DATABASE_URL": "postgresql+asyncpg://aiva:password@postgres:5432/aiva",
        "ENCRYPTION_KEY": "dGVzdC1rZXktdGVzdC1rZXktdGVzdC1rZXktdGVzdGtleTE=",
        "ENVIRONMENT": "production",
        "WEBHOOK_URL": "https://bot.example.ru/webhook",
        "TELEGRAM_WEBHOOK_SECRET": "test-webhook-secret-12345",
        "CLIENT_HASH_SALT": "test-client-hash-salt-12345",
        "REDIS_URL": "redis://redis:6379/0",
        "DATA_COLLECTION_LOG_TEXT": False,
    }


def test_valid_production_configuration() -> None:
    config = Settings(_env_file=None, **production_values())
    assert config.ENVIRONMENT == "production"
    assert config.DATA_COLLECTION_LOG_TEXT is False


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("WEBHOOK_URL", ""),
        ("TELEGRAM_WEBHOOK_SECRET", "short"),
        ("CLIENT_HASH_SALT", "short"),
        ("DATABASE_URL", "sqlite+aiosqlite:///:memory:"),
        ("REDIS_URL", ""),
        ("DATA_COLLECTION_LOG_TEXT", True),
    ],
)
def test_unsafe_production_configuration_is_rejected(
    key: str, value: str | bool
) -> None:
    values = production_values()
    values[key] = value
    with pytest.raises(ValueError, match="Invalid production configuration"):
        Settings(_env_file=None, **values)
