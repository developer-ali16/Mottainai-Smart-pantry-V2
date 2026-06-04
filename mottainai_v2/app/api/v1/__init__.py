"""
API v1 router.
All sub-routers are registered here and included in the main app
under the /api/v1 prefix.
"""
from fastapi import APIRouter

from app.api.v1 import auth, health, notifications, pantry

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(pantry.router)
api_router.include_router(notifications.router)
