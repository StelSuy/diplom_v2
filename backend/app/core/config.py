from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]  # .../backend
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "TimeTracker API"
    env: str = "dev"
    debug: bool = True

    jwt_secret: str = "change_me"
    jwt_alg: str = "HS256"
    access_token_expire_minutes: int = 60

    # ОБОВʼЯЗКОВО
    database_url: str

    admin_username: str = "admin"
    admin_password: str = "admin123"

    terminal_scan_cooldown_seconds: int = 5


settings = Settings()
