"""Test configuration for Aiva AI Bot."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create test database engine."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with test_engine.begin() as conn:
        import src.models  # noqa: F401 — register all models
        from src.models.base import Base

        await conn.run_sync(Base.metadata.create_all)

    yield test_engine
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """Create a database session."""
    session_factory = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def make_master():
    """Factory function to create a master instance."""
    pytest.skip("phase 2")


@pytest.fixture
def make_client():
    """Factory function to create a client instance."""
    pytest.skip("phase 2")


@pytest.fixture
def make_service():
    """Factory function to create a service instance."""
    pytest.skip("phase 2")


@pytest.fixture
def make_subscription():
    """Factory function to create a subscription instance."""
    pytest.skip("phase 2")
