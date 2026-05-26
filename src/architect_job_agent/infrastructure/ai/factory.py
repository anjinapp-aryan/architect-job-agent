"""AI provider factory — configuration-driven selection."""
from __future__ import annotations

from ...core.config import get_settings
from ...core.exceptions import AIProviderUnavailableError
from ...core.logging import get_logger
from .base import AIProvider

logger = get_logger(__name__)


def build_ai_provider(name: str | None = None) -> AIProvider:
    settings = get_settings()
    provider_name = (name or settings.ai_provider).lower()
    ai_cfg = settings.app.ai
    kwargs = dict(
        temperature=ai_cfg.temperature,
        max_tokens=ai_cfg.max_tokens,
        timeout=ai_cfg.request_timeout_seconds,
    )
    try:
        if provider_name == "claude":
            from .claude_provider import ClaudeProvider
            return ClaudeProvider(**kwargs)
        if provider_name == "openai":
            from .openai_provider import OpenAIProvider
            return OpenAIProvider(**kwargs)
        if provider_name == "gemini":
            from .gemini_provider import GeminiProvider
            return GeminiProvider(**kwargs)
        if provider_name == "ollama":
            from .ollama_provider import OllamaProvider
            return OllamaProvider(**kwargs)
        if provider_name == "nvidia":
            from .nvidia_provider import NvidiaProvider
            return NvidiaProvider(**kwargs)
        if provider_name == "openrouter":
            from .openrouter_provider import OpenRouterProvider
            return OpenRouterProvider(**kwargs)
    except AIProviderUnavailableError:
        raise
    except Exception as exc:
        raise AIProviderUnavailableError(f"Failed to init {provider_name}: {exc}") from exc

    raise AIProviderUnavailableError(f"Unknown AI provider: {provider_name}")
