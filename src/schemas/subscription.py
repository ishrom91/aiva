"""Pydantic schemas for subscription operations."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SubscriptionCreate(BaseModel):
    """Schema for creating a new subscription."""

    master_id: str
    tariff_name: str
    monthly_bookings_limit: int
    current_period_start: datetime
    current_period_end: datetime
    is_trial: bool = False


class SubscriptionResponse(BaseModel):
    """Schema for subscription response."""

    id: str
    master_id: str
    tariff_name: str
    status: str
    monthly_bookings_limit: int
    current_period_start: datetime
    current_period_end: datetime
    is_trial: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
