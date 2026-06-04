"""PantryItem-related Pydantic schemas."""
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import Field, field_validator, model_validator

from app.schemas.base import OrmModel

# Allowed unit values
VALID_UNITS = Literal[
    "kg", "gram", "liter", "ml", "pieces",
    "packets", "cups", "bottles", "boxes",
    "cans", "jars", "dozen",
]

# Allowed category values (optional but validated when provided)
VALID_CATEGORIES = Literal[
    "produce", "dairy", "meat", "seafood",
    "grains", "bakery", "beverages", "condiments",
    "frozen", "canned", "snacks", "spices", "other",
]


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class PantryItemCreate(OrmModel):
    item_name: str = Field(..., min_length=1, max_length=100)
    quantity: float = Field(..., gt=0, description="Must be greater than zero")
    unit: VALID_UNITS
    category: Optional[VALID_CATEGORIES] = None
    expiry_date: date
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("item_name")
    @classmethod
    def clean_item_name(cls, v: str) -> str:
        return " ".join(v.strip().split()).lower()

    @model_validator(mode="after")
    def expiry_date_not_in_past(self) -> "PantryItemCreate":
        if self.expiry_date < date.today():
            raise ValueError("Expiry date cannot be in the past.")
        return self


# ---------------------------------------------------------------------------
# Update (all fields optional — PATCH semantics on a PUT endpoint)
# ---------------------------------------------------------------------------

class PantryItemUpdate(OrmModel):
    item_name: Optional[str] = Field(None, min_length=1, max_length=100)
    quantity: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = Field(None, min_length=1, max_length=30)
    category: Optional[str] = Field(None, max_length=50)
    expiry_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("item_name")
    @classmethod
    def clean_item_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return " ".join(v.strip().split()).lower()
        return v


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class PantryItemResponse(OrmModel):
    id: int
    user_id: int
    item_name: str
    quantity: float
    unit: str
    category: Optional[str]
    expiry_date: date
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    @property
    def days_until_expiry(self) -> int:
        return (self.expiry_date - date.today()).days


# ---------------------------------------------------------------------------
# Summary (for the dashboard / heatmap endpoint)
# ---------------------------------------------------------------------------

class PantrySummary(OrmModel):
    total_items: int
    expired: int
    expiring_today: int
    expiring_in_3_days: int
    expiring_in_7_days: int
    expiring_in_30_days: int
    safe: int
