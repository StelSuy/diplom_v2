from __future__ import annotations

import logging

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.crud import terminal as terminal_crud
from app.models.terminal import Terminal
from app.models.user import User

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_terminal(
    x_terminal_key: str | None = Header(default=None, alias="X-Terminal-Key"),
    db: Session = Depends(get_db),
) -> Terminal:
    if not x_terminal_key:
        raise HTTPException(status_code=401, detail="Missing X-Terminal-Key")

    term = terminal_crud.get_by_api_key(db, x_terminal_key)
    if not term:
        raise HTTPException(status_code=401, detail="Invalid terminal key")

    return term


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token."""
    logger.info(f"get_current_user called, creds: {creds is not None}")
    
    if not creds or creds.scheme.lower() != "bearer":
        logger.warning("Missing Bearer token in get_current_user")
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = creds.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except JWTError as e:
        logger.warning(f"Invalid token in get_current_user: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    if not username:
        logger.warning("Invalid token payload - no username")
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"User not found: {username}")
        raise HTTPException(status_code=401, detail="User not found")

    logger.info(f"User authenticated: {username}")
    return user


def require_admin(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    logger.info(f"require_admin called, creds: {creds is not None}")
    
    if not creds or creds.scheme.lower() != "bearer":
        logger.warning("Missing Bearer token in require_admin")
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = creds.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        logger.info(f"Token decoded, sub={payload.get('sub')}, role={payload.get('role')}")
    except JWTError as e:
        logger.warning(f"Invalid token in require_admin: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    sub = payload.get("sub")
    role = payload.get("role")
    if sub != "admin" or role != "admin":
        logger.warning(f"Access denied - sub={sub}, role={role}")
        raise HTTPException(status_code=403, detail="Not allowed")

    logger.info("Admin access granted")
    return payload
