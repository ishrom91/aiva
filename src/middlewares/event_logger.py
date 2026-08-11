"""Event logging middleware for Aiva AI Bot."""

import asyncio
from datetime import datetime
from typing import Any, Callable

import structlog
from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Update

from ..config import settings
from ..database import get_session
from ..models.interaction import Interaction, InteractionDirection
from ..services.master_service import get_master_by_telegram_id
from ..utils.anonymization import extract_time_metadata, generate_client_hash


class EventLoggerMiddleware(BaseMiddleware):
    """Middleware for logging all interactions (event sourcing)."""

    def __init__(self) -> None:
        super().__init__()
        self.logger = structlog.get_logger(__name__)

    async def __call__(self, handler: Callable, event: Update, data: dict) -> Any:
        result = await handler(event, data)

        if settings.DATA_COLLECTION_ENABLED:
            asyncio.create_task(self._log_interaction(event, data))

        return result

    async def _log_interaction(self, event: Update, data: dict) -> None:
        try:
            if not settings.DATA_COLLECTION_ENABLED:
                return

            telegram_id = self._get_telegram_id(event)
            if not telegram_id:
                return

            master_id = await self._resolve_master_id(event, data)
            if not master_id:
                return

            event_type = data.get("event_type") or self._get_event_type(event)
            client_hash = generate_client_hash(telegram_id, settings.CLIENT_HASH_SALT)
            extracted = extract_time_metadata(datetime.now())

            metadata = {
                "time_of_day": extracted.get("time_of_day"),
                "day_of_week": extracted.get("day_of_week"),
                "hour": extracted.get("hour"),
            }

            if event.message and event.message.text:
                metadata["message_text_length"] = len(event.message.text)
            elif event.callback_query and event.callback_query.data:
                metadata["callback_data"] = event.callback_query.data

            if settings.DATA_COLLECTION_LOG_TEXT and event.message:
                metadata["text_content"] = event.message.text

            async with get_session() as session:
                interaction = Interaction(
                    event_type=event_type,
                    master_id=master_id,
                    client_hash=client_hash,
                    direction=InteractionDirection.INBOUND,
                    skill_name=data.get("current_skill"),
                    event_metadata=metadata,
                )
                session.add(interaction)
                await session.commit()

        except Exception as exc:
            self.logger.exception("Failed to log interaction", error=str(exc))

    async def _resolve_master_id(self, event: Update, data: dict) -> str | None:
        if data.get("master_id"):
            return str(data["master_id"])
        if "master" in data and hasattr(data["master"], "id"):
            return data["master"].id

        state: FSMContext | None = data.get("state")
        if state is not None:
            state_data = await state.get_data()
            if state_data.get("master_id"):
                return str(state_data["master_id"])

        telegram_id = self._get_telegram_id(event)
        if telegram_id:
            async with get_session() as session:
                master = await get_master_by_telegram_id(session, telegram_id)
                if master:
                    return master.id
        return None

    def _get_event_type(self, event: Update) -> str:
        if event.message:
            return "message_received"
        if event.callback_query:
            return "callback_query_received"
        return "unknown_event"

    def _get_telegram_id(self, event: Update) -> int | None:
        if event.message and event.message.from_user:
            return event.message.from_user.id
        if event.callback_query and event.callback_query.from_user:
            return event.callback_query.from_user.id
        return None
