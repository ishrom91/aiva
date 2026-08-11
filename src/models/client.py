"""Client model representing customers of masters."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .booking import Booking
    from .master import Master


class Client(Base, UUIDMixin, TimestampMixin):
    """Model for clients of masters."""

    __tablename__ = "clients"

    telegram_id: Mapped[int] = mapped_column(Integer)
    master_id: Mapped[str] = mapped_column(String, ForeignKey("masters.id"), index=True)
    phone_encrypted: Mapped[str | None] = mapped_column(String)
    name_encrypted: Mapped[str | None] = mapped_column(String)
    preferences: Mapped[dict | None] = mapped_column(String)  # JSON in string form
    reliability_score: Mapped[int] = mapped_column(Integer, default=50)

    # Relationships
    master: Mapped["Master"] = relationship(back_populates="clients")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="client")
