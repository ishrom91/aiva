"""Tests for retention / winback service."""

from datetime import datetime, timedelta

import pytest

from src.models.booking import BookingStatus
from src.services.retention_service import find_dormant_clients
from tests.conftest import make_booking, make_client, make_master, make_service


@pytest.mark.asyncio
async def test_find_dormant_clients(db_session):
    master = await make_master(db_session, telegram_id=903001)
    service = await make_service(db_session, master)

    old_client = await make_client(db_session, master, telegram_id=903002, name="Old")
    fresh_client = await make_client(db_session, master, telegram_id=903003, name="Fresh")

    old_visit = datetime.now() - timedelta(days=90)
    fresh_visit = datetime.now() - timedelta(days=5)

    await make_booking(
        db_session, master, old_client, service, old_visit, status=BookingStatus.COMPLETED
    )
    await make_booking(
        db_session,
        master,
        fresh_client,
        service,
        fresh_visit,
        status=BookingStatus.COMPLETED,
    )

    dormant = await find_dormant_clients(db_session, master.id, days=60)
    dormant_ids = {c.id for c in dormant}

    assert old_client.id in dormant_ids
    assert fresh_client.id not in dormant_ids


@pytest.mark.asyncio
async def test_winback_rate_limit(db_session):
    master = await make_master(db_session, telegram_id=903004)
    service = await make_service(db_session, master)
    client = await make_client(db_session, master, telegram_id=903005)
    client.last_winback_at = datetime.now() - timedelta(days=5)
    await db_session.commit()

    old_visit = datetime.now() - timedelta(days=90)
    await make_booking(
        db_session, master, client, service, old_visit, status=BookingStatus.COMPLETED
    )

    dormant = await find_dormant_clients(db_session, master.id, days=60)
    assert all(c.id != client.id for c in dormant)


@pytest.mark.asyncio
async def test_build_winback_message(db_session):
    from src.services.retention_service import build_winback_message

    master = await make_master(db_session, telegram_id=903006, name="Maria")
    await make_service(db_session, master)
    client = await make_client(db_session, master, telegram_id=903007, name="Kate")

    text = await build_winback_message(db_session, client, master)
    assert "Maria" in text
    assert "/book" in text
