from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import Master, Client
from ..utils.encryption import encrypt_phone
from ..database import get_db_session
from ..config import settings
import structlog

router = Router()
logger = structlog.get_logger(__name__)


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Handler for /start command.
    Registers new users or welcomes existing ones.
    """
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    username = message.from_user.username
    
    # Get database session
    async with get_db_session() as session:
        # Check if user is already registered as a client
        result = await session.execute(select(Client).filter(Client.telegram_id == user_id))
        client = result.scalar_one_or_none()
        
        if client:
            # User is already registered
            await message.answer(
                f"👋 Привет, {user_full_name}! С возвращением в Aiva AI.\n\n"
                f"Я помогаю мастерам бьюти-индустрии управлять записями, клиентами и расписанием.\n\n"
                f"Доступные команды:\n"
                f"/book - Записаться на прием\n"
                f"/my_bookings - Мои записи\n"
                f"/help - Помощь"
            )
        else:
            # New user - ask if they are a master or client
            await message.answer(
                f"👋 Привет, {user_full_name}!\n\n"
                f"Добро пожаловать в Aiva AI - помощник для мастеров бьюти-индустрии.\n\n"
                f"Я могу помочь вам:\n"
                f"• Записаться на прием к мастеру\n"
                f"• Управлять записями клиентов (если вы мастер)\n"
                f"• Отслеживать расписание и многое другое\n\n"
                f"Для начала работы:\n"
                f"• Если вы клиент, просто используйте /book для записи\n"
                f"• Если вы мастер, свяжитесь с администратором для регистрации"
            )


@router.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    """
    Handler for /help command.
    Provides help information about the bot.
    """
    await message.answer(
        "🤖 <b>Aiva AI - Помощник для бьюти-мастеров</b>\n\n"
        
        "<b>Доступные команды:</b>\n"
        "• /start - Начать работу с ботом\n"
        "• /book - Записаться на прием\n"
        "• /my_bookings - Посмотреть мои записи\n"
        "• /help - Это сообщение справки\n\n"
        
        "<b>Функции для мастеров:</b>\n"
        "• Управление записями клиентов\n"
        "• Настройка расписания\n"
        "• Отслеживание клиентской базы\n\n"
        
        "Если у вас есть вопросы, свяжитесь с поддержкой."
    )