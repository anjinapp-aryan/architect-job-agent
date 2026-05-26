"""NVIDIA NIM provider (OpenAI-compatible API)."""
from __future__ import annotations

import os

from ...core.exceptions import AIProviderError, AIProviderUnavailableError
from .base import AIProvider


class NvidiaProvider(AIProvider):
    name = "nvidia"

    def __init__(self, **kwargs) -> None:
        model = kwargs.pop("model", None) or os.getenv(
            "NVIDIA_MODEL", "meta/llama-3.1-70b-instruct"
        )
        super().__init__(model=model, **kwargs)
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise AIProviderUnavailableError("NVIDIA_API_KEY not set")
        base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:
            raise AIProviderUnavailableError("openai SDK required for NVIDIA NIM") from exc
        self._client = OpenAI(api_key=api_key, base_url=base_url, timeout=self.timeout)

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
            raise AIProviderError(f"NVIDIA NIM call failed: {exc}") from exc
        return (resp.choices[0].message.content or "").strip()
