"""User-related Pydantic schemas."""
import re
from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field, field_validator

from app.schemas.base import OrmModel


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class UserRegister(OrmModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 chars)")

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, v: str) -> str:
        cleaned = " ".join(v.strip().split())   # collapse internal whitespace
        return cleaned.title()                  # normalize to Title Case

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        v = v.strip()
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class UserLogin(OrmModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

    @field_validator("password")
    @classmethod
    def strip_password(cls, v: str) -> str:
        return v.strip()


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class UserResponse(OrmModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    is_verified: bool
    role: str
    created_at: datetime


class LoginResponse(OrmModel):
    message: str = "Login successful."
    user: UserResponse


# ---------------------------------------------------------------------------
# Password management
# ---------------------------------------------------------------------------

class PasswordResetRequest(OrmModel):
    email: EmailStr


class PasswordResetConfirm(OrmModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        v = v.strip()
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v


class ChangePasswordRequest(OrmModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        v = v.strip()
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v
