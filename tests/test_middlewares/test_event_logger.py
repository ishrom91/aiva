"""Tests for event logger middleware."""

from unittest.mock import AsyncMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, Update, User
from sqlalchemy import select

from src.middlewares.event_logger import EventLoggerMiddleware
from src.models.interaction import Interaction
from src.utils.event_log import _write_event
from tests.conftest import make_master


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
    return state, storage


@pytest.mark.asyncio
async def test_interaction_logged_with_master_id(
    db_session, session_override, tracked_state
):
    state, storage = tracked_state
    master = await make_master(db_session, telegram_id=802001)
    storage["master_id"] = master.id

    user = User(id=802001, is_bot=False, first_name="Log", username="loguser")
    message = AsyncMock(spec=Message)
    message.from_user = user
    message.text = "/start"
    update = Update(update_id=1, message=message)

    middleware = EventLoggerMiddleware()
    with patch("src.middlewares.event_logger.get_session", session_override), patch(
        "src.middlewares.event_logger.settings"
    ) as mock_settings:
        mock_settings.DATA_COLLECTION_ENABLED = True
        mock_settings.CLIENT_HASH_SALT = "test_salt"
        mock_settings.DATA_COLLECTION_LOG_TEXT = False
        await middleware._log_interaction(
            update,
            {"state": state, "master_id": master.id},
        )

    with patch("src.utils.event_log.get_session", session_override):
        await _write_event(master.id, user.id, "booking_created")

    interactions = (
        await db_session.execute(
            select(Interaction).where(Interaction.master_id == master.id)
        )
    ).scalars().all()

    assert len(interactions) >= 2
    assert all(row.master_id is not None for row in interactions)
    event_types = {row.event_type for row in interactions}
    assert "message_received" in event_types
    assert "booking_created" in event_types
