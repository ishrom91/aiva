"""Data API client model for enterprise data buyers."""

from enum import Enum

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class APITier(Enum):
    """Enum for API tier levels."""

    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class DataAPIClient(Base, UUIDMixin, TimestampMixin):
    """Model for data API clients (enterprise customers)."""

    __tablename__ = "data_api_clients"

    company_name: Mapped[str] = mapped_column(String)
    contact_email: Mapped[str] = mapped_column(String)
    api_tier: Mapped[APITier] = mapped_column(
        String
    )  # Using String to store enum value
    monthly_quota: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
