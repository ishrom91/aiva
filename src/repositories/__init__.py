"""Repositories package for Aiva AI Bot."""

from .booking_repo import BookingRepository
from .interaction_repo import InteractionRepo

BookingRepo = BookingRepository

__all__ = ["BookingRepository", "BookingRepo", "InteractionRepo"]
