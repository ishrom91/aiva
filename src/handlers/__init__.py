"""Handlers package for Aiva AI Bot."""

from . import admin, booking, faq, retention, start, subscription

# FAQ router last: catches free text outside FSM
ALL_ROUTERS = [
    start.router,
    booking.router,
    admin.router,
    subscription.router,
    retention.router,
    faq.router,
]

__all__ = ["ALL_ROUTERS"]
