from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..billing.tariffs import get_tariff_config
from ..models.master import Master
from ..models.subscription import Subscription, SubscriptionStatus


class SubscriptionService:
    """Service class for handling subscription operations."""

    async def get_or_create(self, master_id: str) -> Any:
        """Get existing or create a new subscription for a master."""
        raise NotImplementedError("phase 2")

    async def current_month_usage(self, master_id: str) -> int:
        """Get the number of bookings made by a master in the current month."""
        raise NotImplementedError("phase 2")

    async def can_book_more(self, master_id: str) -> bool:
        """Check if a master can book more appointments based on their subscription."""
        raise NotImplementedError("phase 2")

    async def upgrade(self, master_id: str, tariff: str) -> bool:
        """Upgrade a master's subscription to a new tariff."""
        raise NotImplementedError("phase 2")

    async def get_master_subscription(
        self, db_session: AsyncSession, master_id: int
    ) -> Optional[Subscription]:
        """
        Get subscription for a master
        """
        stmt = select(Subscription).where(Subscription.master_id == master_id)
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_subscription(
        self,
        db_session: AsyncSession,
        master_id: int,
        tariff_name: str,
        is_trial: bool = False,
        period_months: int = 1,
    ) -> Optional[Subscription]:
        """
        Create a new subscription for a master
        """
        # Check if master exists
        master_stmt = select(Master).where(Master.id == master_id)
        master_result = await db_session.execute(master_stmt)
        master = master_result.scalar_one_or_none()

        if not master:
            return None

        # Get tariff configuration
        tariff_config = get_tariff_config(tariff_name)
        if not tariff_config:
            return None

        # Calculate subscription period
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30 * period_months)

        # Create subscription
        subscription = Subscription(
            master_id=master_id,
            tariff_name=tariff_name,
            status=SubscriptionStatus.ACTIVE,
            monthly_bookings_limit=tariff_config.monthly_bookings_limit,
            additional_skills=tariff_config.additional_skills,
            current_period_start=start_date,
            current_period_end=end_date,
            is_trial=is_trial,
        )

        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)

        return subscription

    async def check_subscription_limits(
        self, db_session: AsyncSession, master_id: int
    ) -> dict:
        """
        Check if master has exceeded their subscription limits
        """
        subscription = await self.get_master_subscription(db_session, master_id)

        if not subscription or subscription.status != SubscriptionStatus.ACTIVE:
            return {"can_book": False, "reason": "no_active_subscription", "limits": {}}

        # Count bookings in current period
        from ..models.booking import Booking, BookingStatus

        booking_stmt = select(Booking).where(
            Booking.master_id == master_id,
            Booking.datetime >= subscription.current_period_start,
            Booking.datetime <= subscription.current_period_end,
            Booking.status != BookingStatus.CANCELLED,
        )
        booking_result = await db_session.execute(booking_stmt)
        current_bookings = len(booking_result.scalars().all())

        # Check limits
        can_book = True
        reason = ""

        if subscription.monthly_bookings_limit != -1:  # -1 means unlimited
            if current_bookings >= subscription.monthly_bookings_limit:
                can_book = False
                reason = "monthly_limit_exceeded"

        return {
            "can_book": can_book,
            "reason": reason,
            "limits": {
                "monthly_bookings_limit": subscription.monthly_bookings_limit,
                "current_bookings_count": current_bookings,
                "remaining_bookings": subscription.monthly_bookings_limit
                - current_bookings
                if subscription.monthly_bookings_limit != -1
                else float("inf"),
            },
        }

    async def update_subscription_status(
        self,
        db_session: AsyncSession,
        subscription_id: int,
        new_status: SubscriptionStatus,
    ):
        """
        Update subscription status
        """
        stmt = select(Subscription).where(Subscription.id == subscription_id)
        result = await db_session.execute(stmt)
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.status = new_status
            await db_session.commit()
            return subscription

        return None

    async def extend_subscription_period(
        self, db_session: AsyncSession, subscription_id: int, months: int = 1
    ):
        """
        Extend subscription period by specified months
        """
        stmt = select(Subscription).where(Subscription.id == subscription_id)
        result = await db_session.execute(stmt)
        subscription = result.scalar_one_or_none()

        if subscription and subscription.status == SubscriptionStatus.ACTIVE:
            # Extend from current end date
            new_end_date = subscription.current_period_end + timedelta(days=30 * months)
            subscription.current_period_end = new_end_date
            await db_session.commit()
            await db_session.refresh(subscription)
            return subscription

        return None
