"""Tests for LLM factory."""

import pytest

from src.services.llm.dummy import DummyLLM
from src.services.llm.factory import get_llm


def test_get_llm_returns_dummy_when_unconfigured(monkeypatch):
    monkeypatch.setattr("src.services.llm.factory.settings.YANDEX_FOLDER_ID", None)
    monkeypatch.setattr("src.services.llm.factory.settings.YANDEX_API_KEY", None)
    monkeypatch.setattr("src.services.llm.factory.settings.OPENAI_API_KEY", None)
    assert isinstance(get_llm(), DummyLLM)


def test_build_system_prompt():
    from src.services.faq_service import build_system_prompt

    prompt = build_system_prompt("Anna Studio")
    assert "Anna Studio" in prompt
    assert "уточню у мастера" in prompt.lower()


@pytest.mark.asyncio
async def test_dummy_llm_price_hint():
    llm = DummyLLM()
    answer = await llm.answer(
        "сколько стоит?",
        "Услуги:\n- Маникюр: 2500₽, 60 мин",
    )
    assert "2500" in answer
