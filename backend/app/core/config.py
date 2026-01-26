from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import validator

BASE_DIR = Path(__file__).resolve().parents[2]  # .../backend
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "TimeTracker API"
    env: str = "dev"
    debug: bool = True

    # JWT
    jwt_secret: str = "change_me"
    jwt_alg: str = "HS256"
    access_token_expire_minutes: int = 60

    # Database (ОБОВ'ЯЗКОВО)
    database_url: str
    
    # Database pool settings
    sql_echo: bool = False
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 1800

    # Admin (используется только для seed, не для аутентификации)
    admin_username: str = "admin"
    admin_password: str = "admin123"

    # Terminal
    terminal_scan_cooldown_seconds: int = 5
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    @validator('cors_origins', pre=True)
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v


settings = Settings()
