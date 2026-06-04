"""
User repository.
All database interactions for the User model live here.
No business logic — pure data access.
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_verification_token(db: Session, token: str) -> Optional[User]:
    return db.query(User).filter(User.verification_token == token).first()


def get_user_by_reset_token(db: Session, token: str) -> Optional[User]:
    return (
        db.query(User)
        .filter(
            User.reset_token == token,
            User.reset_token_expires_at > datetime.now(timezone.utc),
        )
        .first()
    )


def create_user(
    db: Session,
    *,
    full_name: str,
    email: str,
    password_hash: str,
    verification_token: Optional[str] = None,
) -> User:
    user = User(
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        verification_token=verification_token,
        is_verified=verification_token is None,  # auto-verify if no token needed
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def verify_user_email(db: Session, user: User) -> User:
    user.is_verified = True
    user.verification_token = None
    db.commit()
    db.refresh(user)
    return user


def set_reset_token(db: Session, user: User, expires_in_minutes: int = 30) -> str:
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=expires_in_minutes
    )
    db.commit()
    return token


def update_password(db: Session, user: User, new_password_hash: str) -> User:
    user.password_hash = new_password_hash
    user.reset_token = None
    user.reset_token_expires_at = None
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user: User) -> User:
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
