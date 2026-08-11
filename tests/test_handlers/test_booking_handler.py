"""Tests for booking handler FSM flow."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User
from sqlalchemy import func, select

from src.handlers.booking import (
    BookingStates,
    command_book_handler,
    confirm_booking,
    process_date_selection,
    process_service_selection,
    process_time_selection,
)
from src.models.booking import Booking, BookingStatus
from tests.conftest import make_master, make_service, make_subscription


@pytest.fixture
def booking_user() -> User:
    return User(
        id=501001,
        is_bot=False,
        first_name="Booking",
        last_name="User",
        username="bookuser",
    )


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
def mock_callback(booking_user: User) -> CallbackQuery:
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = booking_user
    callback.answer = AsyncMock()
    callback.message = AsyncMock()
    callback.message.edit_text = AsyncMock()
    return callback


@pytest.mark.asyncio
async def test_book_command_starts_fsm(
    db_session, session_override, booking_user, tracked_state
):
    state, storage = tracked_state
    master = await make_master(db_session, telegram_id=booking_user.id)
    service = await make_service(db_session, master)
    await make_subscription(db_session, master)

    message = AsyncMock(spec=Message)
    message.from_user = booking_user
    message.answer = AsyncMock()

    with patch("src.handlers.booking.get_session", session_override):
        await command_book_handler(message, state)

    state.set_state.assert_awaited_with(BookingStates.choosing_service)
    message.answer.assert_awaited()
    assert storage.get("master_id") == master.id
    assert any(s["id"] == service.id for s in storage.get("services", []))


@pytest.mark.asyncio
async def test_service_selection_state(tracked_state, mock_callback):
    state, storage = tracked_state
    service_id = "svc-123"
    storage["services"] = [
        {"id": service_id, "name": "Manicure", "duration": 60},
    ]
    mock_callback.data = f"service_{service_id}"

    await process_service_selection(mock_callback, state)

    state.set_state.assert_awaited_with(BookingStates.choosing_date)
    assert storage["selected_service_id"] == service_id
    mock_callback.message.edit_text.assert_awaited()


@pytest.mark.asyncio
async def test_date_selection_state(
    db_session, session_override, tracked_state, mock_callback
):
    state, storage = tracked_state
    master = await make_master(db_session, telegram_id=502001)
    service = await make_service(db_session, master)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    storage.update(
        {
            "selected_service_id": service.id,
            "master_id": master.id,
            "services": [{"id": service.id, "name": service.name, "duration": 60}],
        }
    )
    mock_callback.data = f"date_{tomorrow}"

    with patch("src.handlers.booking.get_session", session_override):
        await process_date_selection(mock_callback, state)

    state.set_state.assert_awaited_with(BookingStates.choosing_time)
    assert storage["selected_date"] == tomorrow
    mock_callback.message.edit_text.assert_awaited()


@pytest.mark.asyncio
async def test_time_selection_state(tracked_state, mock_callback):
    state, storage = tracked_state
    service_id = "svc-time"
    date_str = "2030-01-15"
    storage.update(
        {
            "selected_service_id": service_id,
            "selected_date": date_str,
            "services": [{"id": service_id, "name": "Cut", "duration": 60}],
        }
    )
    mock_callback.data = "time_10:00"

    await process_time_selection(mock_callback, state)

    state.set_state.assert_awaited_with(BookingStates.confirmation)
    assert storage["selected_datetime"] == f"{date_str} 10:00:00"
    mock_callback.message.edit_text.assert_awaited()


@pytest.mark.asyncio
async def test_confirmation_creates_booking(
    db_session, session_override, booking_user, tracked_state, mock_callback
):
    state, storage = tracked_state
    master = await make_master(db_session, telegram_id=booking_user.id)
    service = await make_service(db_session, master)
    await make_subscription(db_session, master)

    booking_dt = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(
        days=2
    )
    datetime_str = booking_dt.strftime("%Y-%m-%d %H:%M:%S")
    storage.update(
        {
            "selected_service_id": service.id,
            "master_id": master.id,
            "selected_datetime": datetime_str,
        }
    )
    mock_callback.data = f"confirm_{datetime_str}"

    with patch("src.handlers.booking.get_session", session_override):
        await confirm_booking(mock_callback, state)

    count = await db_session.scalar(select(func.count()).select_from(Booking))
    assert count == 1
    booking = await db_session.scalar(select(Booking))
    assert booking.status == BookingStatus.CONFIRMED
    mock_callback.message.edit_text.assert_awaited()
    state.clear.assert_awaited()


@pytest.mark.asyncio
async def test_my_bookings_empty(
    db_session, session_override, booking_user, tracked_state
):
    master = await make_master(db_session, telegram_id=booking_user.id)
    await make_subscription(db_session, master)

    from src.handlers.booking import command_my_bookings_handler

    message = AsyncMock(spec=Message)
    message.from_user = booking_user
    message.answer = AsyncMock()

    with patch("src.handlers.booking.get_session", session_override):
        await command_my_bookings_handler(message)

    message.answer.assert_awaited()
    assert "нет предстоящих" in message.answer.await_args.args[0].lower()
