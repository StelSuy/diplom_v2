from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.crud import terminal as terminal_crud
from app.models.terminal import Terminal

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


def require_admin(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = creds.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    sub = payload.get("sub")
    role = payload.get("role")
    if sub != "admin" or role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")

    return payload
