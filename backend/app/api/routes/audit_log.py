"""
Audit log API — читання журналу дій адміністратора.
Доступно тільки авторизованому адміну.
"""
from fastapi import APIRouter, Depends, Query
from app.api.deps import require_admin
from app.models.user import User
from app.security.audit import get_audit_log, get_action_types

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/log")
def read_audit_log(
    limit: int = Query(default=100, ge=1, le=500),
    action: str | None = Query(default=None, description="Фільтр по типу дії"),
    _: User = Depends(require_admin),
):
    """
    Повертає останні записи журналу дій адміністратора.
    Зберігається в пам'яті — до 500 записів з моменту старту сервера.
    """
    return {
        "entries": get_audit_log(limit=limit, action_filter=action),
        "total": len(get_audit_log(limit=500, action_filter=action)),
    }


@router.get("/actions")
def list_action_types(_: User = Depends(require_admin)):
    """Список відомих типів дій для фільтру у фронтенді."""
    return get_action_types()
