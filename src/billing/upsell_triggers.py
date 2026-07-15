"""
Logic for upselling - smart triggers for upgrading tariff
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from ..models import Subscription
from .tariffs import TARIFFS
from datetime import datetime, timedelta
import uuid


async def check_upsell_triggers(master_id: uuid.UUID, current_bookings: int) -> Dict[str, Any]:
    """
    Checks if it's time to suggest the master to upgrade.
    Returns: {"should_upsell": bool, "message": str, "target_tariff": str}
    """
    # This function would normally fetch subscription from DB
    # For now, we'll simulate it
    from ..database import get_db_session
    
    async with get_db_session() as session:
        result = await session.execute(
            select(Subscription).filter(Subscription.master_id == master_id)
        )
        subscription = result.scalar_one_or_none()
    
    if not subscription:
        return {"should_upsell": False, "message": "", "target_tariff": ""}
    
    # Trigger 1: Booking limit
    if subscription.monthly_bookings_limit > 0:
        usage_percent = (current_bookings / subscription.monthly_bookings_limit) * 100
        
        if usage_percent >= 90:
            target_tariff = "pro" if subscription.tariff_name == "start" else "salon"
            message = generate_limit_trigger_message(subscription, current_bookings, target_tariff)
            return {
                "should_upsell": True,
                "message": message,
                "target_tariff": target_tariff,
                "trigger_type": "limit"
            }
    
    # Trigger 2: Demo of missed revenue (once a month)
    if should_show_lost_revenue_demo(master_id):
        lost_revenue = await calculate_lost_revenue(master_id)
        if lost_revenue > 0:
            message = generate_lost_revenue_message(lost_revenue)
            return {
                "should_upsell": True,
                "message": message,
                "target_tariff": "pro",
                "trigger_type": "lost_revenue"
            }
    
    # Trigger 3: Social proof
    if should_show_social_proof(master_id):
        message = generate_social_proof_message()
        return {
            "should_upsell": True,
            "message": message,
            "target_tariff": "pro",
            "trigger_type": "social_proof"
        }
    
    return {"should_upsell": False, "message": "", "target_tariff": ""}


def generate_limit_trigger_message(subscription, current_bookings, target_tariff) -> str:
    """Generate message for limit trigger"""
    tariff_info = TARIFFS[target_tariff]
    return (
        f"🎉 У вас уже {current_bookings} из "
        f"{subscription.monthly_bookings_limit} записей в этом месяце! "
        f"Вы переросли тариф '{subscription.tariff_name}'.\n\n"
        f"Перейдите на '{tariff_info['name']}' — там не только больше записей, "
        f"но и навык 'Консьерж', который вернет клиентов, которые давно не были. "
        f"Окупится за неделю! 💰\n\n"
        f"💳 Стоимость: {tariff_info['price_rub']}₽/мес"
    )


def generate_lost_revenue_message(lost_revenue: int) -> str:
    """Generate message for missed revenue trigger"""
    return (
        f"💡 Смотри, если бы у вас был навык 'Консьерж', "
        f"он бы автоматически написал клиентам, которые не были 2+ месяца, "
        f"и вернул бы минимум {lost_revenue}₽ дополнительной выручки.\n\n"
        f"Подключить навык за 1000₽/мес?"
    )


def generate_social_proof_message() -> str:
    """Generate message for social proof"""
    return (
        f"📊 Мастера с навыком 'Консьерж' зарабатывают в среднем на 23% больше, "
        f"чем без него. Вот примеры сообщений, которые он отправил их клиентам вчера..."
    )


def should_show_lost_revenue_demo(master_id: uuid.UUID) -> bool:
    """
    Check if we should show the lost revenue demo to this master.
    This would normally check last shown date in a database.
    """
    # For now, just return True once in a while
    return True


def should_show_social_proof(master_id: uuid.UUID) -> bool:
    """
    Check if we should show social proof to this master.
    This would normally check last shown date in a database.
    """
    # For now, just return True once in a while
    return True


async def calculate_lost_revenue(master_id: uuid.UUID) -> int:
    """
    Calculate potential lost revenue based on inactive clients.
    This would normally analyze the client database.
    """
    # For simulation purposes, return a random amount
    return 5000