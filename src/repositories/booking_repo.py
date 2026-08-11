"""Repository for booking operations in Aiva AI Bot."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.booking import Booking, BookingStatus
from ..models.service import Service


class BookingRepo:
    """Repository class for booking operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        client_id: str,
        service_id: str,
        master_id: str,
        booking_datetime: datetime,
        status: BookingStatus = BookingStatus.CONFIRMED,
    ) -> Booking:
        booking = Booking(
            client_id=client_id,
            service_id=service_id,
            master_id=master_id,
            datetime=booking_datetime,
            status=status,
        )
        self.session.add(booking)
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def get_by_id(self, booking_id: str) -> Booking | None:
        return await self.session.get(Booking, booking_id)

    async def list_by_master(
        self,
        master_id: str,
        *,
        status: BookingStatus | None = None,
    ) -> list[Booking]:
        stmt = select(Booking).where(Booking.master_id == master_id)
        if status is not None:
            stmt = stmt.where(Booking.status == status)
        stmt = stmt.order_by(Booking.datetime.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_confirmed_near(
        self,
        master_id: str,
        center: datetime,
        *,
        hours: int = 12,
    ) -> list[Booking]:
        from datetime import timedelta

        stmt = select(Booking).where(
            Booking.master_id == master_id,
            Booking.status == BookingStatus.CONFIRMED,
            Booking.datetime >= center - timedelta(hours=hours),
            Booking.datetime <= center + timedelta(hours=hours),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_bookings_in_range(
        self,
        master_id: str,
        start_date: datetime,
        end_date: datetime,
        *,
        exclude_cancelled: bool = False,
    ) -> list[Booking]:
        stmt = select(Booking).where(
            Booking.master_id == master_id,
            Booking.datetime >= start_date,
            Booking.datetime <= end_date,
        )
        if exclude_cancelled:
            stmt = stmt.where(Booking.status != BookingStatus.CANCELLED)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_confirmed_with_duration_for_day(
        self,
        master_id: str,
        day_start: datetime,
        day_end: datetime,
    ) -> list[tuple[Booking, int]]:
        stmt = (
            select(Booking, Service.duration_minutes)
            .join(Service, Booking.service_id == Service.id)
            .where(
                Booking.master_id == master_id,
                Booking.status == BookingStatus.CONFIRMED,
                Booking.datetime >= day_start,
                Booking.datetime < day_end,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def count_current_month(self, master_id: str) -> int:
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        stmt = select(func.count(Booking.id)).where(
            Booking.master_id == master_id,
            Booking.status == BookingStatus.CONFIRMED,
            Booking.datetime >= month_start,
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def save(self, booking: Booking) -> Booking:
        await self.session.commit()
        await self.session.refresh(booking)
        return booking
