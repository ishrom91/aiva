from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import Subscription, Master
from ..schemas.subscription import SubscriptionCreateRequest, SubscriptionUpdateRequest
from datetime import datetime, timedelta


class SubscriptionService:
    """Service layer for subscription business logic"""
    
    def __init__(self):
        pass
    
    async def get_subscription_by_master_id(self, db_session: AsyncSession, master_id: int) -> Optional[Subscription]:
        """Get subscription by master ID"""
        result = await db_session.execute(
            select(Subscription).filter(Subscription.master_id == master_id)
        )
        return result.scalar_one_or_none()
    
    async def create_subscription(self, db_session: AsyncSession, subscription_data: SubscriptionCreateRequest) -> Subscription:
        """Create a new subscription"""
        subscription = Subscription(
            master_id=subscription_data.master_id,
            tariff_name=subscription_data.tariff_name,
            monthly_bookings_limit=subscription_data.monthly_bookings_limit,
            additional_skills=subscription_data.additional_skills or [],
            current_period_start=subscription_data.current_period_start,
            current_period_end=subscription_data.current_period_end,
            is_trial=subscription_data.is_trial
        )
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)
        return subscription
    
    async def update_subscription(self, db_session: AsyncSession, subscription_id: int, 
                                  update_data: SubscriptionUpdateRequest) -> Optional[Subscription]:
        """Update a subscription"""
        result = await db_session.execute(
            select(Subscription).filter(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return None
        
        # Update fields
        if update_data.tariff_name is not None:
            subscription.tariff_name = update_data.tariff_name
        if update_data.status is not None:
            subscription.status = update_data.status
        if update_data.monthly_bookings_limit is not None:
            subscription.monthly_bookings_limit = update_data.monthly_bookings_limit
        if update_data.additional_skills is not None:
            subscription.additional_skills = update_data.additional_skills
        if update_data.current_period_end is not None:
            subscription.current_period_end = update_data.current_period_end
        
        await db_session.commit()
        await db_session.refresh(subscription)
        return subscription
    
    async def check_booking_limit(self, db_session: AsyncSession, master_id: int) -> tuple[bool, int]:
        """
        Check if the master has exceeded their booking limit.
        Returns (is_within_limit, current_bookings_count)
        """
        # Get subscription
        subscription = await self.get_subscription_by_master_id(db_session, master_id)
        
        if not subscription:
            # If no subscription, assume limited plan
            return False, 0
        
        if subscription.monthly_bookings_limit == -1:  # Unlimited
            return True, 0
        
        # Count bookings in current period
        from ..models import Booking
        from datetime import datetime
        
        # Get current month's bookings
        now = datetime.utcnow()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        booking_result = await db_session.execute(
            select(Booking)
            .filter(
                Booking.master_id == master_id,
                Booking.created_at >= start_of_month
            )
        )
        current_bookings = len(booking_result.scalars().all())
        
        is_within_limit = current_bookings < subscription.monthly_bookings_limit
        return is_within_limit, current_bookings
    
    async def is_subscription_active(self, db_session: AsyncSession, master_id: int) -> bool:
        """Check if subscription is active"""
        subscription = await self.get_subscription_by_master_id(db_session, master_id)
        
        if not subscription:
            return False
        
        now = datetime.utcnow()
        return (
            subscription.status == "active" and 
            subscription.current_period_end > now
        )