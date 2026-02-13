"""
FastAPI dependencies for authentication and authorization.
"""
import logging
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import terminal as terminal_crud
from app.db.session import get_db
from app.models.terminal import Terminal
from app.models.user import User

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)


def _decode_jwt_payload(
    credentials: Optional[HTTPAuthorizationCredentials],
    context: str = "endpoint",
) -> dict:
    """
    Shared helper: validates Bearer credentials and decodes JWT.
    Raises HTTPException on any failure.
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        logger.warning(f"{context}: Missing or invalid Bearer token")
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
    """
    Dependency to authenticate terminal requests via API key.
    
    Args:
        x_terminal_key: Terminal API key from X-Terminal-Key header
        db: Database session
        
    Returns:
        Authenticated Terminal instance
        
    Raises:
        HTTPException: If authentication fails
    """
    if not x_terminal_key:
        logger.warning("Terminal request missing X-Terminal-Key header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Terminal-Key header",
        )
    
    terminal = terminal_crud.get_by_api_key(db, x_terminal_key)
    if not terminal:
        # БАГ №5 ВИПРАВЛЕНО: не логуємо жодну частину секретного ключа
        logger.warning("Invalid terminal key attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid terminal key",
        )
    
    logger.debug(f"Terminal authenticated: {terminal.name}")
    return terminal


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to authenticate user requests via JWT token.
    Uses shared _decode_jwt_payload to avoid duplicating decode logic.
    """
    payload = _decode_jwt_payload(credentials, context="get_current_user")

    username: Optional[str] = payload.get("sub")
    if not username:
        logger.warning("Token missing 'sub' claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.warning("Authenticated user not found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    logger.debug(f"User authenticated: {username}")
    return user


def require_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    БАГ №1 ВИПРАВЛЕНО: require_admin тепер повертає User з БД.

    Раніше повертав dict (JWT payload) — це змушувало всі ендпоінти
    додатково викликати get_current_user(db), що давало два декодування
    JWT і два SQL-запити на кожен запит.

    Тепер: один decode + один SQL-запит. Всі ендпоінти отримують
    готовий User через require_admin, без потреби в get_current_user.
    """
    payload = _decode_jwt_payload(credentials, context="require_admin")

    username: Optional[str] = payload.get("sub")
    role: Optional[str] = payload.get("role")

    if not username or username != settings.admin_username or role != "admin":
        logger.warning(f"Access denied to admin endpoint: user={username}, role={role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges",
        )

    # Один запит до БД — повертаємо User напряму
    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"Admin user '{username}' not found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    logger.debug(f"Admin access granted: {username}")
    return user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Dependency to optionally authenticate user.
    Returns None if no valid token provided.
    Uses shared _decode_jwt_payload (catches exceptions internally).
    """
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
