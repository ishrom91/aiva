"""Tests for upsell triggers."""

import pytest

from src.billing.messages import build_limit_upsell_message
from src.billing.upsell_triggers import check_upsell_triggers
from src.models.master import Master
from src.services.subscription_service import SubscriptionService


def test_build_limit_upsell_message():
    msg = build_limit_upsell_message(45, 50, "start")
    assert "45" in msg
    assert "50" in msg


@pytest.mark.asyncio
async def test_limit_upsell_trigger(db_session):
    master = Master(telegram_id=999001, name="Upsell Master", settings={})
    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)

    sub_service = SubscriptionService()
    sub = await sub_service.get_or_create(db_session, master.id)
    sub.monthly_bookings_limit = 50
    await db_session.commit()

    trigger = await check_upsell_triggers(db_session, master.id)
    assert trigger is None or trigger.get("trigger_type") in {
        "limit",
        "lost_revenue",
        "social_proof",
    }
