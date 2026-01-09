from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "TimeTracker API"
    env: str = "dev"
    debug: bool = True

    jwt_secret: str = "change_me"
    jwt_alg: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str = "sqlite:///./app.db"

    admin_username: str = "admin"
    admin_password: str = "admin123"


settings = Settings()
