"""Winback handler for masters."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from ..database import get_session
from ..services.master_service import get_master_by_telegram_id
from ..services.retention_service import count_dormant_clients, send_winback_campaign

router = Router()


def _winback_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Запустить", callback_data="winback:run")]
        ]
    )


@router.message(Command("winback"))
async def winback_command(message: Message) -> None:
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        master = await get_master_by_telegram_id(session, user.id)
        if not master:
            await message.answer("Сначала выполните /start")
            return
        dormant_count = await count_dormant_clients(session, master.id)

    await message.answer(
        f"💤 Спящих клиентов (60+ дней без визита): **{dormant_count}**\n\n"
        "Запустить winback-кампанию?",
        parse_mode="Markdown",
        reply_markup=_winback_keyboard(),
    )


@router.callback_query(F.data == "winback:run")
async def winback_run(callback: CallbackQuery) -> None:
    if not callback.from_user or not callback.message:
        await callback.answer()
        return

    bot = callback.bot
    if not bot:
        await callback.answer("Бот недоступен", show_alert=True)
        return

    async with get_session() as session:
        master = await get_master_by_telegram_id(session, callback.from_user.id)
        if not master:
            await callback.answer("Сначала /start", show_alert=True)
            return

    result = await send_winback_campaign(bot, master.id)
    text = (
        f"✅ Написали {result['sent']} клиентам.\n"
        f"Пропущено: {result['skipped']}"
    )
    if callback.message and hasattr(callback.message, "edit_text"):
        await callback.message.edit_text(text)
    await callback.answer()
