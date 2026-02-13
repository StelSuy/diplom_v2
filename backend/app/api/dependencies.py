"""
Dependencies для перевірки прав доступу на основі ролей користувача
"""
from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.core.config import settings
from app.models import UserRole

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Отримує поточного користувача з JWT токена
    
    Returns:
        dict: {"username": str, "role": str, "user_id": int}
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        username = payload.get("sub")
        role = payload.get("role", UserRole.EMPLOYEE.value)
        user_id = payload.get("user_id")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        return {
            "username": username,
            "role": role,
            "user_id": user_id
        }
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


def require_role(allowed_roles: List[str]):
    """
    Dependency factory для перевірки ролі користувача
    
    Args:
        allowed_roles: Список дозволених ролей
    
    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(["admin"]))])
    """
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        
        return current_user
    
    return role_checker


# Готові dependencies для кожної ролі
require_admin = require_role([UserRole.ADMIN.value])
require_manager = require_role([UserRole.ADMIN.value, UserRole.MANAGER.value])
require_hr = require_role([UserRole.ADMIN.value, UserRole.HR.value, UserRole.MANAGER.value])
require_any_staff = require_role([UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.HR.value])
