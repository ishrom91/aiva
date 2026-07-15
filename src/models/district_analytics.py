from sqlalchemy import String, Integer, Numeric, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel
import datetime


class DistrictAnalytics(BaseModel):
    """Aggregated statistics per district (for Data API)"""
    __tablename__ = "district_analytics"
    
    district: Mapped[str] = mapped_column(String(100), primary_key=True)
    city: Mapped[str] = mapped_column(String(100))
    total_masters: Mapped[int]
    total_bookings_30d: Mapped[int]
    avg_price_by_service: Mapped[dict] = mapped_column(JSON, default=dict)  # {"manicure": 2500, "pedicure": 3000}
    demand_trend: Mapped[float]  # Decimal value showing trend (e.g., 0.23 for +23%)
    top_services: Mapped[dict] = mapped_column(JSON, default=dict)
    last_updated: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default="NOW()")