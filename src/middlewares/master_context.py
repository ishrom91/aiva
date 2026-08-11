"""Inject master context into handler data from Telegram user id."""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from ..database import get_session
from ..services.master_service import get_master_by_telegram_id


class MasterContextMiddleware(BaseMiddleware):
    """Resolve master by telegram_id and expose it in handler data + FSM state."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        telegram_id = self._extract_user_id(event)
        if telegram_id is not None:
            async with get_session() as session:
                master = await get_master_by_telegram_id(session, telegram_id)
                if master:
                    data["master"] = master
                    data["master_id"] = master.id
                    state: FSMContext | None = data.get("state")
                    if state is not None:
                        await state.update_data(master_id=master.id)

        return await handler(event, data)

    @staticmethod
    def _extract_user_id(event: TelegramObject) -> int | None:
        if isinstance(event, Update):
            if event.message and event.message.from_user:
                return event.message.from_user.id
            if event.callback_query and event.callback_query.from_user:
                return event.callback_query.from_user.id
            return None
        if isinstance(event, Message) and event.from_user:
            return event.from_user.id
        if isinstance(event, CallbackQuery) and event.from_user:
            return event.from_user.id
        return None
