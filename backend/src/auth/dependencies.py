from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .service import verify_token, get_user_by_id
from .. import printmeup as pm

security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    try:
        user_id = verify_token(credentials.credentials)
        return user_id
    except ValueError as e:
        pm.err(e=e, m="Token verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    try:
        user_id = verify_token(credentials.credentials)
    except ValueError as e:
        pm.err(e=e, m="Token verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(user_id)
    account_type = user.get("accountType", "general_user") if user else "general_user"
    return {"user_id": user_id, "account_type": account_type}
