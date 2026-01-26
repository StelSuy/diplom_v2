# app/core/config.py
from pathlib import Path
from typing import List, Optional
from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]  # .../backend


class Settings(BaseSettings):
    """
    Production-ready конфігурація з підтримкою:
    - Системних ENV-змінних (без .env файлу)
    - Автоматична збірка DATABASE_URL з компонентів
    - Безпечні дефолти для production
    - Підтримка VPS / Render / Railway
    """
    
    model_config = SettingsConfigDict(
        # .env ОПЦІОНАЛЬНО - працює без нього
        env_file=str(BASE_DIR / ".env") if (BASE_DIR / ".env").exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==================== APPLICATION ====================
    app_name: str = Field(default="TimeTracker API", alias="APP_NAME")
    app_env: str = Field(default="production", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    
    @computed_field
    @property
    def debug(self) -> bool:
        """Backward compatibility: debug -> app_debug"""
        return self.app_debug
    
    @computed_field
    @property
    def env(self) -> str:
        """Backward compatibility: env -> app_env"""
        return self.app_env

    # ==================== DATABASE ====================
    # Опція 1: Повний DATABASE_URL (пріоритет)
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    
    # Опція 2: Компоненти (автоматична збірка)
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=3306, alias="DB_PORT")
    db_name: str = Field(default="timetracker", alias="DB_NAME")
    db_user: str = Field(default="root", alias="DB_USER")
    db_password: str = Field(default="", alias="DB_PASSWORD")
    db_driver: str = Field(default="pymysql", alias="DB_DRIVER")  # pymysql, mysqldb, postgresql
    
    @computed_field
    @property
    def computed_database_url(self) -> str:
        """
        Автоматична збірка DATABASE_URL якщо не передано явно.
        Пріоритет: DATABASE_URL > компоненти (DB_HOST, DB_PORT, etc)
        """
        if self.database_url:
            return self.database_url
        
        # Збираємо з компонентів
        if self.db_driver == "pymysql":
            protocol = "mysql+pymysql"
        elif self.db_driver == "mysqldb":
            protocol = "mysql+mysqldb"
        elif self.db_driver == "postgresql":
            protocol = "postgresql+psycopg2"
        else:
            protocol = f"mysql+{self.db_driver}"
        
        return f"{protocol}://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
    
    # Database pool settings
    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    db_pool_recycle: int = Field(default=1800, alias="DB_POOL_RECYCLE")
    
    @computed_field
    @property
    def sql_echo(self) -> bool:
        """SQL echo тільки в debug режимі"""
        return self.app_debug

    # ==================== SECURITY ====================
    # JWT - ОБОВ'ЯЗКОВО в production
    jwt_secret: str = Field(..., min_length=32, alias="JWT_SECRET")
    jwt_alg: str = Field(default="HS256", alias="JWT_ALG")
    access_token_expire_minutes: int = Field(default=1440, alias="ACCESS_TOKEN_EXPIRE_MINUTES")  # 24 години

    # Admin credentials (тільки для seed/bootstrap)
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="", alias="ADMIN_PASSWORD")  # ОБОВ'ЯЗКОВО в production
    
    @field_validator('admin_password')
    @classmethod
    def validate_admin_password(cls, v: str, info) -> str:
        """В production admin_password обов'язковий"""
        app_env = info.data.get('app_env', 'production')
        if app_env == 'production' and not v:
            raise ValueError(
                "ADMIN_PASSWORD is required in production. "
                "Set it via environment variable."
            )
        return v

    # ==================== TERMINAL ====================
    terminal_scan_cooldown_seconds: int = Field(default=5, alias="TERMINAL_SCAN_COOLDOWN_SECONDS")

    # ==================== CORS ====================
    cors_origins: List[str] = Field(
        default_factory=lambda: [],  # Порожній список в production
        alias="CORS_ORIGINS"
    )
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Парсинг CORS з строки або списку"""
        if v is None:
            return []
        if isinstance(v, str):
            if v.strip() == "":
                return []
            # Підтримка "*" для wildcard
            if v.strip() == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    @field_validator('cors_origins', mode='after')
    @classmethod
    def validate_cors_production(cls, v: List[str], info) -> List[str]:
        """Попередження про небезпечний CORS в production"""
        app_env = info.data.get('app_env', 'production')
        if app_env == 'production' and '*' in v:
            import warnings
            warnings.warn(
                "CORS_ORIGINS='*' is insecure in production. "
                "Specify exact domains instead.",
                RuntimeWarning
            )
        return v

    # ==================== SERVER ====================
    server_host: str = Field(default="0.0.0.0", alias="SERVER_HOST")
    server_port: int = Field(default=8000, alias="SERVER_PORT")
    server_workers: int = Field(default=1, alias="SERVER_WORKERS")  # Для Gunicorn
    
    # ==================== LOGGING ====================
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    @computed_field
    @property
    def computed_log_level(self) -> str:
        """Автоматичний log level: DEBUG якщо app_debug, інакше LOG_LEVEL"""
        if self.app_debug:
            return "DEBUG"
        return self.log_level.upper()


# ==================== SINGLETON ====================
settings = Settings()

# ==================== PRODUCTION VALIDATION ====================
def validate_production_settings():
    """Валідація критичних налаштувань для production"""
    errors = []
    
    if settings.app_env == "production":
        # Перевірка JWT_SECRET
        if settings.jwt_secret == "change_me" or len(settings.jwt_secret) < 32:
            errors.append("JWT_SECRET must be at least 32 characters in production")
        
        # Перевірка DEBUG
        if settings.app_debug:
            errors.append("APP_DEBUG=true is dangerous in production")
        
        # Перевірка ADMIN_PASSWORD
        if not settings.admin_password or settings.admin_password == "admin123":
            errors.append("ADMIN_PASSWORD must be set and strong in production")
        
        # Перевірка DATABASE
        if not settings.computed_database_url:
            errors.append("Database configuration is missing")
    
    if errors:
        error_msg = "\n".join([f"  ❌ {err}" for err in errors])
        raise ValueError(
            f"\n{'='*60}\n"
            f"PRODUCTION CONFIGURATION ERRORS:\n"
            f"{error_msg}\n"
            f"{'='*60}\n"
        )

# Валідація при імпорті (тільки в production)
if settings.app_env == "production":
    validate_production_settings()
