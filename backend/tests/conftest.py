"""
Pytest configuration shared across the suite.

Two design choices worth flagging:

1. **No real database in the unit-test layer.** The unit tests under
   `tests/unit/` exercise pure functions (email canonicalisation, password
   validators, etc.) and never touch SQLAlchemy. They run fast even on a
   developer laptop with no Postgres around.

2. **Lazy app construction for integration tests.** Importing `src.main`
   eagerly initialises the LLM agent and connects to the database, both of
   which we don't want in CI. Tests that need the real FastAPI app pull it
   in inside their fixture so the unit-test files don't pay the cost.
"""
import os
import sys
from pathlib import Path

# Add backend/ to the path so `from src import ...` works from anywhere.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_ROOT))

# Provide harmless test defaults for required env vars so importing the
# config module never blows up in CI. Real values come from secrets when
# a test actually exercises an external service (we don't, in this suite).
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-not-for-production-use-only-tests")
os.environ.setdefault("ADMIN_PASSWORD", "test-admin-password")
# We never connect to a real DB in unit tests; the engine is lazy in
# sql_client.py, so as long as nothing calls get_session() the URL is
# irrelevant. Set a syntactically valid placeholder anyway.
os.environ.setdefault(
    "DO_POSTGRES_URL",
    "postgresql://test:test@localhost:5432/medicallm_test",
)
