from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from ..config import settings

import secrets

ADMIN_TOKEN_AUDIENCE = "medicallm-admin"


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    success: bool
    token: str
    expires_in_hours: int


router = APIRouter(prefix="/api/admin", tags=["admin"])
_security = HTTPBearer(auto_error=False)


def _create_admin_token() -> str:
    """Mint a short-lived JWT scoped to admin operations."""
    payload = {
        "sub": settings.admin_username,
        "aud": ADMIN_TOKEN_AUDIENCE,
        "exp": datetime.now(timezone.utc) + timedelta(hours=4),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> str:
    """FastAPI dependency: validates the bearer token belongs to an admin."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=["HS256"],
            audience=ADMIN_TOKEN_AUDIENCE,
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired admin token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    sub = payload.get("sub")
    if not sub or sub != settings.admin_username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an admin token",
        )
    return sub


@router.post("/login", response_model=AdminLoginResponse)
def endpoint_admin_login(body: AdminLoginRequest):
    """
    Authenticate the admin and return a short-lived JWT.

    Comparing both username and password with `secrets.compare_digest` resists
    timing attacks. Admin login is disabled when ADMIN_PASSWORD is unset (S1).
    """
    if not settings.admin_password:
        # Treat as 401 to avoid leaking that the service is misconfigured to
        # an unauthenticated caller.
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    username_ok = secrets.compare_digest(
        body.username.encode("utf-8"),
        settings.admin_username.encode("utf-8"),
    )
    # Support either bcrypt-hashed or plaintext admin password in env, so
    # operators can move to a hashed value without breaking deployments.
    stored = settings.admin_password
    try:
        if stored.startswith("$2") and len(stored) >= 50:
            password_ok = bcrypt.checkpw(
                body.password.encode("utf-8"), stored.encode("utf-8")
            )
        else:
            password_ok = secrets.compare_digest(
                body.password.encode("utf-8"), stored.encode("utf-8")
            )
    except Exception:
        password_ok = False

    if not (username_ok and password_ok):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    token = _create_admin_token()
    return AdminLoginResponse(success=True, token=token, expires_in_hours=4)


@router.get("/stats")
def endpoint_admin_stats(_admin: str = Depends(require_admin)):
    """Return system-wide statistics. Admin only."""
    from .service import get_system_stats
    return get_system_stats()


@router.get("/users")
def endpoint_admin_users(_admin: str = Depends(require_admin)):
    """Return all users with usage stats. Admin only."""
    from .service import get_all_users
    return {"users": get_all_users()}


@router.get("/doctors")
def endpoint_admin_doctors(_admin: str = Depends(require_admin)):
    """Return all doctors. Admin only."""
    from .service import get_all_doctors
    return {"doctors": get_all_doctors()}


@router.get("/patients")
def endpoint_admin_patients(_admin: str = Depends(require_admin)):
    """Return all patients. Admin only."""
    from .service import get_all_patients
    return {"patients": get_all_patients()}


@router.get("/relationships")
def endpoint_admin_relationships(_admin: str = Depends(require_admin)):
    """Return all doctor-patient assignments. Admin only."""
    from .service import get_all_relationships
    return {"relationships": get_all_relationships()}
