from fastapi import APIRouter, HTTPException, Request, status

from .models import RegisterRequest, LoginRequest, AuthResponse
from .service import register_user, login_user
from .. import printmeup as pm
from ..middleware.rate_limiter import limiter, AUTH_LIMIT, get_remote_address

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_register(request: Request, body: RegisterRequest):
    """Register a new user account."""
    try:
        result = register_user(
            email=body.email,
            password=body.password,
            name=body.name,
            account_type=body.account_type,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        pm.err(e=e, m="Registration failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=AuthResponse)
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_login(request: Request, body: LoginRequest):
    """Authenticate and receive a JWT token."""
    try:
        result = login_user(email=body.email, password=body.password)
        return result
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    except Exception as e:
        pm.err(e=e, m="Login failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )
