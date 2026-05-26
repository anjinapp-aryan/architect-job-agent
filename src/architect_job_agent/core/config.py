"""Configuration loader.

Reads YAML files under ``config/`` and exposes typed Pydantic settings.
Environment variables override YAML where indicated. Nothing about countries,
roles, skills, paths or providers is hardcoded.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from .exceptions import ConfigError

load_dotenv()

DEFAULT_CONFIG_DIR = Path(os.getenv("CONFIG_DIR", "config")).resolve()


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Config file missing: {path}")
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"Config root must be a mapping in {path}")
    return data


# ---------- Pydantic models ----------


class DatabaseConfig(BaseModel):
    """Postgres connection + pool tuning. URL must come from env var.

    SQLite is no longer a supported runtime backend. Tests construct their
    own in-memory engine directly.
    """

    url: str = ""
    pool_size: int = 10
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle_seconds: int = 1800
    statement_timeout_ms: int = 30000
    echo: bool = False


class AIConfig(BaseModel):
    provider: str = "claude"
    temperature: float = 0.2
    max_tokens: int = 4000
    request_timeout_seconds: int = 90


class AppConfig(BaseModel):
    name: str = "architect-job-agent"
    log_level: str = "INFO"
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ai: AIConfig = Field(default_factory=AIConfig)


class ProfileConfig(BaseModel):
    full_name: str = "Candidate"
    email: str = ""
    experience_years: int = 0
    current_title: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    preferred_countries: list[str] = Field(default_factory=list)
    preferred_roles: list[str] = Field(default_factory=list)
    visa_status: str = ""


class SearchConfig(BaseModel):
    max_age_days: int = 30
    remote_allowed: bool = True
    minimum_match_score: int = 70
    results_per_query: int = 25
    sources: list[str] = Field(default_factory=lambda: ["linkedin", "indeed"])
    countries: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    rate_limit_seconds: int = 5
    retries: int = 3


class ResumeConfig(BaseModel):
    resume_directory: str = "data/resumes"
    master_resume: str = "data/resumes/master_resume.docx"
    tailored_directory: str = "data/tailored_resumes"
    supported_formats: list[str] = Field(default_factory=lambda: ["docx", "pdf"])


class CoverLetterConfig(BaseModel):
    output_directory: str = "data/cover_letters"
    default_tone: str = "professional, confident, concise"
    max_words: int = 350


class Settings(BaseModel):
    app: AppConfig
    profile: ProfileConfig
    search: SearchConfig
    resume: ResumeConfig
    coverletter: CoverLetterConfig
    countries: list[str]
    roles: list[str]

    @property
    def database_url(self) -> str:
        url = os.getenv("DATABASE_URL", self.app.database.url or "").strip()
        if not url:
            raise ConfigError(
                "DATABASE_URL is not set. Provide a Supabase Postgres DSN, e.g. "
                "postgresql+psycopg://postgres.<ref>:<pwd>@aws-0-<region>"
                ".pooler.supabase.com:6543/postgres"
            )
        if url.startswith("postgres://"):
            # SQLAlchemy 2.x requires the explicit driver scheme
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        if url.startswith("postgresql://") and "+psycopg" not in url:
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        if not url.startswith("postgresql+psycopg://"):
            raise ConfigError(
                f"Unsupported DATABASE_URL scheme: {url.split('://', 1)[0]}. "
                "Only PostgreSQL (postgresql+psycopg://) is supported."
            )
        return url

    @property
    def auto_create_tables(self) -> bool:
        return os.getenv("AUTO_CREATE_TABLES", "false").lower() in {"1", "true", "yes"}

    @property
    def ai_provider(self) -> str:
        return os.getenv("AI_PROVIDER", self.app.ai.provider).lower()


# ---------- Loader ----------


def _load_section(config_dir: Path, file: str, key: str) -> Any:
    data = _load_yaml(config_dir / file)
    if key not in data:
        raise ConfigError(f"Missing key '{key}' in {file}")
    return data[key]


@lru_cache(maxsize=1)
def get_settings(config_dir: str | None = None) -> Settings:
    cdir = Path(config_dir).resolve() if config_dir else DEFAULT_CONFIG_DIR
    try:
        app = AppConfig.model_validate(_load_yaml(cdir / "app.yaml").get("app", {}))
        # database/ai nested under app.yaml top level
        raw_app = _load_yaml(cdir / "app.yaml")
        if "database" in raw_app:
            app.database = DatabaseConfig.model_validate(raw_app["database"])
        if "ai" in raw_app:
            app.ai = AIConfig.model_validate(raw_app["ai"])
        countries = _load_section(cdir, "countries.yaml", "countries")
        roles = _load_section(cdir, "roles.yaml", "roles")
        profile = ProfileConfig.model_validate(
            _load_section(cdir, "profile.yaml", "profile")
        )
        search = SearchConfig.model_validate(
            _load_section(cdir, "search.yaml", "search")
        )
        resume = ResumeConfig.model_validate(
            _load_section(cdir, "resume.yaml", "resume")
        )
        coverletter = CoverLetterConfig.model_validate(
            _load_section(cdir, "coverletter.yaml", "coverletter")
        )
    except ConfigError:
        raise
    except Exception as exc:  # pragma: no cover
        raise ConfigError(f"Failed to load settings: {exc}") from exc

    return Settings(
        app=app,
        profile=profile,
        search=search,
        resume=resume,
        coverletter=coverletter,
        countries=list(countries),
        roles=list(roles),
    )


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()
