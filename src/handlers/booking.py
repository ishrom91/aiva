"""Booking handler for Aiva AI Bot."""

from datetime import datetime, timedelta

import structlog
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from ..database import get_session
from ..models import Booking, Client, Master, Service

router = Router()
logger = structlog.get_logger(__name__)


class BookingStates(StatesGroup):
    """States for the booking FSM"""

    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    confirmation = State()


@router.message(Command("book"))
async def command_book_handler(message: Message, state: FSMContext) -> None:
    """
    Handler for /book command.
    Starts the booking process.
    """
    user_id = message.from_user.id

    async with get_session() as session:
        # Check if user is registered as a client
        result = await session.execute(
            select(Client).filter(Client.telegram_id == user_id)
        )
        client = result.scalar_one_or_none()

        if not client:
            await message.answer(
                "Для записи на прием необходимо быть зарегистрированным клиентом.\n"
                "Пожалуйста, свяжитесь с вашим мастером для регистрации."
            )
            return

        # Get services available for this client's master
        result = await session.execute(
            select(Service)
            .join(Master)
            .filter(Master.id == client.master_id)
            .order_by(Service.name)
        )
        services = result.scalars().all()

        if not services:
            await message.answer("К сожалению, пока нет доступных услуг для записи.")
            return

        # Create inline keyboard with services
        keyboard = []
        row = []
        for i, service in enumerate(services):
            row.append(
                {
                    "text": f"{service.name} ({service.duration_minutes} мин)",
                    "callback_data": f"service_{service.id}",
                }
            )
            if len(row) == 2:  # Two buttons per row
                keyboard.append(row)
                row = []

        if row:  # Add remaining buttons
            keyboard.append(row)

        await message.answer(
            "Выберите услугу:", reply_markup={"inline_keyboard": keyboard}
        )

        # Save services to state for later use
        service_list = [
            {"id": s.id, "name": s.name, "duration": s.duration_minutes}
            for s in services
        ]
        await state.update_data(services=service_list)
        await state.set_state(BookingStates.choosing_service)


@router.callback_query(F.data.startswith("service_"), BookingStates.choosing_service)
async def process_service_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Process service selection from inline keyboard.
    """
    service_id = int(callback.data.split("_")[1])

    # Get service info from state
    data = await state.get_data()
    services = data.get("services", [])
    selected_service = next((s for s in services if s["id"] == service_id), None)

    if not selected_service:
        await callback.answer("Ошибка: услуга не найдена", show_alert=True)
        return

    # Generate available dates for the next 14 days
    dates = []
    for i in range(14):
        date = datetime.now().date() + timedelta(days=i)
        dates.append(date)

    # Create inline keyboard with dates
    keyboard = []
    row = []
    for i, date in enumerate(dates):
        row.append(
            {
                "text": date.strftime("%d.%m"),
                "callback_data": f"date_{date.strftime('%Y-%m-%d')}",
            }
        )
        if len(row) == 3:  # Three buttons per row
            keyboard.append(row)
            row = []

    if row:  # Add remaining buttons
        keyboard.append(row)

    await callback.message.edit_text(
        f"Вы выбрали: {selected_service['name']} ({selected_service['duration']} мин)\n\n"
        f"Выберите дату:",
        reply_markup={"inline_keyboard": keyboard},
    )

    await state.update_data(selected_service_id=service_id)
    await state.set_state(BookingStates.choosing_date)

    await callback.answer()


@router.callback_query(F.data.startswith("date_"), BookingStates.choosing_date)
async def process_date_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Process date selection from inline keyboard.
    """
    date_str = callback.data.split("_", 1)[1]

    data = await state.get_data()
    service_id = data.get("selected_service_id")

    if not service_id:
        await callback.answer("Ошибка: данные о сервисе утеряны", show_alert=True)
        return

    # Get available time slots for selected date and service
    async with get_session() as session:
        service_result = await session.execute(
            select(Service).filter(Service.id == service_id)
        )
        service = service_result.scalar_one_or_none()

        if not service:
            await callback.answer("Ошибка: услуга не найдена", show_alert=True)
            return

        # Get master's working hours
        master_result = await session.execute(
            select(Master).filter(Master.id == service.master_id)
        )
        master = master_result.scalar_one_or_none()

        if not master:
            await callback.answer("Ошибка: мастер не найден", show_alert=True)
            return

        # Generate time slots based on master's working hours
        time_slots = []
        start_hour = master.work_start_hour
        end_hour = master.work_end_hour

        # Get currently booked slots for this date
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_of_day = datetime.combine(date_obj, datetime.min.time())
        end_of_day = datetime.combine(
            date_obj, datetime.max.time().replace(microsecond=0)
        )

        booked_result = await session.execute(
            select(Booking).filter(
                Booking.service_id == service_id,
                Booking.datetime >= start_of_day,
                Booking.datetime <= end_of_day,
                Booking.status != "cancelled",
            )
        )
        booked_bookings = booked_result.scalars().all()

        # Calculate booked time ranges
        booked_ranges = []
        for booking in booked_bookings:
            booking_end = booking.datetime + timedelta(minutes=service.duration_minutes)
            booked_ranges.append((booking.datetime, booking_end))

        # Generate available time slots in 30-minute intervals
        current_time = datetime.combine(
            date_obj, datetime.min.time().replace(hour=start_hour)
        )
        end_time = datetime.combine(
            date_obj, datetime.min.time().replace(hour=end_hour)
        )

        while current_time < end_time:
            slot_end = current_time + timedelta(minutes=service.duration_minutes)

            # Check if this slot overlaps with any booked slot
            is_available = True
            for booked_start, booked_end in booked_ranges:
                # Check for overlap: (current_start < booked_end) AND (booked_start < current_end)
                if (current_time < booked_end) and (booked_start < slot_end):
                    is_available = False
                    break

            if is_available:
                time_slots.append(current_time.strftime("%H:%M"))

            current_time += timedelta(minutes=30)  # 30-minute intervals

    # Create inline keyboard with time slots
    keyboard = []
    row = []
    for i, time_str in enumerate(time_slots):
        row.append({"text": time_str, "callback_data": f"time_{time_str}"})
        if len(row) == 4:  # Four buttons per row
            keyboard.append(row)
            row = []

    if row:  # Add remaining buttons
        keyboard.append(row)

    if not time_slots:
        await callback.message.edit_text(
            f"К сожалению, нет доступных слотов на {date_str} для выбранной услуги."
        )
        await state.clear()
        return

    await callback.message.edit_text(
        f"Дата: {date_str}\n"
        f"Услуга: {next(s['name'] for s in data.get('services', []) if s['id'] == service_id)}\n\n"
        f"Выберите время:",
        reply_markup={"inline_keyboard": keyboard},
    )

    await state.update_data(selected_date=date_str)
    await state.set_state(BookingStates.choosing_time)

    await callback.answer()


@router.callback_query(F.data.startswith("time_"), BookingStates.choosing_time)
async def process_time_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Process time selection from inline keyboard.
    """
    time_str = callback.data.split("_", 1)[1]

    data = await state.get_data()
    service_id = data.get("selected_service_id")
    date_str = data.get("selected_date")

    if not all([service_id, date_str]):
        await callback.answer("Ошибка: данные утеряны", show_alert=True)
        return

    # Combine date and time
    datetime_str = f"{date_str} {time_str}:00"

    # Get service name
    service_name = next(
        s["name"] for s in data.get("services", []) if s["id"] == service_id
    )

    await callback.message.edit_text(
        f"Подтвердите запись:\n\n"
        f"Услуга: {service_name}\n"
        f"Дата: {date_str}\n"
        f"Время: {time_str}\n\n"
        f"Нажмите 'Подтвердить', чтобы создать запись."
    )

    keyboard = [
        [
            {"text": "✅ Подтвердить", "callback_data": f"confirm_{datetime_str}"},
            {"text": "❌ Отмена", "callback_data": "cancel_booking"},
        ]
    ]

    await callback.message.answer(
        "Подтвердите запись:", reply_markup={"inline_keyboard": keyboard}
    )

    await state.update_data(selected_datetime=datetime_str)
    await state.set_state(BookingStates.confirmation)

    await callback.answer()


@router.callback_query(F.data.startswith("confirm_"), BookingStates.confirmation)
async def confirm_booking(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Confirm the booking creation.
    """
    datetime_str = callback.data.split("_", 1)[1]

    user_id = callback.from_user.id
    data = await state.get_data()
    service_id = data.get("selected_service_id")

    if not all([service_id, datetime_str]):
        await callback.answer("Ошибка: данные утеряны", show_alert=True)
        return

    # Create the booking in database
    async with get_session() as session:
        # Get client
        client_result = await session.execute(
            select(Client).filter(Client.telegram_id == user_id)
        )
        client = client_result.scalar_one_or_none()

        if not client:
            await callback.message.edit_text("Ошибка: клиент не найден")
            await state.clear()
            return

        # Get service to check duration
        service_result = await session.execute(
            select(Service).filter(Service.id == service_id)
        )
        service = service_result.scalar_one_or_none()

        if not service:
            await callback.message.edit_text("Ошибка: услуга не найдена")
            await state.clear()
            return

        # Check for conflicts
        booking_datetime = (
            datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
            if "Z" in datetime_str
            else datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        )
        end_datetime = booking_datetime + timedelta(minutes=service.duration_minutes)

        conflict_result = await session.execute(
            select(Booking).filter(
                Booking.client_id == client.id,
                Booking.datetime < end_datetime,
                Booking.datetime + timedelta(minutes=service.duration_minutes)
                > booking_datetime,
                Booking.status != "cancelled",
            )
        )
        conflicts = conflict_result.scalars().all()

        if conflicts:
            await callback.message.edit_text(
                "❌ У вас уже есть запись на это время. Пожалуйста, выберите другое время."
            )
            await state.clear()
            return

        # Create the booking
        booking = Booking(
            client_id=client.id,
            service_id=service_id,
            master_id=client.master_id,
            datetime=booking_datetime,
            status="confirmed",
        )
        session.add(booking)
        await session.commit()
        await session.refresh(booking)

        # Get updated service name
        service_name = service.name

        await callback.message.edit_text(
            f"✅ Ваша запись успешно создана!\n\n"
            f"Услуга: {service_name}\n"
            f"Дата: {booking_datetime.strftime('%d.%m.%Y')}\n"
            f"Время: {booking_datetime.strftime('%H:%M')}\n\n"
            f"ID записи: {booking.id}"
        )

    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel_booking", BookingStates.confirmation)
@router.callback_query(F.data == "cancel_booking")
async def cancel_booking_process(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Cancel the booking process.
    """
    await callback.message.edit_text("Процесс записи отменен.")
    await state.clear()
    await callback.answer()


@router.message(Command("my_bookings"))
async def command_my_bookings_handler(message: Message) -> None:
    """
    Handler for /my_bookings command.
    Shows user's upcoming bookings.
    """
    user_id = message.from_user.id

    async with get_session() as session:
        # Get client
        result = await session.execute(
            select(Client).filter(Client.telegram_id == user_id)
        )
        client = result.scalar_one_or_none()

        if not client:
            await message.answer(
                "Для просмотра записей вы должны быть зарегистрированы."
            )
            return

        # Get upcoming bookings
        now = datetime.now()
        result = await session.execute(
            select(Booking)
            .filter(
                Booking.client_id == client.id,
                Booking.datetime >= now,
                Booking.status != "cancelled",
            )
            .order_by(Booking.datetime)
        )
        bookings = result.scalars().all()

        if not bookings:
            await message.answer("У вас нет предстоящих записей.")
            return

        # Format bookings list
        bookings_text = "ваши предстоящие записи:\n\n"
        for booking in bookings:
            bookings_text += (
                f"📅 {booking.datetime.strftime('%d.%m.%Y %H:%M')}\n"
                f" услуга: {booking.service.name}\n"
                f" продолжительность: {booking.service.duration_minutes} мин\n\n"
            )

        await message.answer(bookings_text)
