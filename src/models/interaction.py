"""Interaction model for event sourcing and data collection."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin

if TYPE_CHECKING:
    from .master import Master


class InteractionDirection(Enum):
    """Enum for interaction directions."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class Interaction(Base, UUIDMixin):
    """Model for all interactions (event sourcing)."""

    __tablename__ = "interactions"

    __table_args__ = (
        CheckConstraint("client_hash IS NOT NULL"),
        CheckConstraint("master_id IS NOT NULL"),
        Index("ix_interactions_master_created", "master_id", "created_at"),
        Index("ix_interactions_event_created", "event_type", "created_at"),
        Index("ix_interactions_service_created", "service_type", "created_at"),
        Index("ix_interactions_district_created", "location_district", "created_at"),
    )

    event_type: Mapped[str] = mapped_column(String, nullable=False)
    master_id: Mapped[str] = mapped_column(
        String, ForeignKey("masters.id"), nullable=False
    )
    client_hash: Mapped[str] = mapped_column(String, nullable=False)
    skill_name: Mapped[str | None] = mapped_column(String)
    direction: Mapped[InteractionDirection] = mapped_column(
        SQLEnum(InteractionDirection)
    )
    service_type: Mapped[str | None] = mapped_column(String)
    price: Mapped[int | None] = mapped_column(Integer)
    location_district: Mapped[str | None] = mapped_column(String)
    event_metadata: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # Changed name to avoid SQLAlchemy conflict
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        server_onupdate=None,
    )

    # Relationships
    master: Mapped["Master"] = relationship(back_populates="interactions")
