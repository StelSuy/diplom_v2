from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import jwt
import bcrypt

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash password using bcrypt directly (passlib has compatibility issues with bcrypt 4.1+)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(subject: str, expires_minutes: Optional[int] = None, extra: Optional[dict[str, Any]] = None) -> str:
    minutes = expires_minutes if expires_minutes is not None else settings.access_token_expire_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)
