import secrets
import threading
import time
from typing import Optional, TypedDict

from fastapi import APIRouter, HTTPException, Request, status

from .models import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SendCodeRequest,
    VerificationCodeRequest,
)
from .service import (
    get_user_by_email,
    login_user,
    register_user,
    reset_password,
    send_verification_email,
)
from ..middleware.rate_limiter import AUTH_LIMIT, get_remote_address, limiter

from logging import getLogger

logger = getLogger(__name__)


# Verification codes are short-lived (default 10 minutes). Storing them in
# memory only is acceptable for a single-process deployment; a future
# multi-worker setup should move these to Redis. The audit (S9) flags both
# the missing expiry and the in-memory persistence — we fix expiry here and
# document the worker-affinity caveat.
_CODE_TTL_SECONDS = 10 * 60


class _PendingVerification(TypedDict):
    code: str
    data: RegisterRequest
    expires_at: float


class _PendingReset(TypedDict):
    code: str
    expires_at: float


_pending_verifications: dict[str, _PendingVerification] = {}
_pending_resets: dict[str, _PendingReset] = {}
_lock = threading.Lock()


def _generate_code() -> str:
    """
    Generate a 6-digit verification code using the `secrets` module so the
    output is suitable for security-sensitive use (audit S8).

    `random.randint` from the previous version is a non-cryptographic PRNG.
    """
    # secrets.randbelow gives a uniform integer in [0, n).
    return f"{secrets.randbelow(1_000_000):06d}"


def _now() -> float:
    return time.time()


def _purge_expired() -> None:
    """Drop expired pending codes. Called from the request path so we don't
    need a background sweeper just for short-lived state."""
    now = _now()
    with _lock:
        for store in (_pending_verifications, _pending_resets):
            stale = [k for k, v in store.items() if v["expires_at"] < now]
            for k in stale:
                store.pop(k, None)


def _check_code(stored: dict, supplied: str) -> bool:
    """Constant-time comparison + expiry check."""
    if _now() > stored["expires_at"]:
        return False
    return secrets.compare_digest(stored["code"], supplied)


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/send-code")
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_send_code(request: Request, body: SendCodeRequest):
    _purge_expired()
    existing = get_user_by_email(body.email)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    code = _generate_code()

    with _lock:
        _pending_verifications[body.email] = _PendingVerification(
            code=code,
            data=RegisterRequest(
                email=body.email,
                password=body.password,
                name=body.name,
                account_type=body.account_type,
            ),
            expires_at=_now() + _CODE_TTL_SECONDS,
        )

    await send_verification_email(body.email, code)

    return {
        "success": True,
        "message": "Verification code sent via email.",
        "expires_in_seconds": _CODE_TTL_SECONDS,
    }


@router.post(
    "/verification-code",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_verification_code(request: Request, body: VerificationCodeRequest):
    _purge_expired()
    with _lock:
        pending = _pending_verifications.get(body.email)

    if not pending:
        raise HTTPException(
            status_code=400,
            detail="No pending verification for this email. Please request a new code.",
        )

    if not _check_code(pending, body.code):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    try:
        data = RegisterRequest.model_validate(pending["data"])
        result = register_user(
            email=data.email,
            password=data.password,
            name=data.name,
        )

        # If user selected "Healthcare Pro", create doctor profile automatically
        if data.account_type == "doctor":
            from ..users.service import create_doctor_profile
            from ..users.models import DoctorBase
            doctor_data = DoctorBase(
                doctor_id="",
                user_id=result.user.userId,
                name=data.name,
                specialty="General",
            )
            create_doctor_profile(result.user.userId, doctor_data)
            # Update the response to reflect doctor status
            result.user.isDoctor = True

        # If user selected "Patient", create patient profile automatically
        if data.account_type == "patient":
            from ..users.service import create_patient_profile
            from ..users.models import PatientBase
            patient_data = PatientBase(
                patient_id="",
                user_id=result.user.userId,
                name=data.name,
            )
            patient = create_patient_profile(result.user.userId, patient_data)
            # Update the response to reflect patient status
            result.user.isPatient = True
            if patient:
                result.user.patientId = patient.patient_id

        with _lock:
            _pending_verifications.pop(body.email, None)

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.error("Registration failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=AuthResponse)
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_login(request: Request, body: LoginRequest):
    try:
        result = login_user(email=body.email, password=body.password)
        return result
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception:
        logger.error("Login failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/forgot-password")
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_forgot_password(request: Request, body: ForgotPasswordRequest):
    _purge_expired()

    user = get_user_by_email(body.email)
    # Don't reveal whether the email is registered or not.
    if user:
        code = _generate_code()
        with _lock:
            _pending_resets[body.email] = _PendingReset(
                code=code,
                expires_at=_now() + _CODE_TTL_SECONDS,
            )
        await send_verification_email(body.email, code)

    return {
        "success": True,
        "message": "If this email is registered, a reset code has been sent.",
    }


@router.post("/reset-password")
@limiter.limit(AUTH_LIMIT, key_func=get_remote_address)
async def endpoint_reset_password(request: Request, body: ResetPasswordRequest):
    _purge_expired()
    with _lock:
        stored = _pending_resets.get(body.email)

    if not stored:
        raise HTTPException(
            status_code=400,
            detail="No pending reset for this email. Please request a new code.",
        )

    if not _check_code(stored, body.code):
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")

    try:
        reset_password(email=body.email, new_password=body.new_password)
        with _lock:
            _pending_resets.pop(body.email, None)
        return {
            "success": True,
            "message": "Password reset successfully. You can now sign in.",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.error("Password reset failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Password reset failed")
