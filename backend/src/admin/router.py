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
    e = HTTPException(status_code=401, detail="Invalid admin credentials")
    pm.err(e=e)
    raise e