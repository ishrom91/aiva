"""
Subscription skill implementation
Handles subscription management functionality
"""

from typing import Any, Dict, Optional, Union

import structlog
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..billing.tariffs import get_tariff_config
from ..models import Master
from ..services.subscription_service import SubscriptionService
from .base import BaseSkill


class SubscriptionSkill(BaseSkill):
    """
    Skill for handling subscription management.
    Provides functionality for subscription checking, upgrades, and management.
    """

    def __init__(self):
        super().__init__()
        self.skill_id = "subscription"
        self.skill_name = "Subscription"
        self.logger = structlog.get_logger(__name__)

    async def can_handle(
        self,
        message: Union[Message, CallbackQuery],
        state: FSMContext,
        db_session: AsyncSession,
        **kwargs,
    ) -> bool:
        """
        Determine if this skill can handle the given event.
        """
        # Check if the message contains subscription-related commands or callbacks
        if isinstance(message, Message):
            text = message.text or ""
            return any(
                cmd in text.lower()
                for cmd in ["/subscription", "/sub", "/upgrade", "/pay"]
            )
        elif isinstance(message, CallbackQuery):
            data = message.data or ""
            return any(
                trigger in data for trigger in ["upgrade_", "subscribe_", "sub_"]
            )

        return False

    async def process(
        self,
        message: Union[Message, CallbackQuery],
        state: FSMContext,
        db_session: AsyncSession,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """
        Process the subscription-related event.
        """
        try:
            # Get user info
            user_id = message.from_user.id

            # Get master record
            master_result = await db_session.execute(
                select(Master).filter(Master.telegram_id == user_id)
            )
            master = master_result.scalar_one_or_none()

            if not master:
                return {
                    "handled": False,
                    "error": "Master not found",
                    "message": "Вы не зарегистрированы как мастер.",
                }

            # Initialize service
            service = SubscriptionService()

            # Process based on message type
            if isinstance(message, Message):
                return await self._process_message(message, master, service, db_session)
            elif isinstance(message, CallbackQuery):
                return await self._process_callback(
                    message, master, service, db_session
                )

        except Exception as e:
            self.logger.error(
                "Error processing subscription skill", error=str(e), exc_info=True
            )
            return {"handled": False, "error": str(e)}

    async def _process_message(
        self,
        message: Message,
        master: Master,
        service: SubscriptionService,
        db_session: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Process a text message for subscription.
        """
        text = message.text.lower()

        if "/subscription" in text or "/sub" in text:
            # Get subscription info
            subscription = await service.get_master_subscription(db_session, master.id)

            if not subscription:
                return {
                    "handled": True,
                    "type": "no_subscription",
                    "message": (
                        "У вас пока нет активной подписки.\n\n"
                        "Доступные тарифы:\n\n"
                        "💎 <b>Старт</b> — 990₽/мес\n"
                        "- Запись клиентов\n"
                        "- Напоминания за 24 часа\n"
                        "- Базовый FAQ\n"
                        "- До 50 записей в месяц\n\n"
                        "⭐ <b>Профи</b> — 1 990₽/мес\n"
                        "- Всё из 'Старт'\n"
                        "- Навык 'Консьерж' (возврат спящих клиентов)\n"
                        "- Навык 'Пост-забота'\n"
                        "- До 200 записей в месяц\n\n"
                        "🏢 <b>Салон</b> — 3 990₽/мес\n"
                        "- Всё из 'Профи'\n"
                        "- Навык 'Авто-Маркетолог'\n"
                        "- Аналитика\n"
                        "- До 5 мастеров\n"
                        "- Безлимит записей"
                    ),
                }

            # Check subscription limits
            limits_info = await service.check_subscription_limits(db_session, master.id)

            tariff_info = get_tariff_config(subscription.tariff_name)
            tariff_name = (
                tariff_info.name if tariff_info else subscription.tariff_name.title()
            )

            sub_info = f"📋 <b>Ваша текущая подписка:</b> {tariff_name}\n\n"

            if subscription.monthly_bookings_limit != -1:
                sub_info += f"📊 <b>Записей в этом месяце:</b> {limits_info['limits']['current_bookings_count']}/{subscription.monthly_bookings_limit}\n\n"
            else:
                sub_info += f"📊 <b>Записей в этом месяце:</b> {limits_info['limits']['current_bookings_count']} (безлимит)\n\n"

            return {
                "handled": True,
                "type": "subscription_info",
                "subscription": subscription,
                "limits_info": limits_info,
                "message": sub_info,
            }

        elif "/upgrade" in text or "/pay" in text:
            # Check subscription limits to suggest upgrade
            limits_info = await service.check_subscription_limits(db_session, master.id)

            # For now, just return a basic upgrade suggestion
            return {
                "handled": True,
                "type": "upgrade_suggestion",
                "limits_info": limits_info,
                "message": "Доступные варианты улучшения подписки:",
            }

        return {
            "handled": False,
            "message": "Неизвестная команда управления подпиской.",
        }

    async def _process_callback(
        self,
        callback: CallbackQuery,
        master: Master,
        service: SubscriptionService,
        db_session: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Process a callback query for subscription.
        """
        data = callback.data

        if data.startswith("upgrade_"):
            # Process upgrade request
            try:
                target_tariff = data.split("_")[1]

                # Check if tariff exists
                tariff_config = get_tariff_config(target_tariff)
                if not tariff_config:
                    return {
                        "handled": False,
                        "error": f"Tariff {target_tariff} not found",
                    }

                # Create upgrade suggestion
                return {
                    "handled": True,
                    "type": "upgrade_confirmation",
                    "target_tariff": target_tariff,
                    "tariff_config": tariff_config,
                    "message": f"Подтверждаете переход на тариф '{tariff_config.name}' за {tariff_config.price_rub}₽/мес?",
                }
            except (IndexError, AttributeError):
                return {"handled": False, "error": "Invalid tariff in callback"}

        elif data.startswith("subscribe_"):
            # Process subscription request
            try:
                tariff_name = data.split("_")[1]

                # Create subscription
                subscription = await service.create_subscription(
                    db_session, master.id, tariff_name
                )

                if subscription:
                    return {
                        "handled": True,
                        "type": "subscription_created",
                        "subscription": subscription,
                        "message": f"Подписка на тариф '{tariff_name}' успешно оформлена!",
                    }
                else:
                    return {"handled": False, "error": "Failed to create subscription"}
            except (IndexError, AttributeError):
                return {
                    "handled": False,
                    "error": "Invalid subscription request in callback",
                }

        return {"handled": False, "message": "Неизвестный тип callback для подписки."}
