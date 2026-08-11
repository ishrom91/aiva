import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from src.models import Master, Subscription
from src.services.subscription_service import SubscriptionService
from src.schemas.subscription import SubscriptionCreate as SubscriptionCreateRequest


@pytest.mark.skip(reason="phase 2")
@pytest.mark.asyncio
async def test_create_subscription(db_session):
    """Test creating a subscription."""
    master = Master(telegram_id=987654321, name="Test Master")
    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)

    service = SubscriptionService()

    subscription_data = SubscriptionCreateRequest(
        master_id=master.id,
        tariff_name="start",
        monthly_bookings_limit=50,
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30),
    )

    subscription = await service.create_subscription(db_session, subscription_data)

    assert subscription is not None
    assert subscription.master_id == master.id
    assert subscription.tariff_name == "start"
    assert subscription.monthly_bookings_limit == 50


@pytest.mark.skip(reason="phase 2")
@pytest.mark.asyncio
async def test_check_booking_limit(db_session):
    """Test checking booking limits."""
    master = Master(telegram_id=987654321, name="Test Master")
    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)

    subscription = Subscription(
        master_id=master.id,
        tariff_name="start",
        status="active",
        monthly_bookings_limit=50,
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30),
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)

    service = SubscriptionService()

    is_within_limit, current_count = await service.check_booking_limit(
        db_session, master.id
    )
    assert is_within_limit is True


@pytest.mark.skip(reason="phase 2")
async def test_get_or_create_default():
    """Test get_or_create with default subscription."""
    raise NotImplementedError("phase 2")


@pytest.mark.skip(reason="phase 2")
async def test_can_book_more_on_limit():
    """Test can_book_more at subscription limit."""
    raise NotImplementedError("phase 2")
