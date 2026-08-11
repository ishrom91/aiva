"""Winback campaigns for dormant clients."""

from datetime import datetime, timedelta

import structlog
from aiogram import Bot
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_session
from ..models.booking import Booking, BookingStatus
from ..models.client import Client
from ..models.master import Master
from ..repositories.client_repo import ClientRepo
from ..services.booking_service import BookingService
from ..utils.encryption import decrypt

logger = structlog.get_logger(__name__)


def _client_display_name(client: Client) -> str:
    if client.name_encrypted:
        name = decrypt(client.name_encrypted)
        if name:
            return name.split()[0]
    return "друг"


async def find_dormant_clients(
    session: AsyncSession,
    master_id: str,
    days: int | None = None,
) -> list[Client]:
    repo = ClientRepo(session)
    return await repo.find_dormant(
        master_id,
        inactive_days=days or settings.WINBACK_DAYS,
    )


async def build_winback_message(
    session: AsyncSession,
    client: Client,
    master: Master,
) -> str:
    name = _client_display_name(client)
    booking_service = BookingService(session)
    tomorrow = datetime.now() + timedelta(days=1)
    slots = await booking_service.get_available_slots(master.id, tomorrow)
    slot_hint = slots[0].strftime("%d.%m в %H:%M") if slots else "ближайшие дни"
    return (
        f"{name}, давно не виделись 💕\n"
        f"У {master.name} есть окошко {slot_hint}.\n"
        f"Записаться: /book"
    )


async def send_winback_campaign(bot: Bot, master_id: str) -> dict:
    """Send winback messages to dormant clients (max once per 30 days each)."""
    sent = 0
    skipped = 0

    async with get_session() as session:
        master = await session.get(Master, master_id)
        if not master:
            return {"sent": 0, "skipped": 0, "total_dormant": 0}

        repo = ClientRepo(session)
        dormant = await repo.find_dormant(
            master_id,
            inactive_days=settings.WINBACK_DAYS,
        )

        for client in dormant:
            text = await build_winback_message(session, client, master)
            try:
                await bot.send_message(client.telegram_id, text)
                await repo.mark_winback_sent(client)
                sent += 1
            except Exception as exc:
                logger.warning(
                    "winback_send_failed",
                    client_id=client.id,
                    error=str(exc),
                )
                skipped += 1

    return {"sent": sent, "skipped": skipped, "total_dormant": sent + skipped}


async def count_dormant_clients(session: AsyncSession, master_id: str) -> int:
    clients = await find_dormant_clients(session, master_id)
    return len(clients)


async def get_client_last_completed(
    session: AsyncSession, client_id: str
) -> datetime | None:
    result = await session.execute(
        select(func.max(Booking.datetime)).where(
            Booking.client_id == client_id,
            Booking.status == BookingStatus.COMPLETED,
        )
    )
    return result.scalar_one_or_none()
