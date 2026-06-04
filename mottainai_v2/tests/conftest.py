"""
Pytest configuration and shared fixtures.

Uses an in-memory SQLite database for fast, isolated tests —
no external PostgreSQL required for the unit/integration test suite.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.core.config import get_settings, Settings

# ── Test database (SQLite in-memory) ─────────────────────────────────────────
TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_settings():
    return Settings(
        database_url=TEST_DATABASE_URL,
        secret_key="test-secret-key-at-least-32-characters-long",
        algorithm="HS256",
        access_token_expire_minutes=60,
        app_env="development",
        debug=False,
        allowed_origins="http://localhost:3000",
    )


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables once per test session."""
    import app.models  # ensure models are registered
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db():
    """Provide a clean database session per test, rolled back after."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db):
    """
    FastAPI TestClient with DB and settings overrides applied.
    Each test gets a fresh client backed by a rolled-back DB transaction.
    """
    from main import create_app
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db
    application.dependency_overrides[get_settings] = override_get_settings
    with TestClient(application, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture()
def registered_user(client):
    """Create and return a registered test user."""
    resp = client.post("/api/v1/auth/register", json={
        "full_name": "Test User",
        "email": "test@example.com",
        "password": "TestPass1",
    })
    assert resp.status_code == 201
    return resp.json()["data"]


@pytest.fixture()
def auth_client(client, registered_user):
    """TestClient that is already logged in."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "TestPass1",
    })
    assert resp.status_code == 200
    return client
