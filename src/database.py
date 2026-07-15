from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import AsyncAdaptedQueuePool
from typing import AsyncGenerator
from contextlib import asynccontextmanager


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


# Global engine and sessionmaker instances
engine = None
AsyncSessionLocal = None


def init_db(database_url: str):
    """Initialize database engine and session factory"""
    global engine, AsyncSessionLocal
    engine = create_async_engine(
        database_url,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=300,
    )
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=async_sessionmaker,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


async def get_session() -> AsyncGenerator[async_sessionmaker, None]:
    """Dependency for FastAPI to get database session"""
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def get_db_session():
    """Context manager for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db():
    """Close database engine"""
    if engine:
        await engine.dispose()