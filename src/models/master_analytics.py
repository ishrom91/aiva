from sqlalchemy import String, Integer, Numeric, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel
import datetime


class MasterAnalytics(BaseModel):
    """Aggregated statistics per master (for quick access)"""
    __tablename__ = "master_analytics"
    
    master_id: Mapped[int] = mapped_column(primary_key=True)  # FK to masters table
    total_bookings: Mapped[int] = mapped_column(default=0)
    total_cancellations: Mapped[int] = mapped_column(default=0)
    total_no_shows: Mapped[int] = mapped_column(default=0)
    avg_price: Mapped[float] = mapped_column(nullable=True)  # Average price in rubles
    top_service_type: Mapped[str] = mapped_column(String(100), nullable=True)
    peak_hours: Mapped[dict] = mapped_column(JSON, default=dict)  # {"monday": ["10:00-12:00", "18:00-20:00"]}
    client_retention_rate: Mapped[float] = mapped_column(nullable=True)  # Decimal value (0.0 to 1.0)
    last_updated: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default="NOW()")