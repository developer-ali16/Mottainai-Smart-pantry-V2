"""
Shared Pydantic base classes and response envelope.
"""
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

DataT = TypeVar("DataT")


class OrmModel(BaseModel):
    """Base class for schemas that are built from SQLAlchemy ORM objects."""
    model_config = ConfigDict(from_attributes=True)


class SuccessResponse(BaseModel, Generic[DataT]):
    """
    Standard success envelope used by all endpoints.

    Example:
        {"success": true, "data": {...}, "message": "User created."}
    """
    success: bool = True
    data: Optional[DataT] = None
    message: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Standard paginated list response."""
    success: bool = True
    data: list[DataT]
    total: int
    page: int
    page_size: int
    total_pages: int
