"""
API endpoints для управління користувачами (адміністраторами)
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User, UserRole
from app.core.security import hash_password
from app.api.dependencies import require_admin, get_current_user
from app.security.audit import audit_log
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6)
    role: str = Field(default=UserRole.EMPLOYEE.value)


class UserUpdate(BaseModel):
    password: str | None = Field(None, min_length=6)
    role: str | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Список всіх користувачів (тільки для адмінів)"""
    users = db.query(User).all()
    return users


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Створення нового користувача (тільки для адмінів)"""
    
    # Перевірка чи username вже існує
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with username '{user_data.username}' already exists"
        )
    
    # Валідація ролі
    valid_roles = [r.value for r in UserRole]
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Allowed: {', '.join(valid_roles)}"
        )
    
    # Створення користувача
    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role=user_data.role
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    audit_log("user_create", current_user["username"], {
        "user_id": user.id,
        "username": user.username,
        "role": user.role
    })
    
    logger.info(f"User created: {user.username} (role: {user.role})")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Оновлення користувача (тільки для адмінів)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    changes = {}
    
    if user_data.password:
        user.password_hash = hash_password(user_data.password)
        changes["password"] = "changed"
    
    if user_data.role:
        valid_roles = [r.value for r in UserRole]
        if user_data.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Allowed: {', '.join(valid_roles)}"
            )
        user.role = user_data.role
        changes["role"] = user_data.role
    
    db.commit()
    db.refresh(user)
    
    audit_log("user_update", current_user["username"], {
        "user_id": user.id,
        "username": user.username,
        "changes": changes
    })
    
    logger.info(f"User updated: {user.username} - {changes}")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Видалення користувача (тільки для адмінів)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    # Не дозволяємо видаляти самого себе
    if user.username == current_user["username"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    username = user.username
    db.delete(user)
    db.commit()
    
    audit_log("user_delete", current_user["username"], {
        "user_id": user_id,
        "username": username
    })
    
    logger.info(f"User deleted: {username}")
    return None


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Інформація про поточного користувача"""
    return {
        "id": current_user.get("user_id", 0),
        "username": current_user["username"],
        "role": current_user["role"]
    }
