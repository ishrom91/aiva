"""LLM abstraction for AI-FAQ."""

from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Base interface for LLM providers."""

    @abstractmethod
    async def answer(self, question: str, context: str) -> str:
        """Answer a question using the provided context."""
        raise NotImplementedError
