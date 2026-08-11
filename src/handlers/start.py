from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message(lambda msg: msg.text == "/start")
async def start_command(message: Message):
    """Handle the /start command."""
    raise NotImplementedError("phase 2")


@router.message(lambda msg: msg.text == "/help")
async def help_command(message: Message):
    """Handle the /help command."""
    raise NotImplementedError("phase 2")
