"""Tests for reminder service."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from src.models.interaction import Interaction
from src.services.reminder_service import send_reminders
from tests.conftest import make_booking, make_client, make_master, make_service


@pytest.fixture
def mock_bot() -> AsyncMock:
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.mark.asyncio
async def test_reminder_sent_for_tomorrow_booking(
    db_session, session_override, mock_bot
):
    master = await make_master(db_session, telegram_id=901001, name="Anna")
    client = await make_client(db_session, master, telegram_id=901002)
    service = await make_service(db_session, master, name="Manicure")
    when = datetime.now() + timedelta(hours=24)
    await make_booking(db_session, master, client, service, when)

    with patch("src.services.reminder_service.get_session", session_override):
        sent = await send_reminders(mock_bot)

    assert sent == 1
    mock_bot.send_message.assert_awaited_once()
    assert "Anna" in mock_bot.send_message.await_args.args[1]

    interactions = (
        await db_session.execute(
            select(Interaction).where(Interaction.event_type == "reminder_sent")
        )
    ).scalars().all()
    assert len(interactions) == 1
    assert interactions[0].master_id == master.id


@pytest.mark.asyncio
async def test_no_reminder_for_today_booking(
    db_session, session_override, mock_bot
):
    master = await make_master(db_session, telegram_id=901003)
    client = await make_client(db_session, master, telegram_id=901004)
    service = await make_service(db_session, master)
    when = datetime.now() + timedelta(hours=2)
    await make_booking(db_session, master, client, service, when)

    with patch("src.services.reminder_service.get_session", session_override):
        sent = await send_reminders(mock_bot)

    assert sent == 0
    mock_bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_reminder_not_sent_twice(db_session, session_override, mock_bot):
    master = await make_master(db_session, telegram_id=901005)
    client = await make_client(db_session, master, telegram_id=901006)
    service = await make_service(db_session, master)
    when = datetime.now() + timedelta(hours=24)
    await make_booking(
        db_session,
        master,
        client,
        service,
        when,
        reminded_at=datetime.now(),
    )

    with patch("src.services.reminder_service.get_session", session_override):
        sent = await send_reminders(mock_bot)

    assert sent == 0
    mock_bot.send_message.assert_not_awaited()
