"""
Subscription handler for Aiva AI Bot.
"""

from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message(lambda msg: msg.text == "/subscription")
async def subscription_command(message: Message):
    """Handle the /subscription command."""
    raise NotImplementedError("phase 2")


@router.message(lambda msg: msg.text == "/upgrade")
async def upgrade_command(message: Message):
    """Handle the /upgrade command."""
    raise NotImplementedError("phase 2")
