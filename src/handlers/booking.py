"""Booking handler with FSM flow."""

from datetime import datetime, timedelta

import structlog
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
from sqlalchemy import select

from ..database import get_session
from ..exceptions import BookingConflictError, SubscriptionLimitExceeded
from ..models import Booking, BookingStatus, Service
from ..services.booking_service import BookingService
from ..services.master_service import get_master_by_telegram_id
from ..utils.event_log import log_event
from .helpers import get_or_create_client, persist_master_context

router = Router()
logger = structlog.get_logger(__name__)


class BookingStates(StatesGroup):
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    confirmation = State()


def _date_keyboard() -> InlineKeyboardMarkup:
    rows = []
    labels = ["Сегодня", "Завтра", "Послезавтра", "+3 дня"]
    for i, label in enumerate(labels):
        date = (datetime.now().date() + timedelta(days=i)).strftime("%Y-%m-%d")
        rows.append([InlineKeyboardButton(text=label, callback_data=f"date_{date}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("book"))
async def command_book_handler(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        master = await get_master_by_telegram_id(session, user.id)
        if not master:
            await message.answer("Сначала выполните /start для регистрации.")
            return

        await persist_master_context(state, master)
        await get_or_create_client(
            session, user.id, master.id, user.full_name or user.first_name
        )

        result = await session.execute(
            select(Service).where(
                Service.master_id == master.id, Service.is_active.is_(True)
            )
        )
        services = result.scalars().all()

    if not services:
        await message.answer(
            "Пока нет услуг. Добавьте через /add_service или кнопку в меню."
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{s.name} ({s.duration_minutes} мин)",
                    callback_data=f"service_{s.id}",
                )
            ]
            for s in services
        ]
    )
    service_list = [
        {"id": s.id, "name": s.name, "duration": s.duration_minutes} for s in services
    ]
    await state.update_data(services=service_list, master_id=master.id)
    await message.answer("Выберите услугу:", reply_markup=keyboard)
    await state.set_state(BookingStates.choosing_service)


@router.callback_query(F.data.startswith("service_"), BookingStates.choosing_service)
async def process_service_selection(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data or not callback.message:
        await callback.answer()
        return

    service_id = callback.data.removeprefix("service_")
    data = await state.get_data()
    selected = next(
        (s for s in data.get("services", []) if s["id"] == service_id), None
    )
    if not selected:
        await callback.answer("Услуга не найдена", show_alert=True)
        return

    await callback.message.edit_text(
        f"Вы выбрали: {selected['name']} ({selected['duration']} мин)\n\n"
        f"Выберите дату:",
        reply_markup=_date_keyboard(),
    )
    await state.update_data(selected_service_id=service_id)
    await state.set_state(BookingStates.choosing_date)
    await callback.answer()


@router.callback_query(F.data.startswith("date_"), BookingStates.choosing_date)
async def process_date_selection(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data or not callback.message:
        await callback.answer()
        return

    date_str = callback.data.split("_", 1)[1]
    data = await state.get_data()
    service_id = data.get("selected_service_id")
    master_id = data.get("master_id")

    if not service_id or not master_id:
        await callback.answer("Данные утеряны", show_alert=True)
        return

    date_obj = datetime.strptime(date_str, "%Y-%m-%d")

    async with get_session() as session:
        booking_service = BookingService(session)
        slots = await booking_service.get_available_slots(
            master_id, date_obj, service_id=service_id
        )

    if not slots:
        await callback.message.edit_text(
            f"На {date_str} нет свободных слотов. Выберите другую дату:",
            reply_markup=_date_keyboard(),
        )
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=slot.strftime("%H:%M"),
                    callback_data=f"time_{slot.strftime('%H:%M')}",
                )
            ]
            for slot in slots[:12]
        ]
    )
    service_name = next(
        s["name"] for s in data.get("services", []) if s["id"] == service_id
    )
    await callback.message.edit_text(
        f"Дата: {date_str}\nУслуга: {service_name}\n\nВыберите время:",
        reply_markup=keyboard,
    )
    await state.update_data(selected_date=date_str)
    await state.set_state(BookingStates.choosing_time)
    await callback.answer()


@router.callback_query(F.data.startswith("time_"), BookingStates.choosing_time)
async def process_time_selection(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data or not callback.message:
        await callback.answer()
        return

    time_str = callback.data.split("_", 1)[1]
    data = await state.get_data()
    service_id = data.get("selected_service_id")
    date_str = data.get("selected_date")

    if not service_id or not date_str:
        await callback.answer("Данные утеряны", show_alert=True)
        return

    service_name = next(
        s["name"] for s in data.get("services", []) if s["id"] == service_id
    )
    datetime_str = f"{date_str} {time_str}:00"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=f"confirm_{datetime_str}",
                ),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_booking"),
            ]
        ]
    )
    await callback.message.edit_text(
        f"Подтвердите запись:\n\n"
        f"Услуга: {service_name}\n"
        f"Дата: {date_str}\n"
        f"Время: {time_str}",
        reply_markup=keyboard,
    )
    await state.update_data(selected_datetime=datetime_str)
    await state.set_state(BookingStates.confirmation)
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_"), BookingStates.confirmation)
async def confirm_booking(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data or not callback.from_user or not callback.message:
        await callback.answer()
        return

    datetime_str = callback.data.split("_", 1)[1]
    user = callback.from_user
    data = await state.get_data()
    service_id = data.get("selected_service_id")
    master_id = data.get("master_id")

    if not all([service_id, master_id, datetime_str]):
        await callback.answer("Данные утеряны", show_alert=True)
        return

    booking_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")

    try:
        async with get_session() as session:
            client, _ = await get_or_create_client(
                session, user.id, master_id, user.full_name or user.first_name
            )
            booking_service = BookingService(session)
            booking = await booking_service.create_booking(
                master_id=master_id,
                client_id=client.id,
                service_id=service_id,
                booking_datetime=booking_datetime,
            )
            service = await session.get(Service, service_id)
            service_name = service.name if service else "услуга"
    except SubscriptionLimitExceeded as exc:
        await callback.message.edit_text(
            exc.upsell_text or str(exc),
        )
        await state.clear()
        await callback.answer()
        return
    except BookingConflictError:
        await callback.message.edit_text(
            "❌ Это время уже занято. Попробуйте /book снова."
        )
        await state.clear()
        await callback.answer()
        return

    log_event(master_id, user.id, "booking_created")
    await callback.message.edit_text(
        f"✅ Записала на {booking_datetime.strftime('%d.%m.%Y %H:%M')}!\n"
        f"Напомню за день до визита.\n\n"
        f"Услуга: {service_name}\n"
        f"ID: {booking.id}"
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel_booking")
async def cancel_booking_process(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message:
        await callback.message.edit_text("Процесс записи отменён.")
    await state.clear()
    await callback.answer()


@router.message(Command("my_bookings"))
async def command_my_bookings_handler(message: Message) -> None:
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        master = await get_master_by_telegram_id(session, user.id)
        if not master:
            await message.answer("Сначала выполните /start")
            return

        client, _ = await get_or_create_client(session, user.id, master.id)
        now = datetime.now()
        result = await session.execute(
            select(Booking)
            .where(
                Booking.client_id == client.id,
                Booking.datetime >= now,
                Booking.status != BookingStatus.CANCELLED,
            )
            .order_by(Booking.datetime)
        )
        bookings = result.scalars().all()

    if not bookings:
        await message.answer("У вас нет предстоящих записей.")
        return

    text = "📅 **Ваши записи:**\n\n"
    for booking in bookings:
        svc_name = booking.service.name if booking.service else "—"
        text += f"• {booking.datetime.strftime('%d.%m.%Y %H:%M')} — {svc_name}\n"
    await message.answer(text, parse_mode="Markdown")
