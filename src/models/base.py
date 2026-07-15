from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from ..database import Base
import uuid


class TimestampMixin:
    """Mixin class for adding timestamp fields to models"""
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )


class UUIDMixin:
    """Mixin class for adding UUID primary key to models"""
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)


class BaseMixin(UUIDMixin, TimestampMixin):
    """Combined mixin with both UUID and timestamps"""
    pass


class BaseModel(Base, BaseMixin):
    """Base model class for all Aiva AI models"""
    __abstract__ = True