"""Tests for upsell triggers."""

from datetime import datetime, timedelta

import pytest

from src.billing.messages import build_limit_upsell_message
from src.billing.upsell_triggers import (
    check_upsell_triggers,
    should_show_lost_revenue_demo,
    should_show_social_proof,
)
from tests.conftest import (
    make_booking,
    make_client,
    make_master,
    make_service,
    make_subscription,
)


def _recent_iso(days_ago: int = 0) -> str:
    return (datetime.now() - timedelta(days=days_ago)).isoformat()


async def _create_bookings(
    session, master, client, service, count: int, *, day_offset: int = 1
) -> None:
    base = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(
        days=day_offset
    )
    for i in range(count):
        await make_booking(
            session,
            master,
            client,
            service,
            base + timedelta(minutes=30 * i),
        )


@pytest.mark.asyncio
async def test_limit_trigger_at_90_percent(db_session):
    master = await make_master(
        db_session,
        telegram_id=301001,
        settings={
            "last_lost_revenue_demo": _recent_iso(1),
            "last_social_proof": _recent_iso(1),
        },
    )
    client = await make_client(db_session, master, telegram_id=301002)
    service = await make_service(db_session, master, duration_minutes=30)
    await make_subscription(db_session, master, monthly_bookings_limit=50)
    await _create_bookings(db_session, master, client, service, 45)

    trigger = await check_upsell_triggers(db_session, master.id)

    assert trigger["should_upsell"] is True
    assert trigger["trigger_type"] == "limit"


@pytest.mark.asyncio
async def test_limit_trigger_below_90(db_session):
    master = await make_master(
        db_session,
        telegram_id=301003,
        settings={
            "last_lost_revenue_demo": _recent_iso(1),
            "last_social_proof": _recent_iso(1),
        },
    )
    client = await make_client(db_session, master, telegram_id=301004)
    service = await make_service(db_session, master, duration_minutes=30)
    await make_subscription(db_session, master, monthly_bookings_limit=50)
    await _create_bookings(db_session, master, client, service, 40)

    trigger = await check_upsell_triggers(db_session, master.id)

    assert trigger["should_upsell"] is False


@pytest.mark.asyncio
async def test_lost_revenue_trigger_monthly(db_session):
    master = await make_master(
        db_session,
        telegram_id=301005,
        settings={"last_lost_revenue_demo": _recent_iso(60)},
    )
    await make_subscription(db_session, master, monthly_bookings_limit=50)

    trigger = await check_upsell_triggers(db_session, master.id)

    assert trigger["should_upsell"] is True
    assert trigger["trigger_type"] == "lost_revenue"


@pytest.mark.asyncio
async def test_lost_revenue_trigger_recent(db_session):
    master = await make_master(
        db_session,
        telegram_id=301006,
        settings={
            "last_lost_revenue_demo": _recent_iso(15),
            "last_social_proof": _recent_iso(1),
        },
    )
    await make_subscription(db_session, master, monthly_bookings_limit=50)

    trigger = await check_upsell_triggers(db_session, master.id)

    assert trigger["should_upsell"] is False


@pytest.mark.asyncio
async def test_social_proof_trigger_weekly(db_session):
    master = await make_master(
        db_session,
        telegram_id=301007,
        settings={
            "last_lost_revenue_demo": _recent_iso(1),
            "last_social_proof": _recent_iso(10),
        },
    )
    await make_subscription(db_session, master, monthly_bookings_limit=50)

    trigger = await check_upsell_triggers(db_session, master.id)

    assert trigger["should_upsell"] is True
    assert trigger["trigger_type"] == "social_proof"


def test_build_limit_upsell_message():
    msg = build_limit_upsell_message(45, 50, "start")
    assert "45" in msg
    assert "50" in msg


def test_should_show_lost_revenue_invalid_date():
    master = type("M", (), {"settings": {"last_lost_revenue_demo": "bad-date"}})()
    assert should_show_lost_revenue_demo(master) is True


def test_should_show_social_proof_recent():
    master = type("M", (), {"settings": {"last_social_proof": datetime.now().isoformat()}})()
    assert should_show_social_proof(master) is False
