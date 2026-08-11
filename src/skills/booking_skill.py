"""
Booking skill implementation
Handles appointment booking functionality
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

import structlog
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Booking, Client
from ..repositories.booking_repo import BookingRepository
from ..services.booking_service import BookingService
from .base import BaseSkill


class BookingSkill(BaseSkill):
    """
    Skill for handling appointment bookings.
    Provides functionality for scheduling, rescheduling, and managing appointments.
    """

    def __init__(self) -> None:
        super().__init__()
        self.skill_id = "booking"
        self.skill_name = "Booking"
        self.logger = structlog.get_logger(__name__)

    @property
    def name(self) -> str:
        return "booking"

    async def can_handle(
        self,
        message: Union[Message, CallbackQuery],
        state: FSMContext,
        db_session: AsyncSession,
        **kwargs: Any,
    ) -> bool:
        """Determine if this skill can handle the given event."""
        if isinstance(message, Message):
            text = message.text or ""
            return any(
                cmd in text.lower()
                for cmd in ["/book", "/booking", "/my_bookings", "/schedule"]
            )
        if isinstance(message, CallbackQuery):
            data = message.data or ""
            return any(
                trigger in data
                for trigger in ["book_", "booking_", "my_bookings", "schedule_"]
            )
        return False

    async def process(
        self,
        message: Union[Message, CallbackQuery],
        state: FSMContext,
        db_session: AsyncSession,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """Process the booking-related event."""
        try:
            user_id = message.from_user.id

            client_result = await db_session.execute(
                select(Client).filter(Client.telegram_id == user_id)
            )
            client = client_result.scalar_one_or_none()

            if not client:
                return {
                    "handled": False,
                    "error": "Client not found",
                    "message": (
                        "Для записи на прием необходимо быть "
                        "зарегистрированным клиентом."
                    ),
                }

            repo = BookingRepository(db_session)
            service = BookingService(repo)

            if isinstance(message, Message):
                return await self._process_message(
                    message, client, service, db_session
                )
            if isinstance(message, CallbackQuery):
                return await self._process_callback(
                    message, client, service, db_session
                )
        except Exception as exc:
            self.logger.error(
                "Error processing booking skill", error=str(exc), exc_info=True
            )
            return {"handled": False, "error": str(exc)}
        return None

    async def _process_message(
        self,
        message: Message,
        client: Client,
        service: BookingService,
        db_session: AsyncSession,
    ) -> Dict[str, Any]:
        """Process a text message for booking."""
        text = (message.text or "").lower()

        if "/book" in text or "/booking" in text or "/schedule" in text:
            services = await service.get_master_services(
                db_session, client.master.telegram_id
            )

            if not services:
                return {
                    "handled": True,
                    "message": "К сожалению, пока нет доступных услуг для записи.",
                    "type": "available_services",
                }

            service_list = [
                {
                    "id": service.id,
                    "name": service.name,
                    "duration": service.duration_minutes,
                    "price": service.price,
                }
                for service in services
            ]

            return {
                "handled": True,
                "type": "available_services",
                "services": service_list,
                "message": (
                    f"Доступные услуги для записи у мастера {client.master.name}:"
                ),
            }

        if "/my_bookings" in text:
            bookings = await service.get_client_bookings(client.telegram_id)

            if not bookings:
                return {
                    "handled": True,
                    "message": "У вас нет предстоящих записей.",
                    "type": "my_bookings",
                }

            bookings_text = "ваши предстоящие записи:\n\n"
            for booking in bookings:
                bookings_text += (
                    f"📅 {booking.datetime.strftime('%d.%m.%Y %H:%M')}\n"
                    f" услуга: {booking.service.name}\n"
                    f" продолжительность: {booking.service.duration_minutes} мин\n\n"
                )

            return {
                "handled": True,
                "type": "my_bookings",
                "bookings": bookings,
                "message": bookings_text,
            }

        return {"handled": False, "message": "Неизвестная команда бронирования."}

    async def _process_callback(
        self,
        callback: CallbackQuery,
        client: Client,
        service: BookingService,
        db_session: AsyncSession,
    ) -> Dict[str, Any]:
        """Process a callback query for booking."""
        data = callback.data or ""

        if data.startswith("book_service_"):
            try:
                service_id = int(data.split("_")[2])
                available_dates = await service.get_available_dates(
                    db_session, service_id
                )

                if not available_dates:
                    return {
                        "handled": True,
                        "message": (
                            "К сожалению, нет доступных слотов для этой услуги "
                            "в ближайшие дни."
                        ),
                        "type": "no_available_slots",
                    }

                return {
                    "handled": True,
                    "type": "available_dates",
                    "service_id": service_id,
                    "dates": available_dates,
                    "message": "Выберите дату для записи:",
                }
            except (ValueError, IndexError):
                return {"handled": False, "error": "Invalid service ID in callback"}

        if data.startswith("book_date_"):
            try:
                parts = data.split("_", 2)
                service_id = int(parts[2])
                date_str = parts[3]
                time_slots = await service.get_available_time_slots(
                    db_session, service_id, date_str
                )

                if not time_slots:
                    return {
                        "handled": True,
                        "message": f"К сожалению, нет доступных слотов на {date_str}.",
                        "type": "no_available_times",
                    }

                return {
                    "handled": True,
                    "type": "available_times",
                    "service_id": service_id,
                    "date": date_str,
                    "times": [ts.strftime("%H:%M") for ts in time_slots],
                    "message": f"Доступное время на {date_str}:",
                }
            except (ValueError, IndexError):
                return {"handled": False, "error": "Invalid date/time in callback"}

        return {
            "handled": False,
            "message": "Неизвестный тип callback для бронирования.",
        }

    async def send_reminders(self, db_session: AsyncSession) -> list[dict[str, Any]]:
        """Send booking reminders to clients."""
        now = datetime.now()
        tomorrow = now + timedelta(days=1)

        booking_result = await db_session.execute(
            select(Booking).filter(
                Booking.datetime >= now,
                Booking.datetime < tomorrow,
                Booking.status == "confirmed",
            )
        )
        bookings = booking_result.scalars().all()

        reminder_messages = []
        for booking in bookings:
            message_text = (
                f"Напоминание о записи:\n\n"
                f"📅 {booking.datetime.strftime('%d.%m.%Y %H:%M')}\n"
                f"Услуга: {booking.service.name}\n"
                f"Мастер: {booking.master.name}\n\n"
                f"Пожалуйста, подтвердите или отмените запись за 24 часа до начала."
            )
            reminder_messages.append(
                {
                    "telegram_id": booking.client.telegram_id,
                    "message": message_text,
                    "booking_id": booking.id,
                }
            )

        self.logger.info("Prepared booking reminders", count=len(reminder_messages))
        return reminder_messages
