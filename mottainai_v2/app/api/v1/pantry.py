"""
Pantry item API endpoints.
All routes are versioned under /api/v1/pantry.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user_id
from app.db.session import get_db
from app.schemas.base import PaginatedResponse, SuccessResponse
from app.schemas.pantry_item import (
    PantryItemCreate,
    PantryItemResponse,
    PantryItemUpdate,
    PantrySummary,
)
from app.services import pantry_service
import math

router = APIRouter(prefix="/pantry", tags=["Pantry"])


@router.post(
    "/",
    response_model=SuccessResponse[PantryItemResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add a new item to the pantry",
)
def create_pantry_item(
    payload: PantryItemCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    item = pantry_service.create_item(db, user_id, payload)
    return SuccessResponse(data=item, message="Pantry item added.")


@router.get(
    "/summary",
    response_model=SuccessResponse[PantrySummary],
    summary="Get expiry heatmap summary for the current user's pantry",
)
def get_pantry_summary(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    summary = pantry_service.get_summary(db, user_id)
    return SuccessResponse(data=summary)


@router.get(
    "/",
    response_model=PaginatedResponse[PantryItemResponse],
    summary="List all pantry items with pagination and filtering",
)
def list_pantry_items(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    expiring_soon: Optional[int] = Query(
        default=None, ge=1, le=365, description="Show items expiring within N days"
    ),
    search: Optional[str] = Query(default=None, description="Search by item name"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    items, total = pantry_service.list_items(
        db, user_id,
        page=page,
        page_size=page_size,
        category=category,
        expiring_soon=expiring_soon,
        search=search,
    )
    return PaginatedResponse(
        data=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.get(
    "/{item_id}",
    response_model=SuccessResponse[PantryItemResponse],
    summary="Get a single pantry item by ID",
)
def get_pantry_item(
    item_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    item = pantry_service.get_item(db, item_id, user_id)
    return SuccessResponse(data=item)


@router.put(
    "/{item_id}",
    response_model=SuccessResponse[PantryItemResponse],
    summary="Update a pantry item (partial update — only provided fields are changed)",
)
def update_pantry_item(
    item_id: int,
    payload: PantryItemUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    item = pantry_service.update_item(db, item_id, user_id, payload)
    return SuccessResponse(data=item, message="Pantry item updated.")


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a pantry item",
)
def delete_pantry_item(
    item_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    pantry_service.delete_item(db, item_id, user_id)
    # 204 No Content — no response body
