"""Tests for SubscriptionService."""

from datetime import datetime, timedelta

import pytest

from src.models.master import Master
from src.models.subscription import SubscriptionStatus
from src.services.subscription_service import SubscriptionService


@pytest.mark.asyncio
async def test_get_or_create_subscription(db_session):
    master = Master(telegram_id=111222333, name="Test Master")
    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)

    service = SubscriptionService()
    sub = await service.get_or_create(db_session, master.id)

    assert sub.master_id == master.id
    assert sub.tariff_name == "start"
    assert sub.is_trial is True
    assert sub.status == SubscriptionStatus.ACTIVE


@pytest.mark.asyncio
async def test_can_book_more_within_limit(db_session):
    master = Master(telegram_id=444555666, name="Limit Master")
    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)

    service = SubscriptionService()
    sub = await service.get_or_create(db_session, master.id)
    sub.monthly_bookings_limit = 50
    await db_session.commit()

    assert await service.can_book_more(db_session, master.id) is True


@pytest.mark.asyncio
async def test_upgrade_changes_tariff(db_session):
    master = Master(telegram_id=777888999, name="Upgrade Master")
    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)

    service = SubscriptionService()
    await service.get_or_create(db_session, master.id)
    upgraded = await service.upgrade(db_session, master.id, "pro")

    assert upgraded.tariff_name == "pro"
    assert upgraded.monthly_bookings_limit == 200
