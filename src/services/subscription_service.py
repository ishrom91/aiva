"""Subscription business logic."""

import json
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..billing.tariffs import get_tariff_config
from ..models.master import Master
from ..models.subscription import Subscription, SubscriptionStatus
from ..repositories.booking_repo import BookingRepo


class SubscriptionService:
    """Service class for handling subscription operations."""

    async def get_or_create(
        self, session: AsyncSession, master_id: str
    ) -> Subscription:
        subscription = await self.get_master_subscription(session, master_id)
        if subscription:
            return subscription

        tariff = get_tariff_config("start")
        if not tariff:
            raise ValueError("Default tariff 'start' is not configured")

        now = datetime.now()
        subscription = Subscription(
            master_id=master_id,
            tariff_name="start",
            status=SubscriptionStatus.ACTIVE,
            monthly_bookings_limit=tariff["monthly_bookings_limit"],
            additional_skills=json.dumps(tariff.get("skills", [])),
            current_period_start=now,
            current_period_end=now + timedelta(days=7),
            is_trial=True,
        )
        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)
        return subscription

    async def current_month_usage(self, session: AsyncSession, master_id: str) -> int:
        return await BookingRepo(session).count_current_month(master_id)

    async def can_book_more(self, session: AsyncSession, master_id: str) -> bool:
        subscription = await self.get_or_create(session, master_id)
        if subscription.monthly_bookings_limit == -1:
            return True
        usage = await self.current_month_usage(session, master_id)
        return usage < subscription.monthly_bookings_limit

    async def upgrade(
        self, session: AsyncSession, master_id: str, new_tariff: str
    ) -> Subscription:
        tariff = get_tariff_config(new_tariff)
        if not tariff:
            raise ValueError(f"Unknown tariff: {new_tariff}")

        subscription = await self.get_or_create(session, master_id)
        subscription.tariff_name = new_tariff.lower()
        subscription.monthly_bookings_limit = tariff["monthly_bookings_limit"]
        subscription.additional_skills = json.dumps(tariff.get("skills", []))
        subscription.is_trial = False
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.current_period_end = subscription.current_period_end + timedelta(
            days=30
        )
        await session.commit()
        await session.refresh(subscription)
        return subscription

    async def get_master_subscription(
        self, session: AsyncSession, master_id: str
    ) -> Subscription | None:
        stmt = select(Subscription).where(Subscription.master_id == master_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_subscription(
        self,
        session: AsyncSession,
        master_id: str,
        tariff_name: str,
        is_trial: bool = False,
        period_days: int = 30,
    ) -> Subscription | None:
        master_result = await session.execute(
            select(Master).where(Master.id == master_id)
        )
        if master_result.scalar_one_or_none() is None:
            return None

        tariff_config = get_tariff_config(tariff_name)
        if not tariff_config:
            return None

        start_date = datetime.now()
        end_date = start_date + timedelta(days=period_days)

        subscription = Subscription(
            master_id=master_id,
            tariff_name=tariff_name.lower(),
            status=SubscriptionStatus.ACTIVE,
            monthly_bookings_limit=tariff_config["monthly_bookings_limit"],
            additional_skills=json.dumps(tariff_config.get("skills", [])),
            current_period_start=start_date,
            current_period_end=end_date,
            is_trial=is_trial,
        )
        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)
        return subscription

    async def check_subscription_limits(
        self, session: AsyncSession, master_id: str
    ) -> dict:
        subscription = await self.get_master_subscription(session, master_id)

        if not subscription or subscription.status != SubscriptionStatus.ACTIVE:
            return {"can_book": False, "reason": "no_active_subscription", "limits": {}}

        booking_repo = BookingRepo(session)
        period_bookings = await booking_repo.get_bookings_in_range(
            master_id,
            subscription.current_period_start,
            subscription.current_period_end,
            exclude_cancelled=True,
        )
        current_bookings = len(period_bookings)

        can_book = True
        reason = ""

        if subscription.monthly_bookings_limit != -1:
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
        session: AsyncSession,
        subscription_id: str,
        new_status: SubscriptionStatus,
    ) -> Subscription | None:
        stmt = select(Subscription).where(Subscription.id == subscription_id)
        result = await session.execute(stmt)
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.status = new_status
            await session.commit()
            return subscription
        return None

    async def extend_subscription_period(
        self, session: AsyncSession, subscription_id: str, months: int = 1
    ) -> Subscription | None:
        stmt = select(Subscription).where(Subscription.id == subscription_id)
        result = await session.execute(stmt)
        subscription = result.scalar_one_or_none()

        if subscription and subscription.status == SubscriptionStatus.ACTIVE:
            subscription.current_period_end = (
                subscription.current_period_end + timedelta(days=30 * months)
            )
            await session.commit()
            await session.refresh(subscription)
            return subscription
        return None
