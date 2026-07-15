import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, MagicMock
from src.models import Base
from src.database import get_session


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        echo=True,
        connect_args={"check_same_thread": False}
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine):
    """Create a test database session."""
    async with AsyncSession(bind=db_engine) as session:
        yield session


@pytest.fixture
def mock_bot():
    """Create a mock Telegram bot."""
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=None)
    return bot


@pytest.fixture
def mock_update():
    """Create a mock update object."""
    update = MagicMock()
    update.message = MagicMock()
    update.callback_query = MagicMock()
    return update