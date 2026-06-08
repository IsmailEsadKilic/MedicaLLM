from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from ..auth.service import verify_token
from ..config import settings

from logging import getLogger
logger = getLogger(__name__)

# Rate limit tiers — applied per-decorator on the routes that should be
# bucketed (LLM endpoints, search endpoints, auth flows). We deliberately
# DO NOT pass default_limits to the Limiter constructor: a global default
# would apply the strictest limit (LLM = 10/min) to every endpoint,
# including cheap reads like GET /api/conversations/. The result was
# users hitting 429 just by refreshing the chat page a few times.
LLM_LIMIT: str = settings.llm_limit or "10/minute"
SEARCH_LIMIT: str = settings.search_limit or "60/minute"
AUTH_LIMIT: str = settings.auth_limit or "20/minute"
# Generous baseline for read endpoints (conversation list, version, etc.).
# Per-IP via the `user_key` resolver, so legitimate page navigations and
# soft-refreshes don't hit it.
READ_LIMIT: str = settings.read_limit if hasattr(settings, "read_limit") and settings.read_limit else "240/minute"



def user_key(request: Request) -> str:
    """
    Extract the authenticated user-id from the Bearer JWT for per-user bucketing.
    Falls back to the client IP if the token is absent or cannot be decoded.
    """
    auth_header: str | None = request.headers.get("authorization", None)
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            user_id = verify_token(token)
            return f"user:{user_id}"
        except ValueError: # invalid token
            pass  # fall through to IP
    return get_remote_address(request)

# singleton Limiter instance shared across all routers
limiter = Limiter(key_func=user_key)

logger.info(
    f"Rate limiter ready "
    f"(LLM={LLM_LIMIT}, search={SEARCH_LIMIT}, auth={AUTH_LIMIT}, read={READ_LIMIT})"
)