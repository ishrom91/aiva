"""Pydantic schemas for booking operations."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BookingCreate(BaseModel):
    """Schema for creating a new booking."""

    client_id: str
    service_id: str
    master_id: str
    datetime: datetime


class BookingResponse(BaseModel):
    """Schema for booking response."""

    id: str
    client_id: str
    service_id: str
    master_id: str
    datetime: datetime
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
