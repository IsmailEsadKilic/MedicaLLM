"""
Shared fixtures for integration tests.

Integration tests run the full FastAPI app with stubbed external
dependencies — no real Postgres, no real LLM agent, no real Resend.
We mock the boundaries so the request → handler → response path is
exercised end-to-end while staying network-free in CI.
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _disable_rate_limiter(monkeypatch):
    """The shared SlowAPI limiter caches counters across tests in the
    same process. Bumping the limit to a very large value is simpler
    than trying to reset the limiter between tests."""
    monkeypatch.setenv("AUTH_LIMIT", "10000/minute")


@pytest.fixture
def app_with_stubs(monkeypatch):
    """
    Returns a TestClient over the real FastAPI app, but with the
    expensive external deps stubbed out:

      * The SQLAlchemy session is a MagicMock — handlers can call .query,
        .add, .commit and they all no-op. Tests that need actual data must
        stub the relevant query result with .return_value.
      * The agent is replaced by a stub that returns a canned response.
      * Email delivery is a no-op.

    Use this fixture for testing routing, validation, and basic shape —
    not for testing data flow that genuinely needs a database.
    """
    # Stub the SQLAlchemy session BEFORE importing the FastAPI app, since
    # main.py kicks off DB connection warmup in its lifespan.
    fake_session = MagicMock()
    fake_session.execute.return_value.first.return_value = (1,)
    fake_session.query.return_value.filter.return_value.first.return_value = None

    def _fake_get_session():
        return fake_session

    monkeypatch.setattr("src.db.sql_client.get_session", _fake_get_session)
    # Some modules import get_session directly; patch those refs too.
    import src.auth.service as auth_service
    monkeypatch.setattr(auth_service, "get_session", _fake_get_session, raising=False)

    # Stub agent init so the app doesn't try to download embeddings.
    async def _noop_init():
        return MagicMock()

    monkeypatch.setattr("src.agent.agent.init_medical_agent", _noop_init)

    # Stub email delivery so registration attempts don't try to talk to
    # Resend or SMTP from the test harness.
    async def _noop_send(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "src.auth.email_sender.send_verification_code",
        _noop_send,
    )

    # Now we can safely build the app.
    from fastapi.testclient import TestClient
    from src.main import app

    return TestClient(app)
