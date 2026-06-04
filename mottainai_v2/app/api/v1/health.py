"""
Health check endpoints.
Used by load balancers, Docker health checks, and Kubernetes probes.
"""
from fastapi import APIRouter
from app.core.config import settings
from app.db.session import check_db_connection

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Liveness probe — is the server running?")
def health_check():
    """Returns 200 if the application is running."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }


@router.get("/health/ready", summary="Readiness probe — is the database reachable?")
def readiness_check():
    """Returns 200 if the application and database are ready to serve traffic."""
    db_ok = check_db_connection()
    return {
        "status": "ready" if db_ok else "not_ready",
        "database": "connected" if db_ok else "unreachable",
    }
