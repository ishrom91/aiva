"""Tests for BookingService."""

from datetime import datetime, timedelta

import pytest

from src.models.booking import BookingStatus
from src.models.client import Client
from src.models.master import Master
from src.models.service import Service
from src.services.booking_service import BookingService


@pytest.mark.asyncio
async def test_create_booking_success(db_session):
    master = Master(telegram_id=123001, name="Booking Master")
    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)

    client = Client(telegram_id=123002, master_id=master.id, name_encrypted="Client")
    service = Service(
        master_id=master.id, name="Manicure", duration_minutes=60, price=2500
    )
    db_session.add_all([client, service])
    await db_session.commit()
    await db_session.refresh(client)
    await db_session.refresh(service)

    booking_service = BookingService(db_session)
    when = datetime.now() + timedelta(days=2)
    booking = await booking_service.create_booking(
        master_id=master.id,
        client_id=client.id,
        service_id=service.id,
        booking_datetime=when,
    )

    assert booking.status == BookingStatus.CONFIRMED
    assert booking.master_id == master.id


@pytest.mark.asyncio
async def test_get_available_slots(db_session):
    master = Master(
        telegram_id=123003,
        name="Slots Master",
        work_start_hour=9,
        work_end_hour=12,
    )
    service = Service(
        master_id=master.id, name="Cut", duration_minutes=60, price=1500
    )
    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)
    service.master_id = master.id
    db_session.add(service)
    await db_session.commit()

    booking_service = BookingService(db_session)
    slots = await booking_service.get_available_slots(
        master.id, datetime.now(), service_id=service.id
    )
    assert len(slots) > 0


@pytest.mark.asyncio
async def test_cancel_booking(db_session):
    master = Master(telegram_id=123004, name="Cancel Master")
    client = Client(telegram_id=123005, master_id=master.id)
    service = Service(
        master_id=master.id, name="Brow", duration_minutes=30, price=800
    )
    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)
    client.master_id = master.id
    service.master_id = master.id
    db_session.add_all([client, service])
    await db_session.commit()
    await db_session.refresh(client)
    await db_session.refresh(service)

    booking_service = BookingService(db_session)
    when = datetime.now() + timedelta(days=1)
    booking = await booking_service.create_booking(
        master.id, client.id, service.id, when
    )
    cancelled = await booking_service.cancel_booking(booking.id, master.id)
    assert cancelled.status == BookingStatus.CANCELLED
