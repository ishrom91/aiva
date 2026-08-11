from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .client import Client
    from .master import Master
    from .service import Service


class BookingStatus(Enum):
    """Enum for booking statuses."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Booking(Base, UUIDMixin, TimestampMixin):
    """Model for bookings/appointments."""

    __tablename__ = "bookings"

    client_id: Mapped[str] = mapped_column(String, ForeignKey("clients.id"))
    service_id: Mapped[str] = mapped_column(String, ForeignKey("services.id"))
    master_id: Mapped[str] = mapped_column(String, ForeignKey("masters.id"))
    datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus), default=BookingStatus.PENDING
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="bookings")
    service: Mapped["Service"] = relationship(back_populates="bookings")
    master: Mapped["Master"] = relationship(back_populates="bookings")
