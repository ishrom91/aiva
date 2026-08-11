"""Reminder notifications for upcoming bookings."""

from datetime import datetime, timedelta

import structlog
from aiogram import Bot

from ..config import settings
from ..database import get_session
from ..models.interaction import InteractionDirection
from ..repositories.booking_repo import BookingRepo
from ..repositories.interaction_repo import InteractionRepo
from ..utils.anonymization import extract_time_metadata, generate_client_hash

logger = structlog.get_logger(__name__)


def _reminder_window() -> tuple[datetime, datetime]:
    now = datetime.now()
    center = settings.REMINDER_HOURS_BEFORE
    return now + timedelta(hours=center - 4), now + timedelta(hours=center + 4)


async def send_reminders(bot: Bot) -> int:
    """Send 24h reminders for confirmed bookings in the 20-28h window."""
    window_start, window_end = _reminder_window()
    sent = 0

    async with get_session() as session:
        repo = BookingRepo(session)
        bookings = await repo.find_due_for_reminder(window_start, window_end)

        for booking in bookings:
            if booking.reminded_at is not None:
                continue

            client = booking.client
            master = booking.master
            if not client or not master:
                continue

            time_str = booking.datetime.strftime("%H:%M")
            service_name = booking.service.name if booking.service else "запись"
            text = (
                f"Напоминаю 🤍 Завтра в {time_str} тебя ждёт {master.name}.\n"
                f"Услуга: {service_name}."
            )

            try:
                await bot.send_message(client.telegram_id, text)
            except Exception as exc:
                logger.warning(
                    "reminder_send_failed",
                    booking_id=booking.id,
                    client_id=client.id,
                    error=str(exc),
                )
                continue

            booking.reminded_at = datetime.now()
            await repo.save(booking)

            meta = extract_time_metadata(datetime.now())
            interaction_repo = InteractionRepo(session)
            await interaction_repo.create(
                event_type="reminder_sent",
                master_id=master.id,
                client_hash=generate_client_hash(
                    client.telegram_id, settings.CLIENT_HASH_SALT
                ),
                direction=InteractionDirection.OUTBOUND,
                event_metadata={
                    "booking_id": booking.id,
                    "time_of_day": meta.get("time_of_day"),
                },
            )
            sent += 1

    if sent:
        logger.info("reminders_sent", count=sent)
    return sent
