from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use the in-repo config dir for tests
os.environ.setdefault("CONFIG_DIR", str(Path(__file__).resolve().parents[1] / "config"))
# Production rejects non-Postgres URLs; tests provide a placeholder that
# satisfies the Settings validator. Test fixtures build their own engines.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://test:test@localhost:5432/test",
)

from architect_job_agent.infrastructure.db.models import Base  # noqa: E402


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)
    s = factory()
    try:
        yield s
        s.commit()
    finally:
        s.close()
        engine.dispose()
