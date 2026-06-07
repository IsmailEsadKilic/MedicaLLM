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

3. **Stub heavyweight ORM imports.** `src.db.sql_models` imports
   `pgvector.sqlalchemy.Vector`. CI doesn't install pgvector (or
   sentence-transformers, langchain, etc.) for the unit suite, so we
   slot a tiny stub into `sys.modules` before any test module imports
   the project. Anything that needs a real Vector column is in the
   integration suite, which has its own gating import-skip.
"""
import os
import sys
import types
from pathlib import Path

# Add backend/ to the path so `from src import ...` works from anywhere.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_ROOT))


def _stub_module(name: str, attrs: dict | None = None) -> None:
    """Insert a placeholder module into sys.modules so `from X import Y`
    resolves without the real package being installed."""
    if name in sys.modules:
        return
    mod = types.ModuleType(name)
    for k, v in (attrs or {}).items():
        setattr(mod, k, v)
    sys.modules[name] = mod


# pgvector — sql_models imports `from pgvector.sqlalchemy import Vector`.
# We provide a no-op SQLAlchemy TypeDecorator-equivalent so the import
# succeeds and the metadata builds. None of the unit tests touch a
# Vector column.
try:
    import pgvector  # noqa: F401
except ImportError:
    from sqlalchemy.types import UserDefinedType

    class _StubVector(UserDefinedType):
        cache_ok = True

        def __init__(self, dim=None):
            self.dim = dim

        def get_col_spec(self, **kw):
            return "VECTOR"

    _stub_module("pgvector")
    _stub_module("pgvector.sqlalchemy", {"Vector": _StubVector})


# Provide harmless test defaults for required env vars so importing the
# config module never blows up in CI. Real values come from secrets when
# a test actually exercises an external service (we don't, in this suite).
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-not-for-production-use-only-tests")
os.environ.setdefault("ADMIN_PASSWORD", "test-admin-password")
os.environ.setdefault(
    "DO_POSTGRES_URL",
    "postgresql://test:test@localhost:5432/medicallm_test",
)
