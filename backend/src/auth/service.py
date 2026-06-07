import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

from .models import UserDto, AuthResponse, User
from .email_utils import canonicalize_email, normalize_email
from ..db.sql_client import get_session
from ..db.sql_models import UserRecord
from ..config import settings

from logging import getLogger

logger = getLogger(__name__)


def _build_user_from_record(user: UserRecord) -> User:
    """Single helper so get_user_by_email and get_user_by_id agree on shape."""
    return User(
        user_id=user.user_id,  # type: ignore
        email=user.email,  # type: ignore
        password=user.password,  # type: ignore
        name=user.name,  # type: ignore
        created_at=user.created_at,  # type: ignore
        updated_at=user.updated_at,  # type: ignore
        is_doctor=user.doctor_profile is not None,
        is_patient=user.patient_profile is not None,
        patient_id=user.patient_profile.patient_id if user.patient_profile else None,
    )


def get_user_by_email(email: str) -> User | None:
    """
    Look up a user by email. Matches against the canonical form first
    (collapses Gmail dot/+plus aliases) and falls back to the raw email
    so that legacy rows registered before the canonical column existed
    are still found.
    """
    canonical = canonicalize_email(email)
    raw = normalize_email(email)
    session = get_session()
    try:
        user = (
            session.query(UserRecord)
            .filter(
                (UserRecord.email_canonical == canonical)
                | (UserRecord.email == raw)
                | (UserRecord.email == email)
            )
            .first()
        )
        if not user:
            return None
        return _build_user_from_record(user)
    except Exception as e:
        logger.error(f"Error looking up user by email {email}: {str(e)}")
        return None
    finally:
        session.close()


def get_user_by_id(user_id: str) -> User | None:
    session = get_session()
    try:
        user = session.query(UserRecord).filter(UserRecord.user_id == user_id).first()
        if not user:
            return None
        return _build_user_from_record(user)
    except Exception as e:
        logger.error(f"Error looking up user by ID {user_id}: {str(e)}")
        return None
    finally:
        session.close()


def register_user(email: str, password: str, name: str) -> AuthResponse:
    """Persist a new user. The raw email is stored as the user typed it
    (modulo lowercase / Unicode normalisation) and the aggressive canonical
    form (Gmail dot trick + plus alias collapsed) is stored alongside so
    duplicate detection survives obvious aliasing tricks."""
    logger.debug(f"[AUTH] Registration attempt for email: {email}, name: {name}")
    existing = get_user_by_email(email)
    if existing:
        logger.warning(f"[AUTH] Registration failed - user already exists: {email}")
        raise ValueError("User already exists")

    raw = normalize_email(email)
    canonical = canonicalize_email(email)

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    # Use a UUID4 instead of a timestamp so concurrent registrations cannot
    # collide on the same `user_id` (audit I15).
    import uuid as _uuid
    user_id = f"user_{_uuid.uuid4().hex}"
    logger.debug(f"[AUTH] Generated user_id: {user_id}, canonical: {canonical}")

    session = get_session()
    try:
        session.add(UserRecord(
            user_id=user_id, email=raw, email_canonical=canonical,
            password=hashed_password,
            name=name,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        ))
        session.commit()
        logger.info(f"[AUTH] User registered successfully: {raw} ({user_id})")
    except Exception as e:
        session.rollback()
        logger.error(f"[AUTH] Error registering user {email}: {str(e)}", exc_info=True)
        raise RuntimeError("Failed to save user") from e
    finally:
        session.close()

    token = _create_token(user_id)

    return AuthResponse(
        token=token,
        user=UserDto(
            userId=user_id,
            email=raw,
            name=name,
            isDoctor=False,
            isPatient=False,
        )
    )


def login_user(email: str, password: str) -> AuthResponse:
    logger.debug(f"[AUTH] Login attempt for email: {email}")
    user = get_user_by_email(email)
    if not user:
        logger.warning(f"[AUTH] Login failed - user not found: {email}")
        raise ValueError("Invalid credentials")

    if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        logger.warning(f"[AUTH] Login failed - invalid password for: {email}")
        raise ValueError("Invalid credentials")

    logger.info(f"[AUTH] Login successful for: {email} ({user.user_id})")
    token = _create_token(user.user_id)

    return AuthResponse(
        token=token,
        user=user.to_dto()
    )


def verify_token(token: str) -> str:
    logger.debug(f"[AUTH] Verifying token")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = payload["userId"]
        logger.debug(f"[AUTH] Token verified for user: {user_id}")
        return user_id
    except jwt.ExpiredSignatureError:
        logger.warning(f"[AUTH] Token expired")
        raise ValueError("Token expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"[AUTH] Invalid token: {str(e)}")
        raise ValueError("Invalid token")


def _create_token(user_id: str) -> str:
    payload = {
        "userId": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def reset_password(email: str, new_password: str) -> None:
    session = get_session()
    try:
        user = session.query(UserRecord).filter(UserRecord.email == email).first()
        if not user:
            raise ValueError("User not found")
        hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user.password = hashed # type: ignore
        session.commit()
        logger.info(f"Password reset for user: {email}")
    except ValueError:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error resetting password for {email}: {str(e)}")
        raise
    finally:
        session.close()

async def send_verification_email(email: str, code: str):
    msg = f"[AUTH] *** VERIFICATION CODE for {email}: {code} ***"
    logger.warning(msg)