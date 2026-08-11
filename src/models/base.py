"""Base classes for all SQLAlchemy models."""

from datetime import datetime
from typing import Annotated
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


uuid_pk = Annotated[str, mapped_column(primary_key=True, default=lambda: str(uuid4()))]


class UUIDMixin:
    """Mixin to add a UUID primary key to models."""

    id: Mapped[uuid_pk]


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )


class BaseMixin(UUIDMixin, TimestampMixin):
    """Combined mixin with both UUID and timestamps"""

    pass


class BaseModel(Base, BaseMixin):
    """Base model class for all Aiva AI models"""

    __abstract__ = True
