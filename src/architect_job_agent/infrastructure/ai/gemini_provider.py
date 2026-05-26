"""Google Gemini provider."""
from __future__ import annotations

import os

from ...core.exceptions import AIProviderError, AIProviderUnavailableError
from .base import AIProvider


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self, **kwargs) -> None:
        model = kwargs.pop("model", None) or os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        super().__init__(model=model, **kwargs)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise AIProviderUnavailableError("GEMINI_API_KEY not set")
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError as exc:
            raise AIProviderUnavailableError("google-generativeai not installed") from exc
        genai.configure(api_key=api_key)
        self._genai = genai

    def _complete(self, system: str, user: str) -> str:
        try:
            model = self._genai.GenerativeModel(
                model_name=self.model,
                system_instruction=system or None,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                },
            )
            resp = model.generate_content(user)
        except Exception as exc:
            raise AIProviderError(f"Gemini call failed: {exc}") from exc
        return (getattr(resp, "text", "") or "").strip()
