"""Shared handler utilities."""

from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.client import Client
from ..models.master import Master
from ..utils.encryption import get_encryption_manager


def _encrypt_field(value: str | None) -> str | None:
    if not value:
        return None
    return get_encryption_manager(settings.ENCRYPTION_KEY).encrypt(value)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить услугу", callback_data="menu:add_service"
                )
            ],
            [InlineKeyboardButton(text="📅 Мои записи", callback_data="menu:bookings")],
            [
                InlineKeyboardButton(
                    text="💳 Подписка", callback_data="menu:subscription"
                )
            ],
            [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="menu:help")],
        ]
    )


async def persist_master_context(state: FSMContext, master: Master) -> None:
    """Save master_id in FSM state for event_logger and downstream handlers."""
    await state.update_data(master_id=master.id)


async def get_or_create_client(
    session: AsyncSession,
    telegram_id: int,
    master_id: str,
    name: str | None = None,
    phone: str | None = None,
) -> tuple[Client, bool]:
    result = await session.execute(
        select(Client).where(
            Client.telegram_id == telegram_id,
            Client.master_id == master_id,
        )
    )
    client = result.scalar_one_or_none()
    if client:
        return client, False

    client = Client(
        telegram_id=telegram_id,
        master_id=master_id,
        name_encrypted=_encrypt_field(name),
        phone_encrypted=_encrypt_field(phone),
    )
    session.add(client)
    await session.commit()
    await session.refresh(client)
    return client, True
