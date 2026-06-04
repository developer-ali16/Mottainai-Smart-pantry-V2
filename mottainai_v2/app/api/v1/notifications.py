"""
Notifications API endpoints.
All routes are versioned under /api/v1/notifications.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user_id
from app.db.session import get_db
from app.schemas.base import PaginatedResponse, SuccessResponse
from app.schemas.notification import NotificationResponse, UnreadCountResponse
from app.services import notification_service
import math

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "/unread-count",
    response_model=SuccessResponse[UnreadCountResponse],
    summary="Get the count of unread notifications",
)
def get_unread_count(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    count = notification_service.get_unread_count(db, user_id)
    return SuccessResponse(data=count)


@router.get(
    "/",
    response_model=PaginatedResponse[NotificationResponse],
    summary="List notifications with optional unread filter",
)
def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False, description="Show only unread notifications"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    items, total = notification_service.list_notifications(
        db, user_id, page=page, page_size=page_size, unread_only=unread_only
    )
    return PaginatedResponse(
        data=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.patch(
    "/read-all",
    summary="Mark all notifications as read",
)
def mark_all_read(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return notification_service.mark_all_notifications_read(db, user_id)


@router.patch(
    "/{notification_id}/read",
    response_model=SuccessResponse[NotificationResponse],
    summary="Mark a single notification as read",
)
def mark_notification_read(
    notification_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    notification = notification_service.mark_notification_read(
        db, notification_id, user_id
    )
    return SuccessResponse(data=notification, message="Notification marked as read.")
