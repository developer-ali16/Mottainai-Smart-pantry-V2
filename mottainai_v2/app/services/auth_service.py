"""
Authentication service.
Business logic for registration, login, logout, and password management.
No direct DB calls — delegates to the repository layer.
"""
import secrets
from typing import Optional

from fastapi import Response
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import (
    ChangePasswordRequest,
    LoginResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    UserRegister,
    UserResponse,
)

logger = get_logger("auth_service")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_user(
    db: Session,
    payload: UserRegister,
    settings: Settings,
) -> UserResponse:
    """
    Create a new user account.
    - Checks for duplicate email (409 Conflict).
    - Hashes the password before storing.
    - Generates a verification token if email is configured.
    """
    if user_repository.get_user_by_email(db, payload.email):
        raise ConflictException("An account with this email address already exists.")

    verification_token = (
        secrets.token_urlsafe(32) if settings.email_configured else None
    )

    user = user_repository.create_user(
        db,
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        verification_token=verification_token,
    )

    logger.info("New user registered: user_id=%d email=%s", user.id, user.email)
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def login_user(
    db: Session,
    payload: "UserLogin",  # noqa: F821  (avoid circular import in type hint)
    response: Response,
    settings: Settings,
) -> LoginResponse:
    """
    Authenticate a user and set the JWT access token as an HTTP-only cookie.

    Security:
    - Returns the same error message for wrong email OR wrong password to
      prevent user enumeration.
    - Cookie is httponly=True, secure=True (in production), samesite="lax".
    """
    from app.schemas.user import UserLogin

    _AUTH_ERROR = "Invalid email or password."

    user = user_repository.get_user_by_email(db, payload.email)
    if not user:
        raise UnauthorizedException(_AUTH_ERROR)

    if not verify_password(payload.password, user.password_hash):
        raise UnauthorizedException(_AUTH_ERROR)

    if not user.is_active:
        raise UnauthorizedException("This account has been deactivated.")

    token = create_access_token(user.id, settings)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.is_production,   # HTTPS-only in production
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )

    logger.info("User logged in: user_id=%d", user.id)
    return LoginResponse(
        message="Login successful.",
        user=UserResponse.model_validate(user),
    )


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

def logout_user(response: Response) -> dict:
    """Clear the access token cookie."""
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return {"message": "Logged out successfully."}


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------

def verify_email(db: Session, token: str) -> UserResponse:
    """Mark the user's email as verified."""
    user = user_repository.get_user_by_verification_token(db, token)
    if not user:
        raise BadRequestException("Invalid or expired verification token.")
    user = user_repository.verify_user_email(db, user)
    logger.info("Email verified: user_id=%d", user.id)
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------

def request_password_reset(
    db: Session,
    payload: PasswordResetRequest,
    settings: Settings,
) -> dict:
    """
    Generate a password reset token.
    Always returns 200 — never reveals whether the email exists.
    """
    user = user_repository.get_user_by_email(db, payload.email)
    if user and user.is_active:
        token = user_repository.set_reset_token(db, user)
        logger.info("Password reset requested: user_id=%d", user.id)
        # In production, send this token via email (see email_service.py)
        # For development, we log it (remove in production!)
        if not settings.is_production:
            logger.debug("Reset token (dev only): %s", token)
    return {
        "message": (
            "If an account with that email exists, "
            "a password reset link has been sent."
        )
    }


def reset_password(db: Session, payload: PasswordResetConfirm) -> dict:
    """Apply a new password using a valid reset token."""
    user = user_repository.get_user_by_reset_token(db, payload.token)
    if not user:
        raise BadRequestException("Invalid or expired reset token.")
    user_repository.update_password(db, user, hash_password(payload.new_password))
    logger.info("Password reset completed: user_id=%d", user.id)
    return {"message": "Password updated successfully."}


def change_password(
    db: Session, user_id: int, payload: ChangePasswordRequest
) -> dict:
    """Change password for an authenticated user."""
    user = user_repository.get_user_by_id(db, user_id)
    if not user:
        raise NotFoundException("User")
    if not verify_password(payload.current_password, user.password_hash):
        raise UnauthorizedException("Current password is incorrect.")
    user_repository.update_password(db, user, hash_password(payload.new_password))
    logger.info("Password changed: user_id=%d", user.id)
    return {"message": "Password changed successfully."}
