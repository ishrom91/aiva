from pydantic import BaseModel as PydanticBaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class TariffName(str, Enum):
    START = "start"
    PRO = "pro"
    SALON = "salon"


class SubscriptionCreateRequest(PydanticBaseModel):
    master_id: int
    tariff_name: TariffName
    monthly_bookings_limit: int
    additional_skills: Optional[List[str]] = None
    current_period_start: datetime
    current_period_end: datetime
    is_trial: Optional[bool] = False


class SubscriptionUpdateRequest(PydanticBaseModel):
    tariff_name: Optional[TariffName] = None
    status: Optional[SubscriptionStatus] = None
    monthly_bookings_limit: Optional[int] = None
    additional_skills: Optional[List[str]] = None
    current_period_end: Optional[datetime] = None


class SubscriptionResponse(PydanticBaseModel):
    id: int
    master_id: int
    tariff_name: TariffName
    status: SubscriptionStatus
    monthly_bookings_limit: int
    additional_skills: Optional[List[str]] = None
    current_period_start: datetime
    current_period_end: datetime
    is_trial: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True