from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, Token

router = APIRouter()


@router.post("/login", response_model=Token)
def login(payload: LoginRequest):
    if payload.username != settings.admin_username or payload.password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(subject="admin", extra={"role": "admin"})
    return Token(access_token=token)
