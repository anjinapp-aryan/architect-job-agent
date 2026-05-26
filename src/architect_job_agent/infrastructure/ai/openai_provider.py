"""OpenAI provider."""
from __future__ import annotations

import os

from ...core.exceptions import AIProviderError, AIProviderUnavailableError
from .base import AIProvider


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self, **kwargs) -> None:
        model = kwargs.pop("model", None) or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        super().__init__(model=model, **kwargs)
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise AIProviderUnavailableError("OPENAI_API_KEY not set")
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:
            raise AIProviderUnavailableError("openai SDK not installed") from exc
        self._client = OpenAI(api_key=api_key, timeout=self.timeout)

    def _complete(self, system: str, user: str) -> str:
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system or "You are a helpful assistant."},
                    {"role": "user", "content": user},
                ],
            )
        except Exception as exc:
            raise AIProviderError(f"OpenAI call failed: {exc}") from exc
        return (resp.choices[0].message.content or "").strip()
