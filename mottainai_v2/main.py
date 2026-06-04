"""
Mottainai Smart Pantry — Application Entry Point
=================================================
Uses an application factory pattern for testability:
  - create_app() builds and returns the configured FastAPI instance.
  - The module-level `app` variable is what Uvicorn/Gunicorn binds to.

Starting the server:
    uvicorn main:app --reload                    # development
    gunicorn main:app -k uvicorn.workers.UvicornWorker -w 4  # production
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure all models are imported before create_tables is called
import app.models  # noqa: F401

from app.api.v1 import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.db.session import create_tables
from app.middleware.middleware import register_middleware
from app.scheduler.expiry_scheduler import start_scheduler, stop_scheduler

logger = get_logger("app")


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(application: FastAPI):
    """
    Application lifespan handler.
    Replaces the deprecated @app.on_event("startup") / "shutdown" pattern.
    """
    # ── Startup ─────────────────────────────────────────────
    setup_logging()
    logger.info("Starting %s v%s [%s]", settings.app_name, settings.app_version, settings.app_env)

    # Create tables if they don't exist (dev / first-run convenience)
    # In production, this is handled by Alembic migrations.
    create_tables()
    logger.info("Database tables verified.")

    # Start background scheduler
    start_scheduler()

    yield   # Application is running

    # ── Shutdown ─────────────────────────────────────────────
    stop_scheduler()
    logger.info("Application shutdown complete.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    """
    Build and return the configured FastAPI application.
    Separating this into a factory function allows tests to create
    fresh app instances without side effects.
    """
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "**Mottainai Smart Pantry API** — inspired by the Japanese concept of "
            "avoiding waste. Track your pantry, get expiry reminders, and reduce food waste."
        ),
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    )

    # ── Custom middleware (logging, security headers) ──────
    register_middleware(application)

    # ── Exception handlers ────────────────────────────────
    register_exception_handlers(application)

    # ── Routers ───────────────────────────────────────────
    application.include_router(api_router)

    return application


# ---------------------------------------------------------------------------
# Module-level app instance (Uvicorn / Gunicorn target)
# ---------------------------------------------------------------------------

app = create_app()
