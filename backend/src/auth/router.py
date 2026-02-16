from fastapi import APIRouter, HTTPException, status

from .models import RegisterRequest, LoginRequest, AuthResponse
from .service import register_user, login_user
from .. import printmeup as pm

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def endpoint_register(request: RegisterRequest):
    """Register a new user account."""
    try:
        result = register_user(
            email=request.email,
            password=request.password,
            name=request.name,
            account_type=request.account_type,
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
async def endpoint_login(request: LoginRequest):
    """Authenticate and receive a JWT token."""
    try:
        result = login_user(email=request.email, password=request.password)
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
