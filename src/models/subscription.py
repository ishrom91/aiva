from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel
from enum import Enum
import datetime
import uuid


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Subscription(BaseModel):
    """Model representing a master's subscription to a tariff"""
    __tablename__ = "subscriptions"
    
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.id"), unique=True, index=True)
    tariff_name: Mapped[str] = mapped_column(String(50))  # 'start', 'pro', 'salon'
    status: Mapped[SubscriptionStatus] = mapped_column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    monthly_bookings_limit: Mapped[int]  # 50 for Start, 200 for Pro, -1 for Salon (unlimited)
    additional_skills: Mapped[dict] = mapped_column(default=dict)  # ["retention", "marketing"] for Pro/Salon
    current_period_start: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    is_trial: Mapped[bool] = mapped_column(default=False)
    
    # Relationship
    master: Mapped["Master"] = relationship("Master", back_populates="subscription")
    
    __table_args__ = (
        # Indexes
        {"postgresql_using": "btree", "columns": ["master_id"]},
        {"postgresql_using": "btree", "columns": ["status"]},
        {"postgresql_using": "btree", "columns": ["current_period_end"]},
    )