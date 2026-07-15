from sqlalchemy import String, Integer, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel


class Service(BaseModel):
    """Model representing a beauty service offered by a master"""
    __tablename__ = "services"
    
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    duration_minutes: Mapped[int] = mapped_column(default=60)
    price: Mapped[float] = mapped_column(Numeric(precision=10, scale=2))
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    
    # Relationship
    master: Mapped["Master"] = relationship("Master", back_populates="services")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="service")


# Adding relationship to Master model needs to be done in master.py
# We'll add it there since we can't do forward reference here properly