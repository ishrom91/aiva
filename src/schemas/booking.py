from pydantic import BaseModel as PydanticBaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BookingCreateRequest(PydanticBaseModel):
    client_id: int
    service_id: int
    datetime: datetime
    notes: Optional[str] = None


class BookingUpdateRequest(PydanticBaseModel):
    status: Optional[BookingStatus] = None
    notes: Optional[str] = None


class BookingResponse(PydanticBaseModel):
    id: int
    client_id: int
    service_id: int
    master_id: int
    datetime: datetime
    status: BookingStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True