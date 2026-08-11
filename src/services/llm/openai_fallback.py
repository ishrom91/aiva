"""OpenAI-compatible LLM fallback."""

import httpx

from ...config import settings
from .base import BaseLLM


class OpenAIFallbackLLM(BaseLLM):
    """Chat completions via OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "gpt-4o-mini",
    ) -> None:
        self.api_key = api_key or settings.OPENAI_API_KEY or ""
        self.base_url = (base_url or settings.OPENAI_BASE_URL).rstrip("/")
        self.model = model

    async def answer(self, question: str, context: str) -> str:
        system = (
            "Ты администратор салона красоты. Отвечай коротко, дружелюбно, "
            "на русском. Используй ТОЛЬКО факты из контекста. "
            "Если не знаешь — скажи 'уточню у мастера'."
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": f"{system}\n\nКонтекст:\n{context}"},
                {"role": "user", "content": question},
            ],
            "temperature": 0.3,
            "max_tokens": 300,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"].strip()
