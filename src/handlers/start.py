"""Start and help handlers."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..database import get_session
from ..services.master_service import get_or_create_master
from ..services.subscription_service import SubscriptionService
from .helpers import main_menu_keyboard, persist_master_context

router = Router()


async def _show_menu(message: Message, greeting: str) -> None:
    await message.answer(
        f"{greeting}\n\nВыберите действие:",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext) -> None:
    """Register master on first /start, show menu on repeat."""
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        master, created = await get_or_create_master(
            session, user.id, user.full_name or user.first_name or "Master"
        )
        sub_service = SubscriptionService()
        await sub_service.get_or_create(session, master.id)

    await persist_master_context(state, master)

    if created:
        greeting = (
            f"👋 Привет, {master.name}!\n"
            "Aiva AI поможет принимать записи, напоминать клиентам и расти.\n"
            "Вам доступен пробный тариф «Старт» на 7 дней."
        )
    else:
        greeting = f"С возвращением, {master.name}!"

    await _show_menu(message, greeting)


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    """Show skills help."""
    await message.answer(
        "ℹ️ **Навыки Aiva AI**\n\n"
        "📅 **Запись** — `/book` — клиенты записываются через бота\n"
        "➕ **Услуги** — `/add_service` — добавьте услуги и цены\n"
        "📋 **Список** — `/services` — управление услугами\n"
        "📊 **Статистика** — `/stats` — аналитика по записям\n"
        "💳 **Подписка** — `/subscription` — тариф и лимиты\n"
        "⬆️ **Апгрейд** — `/upgrade` — расширить возможности\n\n"
        "Команды: /start /book /my_bookings /add_service /services /stats",
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "menu:help")
async def menu_help(callback: CallbackQuery) -> None:
    if callback.message:
        await help_command(callback.message)
    await callback.answer()


@router.callback_query(F.data == "menu:add_service")
async def menu_add_service(callback: CallbackQuery, state: FSMContext) -> None:
    from .admin import begin_add_service

    await begin_add_service(callback, state)


@router.callback_query(F.data == "menu:bookings")
async def menu_bookings(callback: CallbackQuery) -> None:
    from .booking import command_my_bookings_handler

    if callback.message:
        await command_my_bookings_handler(callback.message)
    await callback.answer()


@router.callback_query(F.data == "menu:subscription")
async def menu_subscription(callback: CallbackQuery) -> None:
    from .subscription import show_subscription

    await show_subscription(callback)
    await callback.answer()
