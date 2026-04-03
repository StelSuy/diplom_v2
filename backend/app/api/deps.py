"""
FastAPI dependencies — authentication & authorization.
"""
import logging
from typing import Optional

from datetime import datetime, timezone
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import terminal as terminal_crud
from app.db.session import get_db
from app.models.terminal import Terminal
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)

# Ролі що мають доступ до адмін-ендпоінтів
ADMIN_ROLES = {UserRole.ADMIN.value, UserRole.MANAGER.value}


def _decode_jwt_payload(
    credentials: Optional[HTTPAuthorizationCredentials],
    context: str = "endpoint",
) -> dict:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_alg],
        )
    except JWTError as e:
        logger.warning(f"{context}: JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_terminal(
    x_terminal_key: Optional[str] = Header(None, alias="X-Terminal-Key"),
    db: Session = Depends(get_db),
) -> Terminal:
    if not x_terminal_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Terminal-Key header")

    terminal = terminal_crud.get_by_api_key(db, x_terminal_key)
    if not terminal:
        logger.warning("Invalid terminal key attempt")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid terminal key")

    try:
        terminal.last_seen_at = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        db.rollback()

    return terminal


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = _decode_jwt_payload(credentials, context="get_current_user")
    username: Optional[str] = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Дозволяє доступ будь-якому користувачу з роллю admin або manager.
    Повертає User з БД — один decode + один SQL запит.
    """
    payload = _decode_jwt_payload(credentials, context="require_admin")
    username: Optional[str] = payload.get("sub")

    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if user.role not in ADMIN_ROLES:
        logger.warning(f"Access denied: user={username}, role={user.role}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")

    return user


def require_role(*roles: str):
    """
    Фабрика dep-функцій для перевірки конкретних ролей.
    Використання: Depends(require_role("admin"))
    """
    def _dep(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
        db: Session = Depends(get_db),
    ) -> User:
        payload = _decode_jwt_payload(credentials, context="require_role")
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
        return user
    return _dep


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not credentials or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = _decode_jwt_payload(credentials, context="get_optional_user")
        username = payload.get("sub")
        if username:
            return db.query(User).filter(User.username == username).first()
    except HTTPException:
        pass
    return None
