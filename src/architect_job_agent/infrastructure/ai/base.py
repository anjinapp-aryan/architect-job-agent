"""Abstract AI provider interface + helpers.

All providers expose a single :meth:`generate` method returning a string.
JSON-mode is opt-in via :meth:`generate_json`, which falls back to extracting
the first JSON object from the model's text response (LLM JSON drift is real).
"""
from __future__ import annotations

import abc
import json
import re
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from ...core.exceptions import AIProviderError


class AIProvider(abc.ABC):
    name: str = "abstract"

    def __init__(self, model: str, temperature: float = 0.2, max_tokens: int = 4000, timeout: int = 90) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    @abc.abstractmethod
    def _complete(self, system: str, user: str) -> str:
        """Subclass implements raw text completion."""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=15),
        reraise=True,
    )
    def generate(self, prompt: str, *, system: str = "") -> str:
        try:
            return self._complete(system or "", prompt)
        except AIProviderError:
            raise
        except Exception as exc:
            raise AIProviderError(f"{self.name} call failed: {exc}") from exc

    def generate_json(self, prompt: str, *, system: str = "") -> dict[str, Any]:
        raw = self.generate(
            prompt + "\n\nRespond ONLY with valid JSON. No prose, no markdown.",
            system=system,
        )
        return extract_json(raw)


_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")


def extract_json(text: str) -> dict[str, Any]:
    """Best-effort JSON extraction from an LLM response."""
    text = text.strip()
    # strip ```json fences
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = _JSON_BLOCK_RE.search(text)
        if not match:
            raise AIProviderError(f"No JSON in response: {text[:200]}")
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise AIProviderError(f"Invalid JSON in response: {exc}") from exc
