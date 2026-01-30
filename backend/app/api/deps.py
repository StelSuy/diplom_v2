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
        logger.warning(f"Invalid terminal key: {x_terminal_key[:8]}...")
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
    
    Args:
        credentials: Bearer token from Authorization header
        db: Database session
        
    Returns:
        Authenticated User instance
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        logger.warning("Missing or invalid Bearer token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_alg],
        )
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
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
        logger.warning(f"User not found: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    logger.debug(f"User authenticated: {username}")
    return user


def require_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    """
    Dependency to require admin role.
    
    Args:
        credentials: Bearer token from Authorization header
        
    Returns:
        JWT payload dict
        
    Raises:
        HTTPException: If not admin or authentication fails
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        logger.warning("Admin endpoint: Missing Bearer token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_alg],
        )
    except JWTError as e:
        logger.warning(f"Admin endpoint: JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    role = payload.get("role")
    
    # Check admin privileges
    if username != settings.admin_username or role != "admin":
        logger.warning(f"Access denied to admin endpoint: user={username}, role={role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges",
        )
    
    logger.debug(f"Admin access granted: {username}")
    return payload


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Dependency to optionally authenticate user.
    Returns None if no valid token provided.
    
    Args:
        credentials: Bearer token from Authorization header
        db: Database session
        
    Returns:
        User instance or None
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        return None
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_alg],
        )
        username = payload.get("sub")
        if username:
            return db.query(User).filter(User.username == username).first()
    except JWTError:
        pass
    
    return None
