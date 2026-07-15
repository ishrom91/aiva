from typing import List, Optional
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.booking_repo import BookingRepository
from ..models import Client, Service, Master, Booking
from ..schemas.booking import BookingCreateRequest
from ..utils.encryption import decrypt_phone


class BookingService:
    """Service layer for booking business logic"""
    
    def __init__(self, repo: BookingRepository):
        self.repo = repo
    
    async def create_booking(
        self, 
        db_session: AsyncSession, 
        client_telegram_id: int, 
        service_id: int, 
        datetime_str: str
    ) -> Optional[Booking]:
        """
        Create a new booking with validation
        """
        # Parse datetime string
        try:
            booking_datetime = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except ValueError:
            return None
        
        # Get client by telegram ID
        client = await self.repo.get_client_by_telegram_id(client_telegram_id)
        if not client:
            return None
        
        # Get service to validate and get master ID
        service_stmt = select(Service).where(Service.id == service_id)
        service_result = await db_session.execute(service_stmt)
        service = service_result.scalar_one_or_none()
        if not service:
            return None
        
        # Check for conflicts
        conflicts = await self.repo.get_conflicting_bookings(
            client_id=client.id,
            service_id=service_id,
            datetime=booking_datetime
        )
        
        if conflicts:
            return None  # Conflict found
        
        # Create booking request object
        booking_request = BookingCreateRequest(
            client_id=client.id,
            service_id=service_id,
            datetime=booking_datetime
        )
        
        # Create the booking
        booking = await self.repo.create(booking_request)
        
        # Update client's reliability score if needed
        # For now, we'll just return the booking
        return booking
    
    async def get_available_slots(
        self, 
        db_session: AsyncSession, 
        service_id: int, 
        date_obj: date
    ) -> List[datetime]:
        """
        Get available time slots for a service on a specific date
        """
        # Convert date to datetime at midnight
        date_datetime = datetime.combine(date_obj, datetime.min.time())
        return await self.repo.get_available_slots(service_id, date_datetime)
    
    async def get_available_dates(
        self, 
        db_session: AsyncSession, 
        service_id: int,
        days_ahead: int = 14
    ) -> List[date]:
        """
        Get available dates for booking in the next N days
        """
        available_dates = []
        today = date.today()
        
        for i in range(days_ahead):
            current_date = today + timedelta(days=i)
            
            # Check if this date has available slots
            slots = await self.get_available_slots(db_session, service_id, current_date)
            if slots:
                available_dates.append(current_date)
        
        return available_dates
    
    async def get_available_time_slots(
        self, 
        db_session: AsyncSession, 
        service_id: int, 
        date_str: str
    ) -> List[datetime]:
        """
        Get available time slots for a specific date and service
        """
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return []
        
        return await self.get_available_slots(db_session, service_id, date_obj)
    
    async def cancel_booking(self, booking_id: int) -> Optional[Booking]:
        """
        Cancel a booking
        """
        return await self.repo.cancel_booking(booking_id)
    
    async def get_client_bookings(self, client_telegram_id: int) -> List[Booking]:
        """
        Get all bookings for a client
        """
        client = await self.repo.get_client_by_telegram_id(client_telegram_id)
        if not client:
            return []
        
        return await self.repo.get_by_client(client.id)
    
    async def get_master_services(self, db_session: AsyncSession, master_telegram_id: int) -> List[Service]:
        """
        Get all services for a master identified by telegram ID
        """
        # First get the master
        master_stmt = select(Master).where(Master.telegram_id == master_telegram_id)
        master_result = await db_session.execute(master_stmt)
        master = master_result.scalar_one_or_none()
        
        if not master:
            return []
        
        # Get services for this master
        return await self.repo.get_master_services(master.id)


# Import here to avoid circular import
from sqlalchemy import select