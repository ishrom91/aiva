"""
Tariff definitions for Aiva AI Bot
"""

from typing import Dict, Optional

TARIFFS = {
    "start": {
        "name": "Старт",
        "price": 990,
        "monthly_bookings_limit": 50,
        "skills": ["booking"],
        "features": ["basic_faq", "reminders"],
    },
    "pro": {
        "name": "Профи",
        "price": 1990,
        "monthly_bookings_limit": 200,
        "skills": ["booking", "retention", "post_care"],
        "features": ["ai_faq_rag", "advanced_reminders"],
    },
    "salon": {
        "name": "Салон",
        "price": 3990,
        "monthly_bookings_limit": -1,  # Unlimited
        "skills": ["booking", "retention", "marketing", "analytics"],
        "features": ["multi_master_support", "advanced_analytics"],
    },
}


def get_tariff_config(tariff_name: str) -> Optional[Dict]:
    """
    Get tariff configuration by name
    """
    return TARIFFS.get(tariff_name.lower())


VOICE_ADDON = {
    "name": "Голос",
    "price": 990,
    "skill": "voice",
    "features": ["calls", "alice_integration"],
}
