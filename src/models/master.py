from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel


class Master(BaseModel):
    """Model representing a beauty industry professional (master)"""
    __tablename__ = "masters"
    
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    settings: Mapped[dict] = mapped_column(JSON, default=dict)  # Store business settings like working hours, break times
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")  # Master's local timezone
    work_start_hour: Mapped[int] = mapped_column(default=9)  # Start of work day (24h format)
    work_end_hour: Mapped[int] = mapped_column(default=18)   # End of work day (24h format)
    appointment_duration: Mapped[int] = mapped_column(default=60)  # Default appointment duration in minutes
    
    # Relationships
    clients: Mapped[list["Client"]] = relationship("Client", back_populates="master")
    services: Mapped[list["Service"]] = relationship("Service", back_populates="master")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="master")