from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel
from enum import Enum
from sqlalchemy import Enum as SQLEnum
import datetime


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Booking(BaseModel):
    """Model representing a booking/appointment"""
    __tablename__ = "bookings"
    
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), index=True)
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.id"), index=True)
    datetime: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[BookingStatus] = mapped_column(SQLEnum(BookingStatus), default=BookingStatus.PENDING)
    notes: Mapped[str] = mapped_column(String(500), nullable=True)
    
    # Relationships using string-based references
    client: Mapped["Client"] = relationship("Client", back_populates="bookings")
    service: Mapped["Service"] = relationship("Service", back_populates="bookings")
    master: Mapped["Master"] = relationship("Master", back_populates="bookings")