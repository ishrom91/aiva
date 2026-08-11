from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .booking import Booking
    from .client import Client
    from .interaction import Interaction
    from .service import Service
    from .subscription import Subscription


class Master(Base, UUIDMixin, TimestampMixin):
    """Model for beauty professionals (masters) using the bot."""

    __tablename__ = "masters"

    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    settings: Mapped[dict | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    work_start_hour: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=9
    )
    work_end_hour: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=18
    )

    # Relationships
    clients: Mapped[list["Client"]] = relationship(back_populates="master")
    services: Mapped[list["Service"]] = relationship(back_populates="master")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="master")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="master")
    interactions: Mapped[list["Interaction"]] = relationship(back_populates="master")
