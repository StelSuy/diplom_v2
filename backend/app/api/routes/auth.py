import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.schemas.auth import LoginRequest, Token
from app.security.audit import audit_log
from app.security.rate_limit import check_rate_limit
from app.db.session import get_db
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter()


# БАГ №3 ВИПРАВЛЕНО: глобальний кеш пароля перенесено в settings через init_admin_hash()
# Хеш обчислюється один раз при старті застосунку (main.py on_startup),
# а не в кожному воркері окремо при першому запиті.
def _get_admin_hash() -> str:
    """Повертає хеш з settings, обчислений один раз при старті в main.py."""
    h = getattr(settings, "_admin_password_hash", None)
    if not h:
        raise RuntimeError("Admin password hash not initialized. Call init_admin_hash() on startup.")
    return h


def init_admin_hash() -> None:
    """
    Хешує пароль адміна і зберігає в settings — викликати один раз при старті.
    bcrypt.hashpw швидкий при старті, але повільний при кожному login-запиті.
    """
    from app.core.security import hash_password
    settings._admin_password_hash = hash_password(settings.admin_password)
    logger.info("Адмін-пароль захешовано (bcrypt)")


# БАГ №4 ВИПРАВЛЕНО: додано Depends(check_rate_limit) — захист від brute-force
@router.post("/login", response_model=Token, dependencies=[Depends(check_rate_limit)])
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Автентифікація користувача. Rate-limited: макс. 120 запитів/хвилину з IP."""
    
    # Спочатку перевіряємо БД
    user = db.query(User).filter(User.username == payload.username).first()
    
    if user:
        # Користувач знайдений в БД
        is_valid_pass = verify_password(payload.password, user.password_hash)
        
        if not is_valid_pass:
            logger.warning(
                f"Failed login attempt from {request.client.host if request.client else 'unknown'} for user {payload.username}"
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Успішна авторизація
        token = create_access_token(
            subject=user.username,
            extra={"role": user.role, "user_id": user.id}
        )
        audit_log("admin_login", user.username, details={"role": user.role})
        return Token(access_token=token)
    
    else:
        # Fallback на старого адміна зі змінних оточення (для зворотної сумісності)
        is_valid_user = payload.username == settings.admin_username
        is_valid_pass = verify_password(payload.password, _get_admin_hash())

        if not is_valid_user or not is_valid_pass:
            logger.warning(
                f"Failed login attempt from {request.client.host if request.client else 'unknown'}"
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token(subject="admin", extra={"role": "admin"})
        audit_log("admin_login", payload.username, details={"role": "admin"})
        return Token(access_token=token)
