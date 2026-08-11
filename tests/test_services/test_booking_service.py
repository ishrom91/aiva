"""Tests for BookingService."""

from datetime import datetime, timedelta

import pytest

from src.exceptions import BookingConflictError, SubscriptionLimitExceeded
from src.models.booking import BookingStatus
from src.services.booking_service import BookingService
from tests.conftest import (
    make_booking,
    make_client,
    make_master,
    make_service,
    make_subscription,
)


@pytest.mark.asyncio
async def test_create_booking_success(db_session):
    master = await make_master(db_session, telegram_id=123001)
    client = await make_client(db_session, master, telegram_id=123002)
    service = await make_service(db_session, master)
    await make_subscription(db_session, master)

    booking_service = BookingService(db_session)
    when = datetime.now().replace(hour=15, minute=0, second=0, microsecond=0) + timedelta(
        days=2
    )
    booking = await booking_service.create_booking(
        master_id=master.id,
        client_id=client.id,
        service_id=service.id,
        booking_datetime=when,
    )

    assert booking.status == BookingStatus.CONFIRMED
    assert booking.master_id == master.id
    assert booking.client_id == client.id


@pytest.mark.asyncio
async def test_create_booking_conflict(db_session):
    master = await make_master(db_session, telegram_id=123010)
    client = await make_client(db_session, master, telegram_id=123011)
    service = await make_service(db_session, master, duration_minutes=60)
    await make_subscription(db_session, master)

    tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )
    existing_time = tomorrow.replace(hour=14, minute=0)
    await make_booking(db_session, master, client, service, existing_time)

    booking_service = BookingService(db_session)
    conflict_time = tomorrow.replace(hour=14, minute=30)

    with pytest.raises(BookingConflictError):
        await booking_service.create_booking(
            master_id=master.id,
            client_id=client.id,
            service_id=service.id,
            booking_datetime=conflict_time,
        )


@pytest.mark.asyncio
async def test_create_booking_subscription_limit(db_session):
    master = await make_master(db_session, telegram_id=123020)
    client = await make_client(db_session, master, telegram_id=123021)
    service = await make_service(db_session, master, duration_minutes=30)
    await make_subscription(db_session, master, monthly_bookings_limit=50)

    base = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )
    for i in range(50):
        when = base + timedelta(minutes=30 * i)
        await make_booking(db_session, master, client, service, when)

    booking_service = BookingService(db_session)
    with pytest.raises(SubscriptionLimitExceeded):
        await booking_service.create_booking(
            master_id=master.id,
            client_id=client.id,
            service_id=service.id,
            booking_datetime=base + timedelta(hours=25),
        )


@pytest.mark.asyncio
async def test_get_available_slots(db_session):
    master = await make_master(
        db_session,
        telegram_id=123030,
        work_start_hour=9,
        work_end_hour=18,
    )
    client = await make_client(db_session, master, telegram_id=123031)
    service = await make_service(db_session, master, duration_minutes=60)

    tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )
    await make_booking(
        db_session,
        master,
        client,
        service,
        tomorrow.replace(hour=10, minute=0),
    )
    await make_booking(
        db_session,
        master,
        client,
        service,
        tomorrow.replace(hour=14, minute=0),
    )

    booking_service = BookingService(db_session)
    slots = await booking_service.get_available_slots(
        master.id, tomorrow, service_id=service.id
    )
    slot_times = {slot.strftime("%H:%M") for slot in slots}

    assert "10:00" not in slot_times
    assert "10:30" not in slot_times
    assert "14:00" not in slot_times
    assert "14:30" not in slot_times
    assert "09:00" in slot_times
    assert "11:00" in slot_times
    assert "16:00" in slot_times


@pytest.mark.asyncio
async def test_cancel_booking(db_session):
    master = await make_master(db_session, telegram_id=123040)
    client = await make_client(db_session, master, telegram_id=123041)
    service = await make_service(db_session, master, duration_minutes=30)
    await make_subscription(db_session, master)

    when = datetime.now() + timedelta(days=1)
    booking = await make_booking(db_session, master, client, service, when)

    booking_service = BookingService(db_session)
    cancelled = await booking_service.cancel_booking(booking.id, master.id)
    assert cancelled.status == BookingStatus.CANCELLED


@pytest.mark.asyncio
async def test_mark_no_show(db_session):
    master = await make_master(db_session, telegram_id=123050)
    client = await make_client(db_session, master, telegram_id=123051)
    service = await make_service(db_session, master, duration_minutes=30)

    when = datetime.now() + timedelta(days=1)
    booking = await make_booking(db_session, master, client, service, when)

    booking_service = BookingService(db_session)
    updated = await booking_service.mark_no_show(booking.id, master.id)
    assert updated.status == BookingStatus.NO_SHOW


@pytest.mark.asyncio
async def test_cancel_booking_wrong_master(db_session):
    from src.exceptions import OwnershipError

    master = await make_master(db_session, telegram_id=123060)
    other = await make_master(db_session, telegram_id=123061)
    client = await make_client(db_session, master, telegram_id=123062)
    service = await make_service(db_session, master)
    booking = await make_booking(
        db_session, master, client, service, datetime.now() + timedelta(days=1)
    )

    booking_service = BookingService(db_session)
    with pytest.raises(OwnershipError):
        await booking_service.cancel_booking(booking.id, other.id)
