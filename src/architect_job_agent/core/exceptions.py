"""Domain-wide exception hierarchy."""
from __future__ import annotations


class ArchitectJobAgentError(Exception):
    """Base class for all application errors."""


class ConfigError(ArchitectJobAgentError):
    """Raised when configuration loading or validation fails."""


class JobSourceUnavailableError(ArchitectJobAgentError):
    """Raised when an upstream job board is unreachable."""


class RateLimitedError(ArchitectJobAgentError):
    """Raised when an upstream provider rate-limits us."""


class AIProviderError(ArchitectJobAgentError):
    """Raised when an AI provider call fails irrecoverably."""


class AIProviderUnavailableError(AIProviderError):
    """Raised when no AI provider can be reached."""


class ResumeParsingError(ArchitectJobAgentError):
    """Raised when resume parsing fails (corrupt / unsupported / missing)."""


class CoverLetterGenerationError(ArchitectJobAgentError):
    """Raised when cover-letter generation fails."""


class DuplicateJobError(ArchitectJobAgentError):
    """Raised internally when an attempt is made to insert a duplicate job."""


class RepositoryError(ArchitectJobAgentError):
    """Raised on persistence-layer failures."""
