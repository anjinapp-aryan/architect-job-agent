"""Anthropic Claude provider."""
from __future__ import annotations

import os

from ...core.exceptions import AIProviderError, AIProviderUnavailableError
from .base import AIProvider


class ClaudeProvider(AIProvider):
    name = "claude"

    def __init__(self, **kwargs) -> None:
        model = kwargs.pop("model", None) or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        super().__init__(model=model, **kwargs)
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise AIProviderUnavailableError("ANTHROPIC_API_KEY not set")
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError as exc:
            raise AIProviderUnavailableError("anthropic SDK not installed") from exc
        self._client = Anthropic(api_key=api_key, timeout=self.timeout)

    def _complete(self, system: str, user: str) -> str:
        try:
            msg = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system or "You are a helpful assistant.",
                messages=[{"role": "user", "content": user}],
            )
        except Exception as exc:
            raise AIProviderError(f"Claude call failed: {exc}") from exc
        parts = [b.text for b in msg.content if getattr(b, "type", "") == "text"]
        return "".join(parts).strip()
