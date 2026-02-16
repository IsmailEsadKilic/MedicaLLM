from pydantic import BaseModel, EmailStr, Field
from typing import Literal


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1)
    account_type: Literal["general_user", "healthcare_professional"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    account_type: str


class AuthResponse(BaseModel):
    token: str
    user: UserResponse
