from typing import Literal
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

from backend.src.auth.models import AuthResponse, UserDto

from ..db.sql_client import get_session
from ..db.sql_models import UserRecord
from ..config import settings
from .models import User

from logging import getLogger

logger = getLogger(__name__)


def get_user_by_email(email: str) -> User | None:
    session = get_session()
    try:
        user = session.query(UserRecord).filter(UserRecord.email == email).first()
        return User.model_validate(user) if user else None

    except Exception as e:
        logger.error(f"Error looking up user by email {email}: {str(e)}")
        return None
    finally:
        session.close()


def get_user_by_id(user_id: str) -> User | None:
    session = get_session()
    try:
        user = session.query(UserRecord).filter(UserRecord.user_id == user_id).first()
        return User.model_validate(user) if user else None
    except Exception as e:
        logger.error(f"Error looking up user by ID {user_id}: {str(e)}")
        return None
    finally:
        session.close()


def register_user(email: str, password: str, name: str, account_type: Literal["doctor", "user", "patient"]) -> AuthResponse:
    existing = get_user_by_email(email)
    if existing:
        raise ValueError("User already exists")

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user_id = f"user_{int(datetime.now(timezone.utc).timestamp() * 1000)}"

    session = get_session()
    try:
        session.add(UserRecord(
            user_id=user_id, email=email, password=hashed_password,
            name=name, account_type=account_type,
            created_at=datetime.now(timezone.utc).isoformat(),
        ))
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error registering user {email}: {str(e)}")
        raise RuntimeError("Failed to save user") from e
    finally:
        session.close()

    logger.info(f"User registered: {email} ({user_id})")
    token = _create_token(user_id)

    return AuthResponse(
        token=token,
        user=UserDto(
            userId=user_id,
            email=email,
            name=name,
            accountType=account_type,
        )
    )


def login_user(email: str, password: str) -> AuthResponse:
    user = get_user_by_email(email)
    if not user:
        raise ValueError("Invalid credentials")

    if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        raise ValueError("Invalid credentials")

    token = _create_token(user.user_id)

    return AuthResponse(
        token=token,
        user=user.to_dto()
    )


def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload["userId"]
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
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
    print("========================================")
    print(f"  VERIFICATION CODE for {email}")
    print(f"  Code: {code}")
    print("========================================")