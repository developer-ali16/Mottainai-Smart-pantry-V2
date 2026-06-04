"""
Pantry service.
Business logic for pantry item management.
"""
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.logging import get_logger
from app.models.pantry_item import PantryItem
from app.repositories import pantry_repository
from app.schemas.pantry_item import (
    PantryItemCreate,
    PantryItemResponse,
    PantryItemUpdate,
    PantrySummary,
)

logger = get_logger("pantry_service")


def create_item(
    db: Session, user_id: int, payload: PantryItemCreate
) -> PantryItemResponse:
    item = pantry_repository.create_pantry_item(db, user_id, payload)
    logger.info("Pantry item created: item_id=%d user_id=%d", item.id, user_id)
    return PantryItemResponse.model_validate(item)


def get_item(db: Session, item_id: int, user_id: int) -> PantryItemResponse:
    item = pantry_repository.get_pantry_item(db, item_id, user_id)
    if not item:
        raise NotFoundException("Pantry item")
    return PantryItemResponse.model_validate(item)


def list_items(
    db: Session,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    expiring_soon: Optional[int] = None,
    search: Optional[str] = None,
) -> Tuple[List[PantryItemResponse], int]:
    skip = (page - 1) * page_size
    items, total = pantry_repository.get_all_pantry_items(
        db, user_id,
        skip=skip,
        limit=page_size,
        category=category,
        expiring_soon=expiring_soon,
        search=search,
    )
    return [PantryItemResponse.model_validate(i) for i in items], total


def update_item(
    db: Session, item_id: int, user_id: int, payload: PantryItemUpdate
) -> PantryItemResponse:
    item = pantry_repository.get_pantry_item(db, item_id, user_id)
    if not item:
        raise NotFoundException("Pantry item")
    item = pantry_repository.update_pantry_item(db, item, payload)
    logger.info("Pantry item updated: item_id=%d user_id=%d", item_id, user_id)
    return PantryItemResponse.model_validate(item)


def delete_item(db: Session, item_id: int, user_id: int) -> None:
    item = pantry_repository.get_pantry_item(db, item_id, user_id)
    if not item:
        raise NotFoundException("Pantry item")
    pantry_repository.delete_pantry_item(db, item)
    logger.info("Pantry item deleted: item_id=%d user_id=%d", item_id, user_id)


def get_summary(db: Session, user_id: int) -> PantrySummary:
    return pantry_repository.get_pantry_summary(db, user_id)
