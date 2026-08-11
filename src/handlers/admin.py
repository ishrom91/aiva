from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message(lambda msg: msg.text == "/admin")
async def admin_command(message: Message):
    """Handle the /admin command."""
    raise NotImplementedError("phase 2")
