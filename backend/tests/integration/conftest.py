"""
Shared fixtures for integration tests.

Integration tests run the full FastAPI app with stubbed external
dependencies — no real Postgres, no real LLM agent, no real Resend.
We mock the boundaries so the request → handler → response path is
exercised end-to-end while staying network-free in CI.

Skip note
---------
The full FastAPI app pulls in `src.agent.agent`, which transitively
imports langchain + sentence-transformers + pgvector. CI installs only
the lightweight test deps — bringing in the whole prod stack just to
boot the app is a 2-minute pip install we don't want to pay on every PR.
We skip the entire integration module when those deps aren't available;
the unit suite still covers all the pure logic. A dedicated integration
job (with the prod stack installed and a real Postgres container) can
be added later when the value of the extra coverage justifies the cost.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

# Bail out cleanly if the heavyweight stack isn't installed (typical CI).
pytest.importorskip(
    "langchain",
    reason="integration tests require the full prod stack; see conftest docstring",
)
pytest.importorskip("pgvector", reason="pgvector required for ORM imports")


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
    fake_session = MagicMock()
    fake_session.execute.return_value.first.return_value = (1,)
    fake_session.query.return_value.filter.return_value.first.return_value = None

    def _fake_get_session():
        return fake_session

    monkeypatch.setattr("src.db.sql_client.get_session", _fake_get_session)
    import src.auth.service as auth_service
    monkeypatch.setattr(auth_service, "get_session", _fake_get_session, raising=False)

    async def _noop_init():
        return MagicMock()

    monkeypatch.setattr("src.agent.agent.init_medical_agent", _noop_init)

    async def _noop_send(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "src.auth.email_sender.send_verification_code",
        _noop_send,
    )

    from fastapi.testclient import TestClient
    from src.main import app

    return TestClient(app)
