"""Tests for admin handlers."""

from unittest.mock import AsyncMock, patch

import pytest
from aiogram.types import Message, User

from src.handlers.admin import add_service_command, show_stats
from tests.conftest import make_master, make_subscription


@pytest.fixture
def admin_user() -> User:
    return User(id=701001, is_bot=False, first_name="Admin", username="admin")


@pytest.mark.asyncio
async def test_add_service_starts_fsm(db_session, session_override, admin_user):
    master = await make_master(db_session, telegram_id=admin_user.id)
    await make_subscription(db_session, master)

    message = AsyncMock(spec=Message)
    message.from_user = admin_user
    message.answer = AsyncMock()
    state = AsyncMock()
    state.set_state = AsyncMock()
    state.update_data = AsyncMock()

    with patch("src.handlers.admin.get_session", session_override):
        await add_service_command(message, state)

    message.answer.assert_awaited()
    state.set_state.assert_awaited()


@pytest.mark.asyncio
async def test_stats_command(db_session, session_override, admin_user):
    master = await make_master(db_session, telegram_id=admin_user.id)
    await make_subscription(db_session, master)

    message = AsyncMock(spec=Message)
    message.from_user = admin_user
    message.answer = AsyncMock()

    with patch("src.handlers.admin.get_session", session_override):
        await show_stats(message)

    message.answer.assert_awaited()
    assert "статист" in message.answer.await_args.args[0].lower()
