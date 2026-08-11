"""Subscription model representing master's subscription plans."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .master import Master


class SubscriptionStatus(Enum):
    """Enum for subscription statuses."""

    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Subscription(Base, UUIDMixin, TimestampMixin):
    """Model for master subscriptions."""

    __tablename__ = "subscriptions"

    master_id: Mapped[str] = mapped_column(
        String, ForeignKey("masters.id"), unique=True
    )
    tariff_name: Mapped[str] = mapped_column(String)
    status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE
    )
    monthly_bookings_limit: Mapped[int] = mapped_column(Integer)
    additional_skills: Mapped[dict | None] = mapped_column(
        String
    )  # JSON in string form
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_trial: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    master: Mapped["Master"] = relationship(back_populates="subscriptions")
