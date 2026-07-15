from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import Master, Client, Subscription
from ..services.subscription_service import SubscriptionService
from ..billing.tariffs import TARIFFS
from ..billing.upsell_triggers import check_upsell_triggers
from ..database import get_db_session
import structlog

router = Router()
logger = structlog.get_logger(__name__)


def get_upgrade_keyboard(target_tariff: str):
    """Create keyboard for upgrade options"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"Upgrade to {TARIFFS[target_tariff]['name']}", 
                callback_data=f"upgrade_{target_tariff}"
            )
        ],
        [
            InlineKeyboardButton(text="Подробнее", callback_data=f"info_{target_tariff}")
        ]
    ])
    return keyboard


@router.message(Command("subscription"))
async def cmd_subscription(message: Message) -> None:
    """Show current subscription and available tariffs"""
    user_id = message.from_user.id
    
    async with get_db_session() as session:
        # Find master by telegram ID
        result = await session.execute(select(Master).filter(Master.telegram_id == user_id))
        master = result.scalar_one_or_none()
        
        if not master:
            await message.answer("Вы не зарегистрированы как мастер. Обратитесь к администратору.")
            return
        
        # Get subscription
        result = await session.execute(
            select(Subscription).filter(Subscription.master_id == master.id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            await message.answer(
                "У вас пока нет активной подписки.\n\n"
                "Доступные тарифы:\n\n"
                "💎 <b>Старт</b> — 990₽/мес\n"
                "- Запись клиентов\n"
                "- Напоминания за 24 часа\n"
                "- Базовый FAQ\n"
                "- До 50 записей в месяц\n\n"
                
                "⭐ <b>Профи</b> — 1 990₽/мес\n"
                "- Всё из 'Старт'\n"
                "- Навык 'Консьерж' (возврат спящих клиентов)\n"
                "- Навык 'Пост-забота'\n"
                "- До 200 записей в месяц\n\n"
                
                "🏢 <b>Салон</b> — 3 990₽/мес\n"
                "- Всё из 'Профи'\n"
                "- Навык 'Авто-Маркетолог'\n"
                "- Аналитика\n"
                "- До 5 мастеров\n"
                "- Безлимит записей"
            )
            return
        
        # Count current bookings in this period
        from datetime import datetime
        from ..models import Booking
        
        now = datetime.utcnow()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        booking_result = await session.execute(
            select(Booking)
            .filter(
                Booking.master_id == master.id,
                Booking.created_at >= start_of_month
            )
        )
        current_bookings = len(booking_result.scalars().all())
        
        tariff_info = TARIFFS.get(subscription.tariff_name, {})
        tariff_name = tariff_info.get('name', subscription.tariff_name.title())
        
        text = f"📋 <b>Ваша текущая подписка:</b> {tariff_name}\n\n"
        text += f"📊 <b>Записей в этом месяце:</b> {current_bookings}"
        
        if subscription.monthly_bookings_limit != -1:
            text += f"/{subscription.monthly_bookings_limit}\n\n"
        else:
            text += " (безлимит)\n\n"
        
        text += "<b>💎 Доступные тарифы:</b>\n\n"
        for tariff_key, tariff_info in TARIFFS.items():
            current = "✅ " if subscription.tariff_name == tariff_key else ""
            text += f"{current}<b>{tariff_info['name']}</b> — {tariff_info['price_rub']}₽/мес\n"
            text += f"   {', '.join(tariff_info['features'][:2])}...\n\n"
        
        await message.answer(text)


@router.message(Command("upgrade"))
async def cmd_upgrade(message: Message) -> None:
    """Suggest upgrade"""
    user_id = message.from_user.id
    
    async with get_db_session() as session:
        # Find master by telegram ID
        result = await session.execute(select(Master).filter(Master.telegram_id == user_id))
        master = result.scalar_one_or_none()
        
        if not master:
            await message.answer("Вы не зарегистрированы как мастер.")
            return
        
        # Count current bookings
        from datetime import datetime
        from ..models import Booking
        
        now = datetime.utcnow()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        booking_result = await session.execute(
            select(Booking)
            .filter(
                Booking.master_id == master.id,
                Booking.created_at >= start_of_month
            )
        )
        current_bookings = len(booking_result.scalars().all())
        
        # Check upsell triggers
        upsell_result = await check_upsell_triggers(master.id, current_bookings)
        
        if upsell_result["should_upsell"]:
            await message.answer(
                upsell_result["message"],
                reply_markup=get_upgrade_keyboard(upsell_result["target_tariff"])
            )
        else:
            await message.answer("У вас уже оптимальный тариф! 🎉")