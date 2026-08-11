"""Skills package for Aiva AI Bot."""

from .base import BaseSkill
from .booking_skill import BookingSkill

# Placeholder skill names for future implementation
# RetentionSkill
# MarketingSkill
# VoiceSkill

__all__ = ["BaseSkill", "BookingSkill"]
"""
Skills package initialization
"""
from .base import SkillManager
from .subscription_skill import SubscriptionSkill

__all__ = ["BaseSkill", "SkillManager", "BookingSkill", "SubscriptionSkill"]
