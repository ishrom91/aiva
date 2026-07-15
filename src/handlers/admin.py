from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models import Master, Client, Service, Booking
from ..database import get_db_session
from ..config import settings
import structlog

router = Router()
logger = structlog.get_logger(__name__)

# List of admin user IDs (should be configured in settings or database)
ADMIN_USER_IDS = []  # Will be populated from settings or database


@router.message(Command("admin"))
async def command_admin_handler(message: Message) -> None:
    """
    Handler for /admin command.
    Provides admin panel access for authorized users.
    """
    user_id = message.from_user.id
    
    # Check if user is admin (this would typically be checked against a database or settings)
    if str(user_id) not in getattr(settings, 'ADMIN_USER_IDS', []):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    await message.answer(
        "🔐 <b>Панель администратора</b>\n\n"
        "<b>Доступные команды:</b>\n"
        "• /stats - Статистика по боту\n"
        "• /add_service - Добавить новую услугу\n"
        "• /manage_clients - Управление клиентами\n"
        "• /broadcast - Отправить сообщение всем пользователям"
    )


@router.message(Command("stats"))
async def command_stats_handler(message: Message) -> None:
    """
    Handler for /stats command.
    Shows statistics for the bot.
    """
    user_id = message.from_user.id
    
    # Check if user is admin
    if str(user_id) not in getattr(settings, 'ADMIN_USER_IDS', []):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    async with get_db_session() as session:
        # Count masters
        masters_count = await session.execute(select(func.count(Master.id)))
        masters_count = masters_count.scalar()
        
        # Count clients
        clients_count = await session.execute(select(func.count(Client.id)))
        clients_count = clients_count.scalar()
        
        # Count services
        services_count = await session.execute(select(func.count(Service.id)))
        services_count = services_count.scalar()
        
        # Count bookings (today)
        from datetime import date
        today = date.today()
        bookings_today = await session.execute(
            select(func.count(Booking.id)).filter(
                func.date(Booking.datetime) == today
            )
        )
        bookings_today = bookings_today.scalar()
        
        # Count total bookings
        total_bookings = await session.execute(select(func.count(Booking.id)))
        total_bookings = total_bookings.scalar()
        
        stats_message = (
            "📊 <b>Статистика Aiva AI</b>\n\n"
            f"Мастеров: <b>{masters_count}</b>\n"
            f"Клиентов: <b>{clients_count}</b>\n"
            f"Услуг: <b>{services_count}</b>\n"
            f"Всего записей: <b>{total_bookings}</b>\n"
            f"Записей сегодня: <b>{bookings_today}</b>"
        )
        
        await message.answer(stats_message)


@router.message(Command("add_service"))
async def command_add_service_handler(message: Message) -> None:
    """
    Handler for /add_service command.
    Allows admins to add new services for masters.
    """
    user_id = message.from_user.id
    
    # Check if user is admin
    if str(user_id) not in getattr(settings, 'ADMIN_USER_IDS', []):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    # This would normally trigger a multi-step process to add a service
    # For now, just inform the admin
    await message.answer(
        "🔧 <b>Добавление новой услуги</b>\n\n"
        "Для добавления новой услуги, пожалуйста, укажите:\n"
        "1. Имя мастера (Telegram ID или имя)\n"
        "2. Название услуги\n"
        "3. Продолжительность (в минутах)\n"
        "4. Стоимость\n\n"
        "Пример: /add_service 123456789 'Маникюр гель-лак' 60 2500"
    )


@router.message(Command("broadcast"))
async def command_broadcast_handler(message: Message) -> None:
    """
    Handler for /broadcast command.
    Allows admins to send messages to all users.
    """
    user_id = message.from_user.id
    
    # Check if user is admin
    if str(user_id) not in getattr(settings, 'ADMIN_USER_IDS', []):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    # Extract the message to broadcast
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer(
            "❌ Для отправки сообщения всем пользователям используйте:\n"
            "/broadcast текст_сообщения"
        )
        return
    
    broadcast_message = command_parts[1]
    
    # In a real implementation, we would iterate through all users and send the message
    # For now, just acknowledge the command
    await message.answer(f"📢 Сообщение будет отправлено всем пользователям:\n\n{broadcast_message}")
    
    # Log the broadcast action
    logger.info("Broadcast message sent by admin", admin_id=user_id, message=broadcast_message)