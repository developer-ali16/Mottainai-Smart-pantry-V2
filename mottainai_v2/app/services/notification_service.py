"""
Notification service.
Business logic for in-app notifications.
"""
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.repositories import notification_repository
from app.schemas.notification import NotificationResponse, UnreadCountResponse


def list_notifications(
    db: Session,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
    unread_only: bool = False,
) -> Tuple[List[NotificationResponse], int]:
    skip = (page - 1) * page_size
    items, total = notification_repository.get_notifications(
        db, user_id, skip=skip, limit=page_size, unread_only=unread_only
    )
    return [NotificationResponse.model_validate(n) for n in items], total


def mark_notification_read(
    db: Session, notification_id: int, user_id: int
) -> NotificationResponse:
    notification = notification_repository.get_notification(db, notification_id, user_id)
    if not notification:
        raise NotFoundException("Notification")
    notification = notification_repository.mark_as_read(db, notification)
    return NotificationResponse.model_validate(notification)


def mark_all_notifications_read(db: Session, user_id: int) -> dict:
    count = notification_repository.mark_all_as_read(db, user_id)
    return {"message": f"{count} notification(s) marked as read."}


def get_unread_count(db: Session, user_id: int) -> UnreadCountResponse:
    count = notification_repository.get_unread_count(db, user_id)
    return UnreadCountResponse(unread_count=count)
