"""Database connection and session management."""

from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .models.base import Base

engine = None
SessionLocal = None

__all__ = ["Base", "engine", "SessionLocal", "init_db", "get_session", "close_db"]


async def init_db(database_url: str) -> None:
    """Initialize database connection."""
    global engine, SessionLocal
    engine = create_async_engine(database_url)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def get_session():
    """Get database session."""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db first.")

    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db() -> None:
    """Close database connections."""
    global engine
    if engine:
        await engine.dispose()
        engine = None
