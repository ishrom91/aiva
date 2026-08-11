"""Predefined responses when no LLM is configured."""

from .base import BaseLLM


class DummyLLM(BaseLLM):
    """Offline stub with canned FAQ-style answers."""

    async def answer(self, question: str, context: str) -> str:
        lower = question.lower()
        if any(word in lower for word in ("цена", "стоим", "сколько")):
            for line in context.splitlines():
                if "₽" in line or "руб" in line.lower():
                    return f"По прайсу: {line.strip()}"
        if "адрес" in lower or "где" in lower or "район" in lower:
            for line in context.splitlines():
                if "Район" in line or "Адрес" in line:
                    return line.strip()
        return "Спасибо за вопрос! Уточню у мастера и вернусь с ответом."
