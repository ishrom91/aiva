"""Service model representing beauty services offered by masters."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .booking import Booking
    from .master import Master


class Service(Base, UUIDMixin, TimestampMixin):
    """Model for services offered by masters."""

    __tablename__ = "services"

    master_id: Mapped[str] = mapped_column(String, ForeignKey("masters.id"))
    name: Mapped[str] = mapped_column(String)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    price: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    master: Mapped["Master"] = relationship(back_populates="services")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="service")
