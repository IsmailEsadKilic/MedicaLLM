import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

from ..db.sql_client import get_session
from ..db.sql_models import User
from ..config import settings
from .. import printmeup as pm


def get_user_by_email(email: str) -> dict | None:
    session = get_session()
    try:
        user = session.query(User).filter(User.email == email).first()
        return _user_to_dict(user) if user else None
    except Exception as e:
        pm.err(e=e, m=f"Error looking up user by email {email}")
        return None
    finally:
        session.close()


def get_user_by_id(user_id: str) -> dict | None:
    session = get_session()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        return _user_to_dict(user) if user else None
    except Exception as e:
        pm.err(e=e, m=f"Error looking up user by id {user_id}")
        return None
    finally:
        session.close()


def _user_to_dict(user: User) -> dict:
    return {
        "userId": user.user_id,
        "email": user.email,
        "password": user.password,
        "name": user.name,
        "accountType": user.account_type,
        "createdAt": user.created_at,
    }


def register_user(email: str, password: str, name: str, account_type: str) -> dict:
    existing = get_user_by_email(email)
    if existing:
        raise ValueError("User already exists")

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user_id = f"user_{int(datetime.now(timezone.utc).timestamp() * 1000)}"

    session = get_session()
    try:
        session.add(User(
            user_id=user_id, email=email, password=hashed_password,
            name=name, account_type=account_type,
            created_at=datetime.now(timezone.utc).isoformat(),
        ))
        session.commit()
    except Exception as e:
        session.rollback()
        pm.err(e=e, m=f"Error writing new user {email} ({user_id})")
        raise RuntimeError("Failed to save user") from e
    finally:
        session.close()

    pm.suc(f"User registered: {email} ({user_id})")
    token = _create_token(user_id)
    return {
        "token": token,
        "user": {"user_id": user_id, "email": email, "name": name, "account_type": account_type},
    }


def login_user(email: str, password: str) -> dict:
    user = get_user_by_email(email)
    if not user:
        raise ValueError("Invalid credentials")

    if not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
        raise ValueError("Invalid credentials")

    token = _create_token(user["userId"])
    return {
        "token": token,
        "user": {
            "user_id": user["userId"], "email": user["email"],
            "name": user["name"], "account_type": user["accountType"],
        },
    }


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
    """Reset a user's password."""
    session = get_session()
    try:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("User not found")
        hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user.password = hashed
        session.commit()
        pm.suc(f"Password reset for {email}")
    except ValueError:
        raise
    except Exception as e:
        session.rollback()
        pm.err(e=e, m=f"Error resetting password for {email}")
        raise
    finally:
        session.close()
