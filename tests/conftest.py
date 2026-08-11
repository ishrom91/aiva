"""Test configuration for Aiva AI Bot."""

import os
import subprocess
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import AsyncIterator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.models import Base  # noqa: F401 — register all tables
from src.models.booking import Booking, BookingStatus
from src.models.client import Client
from src.models.master import Master
from src.models.service import Service
from src.models.subscription import Subscription, SubscriptionStatus

TEST_DB_URL = "sqlite+aiosqlite:///./test_pytest.db"
TEST_DB_SYNC = "sqlite:///./test_pytest.db"


@pytest.fixture(scope="session", autouse=True)
def _migrate_test_db():
    if os.path.exists("test_pytest.db"):
        os.remove("test_pytest.db")
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DB_SYNC
    subprocess.run(["alembic", "upgrade", "head"], check=True, env=env)
    yield
    if os.path.exists("test_pytest.db"):
        os.remove("test_pytest.db")


@pytest_asyncio.fixture(scope="session")
async def engine():
    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    yield test_engine
    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _reset_db(engine):
    """Clear all tables before and after each test for isolation."""
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def db_session(engine):
    session_factory = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def session_override(db_session):
    """Patch get_session in handlers to use the test db_session."""

    @asynccontextmanager
    async def _get_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    return _get_session


@pytest.fixture
def mock_user() -> User:
    return User(
        id=900001,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser",
    )


@pytest.fixture
def mock_message(mock_user: User) -> Message:
    message = AsyncMock(spec=Message)
    message.from_user = mock_user
    message.message_id = 1
    message.text = "/start"
    message.answer = AsyncMock()
    message.edit_text = AsyncMock()
    return message


@pytest.fixture
def mock_state() -> FSMContext:
    state = AsyncMock(spec=FSMContext)
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    state.clear = AsyncMock()
    return state


async def make_master(
    session: AsyncSession,
    *,
    telegram_id: int = 100001,
    name: str = "Test Master",
    work_start_hour: int = 9,
    work_end_hour: int = 18,
    settings: dict | None = None,
) -> Master:
    master = Master(
        telegram_id=telegram_id,
        name=name,
        work_start_hour=work_start_hour,
        work_end_hour=work_end_hour,
        settings=settings or {},
        is_active=True,
    )
    session.add(master)
    await session.commit()
    await session.refresh(master)
    return master


async def make_client(
    session: AsyncSession,
    master: Master,
    *,
    telegram_id: int = 100002,
    name: str = "Test Client",
) -> Client:
    client = Client(
        telegram_id=telegram_id,
        master_id=master.id,
        name_encrypted=name,
    )
    session.add(client)
    await session.commit()
    await session.refresh(client)
    return client


async def make_service(
    session: AsyncSession,
    master: Master,
    *,
    name: str = "Manicure",
    duration_minutes: int = 60,
    price: int = 2500,
) -> Service:
    service = Service(
        master_id=master.id,
        name=name,
        duration_minutes=duration_minutes,
        price=price,
        is_active=True,
    )
    session.add(service)
    await session.commit()
    await session.refresh(service)
    return service


async def make_subscription(
    session: AsyncSession,
    master: Master,
    *,
    tariff_name: str = "start",
    monthly_bookings_limit: int = 50,
    is_trial: bool = True,
) -> Subscription:
    now = datetime.now()
    subscription = Subscription(
        master_id=master.id,
        tariff_name=tariff_name,
        status=SubscriptionStatus.ACTIVE,
        monthly_bookings_limit=monthly_bookings_limit,
        additional_skills="[]",
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        is_trial=is_trial,
    )
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)
    return subscription


async def make_booking(
    session: AsyncSession,
    master: Master,
    client: Client,
    service: Service,
    when: datetime,
    *,
    status: BookingStatus = BookingStatus.CONFIRMED,
    reminded_at: datetime | None = None,
) -> Booking:
    booking = Booking(
        master_id=master.id,
        client_id=client.id,
        service_id=service.id,
        datetime=when,
        status=status,
        reminded_at=reminded_at,
    )
    session.add(booking)
    await session.commit()
    await session.refresh(booking)
    return booking
