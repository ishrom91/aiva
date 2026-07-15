import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from src.models import Client, Master, Service, Booking
from src.services.booking_service import BookingService
from src.repositories.booking_repo import BookingRepository


@pytest.mark.asyncio
async def test_create_booking_success(db_session):
    """Test successful booking creation."""
    # Create a master
    master = Master(telegram_id=987654321, name="Test Master")
    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)
    
    # Create a client
    client = Client(telegram_id=123456789, master_id=master.id, phone="encrypted_phone", name="Test Client")
    db_session.add(client)
    await db_session.commit()
    await db_session.refresh(client)
    
    # Create a service
    service = Service(master_id=master.id, name="Manicure", duration_minutes=60, price=2500.0)
    db_session.add(service)
    await db_session.commit()
    await db_session.refresh(service)
    
    # Create repository and service
    repo = BookingRepository(db_session)
    booking_service = BookingService(repo)
    
    # Define booking datetime
    future_datetime = datetime.now() + timedelta(days=1)
    
    # Create booking
    booking = await booking_service.create_booking(
        db_session=db_session,
        client_telegram_id=client.telegram_id,
        service_id=service.id,
        datetime_str=future_datetime.isoformat()
    )
    
    # Assertions
    assert booking is not None
    assert booking.client_id == client.id
    assert booking.service_id == service.id
    assert booking.master_id == master.id
    assert booking.status == "confirmed"


@pytest.mark.asyncio
async def test_get_available_dates(db_session):
    """Test getting available dates for booking."""
    # Create a master
    master = Master(telegram_id=987654321, name="Test Master", work_start_hour=9, work_end_hour=18)
    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)
    
    # Create a client
    client = Client(telegram_id=123456789, master_id=master.id, phone="encrypted_phone", name="Test Client")
    db_session.add(client)
    await db_session.commit()
    await db_session.refresh(client)
    
    # Create a service
    service = Service(master_id=master.id, name="Manicure", duration_minutes=60, price=2500.0)
    db_session.add(service)
    await db_session.commit()
    await db_session.refresh(service)
    
    # Create repository and service
    repo = BookingRepository(db_session)
    booking_service = BookingService(repo)
    
    # Get available dates
    available_dates = await booking_service.get_available_dates(
        db_session=db_session,
        service_id=service.id,
        days_ahead=7
    )
    
    # Should return at least today and some future dates
    assert len(available_dates) > 0