import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from src.models import Master, Subscription
from src.services.subscription_service import SubscriptionService
from src.schemas.subscription import SubscriptionCreateRequest, TariffName


@pytest.mark.asyncio
async def test_create_subscription(db_session):
    """Test creating a subscription."""
    # Create a master
    master = Master(telegram_id=987654321, name="Test Master")
    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)
    
    # Create subscription service
    service = SubscriptionService()
    
    # Create subscription
    subscription_data = SubscriptionCreateRequest(
        master_id=master.id,
        tariff_name=TariffName.START,
        monthly_bookings_limit=50,
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30)
    )
    
    subscription = await service.create_subscription(db_session, subscription_data)
    
    # Assertions
    assert subscription is not None
    assert subscription.master_id == master.id
    assert subscription.tariff_name == TariffName.START
    assert subscription.monthly_bookings_limit == 50


@pytest.mark.asyncio
async def test_check_booking_limit(db_session):
    """Test checking booking limits."""
    # Create a master
    master = Master(telegram_id=987654321, name="Test Master")
    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)
    
    # Create subscription
    subscription = Subscription(
        master_id=master.id,
        tariff_name="start",
        status="active",
        monthly_bookings_limit=50,
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30)
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)
    
    # Create subscription service
    service = SubscriptionService()
    
    # Test within limit
    is_within_limit, current_count = await service.check_booking_limit(db_session, master.id)
    assert is_within_limit is True  # Since we haven't created any bookings yet