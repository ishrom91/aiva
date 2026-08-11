"""Booking business logic."""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..billing.messages import build_limit_upsell_message
from ..exceptions import BookingConflictError, OwnershipError, SubscriptionLimitExceeded
from ..models.booking import Booking, BookingStatus
from ..models.master import Master
from ..models.service import Service
from ..services.subscription_service import SubscriptionService


class BookingService:
    """Service class for handling booking operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.subscription_service = SubscriptionService()

    async def create_booking(
        self,
        master_id: str,
        client_id: str,
        service_id: str,
        booking_datetime: datetime,
    ) -> Booking:
        master_result = await self.session.execute(
            select(Master).where(Master.id == master_id)
        )
        master = master_result.scalar_one_or_none()
        if not master or not master.is_active:
            raise OwnershipError("Master is not active")

        service_result = await self.session.execute(
            select(Service).where(Service.id == service_id)
        )
        service = service_result.scalar_one_or_none()
        if not service or service.master_id != master_id:
            raise OwnershipError("Service does not belong to this master")

        duration = service.duration_minutes
        slot_end = booking_datetime + timedelta(minutes=duration)

        conflict_stmt = select(Booking).where(
            Booking.master_id == master_id,
            Booking.status == BookingStatus.CONFIRMED,
            Booking.datetime >= booking_datetime - timedelta(hours=12),
            Booking.datetime <= booking_datetime + timedelta(hours=12),
        )
        existing_bookings = (await self.session.execute(conflict_stmt)).scalars().all()
        for existing in existing_bookings:
            existing_service = await self.session.get(Service, existing.service_id)
            existing_duration = (
                existing_service.duration_minutes if existing_service else duration
            )
            existing_end = existing.datetime + timedelta(minutes=existing_duration)
            if booking_datetime < existing_end and slot_end > existing.datetime:
                raise BookingConflictError("Time slot is already booked")

        if not await self.subscription_service.can_book_more(self.session, master_id):
            subscription = await self.subscription_service.get_or_create(
                self.session, master_id
            )
            usage = await self.subscription_service.current_month_usage(
                self.session, master_id
            )
            upsell = build_limit_upsell_message(
                usage, subscription.monthly_bookings_limit, subscription.tariff_name
            )
            raise SubscriptionLimitExceeded(
                "Monthly booking limit exceeded",
                upsell_text=upsell,
            )

        booking = Booking(
            client_id=client_id,
            service_id=service_id,
            master_id=master_id,
            datetime=booking_datetime,
            status=BookingStatus.CONFIRMED,
        )
        self.session.add(booking)
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def get_available_slots(
        self,
        master_id: str,
        date: datetime,
        service_id: str | None = None,
    ) -> list[datetime]:
        master_result = await self.session.execute(
            select(Master).where(Master.id == master_id)
        )
        master = master_result.scalar_one_or_none()
        if not master:
            return []

        start_hour = master.work_start_hour or 9
        end_hour = master.work_end_hour or 18
        date_only = date.date()

        day_start = datetime.combine(date_only, datetime.min.time()).replace(
            hour=start_hour
        )
        day_end = datetime.combine(date_only, datetime.min.time()).replace(
            hour=end_hour
        )

        bookings_stmt = (
            select(Booking, Service.duration_minutes)
            .join(Service, Booking.service_id == Service.id)
            .where(
                Booking.master_id == master_id,
                Booking.status == BookingStatus.CONFIRMED,
                Booking.datetime >= day_start,
                Booking.datetime < day_end + timedelta(days=1),
            )
        )
        rows = (await self.session.execute(bookings_stmt)).all()

        booked_ranges: list[tuple[datetime, datetime]] = []
        for booking, duration_minutes in rows:
            booked_ranges.append(
                (
                    booking.datetime,
                    booking.datetime + timedelta(minutes=duration_minutes),
                )
            )

        services_stmt = select(Service).where(
            Service.master_id == master_id, Service.is_active.is_(True)
        )
        if service_id:
            svc = await self.session.get(Service, service_id)
            default_duration = svc.duration_minutes if svc else 60
        else:
            services = (await self.session.execute(services_stmt)).scalars().all()
            default_duration = min((s.duration_minutes for s in services), default=60)

        slots: list[datetime] = []
        current = day_start
        while current + timedelta(minutes=default_duration) <= day_end:
            slot_end = current + timedelta(minutes=default_duration)
            overlap = any(
                current < booked_end and booked_start < slot_end
                for booked_start, booked_end in booked_ranges
            )
            if not overlap:
                slots.append(current)
            current += timedelta(minutes=30)

        return slots

    async def cancel_booking(self, booking_id: str, master_id: str) -> Booking:
        booking = await self.session.get(Booking, booking_id)
        if not booking:
            raise OwnershipError("Booking not found")
        if booking.master_id != master_id:
            raise OwnershipError("Booking does not belong to this master")

        booking.status = BookingStatus.CANCELLED
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def mark_no_show(self, booking_id: str, master_id: str) -> Booking:
        booking = await self.session.get(Booking, booking_id)
        if not booking:
            raise OwnershipError("Booking not found")
        if booking.master_id != master_id:
            raise OwnershipError("Booking does not belong to this master")

        booking.status = BookingStatus.NO_SHOW
        await self.session.commit()
        await self.session.refresh(booking)
        return booking
