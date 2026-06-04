"""
Application configuration using Pydantic BaseSettings.
All settings are type-validated, documented, and loaded from environment variables.
"""
from functools import lru_cache
from typing import List

from pydantic import EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────
    app_name: str = "Mottainai Smart Pantry"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = False

    # ── Database ─────────────────────────────────────────────
    database_url: str

    # ── Security ─────────────────────────────────────────────
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # ── CORS ─────────────────────────────────────────────────
    allowed_origins: str = "http://localhost:3000,http://localhost:8080"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    # ── Email ─────────────────────────────────────────────────
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = ""
    mail_port: int = 587
    mail_server: str = "smtp.gmail.com"

    @property
    def email_configured(self) -> bool:
        return bool(self.mail_username and self.mail_password and self.mail_from)

    # ── Rate Limiting ─────────────────────────────────────────
    rate_limit_per_minute: int = 60
    auth_rate_limit_per_minute: int = 10

    # ── Scheduler ────────────────────────────────────────────
    expiry_check_days_ahead: int = 3  # warn N days before expiry

    # ── Validators ───────────────────────────────────────────
    @field_validator("secret_key")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("app_env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v.lower() not in allowed:
            raise ValueError(f"APP_ENV must be one of: {allowed}")
        return v.lower()

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance. Use this everywhere via Depends(get_settings).
    The lru_cache ensures settings are loaded only once per process.
    """
    return Settings()


# Module-level singleton for non-DI contexts (e.g. Alembic env.py)
settings = get_settings()
