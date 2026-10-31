"""Tests for subscription handlers."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from aiogram.types import CallbackQuery, Message, User

from src.handlers.subscription import (
    process_upgrade,
    subscription_command,
    upgrade_command,
)
from tests.conftest import make_master, make_subscription


@pytest.fixture
def sub_user() -> User:
    return User(id=601001, is_bot=False, first_name="Sub", username="subuser")


@pytest.mark.asyncio
async def test_subscription_command(db_session, session_override, sub_user):
    master = await make_master(db_session, telegram_id=sub_user.id)
    await make_subscription(db_session, master)

    message = AsyncMock(spec=Message)
    message.from_user = sub_user
    message.answer = AsyncMock()

    with patch("src.handlers.subscription.get_session", session_override):
        await subscription_command(message)

    message.answer.assert_awaited()
    text = message.answer.await_args.args[0]
    assert "Тариф" in text


@pytest.mark.asyncio
async def test_upgrade_command_no_trigger(db_session, session_override, sub_user):
    recent_demo = datetime.now().isoformat()
    master = await make_master(
        db_session,
        telegram_id=sub_user.id,
        settings={
            "last_lost_revenue_demo": recent_demo,
            "last_social_proof": recent_demo,
        },
    )
    await make_subscription(db_session, master)

    message = AsyncMock(spec=Message)
    message.from_user = sub_user
    message.answer = AsyncMock()

    with patch("src.handlers.subscription.get_session", session_override):
        await upgrade_command(message)

    message.answer.assert_awaited()
    assert "апгрейдить" in message.answer.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_process_upgrade(db_session, session_override, sub_user):
    master = await make_master(db_session, telegram_id=sub_user.id)
    await make_subscription(db_session, master, tariff_name="start")

    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = sub_user
    callback.data = "upgrade:pro"
    callback.answer = AsyncMock()
    callback.message = AsyncMock()
    callback.message.edit_text = AsyncMock()

    with patch("src.handlers.subscription.get_session", session_override), patch(
        "src.handlers.subscription.log_event"
    ):
        await process_upgrade(callback)

    callback.message.edit_text.assert_awaited()
    text = callback.message.edit_text.await_args.args[0]
    assert "200" in text
