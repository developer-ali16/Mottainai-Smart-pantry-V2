"""Notification database model."""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Notification(Base):
    __tablename__ = "notifications"

    __table_args__ = (
        # Fast unread-count queries per user
        Index("ix_notifications_user_read", "user_id", "is_read"),
    )

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pantry_item_id = Column(
        Integer, ForeignKey("pantry_items.id", ondelete="CASCADE"), nullable=False
    )

    # Content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False, default="expiry_reminder")

    # State
    is_read = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="notifications")
    pantry_item = relationship("PantryItem", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user_id={self.user_id} read={self.is_read}>"
