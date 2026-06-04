"""
PantryItem repository.
All database interactions for the PantryItem model.
"""
from datetime import date, timedelta
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.pantry_item import PantryItem
from app.schemas.pantry_item import PantryItemCreate, PantryItemUpdate, PantrySummary


def create_pantry_item(
    db: Session, user_id: int, item_data: PantryItemCreate
) -> PantryItem:
    item = PantryItem(
        user_id=user_id,
        item_name=item_data.item_name,
        quantity=item_data.quantity,
        unit=item_data.unit,
        category=item_data.category,
        expiry_date=item_data.expiry_date,
        notes=item_data.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_pantry_item(db: Session, item_id: int, user_id: int) -> Optional[PantryItem]:
    """Fetch a single item scoped to the owning user."""
    return (
        db.query(PantryItem)
        .filter(PantryItem.id == item_id, PantryItem.user_id == user_id)
        .first()
    )


def get_all_pantry_items(
    db: Session,
    user_id: int,
    *,
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    expiring_soon: Optional[int] = None,   # days ahead, e.g. 3
    search: Optional[str] = None,
) -> Tuple[List[PantryItem], int]:
    """
    Return (items, total_count) for the given user with optional filters.

    Parameters
    ----------
    skip            Pagination offset.
    limit           Page size (max 100).
    category        Filter by category string.
    expiring_soon   If provided, return only items expiring within this many days.
    search          Case-insensitive substring match on item_name.
    """
    limit = min(limit, 100)  # hard cap

    query = db.query(PantryItem).filter(PantryItem.user_id == user_id)

    if category:
        query = query.filter(PantryItem.category == category.lower())

    if expiring_soon is not None:
        today = date.today()
        cutoff = today + timedelta(days=expiring_soon)
        query = query.filter(
            PantryItem.expiry_date >= today,
            PantryItem.expiry_date <= cutoff,
        )

    if search:
        query = query.filter(PantryItem.item_name.ilike(f"%{search.lower()}%"))

    total = query.count()
    items = (
        query.order_by(PantryItem.expiry_date.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items, total


def update_pantry_item(
    db: Session, item: PantryItem, update_data: PantryItemUpdate
) -> PantryItem:
    """Apply partial update — only fields explicitly provided are changed."""
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_pantry_item(db: Session, item: PantryItem) -> None:
    db.delete(item)
    db.commit()


def get_expiring_items(
    db: Session, target_date: date
) -> List[PantryItem]:
    """
    Return all items across all users expiring exactly on *target_date*.
    Used by the background scheduler.
    """
    return (
        db.query(PantryItem)
        .filter(PantryItem.expiry_date == target_date)
        .all()
    )


def get_pantry_summary(db: Session, user_id: int) -> PantrySummary:
    """
    Return expiry heatmap counts for the user's pantry.
    Enables a dashboard overview without fetching all items.
    """
    today = date.today()
    items = db.query(PantryItem).filter(PantryItem.user_id == user_id).all()

    expired = sum(1 for i in items if i.expiry_date < today)
    expiring_today = sum(1 for i in items if i.expiry_date == today)
    in_3 = sum(1 for i in items if today < i.expiry_date <= today + timedelta(days=3))
    in_7 = sum(1 for i in items if today + timedelta(days=3) < i.expiry_date <= today + timedelta(days=7))
    in_30 = sum(1 for i in items if today + timedelta(days=7) < i.expiry_date <= today + timedelta(days=30))
    safe = sum(1 for i in items if i.expiry_date > today + timedelta(days=30))

    return PantrySummary(
        total_items=len(items),
        expired=expired,
        expiring_today=expiring_today,
        expiring_in_3_days=in_3,
        expiring_in_7_days=in_7,
        expiring_in_30_days=in_30,
        safe=safe,
    )
