"""Tests for start handler."""

from unittest.mock import AsyncMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, Message, User
from sqlalchemy import func, select

from src.handlers.start import help_command, start_command
from src.models.master import Master
from src.models.subscription import Subscription
from tests.conftest import make_master, make_subscription


@pytest.fixture
def tracked_state() -> tuple[FSMContext, dict]:
    storage: dict = {}

    state = AsyncMock(spec=FSMContext)

    async def update_data(**kwargs: object) -> None:
        storage.update(kwargs)

    async def get_data() -> dict:
        return storage.copy()

    state.update_data = update_data
    state.get_data = get_data
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    return state, storage


@pytest.fixture
def new_user_message() -> Message:
    user = User(
        id=401001,
        is_bot=False,
        first_name="New",
        last_name="Master",
        username="newmaster",
    )
    message = AsyncMock(spec=Message)
    message.from_user = user
    message.answer = AsyncMock()
    return message


@pytest.fixture
def existing_user_message() -> Message:
    user = User(
        id=401002,
        is_bot=False,
        first_name="Existing",
        last_name="Master",
        username="existing",
    )
    message = AsyncMock(spec=Message)
    message.from_user = user
    message.answer = AsyncMock()
    return message


@pytest.mark.asyncio
async def test_start_creates_master(
    db_session, session_override, new_user_message, tracked_state
):
    state, _ = tracked_state

    with patch("src.handlers.start.get_session", session_override):
        await start_command(new_user_message, state)

    master = await db_session.scalar(
        select(Master).where(Master.telegram_id == new_user_message.from_user.id)
    )
    assert master is not None
    assert master.name == "New Master"
    sub_count = await db_session.scalar(
        select(func.count())
        .select_from(Subscription)
        .where(Subscription.master_id == master.id)
    )
    assert sub_count == 1


@pytest.mark.asyncio
async def test_start_returns_menu(
    db_session, session_override, existing_user_message, tracked_state
):
    state, _ = tracked_state
    master = await make_master(
        db_session,
        telegram_id=existing_user_message.from_user.id,
        name="Existing Master",
    )
    await make_subscription(db_session, master)

    with patch("src.handlers.start.get_session", session_override):
        await start_command(existing_user_message, state)

    new_user_message = existing_user_message
    assert new_user_message.answer.await_count == 1
    args, kwargs = new_user_message.answer.await_args
    assert isinstance(kwargs.get("reply_markup"), InlineKeyboardMarkup)
    assert "С возвращением" in args[0]


@pytest.mark.asyncio
async def test_help_command(new_user_message):
    await help_command(new_user_message)
    new_user_message.answer.assert_awaited()
    assert "Запись" in new_user_message.answer.await_args.args[0]
