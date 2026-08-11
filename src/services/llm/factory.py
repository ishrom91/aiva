"""LLM provider factory."""

from ...config import settings
from .base import BaseLLM
from .dummy import DummyLLM
from .openai_fallback import OpenAIFallbackLLM
from .yandexgpt import YandexGPTLLM


def get_llm() -> BaseLLM:
    """Return YandexGPT, OpenAI fallback, or DummyLLM."""
    if settings.YANDEX_FOLDER_ID and settings.YANDEX_API_KEY:
        return YandexGPTLLM()
    if settings.OPENAI_API_KEY:
        return OpenAIFallbackLLM()
    return DummyLLM()
