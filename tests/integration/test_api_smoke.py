"""API smoke test.

Production runs Postgres. For fast CI we monkey-patch the session module
with an isolated in-memory SQLite engine before the app starts up.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from architect_job_agent.infrastructure.db import session as session_mod
from architect_job_agent.infrastructure.db.models import Base


@pytest.fixture()
def app_client(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    # Bypass the production engine factory.
    monkeypatch.setattr(session_mod, "_engine", engine, raising=False)
    monkeypatch.setattr(session_mod, "_SessionLocal", factory, raising=False)
    monkeypatch.setattr(session_mod, "init_db", lambda url=None: None)

    from architect_job_agent.presentation.api.app import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client
    engine.dispose()


def test_health(app_client):
    r = app_client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_config(app_client):
    r = app_client.get("/api/config")
    assert r.status_code == 200
    body = r.json()
    assert "countries" in body
    assert "roles" in body


def test_dashboard(app_client):
    r = app_client.get("/api/dashboard")
    assert r.status_code == 200
    assert "total_jobs" in r.json()
