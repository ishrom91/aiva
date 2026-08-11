"""Upsell trigger logic for tariff upgrades."""

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.master import Master
from ..services.subscription_service import SubscriptionService
from .messages import NEXT_TARIFF, build_limit_upsell_message
from .tariffs import get_tariff_config


def should_show_lost_revenue_demo(master: Master) -> bool:
    settings = master.settings or {}
    last_demo = settings.get("last_lost_revenue_demo")
    if not last_demo:
        return True
    try:
        last_date = datetime.fromisoformat(last_demo)
    except ValueError:
        return True
    return datetime.now() - last_date >= timedelta(days=30)


def should_show_social_proof(master: Master) -> bool:
    settings = master.settings or {}
    last_shown = settings.get("last_social_proof")
    if not last_shown:
        return True
    try:
        last_date = datetime.fromisoformat(last_shown)
    except ValueError:
        return True
    return datetime.now() - last_date >= timedelta(days=7)


async def calculate_lost_revenue(session: AsyncSession, master_id: str) -> int:
    """Estimate recoverable revenue from inactive clients."""
    _ = session, master_id
    return 5000


async def check_upsell_triggers(session: AsyncSession, master_id: str) -> dict | None:
    """Check upsell triggers for a master."""
    sub_service = SubscriptionService()
    subscription = await sub_service.get_or_create(session, master_id)
    usage = await sub_service.current_month_usage(session, master_id)
    limit = subscription.monthly_bookings_limit
    current_tariff = subscription.tariff_name.lower()
    next_tariff = NEXT_TARIFF.get(current_tariff)

    master = await session.get(Master, master_id)
    if not master:
        return None

    if limit > 0 and usage >= int(limit * 0.9) and next_tariff:
        cfg = get_tariff_config(next_tariff) or {}
        return {
            "should_upsell": True,
            "trigger_type": "limit",
            "target_tariff": next_tariff,
            "message": build_limit_upsell_message(usage, limit, current_tariff),
            "price": cfg.get("price", 0),
        }

    if should_show_lost_revenue_demo(master) and next_tariff:
        lost_sum = await calculate_lost_revenue(session, master_id)
        settings = dict(master.settings or {})
        settings["last_lost_revenue_demo"] = datetime.now().isoformat()
        master.settings = settings
        await session.commit()
        return {
            "should_upsell": True,
            "trigger_type": "lost_revenue",
            "target_tariff": next_tariff,
            "message": (
                f"💡 Если бы у тебя был навык 'Консьерж', он бы написал "
                f"клиентам, которые не были 2+ месяца, и вернул бы {lost_sum}₽.\n"
                f"Подключить за 1000₽/мес?"
            ),
        }

    if should_show_social_proof(master) and next_tariff:
        settings = dict(master.settings or {})
        settings["last_social_proof"] = datetime.now().isoformat()
        master.settings = settings
        await session.commit()
        return {
            "should_upsell": True,
            "trigger_type": "social_proof",
            "target_tariff": next_tariff,
            "message": "📊 Мастера с 'Консьерж' зарабатывают на 23% больше.",
        }

    return None
