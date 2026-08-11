"""Subscription and upgrade handlers."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from ..billing.messages import NEXT_TARIFF
from ..billing.tariffs import get_tariff_config
from ..billing.upsell_triggers import check_upsell_triggers
from ..database import get_session
from ..services.master_service import get_master_by_telegram_id
from ..services.subscription_service import SubscriptionService
from ..utils.event_log import log_event

router = Router()


def _upgrade_keyboard(current_tariff: str) -> InlineKeyboardMarkup | None:
    next_tariff = NEXT_TARIFF.get(current_tariff.lower())
    if not next_tariff:
        return None
    cfg = get_tariff_config(next_tariff) or {}
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"⬆️ Перейти на {cfg.get('name', next_tariff)} ({cfg.get('price', 0)}₽)",
                    callback_data=f"upgrade:{next_tariff}",
                )
            ]
        ]
    )


async def show_subscription_message(message: Message, master_id: str) -> None:
    async with get_session() as session:
        sub_service = SubscriptionService()
        subscription = await sub_service.get_or_create(session, master_id)
        usage = await sub_service.current_month_usage(session, master_id)
        limit = subscription.monthly_bookings_limit
        tariff_cfg = get_tariff_config(subscription.tariff_name) or {}
        limit_text = "безлимит" if limit == -1 else str(limit)

    text = (
        f"💳 **Тариф:** {tariff_cfg.get('name', subscription.tariff_name)}\n"
        f"📅 Записей в этом месяце: {usage} / {limit_text}\n"
        f"Пробный период: {'да' if subscription.is_trial else 'нет'}\n"
        f"Действует до: {subscription.current_period_end.strftime('%d.%m.%Y')}"
    )
    keyboard = _upgrade_keyboard(subscription.tariff_name)
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)


async def show_subscription(callback: CallbackQuery) -> None:
    if not callback.from_user or not callback.message:
        return
    async with get_session() as session:
        master = await get_master_by_telegram_id(session, callback.from_user.id)
        if not master:
            await callback.message.answer("Сначала выполните /start")
            return
    await show_subscription_message(callback.message, master.id)


@router.message(Command("subscription"))
async def subscription_command(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    async with get_session() as session:
        master = await get_master_by_telegram_id(session, user.id)
        if not master:
            await message.answer("Сначала выполните /start")
            return
    await show_subscription_message(message, master.id)


@router.message(Command("upgrade"))
async def upgrade_command(message: Message) -> None:
    user = message.from_user
    if not user:
        return

    async with get_session() as session:
        master = await get_master_by_telegram_id(session, user.id)
        if not master:
            await message.answer("Сначала выполните /start")
            return

        trigger = await check_upsell_triggers(session, master.id)

    if trigger and trigger.get("should_upsell"):
        target = trigger.get("target_tariff")
        keyboard = None
        if target:
            cfg = get_tariff_config(target) or {}
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"⬆️ {cfg.get('name', target)} — {cfg.get('price', 0)}₽",
                            callback_data=f"upgrade:{target}",
                        )
                    ]
                ]
            )
        log_event(master.id, user.id, "upsell_shown")
        await message.answer(trigger["message"], reply_markup=keyboard)
    else:
        async with get_session() as session:
            master = await get_master_by_telegram_id(session, user.id)
            sub = await SubscriptionService().get_or_create(session, master.id)
        keyboard = _upgrade_keyboard(sub.tariff_name)
        await message.answer(
            "Сейчас нет срочных предложений. Вы можете апгрейдить тариф:",
            reply_markup=keyboard,
        )


@router.callback_query(F.data.startswith("upgrade:"))
async def process_upgrade(callback: CallbackQuery) -> None:
    if not callback.from_user or not callback.data or not callback.message:
        await callback.answer()
        return

    new_tariff = callback.data.split(":", 1)[1]

    async with get_session() as session:
        master = await get_master_by_telegram_id(session, callback.from_user.id)
        if not master:
            await callback.answer("Сначала /start", show_alert=True)
            return

        sub_service = SubscriptionService()
        subscription = await sub_service.upgrade(session, master.id, new_tariff)
        cfg = get_tariff_config(subscription.tariff_name) or {}

    log_event(master.id, callback.from_user.id, "upsell_accepted")
    await callback.message.edit_text(
        f"✅ Тариф обновлён на «{cfg.get('name', subscription.tariff_name)}»!\n"
        f"Лимит записей: {subscription.monthly_bookings_limit}"
    )
    await callback.answer()
