"""API request log model for tracking data API usage."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin


class APIRequestLog(Base, UUIDMixin):
    """Model for logging API requests to the data API."""

    __tablename__ = "api_request_logs"

    api_key_id: Mapped[str] = mapped_column(String, ForeignKey("api_keys.id"))
    endpoint: Mapped[str] = mapped_column(String)
    method: Mapped[str] = mapped_column(String)
    status_code: Mapped[int] = mapped_column(Integer)
    response_time_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
