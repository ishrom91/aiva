"""Handlers package for Aiva AI Bot."""

from . import admin, booking, start, subscription

# Export all routers
ALL_ROUTERS = [start.router, booking.router, admin.router, subscription.router]

__all__ = ["ALL_ROUTERS"]
