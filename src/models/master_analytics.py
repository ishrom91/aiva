"""Master analytics model for tracking master performance metrics."""

from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MasterAnalytics(Base):
    """Model for master analytics data."""

    __tablename__ = "master_analytics"

    master_id: Mapped[str] = mapped_column(
        String, ForeignKey("masters.id"), primary_key=True
    )
    total_bookings: Mapped[int] = mapped_column(Integer, default=0)
    total_cancellations: Mapped[int] = mapped_column(Integer, default=0)
    total_no_shows: Mapped[int] = mapped_column(Integer, default=0)
    avg_price: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    top_service_type: Mapped[str | None] = mapped_column(String)
    peak_hours: Mapped[dict | None] = mapped_column(String)  # JSON in string form
    client_retention_rate: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2)
    )
    last_updated: Mapped[DateTime] = mapped_column(DateTime)
