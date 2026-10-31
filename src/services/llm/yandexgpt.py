"""YandexGPT via Yandex Cloud Foundation Models."""

import httpx

from ...config import settings
from .base import BaseLLM


class YandexGPTLLM(BaseLLM):
    """YandexGPT completion API."""

    def __init__(
        self,
        folder_id: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.folder_id = folder_id or settings.YANDEX_FOLDER_ID or ""
        self.api_key = api_key or settings.YANDEX_API_KEY or ""
        self.url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    async def answer(self, question: str, context: str) -> str:
        system = (
            "Ты администратор салона красоты. Отвечай коротко, дружелюбно, "
            "на русском. Используй ТОЛЬКО факты из контекста. "
            "Если не знаешь — скажи 'уточню у мастера'."
        )
        payload = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 300,
            },
            "messages": [
                {"role": "system", "text": f"{system}\n\nКонтекст:\n{context}"},
                {"role": "user", "text": question},
            ],
        }
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return data["result"]["alternatives"][0]["message"]["text"].strip()
