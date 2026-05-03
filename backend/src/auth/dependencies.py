from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import lru_cache

from ..auth.models import UserBase
from .service import verify_token, get_user_by_id

from logging import getLogger

logger = getLogger(__name__)


security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    try:
        logger.debug(f"[AUTH] Verifying token")
        user_id = verify_token(credentials.credentials)
        logger.debug(f"[AUTH] Token verified for user: {user_id}")
        return user_id
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserBase:
    try:
        user_id = verify_token(credentials.credentials)
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(user_id)
    if not user:
        logger.error(f"User not found for ID {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info(f"Current user retrieved: {user_id}")

    return UserBase(
        user_id=user_id,
        email=user.email,
        name=user.name,
        is_doctor=user.is_doctor,
        is_patient=user.is_patient,
    )
