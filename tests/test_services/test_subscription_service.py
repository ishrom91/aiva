"""Tests for SubscriptionService."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import func, select

from src.models.subscription import Subscription, SubscriptionStatus
from src.services.subscription_service import SubscriptionService
from tests.conftest import (
    make_booking,
    make_client,
    make_master,
    make_service,
    make_subscription,
)


@pytest.mark.asyncio
async def test_get_or_create_creates_new(db_session):
    master = await make_master(db_session, telegram_id=201001)
    service = SubscriptionService()

    sub = await service.get_or_create(db_session, master.id)

    assert sub.master_id == master.id
    assert sub.tariff_name == "start"
    assert sub.is_trial is True
    assert sub.status == SubscriptionStatus.ACTIVE


@pytest.mark.asyncio
async def test_get_or_create_returns_existing(db_session):
    master = await make_master(db_session, telegram_id=201002)
    existing = await make_subscription(db_session, master, tariff_name="pro", is_trial=False)
    service = SubscriptionService()

    sub = await service.get_or_create(db_session, master.id)

    assert sub.id == existing.id
    assert sub.tariff_name == "pro"
    count = await db_session.scalar(
        select(func.count())
        .select_from(Subscription)
        .where(Subscription.master_id == master.id)
    )
    assert count == 1


@pytest.mark.asyncio
async def test_current_month_usage(db_session):
    master = await make_master(db_session, telegram_id=201003)
    client = await make_client(db_session, master, telegram_id=201004)
    svc = await make_service(db_session, master)

    now = datetime.now()
    current_month = now.replace(day=15, hour=12, minute=0, second=0, microsecond=0)
    past_month = (now.replace(day=1) - timedelta(days=1)).replace(
        hour=12, minute=0, second=0, microsecond=0
    )

    for i in range(10):
        await make_booking(
            db_session,
            master,
            client,
            svc,
            current_month + timedelta(hours=i),
        )
    for i in range(5):
        await make_booking(
            db_session,
            master,
            client,
            svc,
            past_month + timedelta(hours=i),
        )

    service = SubscriptionService()
    usage = await service.current_month_usage(db_session, master.id)
    assert usage == 10


@pytest.mark.asyncio
async def test_can_book_more_within_limit(db_session):
    master = await make_master(db_session, telegram_id=201005)
    client = await make_client(db_session, master, telegram_id=201006)
    svc = await make_service(db_session, master, duration_minutes=30)
    await make_subscription(db_session, master, monthly_bookings_limit=50)

    base = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )
    for i in range(30):
        await make_booking(db_session, master, client, svc, base + timedelta(minutes=30 * i))

    service = SubscriptionService()
    assert await service.can_book_more(db_session, master.id) is True


@pytest.mark.asyncio
async def test_can_book_more_exceeded(db_session):
    master = await make_master(db_session, telegram_id=201007)
    client = await make_client(db_session, master, telegram_id=201008)
    svc = await make_service(db_session, master, duration_minutes=30)
    await make_subscription(db_session, master, monthly_bookings_limit=50)

    base = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )
    for i in range(50):
        await make_booking(db_session, master, client, svc, base + timedelta(minutes=30 * i))

    service = SubscriptionService()
    assert await service.can_book_more(db_session, master.id) is False


@pytest.mark.asyncio
async def test_upgrade(db_session):
    master = await make_master(db_session, telegram_id=201009)
    await make_subscription(db_session, master, tariff_name="start", monthly_bookings_limit=50)
    service = SubscriptionService()

    upgraded = await service.upgrade(db_session, master.id, "pro")

    assert upgraded.tariff_name == "pro"
    assert upgraded.monthly_bookings_limit == 200


@pytest.mark.asyncio
async def test_create_subscription(db_session):
    master = await make_master(db_session, telegram_id=201010)
    service = SubscriptionService()

    sub = await service.create_subscription(db_session, master.id, "pro", is_trial=False)

    assert sub is not None
    assert sub.tariff_name == "pro"
    assert sub.is_trial is False


@pytest.mark.asyncio
async def test_check_subscription_limits_exceeded(db_session):
    master = await make_master(db_session, telegram_id=201011)
    client = await make_client(db_session, master, telegram_id=201012)
    svc = await make_service(db_session, master, duration_minutes=30)
    await make_subscription(db_session, master, monthly_bookings_limit=2)

    base = datetime.now().replace(hour=11, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )
    await make_booking(db_session, master, client, svc, base)
    await make_booking(db_session, master, client, svc, base + timedelta(hours=1))

    service = SubscriptionService()
    limits = await service.check_subscription_limits(db_session, master.id)

    assert limits["can_book"] is False
    assert limits["reason"] == "monthly_limit_exceeded"
