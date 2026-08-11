"""API key model for data API authentication."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class APIKey(Base, UUIDMixin, TimestampMixin):
    """Model for API keys used for data API authentication."""

    __tablename__ = "api_keys"

    data_api_client_id: Mapped[str] = mapped_column(
        String, ForeignKey("data_api_clients.id")
    )
    key_hash: Mapped[str] = mapped_column(
        String, index=True
    )  # Hash of the actual API key
    name: Mapped[str] = mapped_column(String)
    permissions: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # JSON in dict form
    rate_limit: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
