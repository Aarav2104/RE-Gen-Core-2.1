"""Configurable LLM client. Defaults to Groq (matching the reference RAG
project), but is isolated behind a single call() function so the provider
can be swapped without touching generation logic."""
from __future__ import annotations

from researchgen import config


class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self):
        self._llm = None

    def _ensure_client(self):
        if self._llm is not None:
            return
        if config.LLM_PROVIDER == "groq":
            if not config.GROQ_API_KEY:
                raise LLMError(
                    "GROQ_API_KEY is not set. Add it to your .env file before running generation."
                )
            from langchain_groq import ChatGroq

            self._llm = ChatGroq(
                groq_api_key=config.GROQ_API_KEY,
                model_name=config.GROQ_MODEL,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
            )
        else:
            raise LLMError(f"Unsupported LLM provider: {config.LLM_PROVIDER}")

    def complete(self, prompt: str) -> str:
        """Send a single prompt and return the text response."""
        self._ensure_client()
        try:
            response = self._llm.invoke(prompt)
            return getattr(response, "content", str(response)).strip()
        except Exception as exc:  # surface a clean error to the UI layer
            raise LLMError(f"LLM request failed: {exc}") from exc


_client_singleton: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = LLMClient()
    return _client_singleton
