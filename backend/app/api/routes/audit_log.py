"""Audit log API — читання з БД з фільтрами."""
import json
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.security.audit import get_action_types

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/log")
def read_audit_log(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    action: str | None = Query(default=None, description="Фільтр по типу дії"),
    admin_username: str | None = Query(default=None, description="Фільтр по адміністратору"),
    date_from: date | None = Query(default=None, description="Дата від (РРРР-ММ-ДД)"),
    date_to: date | None = Query(default=None, description="Дата до (РРРР-ММ-ДД)"),
    entity_type: str | None = Query(default=None, description="Тип сутності"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Журнал дій з фільтрами по даті, адміністратору, типу дії."""
    q = db.query(AuditLog)

    if action:
        q = q.filter(AuditLog.action == action)
    if admin_username:
        q = q.filter(AuditLog.admin_username.ilike(f"%{admin_username}%"))
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if date_from:
        q = q.filter(AuditLog.created_at >= datetime(date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc))
    if date_to:
        q = q.filter(AuditLog.created_at < datetime(date_to.year, date_to.month, date_to.day + 1, tzinfo=timezone.utc))

    total = q.count()
    rows = q.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()

    entries = []
    for r in rows:
        details = None
        if r.details:
            try:
                details = json.loads(r.details)
            except Exception:
                details = r.details
        entries.append({
            "id": r.id,
            "admin_username": r.admin_username,
            "admin_id": r.admin_id,
            "action": r.action,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "details": details,
            "created_at": r.created_at.isoformat(),
        })

    return {"entries": entries, "total": total, "limit": limit, "offset": offset}


@router.get("/actions")
def list_action_types(_: User = Depends(require_admin)):
    """Список типів дій для фільтру."""
    return get_action_types()
