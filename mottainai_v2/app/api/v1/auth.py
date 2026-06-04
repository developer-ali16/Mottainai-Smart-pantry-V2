"""
Authentication API endpoints.
All routes are versioned under /api/v1/auth.
"""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import get_current_user_id
from app.db.session import get_db
from app.repositories import user_repository
from app.schemas.base import SuccessResponse
from app.schemas.user import (
    ChangePasswordRequest,
    LoginResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    payload: UserRegister,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = auth_service.register_user(db, payload, settings)
    return SuccessResponse(
        data=user,
        message="Account created. Please check your email to verify your account.",
    )


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Log in and receive a session cookie",
)
def login(
    payload: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    return auth_service.login_user(db, payload, response, settings)


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@router.post(
    "/logout",
    summary="Log out and clear the session cookie",
)
def logout(response: Response):
    return auth_service.logout_user(response)


# ---------------------------------------------------------------------------
# Current user profile
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="Get the currently authenticated user's profile",
)
def get_me(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    from app.core.exceptions import NotFoundException
    user = user_repository.get_user_by_id(db, user_id)
    if not user:
        raise NotFoundException("User")
    return SuccessResponse(data=UserResponse.model_validate(user))


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------

@router.get(
    "/verify-email",
    response_model=SuccessResponse[UserResponse],
    summary="Verify email address using the token sent by email",
)
def verify_email(token: str, db: Session = Depends(get_db)):
    user = auth_service.verify_email(db, token)
    return SuccessResponse(data=user, message="Email verified successfully.")


# ---------------------------------------------------------------------------
# Password management
# ---------------------------------------------------------------------------

@router.post(
    "/forgot-password",
    summary="Request a password reset email",
)
def forgot_password(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    return auth_service.request_password_reset(db, payload, settings)


@router.post(
    "/reset-password",
    summary="Reset password using a valid token",
)
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    return auth_service.reset_password(db, payload)


@router.post(
    "/change-password",
    summary="Change password for the authenticated user",
)
def change_password(
    payload: ChangePasswordRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return auth_service.change_password(db, user_id, payload)
