"""Admin handlers for masters."""

from datetime import datetime
from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import func, select

from ..database import get_session
from ..models.booking import Booking, BookingStatus
from ..models.master_analytics import MasterAnalytics
from ..models.service import Service
from ..services.master_service import get_master_by_telegram_id
from .helpers import persist_master_context

router = Router()


class AddServiceStates(StatesGroup):
    name = State()
    duration = State()
    price = State()


async def begin_add_service(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return

    async with get_session() as session:
        master = await get_master_by_telegram_id(session, callback.from_user.id)
        if not master:
            await callback.message.answer("Сначала выполните /start")
            await callback.answer()
            return
        await persist_master_context(state, master)

    await callback.message.answer("Введите название услуги:")
    await state.set_state(AddServiceStates.name)
    await callback.answer()


@router.message(Command("add_service"))
async def add_service_command(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        master = await get_master_by_telegram_id(session, user.id)
        if not master:
            await message.answer("Сначала выполните /start")
            return
        await persist_master_context(state, master)

    await message.answer("Введите название услуги:")
    await state.set_state(AddServiceStates.name)


@router.message(AddServiceStates.name)
async def add_service_name(message: Message, state: FSMContext) -> None:
    await state.update_data(service_name=(message.text or "").strip())
    await message.answer("Длительность в минутах (например, 60):")
    await state.set_state(AddServiceStates.duration)


@router.message(AddServiceStates.duration)
async def add_service_duration(message: Message, state: FSMContext) -> None:
    try:
        duration = int((message.text or "").strip())
    except ValueError:
        await message.answer("Введите число минут, например 60")
        return
    await state.update_data(service_duration=duration)
    await message.answer("Цена в рублях (например, 2500):")
    await state.set_state(AddServiceStates.price)


@router.message(AddServiceStates.price)
async def add_service_price(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user:
        return

    try:
        price = int((message.text or "").strip())
    except ValueError:
        await message.answer("Введите цену числом, например 2500")
        return

    data = await state.get_data()
    name = data.get("service_name", "Услуга")
    duration = data.get("service_duration", 60)

    async with get_session() as session:
        master = await get_master_by_telegram_id(session, user.id)
        if not master:
            await message.answer("Сначала выполните /start")
            await state.clear()
            return

        service = Service(
            master_id=master.id,
            name=name,
            duration_minutes=duration,
            price=price,
            is_active=True,
        )
        session.add(service)
        await session.commit()

    await state.clear()
    await message.answer(f"✅ Услуга «{name}» добавлена: {duration} мин, {price}₽")


@router.message(Command("services"))
async def list_services(message: Message) -> None:
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        master = await get_master_by_telegram_id(session, user.id)
        if not master:
            await message.answer("Сначала выполните /start")
            return

        result = await session.execute(
            select(Service).where(
                Service.master_id == master.id, Service.is_active.is_(True)
            )
        )
        services = result.scalars().all()

    if not services:
        await message.answer("У вас пока нет услуг. Добавьте через /add_service")
        return

    text = "📋 **Ваши услуги:**\n\n"
    keyboard_rows = []
    for svc in services:
        text += f"• {svc.name} — {svc.duration_minutes} мин, {svc.price}₽\n"
        keyboard_rows.append(
            [
                InlineKeyboardButton(
                    text=f"🗑 Удалить {svc.name}",
                    callback_data=f"del_service:{svc.id}",
                )
            ]
        )

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows),
    )


@router.callback_query(F.data.startswith("del_service:"))
async def delete_service(callback: CallbackQuery) -> None:
    if not callback.from_user or not callback.data:
        await callback.answer()
        return

    service_id = callback.data.split(":", 1)[1]

    async with get_session() as session:
        master = await get_master_by_telegram_id(session, callback.from_user.id)
        service = await session.get(Service, service_id)
        if not master or not service or service.master_id != master.id:
            await callback.answer("Услуга не найдена", show_alert=True)
            return
        service.is_active = False
        await session.commit()

    if callback.message:
        await callback.message.edit_text("🗑 Услуга удалена.")
    await callback.answer()


@router.message(Command("stats"))
async def show_stats(message: Message) -> None:
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        master = await get_master_by_telegram_id(session, user.id)
        if not master:
            await message.answer("Сначала выполните /start")
            return

        analytics = await session.get(MasterAnalytics, master.id)
        if not analytics:
            total = (
                await session.execute(
                    select(func.count(Booking.id)).where(
                        Booking.master_id == master.id,
                        Booking.status == BookingStatus.CONFIRMED,
                    )
                )
            ).scalar_one()
            avg_price = (
                await session.execute(
                    select(func.avg(Service.price)).where(
                        Service.master_id == master.id
                    )
                )
            ).scalar_one()
            analytics = MasterAnalytics(
                master_id=master.id,
                total_bookings=int(total or 0),
                total_cancellations=0,
                total_no_shows=0,
                avg_price=Decimal(str(avg_price or 0)),
                client_retention_rate=Decimal("0"),
                last_updated=datetime.now(),
            )
            session.add(analytics)
            await session.commit()

        text = (
            f"📊 **Статистика**\n\n"
            f"Всего записей: {analytics.total_bookings}\n"
            f"Отмен: {analytics.total_cancellations}\n"
            f"No-show: {analytics.total_no_shows}\n"
            f"Средний чек: {analytics.avg_price}₽\n"
            f"Retention: {analytics.client_retention_rate}%"
        )

    await message.answer(text, parse_mode="Markdown")
