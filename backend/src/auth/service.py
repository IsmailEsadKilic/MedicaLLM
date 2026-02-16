import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from ..db.client import dynamodb_client
from ..config import settings
from .. import printmeup as pm


USERS_TABLE = "Users"


def get_user_by_email(email: str) -> dict | None:
    """Look up a user by email using the EmailIndex GSI."""
    try:
        table = dynamodb_client.Table(USERS_TABLE)  # type: ignore
        response = table.query(
            IndexName="EmailIndex",
            KeyConditionExpression=Key("email").eq(email),
        )
        items = response.get("Items", [])
        return items[0] if items else None
    except ClientError as e:
        pm.err(e=e, m=f"Error looking up user by email {email}")
        return None


def get_user_by_id(user_id: str) -> dict | None:
    """Get a user by userId (PK)."""
    try:
        table = dynamodb_client.Table(USERS_TABLE)  # type: ignore
        response = table.get_item(
            Key={"PK": f"USER#{user_id}", "SK": "PROFILE"}
        )
        return response.get("Item")
    except ClientError as e:
        pm.err(e=e, m=f"Error looking up user by id {user_id}")
        return None


def register_user(email: str, password: str, name: str, account_type: str) -> dict:
    """
    Register a new user. Returns dict with token and user info.
    Raises ValueError if user already exists.
    """
    existing = get_user_by_email(email)
    if existing:
        raise ValueError("User already exists")

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user_id = f"user_{int(datetime.now(timezone.utc).timestamp() * 1000)}"

    table = dynamodb_client.Table(USERS_TABLE)  # type: ignore
    table.put_item(
        Item={
            "PK": f"USER#{user_id}",
            "SK": "PROFILE",
            "email": email,
            "userId": user_id,
            "password": hashed_password,
            "name": name,
            "accountType": account_type,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
    )
    pm.suc(f"User registered: {email} ({user_id})")

    token = _create_token(user_id)
    return {
        "token": token,
        "user": {
            "user_id": user_id,
            "email": email,
            "name": name,
            "account_type": account_type,
        },
    }


def login_user(email: str, password: str) -> dict:
    """
    Authenticate a user. Returns dict with token and user info.
    Raises ValueError on invalid credentials.
    """
    user = get_user_by_email(email)
    if not user:
        raise ValueError("Invalid credentials")

    stored_hash = user["password"]
    if not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
        raise ValueError("Invalid credentials")

    token = _create_token(user["userId"])
    return {
        "token": token,
        "user": {
            "user_id": user["userId"],
            "email": user["email"],
            "name": user["name"],
            "account_type": user["accountType"],
        },
    }


def verify_token(token: str) -> str:
    """
    Verify a JWT token and return the userId.
    Raises ValueError if invalid.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload["userId"]
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


def _create_token(user_id: str) -> str:
    """Create a JWT token for a user."""
    payload = {
        "userId": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
