"""
Notification repository.
All database interactions for the Notification model.
"""
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session,
    *,
    user_id: int,
    pantry_item_id: int,
    title: str,
    message: str,
    notification_type: str = "expiry_reminder",
) -> Notification:
    notification = Notification(
        user_id=user_id,
        pantry_item_id=pantry_item_id,
        title=title,
        message=message,
        notification_type=notification_type,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_notifications(
    db: Session,
    user_id: int,
    *,
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False,
) -> Tuple[List[Notification], int]:
    """Return (notifications, total_count) for the user."""
    limit = min(limit, 100)
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)  # noqa: E712
    total = query.count()
    items = (
        query.order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items, total


def get_notification(
    db: Session, notification_id: int, user_id: int
) -> Optional[Notification]:
    return (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        .first()
    )


def mark_as_read(db: Session, notification: Notification) -> Notification:
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_as_read(db: Session, user_id: int) -> int:
    """Mark all unread notifications as read. Returns the count updated."""
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .update({"is_read": True})
    )
    db.commit()
    return count


def get_unread_count(db: Session, user_id: int) -> int:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .count()
    )


def notification_already_sent(
    db: Session, user_id: int, pantry_item_id: int, notification_type: str
) -> bool:
    """
    Check if a notification of the given type was already created today
    for this pantry item. Prevents duplicate notifications.
    """
    from datetime import date
    today = date.today()
    result = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.pantry_item_id == pantry_item_id,
            Notification.notification_type == notification_type,
        )
        .first()
    )
    if result is None:
        return False
    return result.created_at.date() == today
