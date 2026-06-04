"""PantryItem database model."""
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class PantryItem(Base):
    __tablename__ = "pantry_items"

    # Table-level indexes for the most common query patterns
    __table_args__ = (
        # Scheduler queries: "give me all items expiring on date X"
        Index("ix_pantry_items_user_expiry", "user_id", "expiry_date"),
        # List queries: "give me all items for user Y"
        Index("ix_pantry_items_user_id", "user_id"),
    )

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Item details
    item_name = Column(String(100), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False)
    category = Column(String(50), nullable=True)   # produce, dairy, grains, etc.
    notes = Column(Text, nullable=True)            # optional user notes

    # Expiry
    expiry_date = Column(Date, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="pantry_items")
    notifications = relationship(
        "Notification", back_populates="pantry_item", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PantryItem id={self.id} name={self.item_name!r} expires={self.expiry_date}>"
