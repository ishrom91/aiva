"""Test configuration for Aiva AI Bot."""

import os
import subprocess

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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


@pytest_asyncio.fixture
async def db_session(engine):
    session_factory = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_factory() as session:
        yield session
        await session.rollback()
