from sqlalchemy import String, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel


class Client(BaseModel):
    """Model representing a client/customer"""
    __tablename__ = "clients"
    
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.id"), index=True)
    phone: Mapped[str] = mapped_column(String(20))  # Encrypted phone number
    name: Mapped[str] = mapped_column(String(255))
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)  # Service preferences, notes
    reliability_score: Mapped[float] = mapped_column(default=5.0)  # Rating from 1-5 based on attendance
    
    # Relationship
    master: Mapped["Master"] = relationship("Master", back_populates="clients")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="client")