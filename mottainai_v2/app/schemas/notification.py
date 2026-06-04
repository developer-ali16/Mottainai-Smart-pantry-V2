"""Notification-related Pydantic schemas."""
from datetime import datetime

from app.schemas.base import OrmModel


class NotificationResponse(OrmModel):
    id: int
    user_id: int
    pantry_item_id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime


class UnreadCountResponse(OrmModel):
    unread_count: int
