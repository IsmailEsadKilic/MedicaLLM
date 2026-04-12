"""
Creates a single ``Limiter`` singleton that is shared across all routers.
Three tiers are defined:

    LLM_LIMIT   = 10/minute  per authenticated user  (agent query endpoints)
    SEARCH_LIMIT = 60/minute per authenticated user  (drug search / interactions)
    AUTH_LIMIT  = 20/minute  per client IP           (login / register)
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from ..auth.service import verify_token
from .. import printmeup as pm

#* Rate limit tiers
LLM_LIMIT: str = "10/minute"
SEARCH_LIMIT: str = "60/minute"
AUTH_LIMIT: str = "20/minute"



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
        except ValueError: #* invalid token
            pass  #* fall through to IP
    return get_remote_address(request)

#* singleton Limiter instance shared across all routers
limiter = Limiter(key_func=user_key, default_limits=[])

pm.suc(
    f"Rate limiter ready "
    f"(LLM={LLM_LIMIT}, search={SEARCH_LIMIT}, auth={AUTH_LIMIT})"
)