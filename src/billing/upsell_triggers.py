"""
Logic for upselling - smart triggers for upgrading tariff
"""


async def check_upsell_triggers(master_id: str, current_bookings: int) -> dict:
    """Check if any upsell triggers should be activated for a master.

    Returns a dict with should_upsell, message, target_tariff, and trigger_type.
    """
    raise NotImplementedError("phase 2")


async def should_show_lost_revenue_demo():
    """Check if lost revenue demo should be shown.

    TODO: Implement logic based on time flags or other business metrics
    """
    raise NotImplementedError("phase 2")


async def should_show_social_proof():
    """Check if social proof should be shown.

    TODO: Implement logic based on time flags or other business metrics
    """
    raise NotImplementedError("phase 2")


async def calculate_lost_revenue(master_id: int) -> int:
    """
    Calculate potential lost revenue based on inactive clients.
    This would normally analyze the client database.
    """
    # For simulation purposes, return a random amount
    return 5000
