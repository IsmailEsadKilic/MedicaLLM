import random
import threading
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from .models import RegisterRequest, LoginRequest, AuthResponse
from .service import register_user, login_user, get_user_by_email, reset_password
from .. import printmeup as pm
from ..middleware.rate_limiter import limiter, AUTH_LIMIT, get_remote_address

router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory store for pending verification codes
_pending_verifications: dict[str, dict] = {}
_pending_resets: dict[str, str] = {}  # email -> code
_lock = threading.Lock()


class SendCodeRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    account_type: str


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str


@router.post("/send-code")
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_send_code(request: Request, body: SendCodeRequest):
    """Send a 6-digit verification code to the user's email.
    
    Currently prints to server logs. Will be replaced with actual
    email sending in production.
    """
    # Check if user already exists
    existing = get_user_by_email(body.email)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    code = f"{random.randint(100000, 999999)}"

    with _lock:
        _pending_verifications[body.email] = {
            "code": code,
            "data": {
                "email": body.email,
                "password": body.password,
                "name": body.name,
                "account_type": body.account_type,
            },
        }

    # TODO: Replace with actual email sending (SMTP, SendGrid, etc.)
    pm.inf(f"")
    pm.inf(f"========================================")
    pm.inf(f"  VERIFICATION CODE for {body.email}")
    pm.inf(f"  Code: {code}")
    pm.inf(f"========================================")
    pm.inf(f"")

    return {"success": True, "message": "Verification code sent"}


@router.post("/verify-code", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_verify_code(request: Request, body: VerifyCodeRequest):
    """Verify the code and complete registration."""
    with _lock:
        pending = _pending_verifications.get(body.email)

    if not pending:
        raise HTTPException(status_code=400, detail="No pending verification for this email. Please request a new code.")

    if pending["code"] != body.code:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    # Code is correct — register the user
    try:
        data = pending["data"]
        result = register_user(
            email=data["email"],
            password=data["password"],
            name=data["name"],
            account_type=data["account_type"],
        )

        # Clean up
        with _lock:
            _pending_verifications.pop(body.email, None)

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        pm.err(e=e, m="Registration failed after verification")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_register(request: Request, body: RegisterRequest):
    """Direct registration (bypasses email verification). Kept for backward compatibility."""
    try:
        result = register_user(
            email=body.email, password=body.password,
            name=body.name, account_type=body.account_type,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        pm.err(e=e, m="Registration failed")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=AuthResponse)
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_login(request: Request, body: LoginRequest):
    """Authenticate and receive a JWT token."""
    try:
        result = login_user(email=body.email, password=body.password)
        return result
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        pm.err(e=e, m="Login failed")
        raise HTTPException(status_code=500, detail="Login failed")


# ── Forgot Password ──────────────────────────────────────────────────────────


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str


@router.post("/forgot-password")
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_forgot_password(request: Request, body: ForgotPasswordRequest):
    """Send a password reset code to the user's email."""
    user = get_user_by_email(body.email)
    if not user:
        # Don't reveal whether the email exists
        return {"success": True, "message": "If this email is registered, a reset code has been sent."}

    code = f"{random.randint(100000, 999999)}"

    with _lock:
        _pending_resets[body.email] = code

    pm.inf(f"")
    pm.inf(f"========================================")
    pm.inf(f"  PASSWORD RESET CODE for {body.email}")
    pm.inf(f"  Code: {code}")
    pm.inf(f"========================================")
    pm.inf(f"")

    return {"success": True, "message": "If this email is registered, a reset code has been sent."}


@router.post("/reset-password")
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_reset_password(request: Request, body: ResetPasswordRequest):
    """Verify reset code and set a new password."""
    with _lock:
        stored_code = _pending_resets.get(body.email)

    if not stored_code:
        raise HTTPException(status_code=400, detail="No pending reset for this email. Please request a new code.")

    if stored_code != body.code:
        raise HTTPException(status_code=400, detail="Invalid reset code")

    try:
        reset_password(email=body.email, new_password=body.new_password)
        with _lock:
            _pending_resets.pop(body.email, None)
        return {"success": True, "message": "Password reset successfully. You can now sign in."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        pm.err(e=e, m="Password reset failed")
        raise HTTPException(status_code=500, detail="Password reset failed")
