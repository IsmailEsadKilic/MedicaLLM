from pdb import pm
import random
import threading
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from .models import RegisterRequest, LoginRequest, AuthResponse
from .service import (
    register_user,
    login_user,
    get_user_by_email,
    reset_password,
    send_verification_email,
)
from ..middleware.rate_limiter import limiter, AUTH_LIMIT, get_remote_address

from logging import getLogger

logger = getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory store for pending verification codes
_pending_verifications: dict[
    str, dict[str, str | RegisterRequest]
] = {}  # email -> {"code": str, "data": RegisterRequest}
_pending_resets: dict[str, str] = {}  # email -> code
_lock = threading.Lock()


class SendCodeRequest(RegisterRequest):
    pass


class VerificationCodeRequest(BaseModel):
    email: EmailStr
    code: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str


@router.post("/send-code")
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_send_code(request: Request, body: SendCodeRequest):
    existing = get_user_by_email(body.email)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    code = f"{random.randint(100000, 999999)}"

    with _lock:
        _pending_verifications[body.email] = {
            "code": code,
            "data": RegisterRequest(
                email=body.email,
                password=body.password,
                name=body.name,
                account_type=body.account_type,
            ),
        }

    await send_verification_email(body.email, code)

    return {"success": True, "message": "Verification code sent via email."}


@router.post(
    "/verification-code",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_verification_code(request: Request, body: VerificationCodeRequest):
    with _lock:
        pending = _pending_verifications.get(body.email)

    if not pending:
        raise HTTPException(
            status_code=400,
            detail="No pending verification for this email. Please request a new code.",
        )

    if pending["code"] != body.code:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    try:
        data = RegisterRequest.model_validate(pending["data"])
        result = register_user(
            email=data.email,
            password=data.password,
            name=data.name,
            account_type=data.account_type,
        )

        with _lock:
            # clean up
            _pending_verifications.pop(body.email, None)

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=AuthResponse)
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_login(request: Request, body: LoginRequest):
    try:
        result = login_user(email=body.email, password=body.password)
        return result
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/forgot-password")
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_forgot_password(request: Request, body: ForgotPasswordRequest):

    user = get_user_by_email(body.email)
    # don't reveal whether the email is registered or not
    if user:
        code = f"{random.randint(100000, 999999)}"

        with _lock:
            _pending_resets[body.email] = code

        await send_verification_email(body.email, code)

    return {
        "success": True,
        "message": "If this email is registered, a reset code has been sent.",
    }


@router.post("/reset-password")
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_reset_password(request: Request, body: ResetPasswordRequest):
    with _lock:
        stored_code = _pending_resets.get(body.email)

    if not stored_code:
        raise HTTPException(
            status_code=400,
            detail="No pending reset for this email. Please request a new code.",
        )

    if stored_code != body.code:
        raise HTTPException(status_code=400, detail="Invalid reset code")

    try:
        reset_password(email=body.email, new_password=body.new_password)
        with _lock:
            # clean up
            _pending_resets.pop(body.email, None)
        return {
            "success": True,
            "message": "Password reset successfully. You can now sign in.",
        }
    except ValueError as e:
        # this happens if user is not found.
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Password reset failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Password reset failed")
