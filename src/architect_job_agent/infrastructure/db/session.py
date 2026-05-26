"""SQLAlchemy 2.x engine + session factory for Supabase PostgreSQL.

Production stance:
- Postgres only (`postgresql+psycopg://...`). SQLite is gone.
- ``QueuePool`` with ``pool_pre_ping`` + ``pool_recycle`` — survives
  Supabase pooler idle disconnects.
- Per-connection ``statement_timeout`` so a runaway query cannot wedge a worker.
- ``application_name`` set so it shows up clearly in Supabase logs.
- Schema lifecycle owned by Alembic. ``init_db()`` only calls
  ``create_all()`` if ``AUTO_CREATE_TABLES=true`` (dev shortcut).
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ...core.config import get_settings
from ...core.logging import get_logger
from .models import Base

logger = get_logger(__name__)

APPLICATION_NAME = "architect-job-agent"


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes"}


def make_engine(url: str | None = None) -> Engine:
    settings = get_settings()
    db_url = url or settings.database_url
    cfg = settings.app.database

    pool_size = _int_env("DB_POOL_SIZE", cfg.pool_size)
    max_overflow = _int_env("DB_MAX_OVERFLOW", cfg.max_overflow)
    pool_timeout = _int_env("DB_POOL_TIMEOUT", cfg.pool_timeout)
    pool_recycle = _int_env("DB_POOL_RECYCLE", cfg.pool_recycle_seconds)
    statement_timeout_ms = _int_env("DB_STATEMENT_TIMEOUT_MS", cfg.statement_timeout_ms)
    echo = _bool_env("DB_ECHO", cfg.echo)

    engine = create_engine(
        db_url,
        future=True,
        echo=echo,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=True,
        connect_args={
            "application_name": APPLICATION_NAME,
            "options": f"-c statement_timeout={statement_timeout_ms}",
        },
    )

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_conn, _):  # pragma: no cover
        logger.debug("db.connect", pid=getattr(dbapi_conn, "info", None))

    return engine


_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def init_db(url: str | None = None) -> None:
    """Initialise the global engine + session factory.

    Schema management belongs to Alembic. ``create_all`` only runs when the
    dev escape hatch ``AUTO_CREATE_TABLES=true`` is set.
    """
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = make_engine(url)
    _SessionLocal = sessionmaker(
        bind=_engine, autoflush=False, autocommit=False, future=True
    )
    if get_settings().auto_create_tables:
        logger.warning("db.auto_create_tables.enabled")
        Base.metadata.create_all(_engine)


def get_engine() -> Engine:
    if _engine is None:
        init_db()
    assert _engine is not None
    return _engine


def get_session_factory() -> sessionmaker:
    if _SessionLocal is None:
        init_db()
    assert _SessionLocal is not None
    return _SessionLocal


@contextmanager
def session_scope() -> Iterator[Session]:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def dispose_engine() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
