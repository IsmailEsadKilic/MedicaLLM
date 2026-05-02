from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Literal
import re

class UserBase(BaseModel):
    # used interally and in llm context
    user_id: str
    email: EmailStr
    name: str
    is_doctor: bool = False  # Computed from doctor_profile existence
    is_patient: bool = False  # Computed from patient_profile existence
    
    def to_dto(self) -> UserDto:
        return UserDto(
            userId=self.user_id,
            email=self.email,
            name=self.name,
            isDoctor=self.is_doctor,
            isPatient=self.is_patient,
        )
        
class User(UserBase):
    password: str
    created_at: str
    updated_at: str

class UserDto(BaseModel):
    # used in API responses
    userId: str
    email: EmailStr
    name: str
    isDoctor: bool = False
    isPatient: bool = False

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

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1)
    
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
class SendCodeRequest(RegisterRequest):
    pass

class VerificationCodeRequest(BaseModel):
    email: EmailStr
    code: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

class AuthResponse(BaseModel):
    token: str
    user: UserDto