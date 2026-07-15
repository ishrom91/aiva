from sqlalchemy import String, Integer, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel
from enum import Enum
import datetime


class InteractionDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class Interaction(BaseModel):
    """Event sourcing model: logging ALL interactions for future Data API"""
    __tablename__ = "interactions"
    
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'message_received', 'booking_created', etc.
    master_id: Mapped[int] = mapped_column(nullable=False)  # FK to masters table
    client_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256(telegram_id + salt)
    skill_name: Mapped[str] = mapped_column(String(50), nullable=True)  # 'booking', 'retention', 'faq'
    direction: Mapped[InteractionDirection] = mapped_column(SQLEnum(InteractionDirection), nullable=True)
    service_type: Mapped[str] = mapped_column(String(100), nullable=True)  # 'manicure_classic', 'pedicure_hardware'
    price: Mapped[int] = mapped_column(nullable=True)  # Price in kopecks
    location_district: Mapped[str] = mapped_column(String(100), nullable=True)  # District of the master
    metadata: Mapped[dict] = mapped_column(JSON, nullable=True)  # Additional data like {"message_text_length": 45, ...}
    
    __table_args__ = (
        # Indexes for performance
        {"postgresql_using": "btree", "columns": ["master_id", "created_at"]},
        {"postgresql_using": "btree", "columns": ["event_type", "created_at"]},
        {"postgresql_using": "btree", "columns": ["service_type", "created_at"]},
        {"postgresql_using": "btree", "columns": ["location_district", "created_at"]},
    )