"""District analytics model for aggregated location-based insights."""

from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class DistrictAnalytics(Base):
    """Model for district-level analytics data."""

    __tablename__ = "district_analytics"

    district: Mapped[str] = mapped_column(String, primary_key=True)
    city: Mapped[str | None] = mapped_column(String)
    total_masters: Mapped[int] = mapped_column(Integer, default=0)
    total_bookings_30d: Mapped[int] = mapped_column(Integer, default=0)
    avg_price_by_service: Mapped[dict | None] = mapped_column(
        String
    )  # JSON in string form
    demand_trend: Mapped[Decimal] = mapped_column(Numeric(precision=5, scale=2))
    top_services: Mapped[dict | None] = mapped_column(String)  # JSON in string form
    last_updated: Mapped[DateTime] = mapped_column(DateTime)
