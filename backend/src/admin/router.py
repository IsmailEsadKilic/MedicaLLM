from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config import settings


class AdminLoginRequest(BaseModel):
    username: str
    password: str


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/login")
async def endpoint_admin_login(body: AdminLoginRequest):
    if (
        body.username == settings.admin_username
        and body.password == settings.admin_password
    ):
        return {"success": True}
    raise HTTPException(status_code=401, detail="Invalid admin credentials")
