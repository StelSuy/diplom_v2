"""
Application configuration management.
"""
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root directory
BASE_DIR = Path(__file__).resolve().parents[2]  # backend/
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "TimeTracker API"
    env: str = "development"
    debug: bool = True

    # Database
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 1800
    sql_echo: bool = False

    # Security
    jwt_secret: str
    jwt_alg: str = "HS256"
    access_token_expire_minutes: int = 60

    # Admin
    admin_username: str = "admin"
    admin_password: str

    # Terminal
    terminal_scan_cooldown_seconds: int = 5

    # CORS
    allowed_origins: str = "*"

    # Logging
    log_level: str = "INFO"

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate and clean database URL."""
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v.strip()

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Ensure JWT secret is sufficiently strong."""
        if not v or len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.env.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.env.lower() in ("development", "dev")


# Global settings instance
settings = Settings()
