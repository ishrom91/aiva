from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, asc
from datetime import datetime, timedelta
from ..models import Booking, Client, Service, Master
from ..schemas.booking import BookingCreateRequest


class BookingRepository:
    """Repository for handling booking-related database operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, booking_data: BookingCreateRequest) -> Booking:
        """Create a new booking"""
        booking = Booking(
            client_id=booking_data.client_id,
            service_id=booking_data.service_id,
            datetime=booking_data.datetime,
            notes=booking_data.notes
        )
        self.session.add(booking)
        await self.session.commit()
        await self.session.refresh(booking)
        return booking
    
    async def get_by_id(self, booking_id: int) -> Optional[Booking]:
        """Get booking by ID"""
        stmt = select(Booking).where(Booking.id == booking_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_client(self, client_id: int) -> List[Booking]:
        """Get all bookings for a specific client"""
        stmt = select(Booking).where(Booking.client_id == client_id).order_by(Booking.datetime.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_upcoming_bookings(self, client_id: int, days: int = 30) -> List[Booking]:
        """Get upcoming bookings for a client within specified days"""
        now = datetime.utcnow()
        future_date = now + timedelta(days=days)
        
        stmt = select(Booking).where(
            and_(
                Booking.client_id == client_id,
                Booking.datetime >= now,
                Booking.datetime <= future_date,
                Booking.status != "cancelled"
            )
        ).order_by(Booking.datetime.asc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_available_slots(
        self, 
        service_id: int, 
        date: datetime, 
        master_id: Optional[int] = None
    ) -> List[datetime]:
        """Get available time slots for a service on a specific date"""
        from sqlalchemy import extract
        
        # Get service duration
        service_stmt = select(Service).where(Service.id == service_id)
        service_result = await self.session.execute(service_stmt)
        service = service_result.scalar_one_or_none()
        
        if not service:
            return []
        
        duration_minutes = service.duration_minutes
        
        # Get master's working hours
        master_stmt = select(Master).where(Master.id == service.master_id)
        master_result = await self.session.execute(master_stmt)
        master = master_result.scalar_one_or_none()
        
        if not master:
            return []
        
        start_hour = master.work_start_hour
        end_hour = master.work_end_hour
        
        # Get booked slots for this date
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        booked_stmt = select(Booking).where(
            and_(
                Booking.service_id == service_id,
                Booking.datetime >= start_of_day,
                Booking.datetime <= end_of_day,
                Booking.status != "cancelled"
            )
        ).order_by(Booking.datetime.asc())
        
        booked_result = await self.session.execute(booked_stmt)
        booked_slots = booked_result.scalars().all()
        
        # Calculate available slots
        available_slots = []
        current_time = start_of_day.replace(hour=start_hour, minute=0)
        end_time = start_of_day.replace(hour=end_hour, minute=0)
        
        booked_times = [booking.datetime for booking in booked_slots]
        
        while current_time < end_time:
            slot_end_time = current_time + timedelta(minutes=duration_minutes)
            
            # Check if this slot overlaps with any booked slot
            is_available = True
            for booked_time in booked_times:
                booked_end_time = booked_time + timedelta(minutes=service.duration_minutes)
                
                # Check for overlap: (current_start < booked_end) AND (booked_start < current_end)
                if (current_time < booked_end_time) and (booked_time < slot_end_time):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append(current_time)
            
            current_time += timedelta(minutes=30)  # 30-minute intervals
        
        return available_slots
    
    async def get_conflicting_bookings(
        self, 
        client_id: int, 
        service_id: int, 
        datetime: datetime,
        exclude_booking_id: Optional[int] = None
    ) -> List[Booking]:
        """Check for conflicting bookings"""
        service_stmt = select(Service).where(Service.id == service_id)
        service_result = await self.session.execute(service_stmt)
        service = service_result.scalar_one_or_none()
        
        if not service:
            return []
        
        duration_minutes = service.duration_minutes
        end_datetime = datetime + timedelta(minutes=duration_minutes)
        
        conditions = [
            Booking.client_id == client_id,
            Booking.datetime < end_datetime,
            Booking.datetime + timedelta(minutes=service.duration_minutes) > datetime,
            Booking.status != "cancelled"
        ]
        
        if exclude_booking_id:
            conditions.append(Booking.id != exclude_booking_id)
        
        stmt = select(Booking).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_status(self, booking_id: int, status: str) -> Optional[Booking]:
        """Update booking status"""
        stmt = select(Booking).where(Booking.id == booking_id)
        result = await self.session.execute(stmt)
        booking = result.scalar_one_or_none()
        
        if booking:
            booking.status = status
            await self.session.commit()
            await self.session.refresh(booking)
        
        return booking
    
    async def cancel_booking(self, booking_id: int) -> Optional[Booking]:
        """Cancel a booking by setting its status to cancelled"""
        return await self.update_status(booking_id, "cancelled")
    
    async def get_client_by_telegram_id(self, telegram_id: int) -> Optional[Client]:
        """Get client by Telegram ID"""
        stmt = select(Client).where(Client.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_master_services(self, master_id: int) -> List[Service]:
        """Get all services for a specific master"""
        stmt = select(Service).where(Service.master_id == master_id).order_by(Service.name.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()