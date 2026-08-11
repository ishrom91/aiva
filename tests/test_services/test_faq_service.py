"""Tests for FAQ RAG service."""


import pytest

from src.services.faq_service import answer_client_question, build_context
from src.services.llm.base import BaseLLM
from tests.conftest import make_master, make_service


class MockLLM(BaseLLM):
    def __init__(self, response: str = "", fail: bool = False) -> None:
        self.response = response
        self.fail = fail

    async def answer(self, question: str, context: str) -> str:
        if self.fail:
            raise RuntimeError("LLM unavailable")
        return self.response


@pytest.mark.asyncio
async def test_faq_answers_price_from_context(db_session):
    master = await make_master(
        db_session, telegram_id=902001, name="Salon Lux", settings={"district": "Центр"}
    )
    await make_service(db_session, master, name="Маникюр", price=2500)

    context = await build_context(db_session, master.id)
    assert "2500" in context

    answer = await answer_client_question(
        db_session,
        master.id,
        "Сколько стоит маникюр?",
        llm=MockLLM("Маникюр стоит 2500₽, длительность 60 мин."),
    )
    assert "2500" in answer


@pytest.mark.asyncio
async def test_faq_fallback_when_llm_unavailable(db_session):
    master = await make_master(db_session, telegram_id=902002, name="Studio")
    await make_service(db_session, master, name="Маникюр", price=3000)

    answer = await answer_client_question(
        db_session,
        master.id,
        "Расскажи про маникюр",
        llm=MockLLM(fail=True),
    )
    assert "3000" in answer or "Маникюр" in answer


@pytest.mark.asyncio
async def test_faq_unknown_answer_says_will_ask_master(db_session):
    master = await make_master(db_session, telegram_id=902003)
    await make_service(db_session, master, name="Стрижка", price=1500)

    answer = await answer_client_question(
        db_session,
        master.id,
        "Есть ли парковка для вертолёта?",
        llm=MockLLM(fail=True),
    )
    assert "уточню у мастера" in answer.lower()
