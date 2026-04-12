from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import service
from ..config import settings
from .. import printmeup as pm

router = APIRouter(prefix="/api/admin", tags=["admin"])


class AdminLoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def endpoint_admin_login(body: AdminLoginRequest):
    """Verify admin credentials."""
    if body.username == settings.admin_username and body.password == settings.admin_password:
        return {"success": True}
    raise HTTPException(status_code=401, detail="Invalid admin credentials")


@router.get("/stats")
async def endpoint_system_stats():
    """Get overall system statistics."""
    try:
        return service.get_system_stats()
    except Exception as e:
        pm.err(e=e, m="Error fetching system stats")
        raise HTTPException(status_code=500, detail="Failed to fetch stats")


@router.get("/users")
async def endpoint_all_users():
    """Get all users with their usage statistics."""
    try:
        users = service.get_all_users_stats()
        return {"users": users, "count": len(users)}
    except Exception as e:
        pm.err(e=e, m="Error fetching user stats")
        raise HTTPException(status_code=500, detail="Failed to fetch users")
