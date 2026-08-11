"""Tests for FAQ handler."""

from unittest.mock import AsyncMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User

from src.handlers.faq import faq_message_handler
from src.services.llm.base import BaseLLM
from tests.conftest import make_master, make_service


class StaticLLM(BaseLLM):
    async def answer(self, question: str, context: str) -> str:
        return "Маникюр — 2500₽"


@pytest.fixture
def faq_user() -> User:
    return User(id=904001, is_bot=False, first_name="Client", username="client")


@pytest.mark.asyncio
async def test_faq_handler_answers_question(
    db_session, session_override, faq_user, monkeypatch
):
    monkeypatch.setattr("src.config.settings.AI_FAQ_ENABLED", True)
    master = await make_master(db_session, telegram_id=faq_user.id, name="Salon")
    await make_service(db_session, master, name="Маникюр", price=2500)

    message = AsyncMock(spec=Message)
    message.from_user = faq_user
    message.text = "Сколько стоит маникюр?"
    message.answer = AsyncMock()

    state = AsyncMock(spec=FSMContext)

    with patch("src.handlers.faq.get_session", session_override), patch(
        "src.services.faq_service.get_llm", return_value=StaticLLM()
    ):
        await faq_message_handler(message, state)

    message.answer.assert_awaited_once()
    assert "2500" in message.answer.await_args.args[0]
