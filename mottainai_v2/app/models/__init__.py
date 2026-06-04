"""
Import all models here so that:
  1. Alembic's autogenerate can discover all tables.
  2. SQLAlchemy's relationship() resolution works correctly.
"""
from app.models.user import User
from app.models.pantry_item import PantryItem
from app.models.notification import Notification

__all__ = ["User", "PantryItem", "Notification"]
