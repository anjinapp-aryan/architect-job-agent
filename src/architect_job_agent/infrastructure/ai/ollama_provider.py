"""Ollama provider (local OpenAI-compatible HTTP endpoint)."""
from __future__ import annotations

import os

import httpx

from ...core.exceptions import AIProviderError, AIProviderUnavailableError
from .base import AIProvider


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(self, **kwargs) -> None:
        model = kwargs.pop("model", None) or os.getenv("OLLAMA_MODEL", "llama3.1")
        super().__init__(model=model, **kwargs)
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")

    def _complete(self, system: str, user: str) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
            "messages": [
                {"role": "system", "content": system or "You are a helpful assistant."},
                {"role": "user", "content": user},
            ],
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
        except httpx.RequestError as exc:
            raise AIProviderUnavailableError(f"Ollama unreachable: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise AIProviderError(f"Ollama HTTP {exc.response.status_code}: {exc.response.text}") from exc
        data = resp.json()
        return (data.get("message", {}).get("content") or "").strip()
