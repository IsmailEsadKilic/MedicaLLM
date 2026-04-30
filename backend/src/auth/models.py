from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Literal
import re

class UserDetails(BaseModel):
    # used internally and in llm prompts
    user_id: str
    email: EmailStr
    name: str
    account_type: Literal["doctor", "user", "patient"]
    
    def to_dto(self) -> UserDto:
        return UserDto(
            userId=self.user_id,
            email=self.email,
            name=self.name,
            accountType=self.account_type,
        )
        
class User(UserDetails):
    password: str
    created_at: str
    updated_at: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1)
    account_type: Literal["doctor", "user", "patient"]

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least 1 uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least 1 lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least 1 number")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", v):
            raise ValueError("Password must contain at least 1 special character")
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserDto(BaseModel):
    # used in API responses
    userId: str
    email: EmailStr
    name: str
    accountType: Literal["doctor", "user", "patient"]

class AuthResponse(BaseModel):
    token: str
    user: UserDto


