"""
Application configuration — loaded from environment variables / .env file.
"""
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]   # project root
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """All application settings. Values are loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = "TimeTracker API"
    app_version: str = "1.0.0"
    env: str = "production"
    debug: bool = False

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 1800   # seconds — prevents stale connections
    db_pool_pre_ping: bool = True  # validate connection before use
    sql_echo: bool = False

    # ── Security ─────────────────────────────────────────────────────────────
    jwt_secret: str
    jwt_alg: str = "HS256"
    access_token_expire_minutes: int = 60

    # ── Admin ─────────────────────────────────────────────────────────────────
    admin_username: str = "admin"
    admin_password: str = "change_me_in_production"

    # ── Terminal ─────────────────────────────────────────────────────────────
    terminal_scan_cooldown_seconds: int = 5

    # ── CORS ─────────────────────────────────────────────────────────────────
    # "*" allows all origins — fine for dev, restrict in production
    allowed_origins: str = "*"

    # ── Gunicorn (used in CMD via shell env, not by Python directly) ──────────
    gunicorn_workers: int = 2
    gunicorn_timeout: int = 120

    # ── Logging ──────────────────────────────────────────────────────────────
    log_level: str = "INFO"

    # ── Validators ───────────────────────────────────────────────────────────
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("DATABASE_URL is required")
        return v.strip()

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if not v or len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v

    @field_validator("admin_password")
    @classmethod
    def validate_admin_password(cls, v: str, info) -> str:
        env = info.data.get("env", "production")
        if env == "production" and v in ("admin", "change_me", "change_me_in_production", "password"):
            raise ValueError(
                "ADMIN_PASSWORD must be changed from the default value in production"
            )
        return v

    # ── Properties ───────────────────────────────────────────────────────────
    @property
    def cors_origins(self) -> List[str]:
        if self.allowed_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.env.lower() in ("development", "dev")

    @property
    def db_connect_args(self) -> dict:
        """Extra connection args depending on DB driver."""
        if "sqlite" in self.database_url:
            return {"check_same_thread": False}
        return {}


settings = Settings()
