"""Positions API route."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.position import Position
from app.models.user import User
from app.security.audit import audit_log

router = APIRouter(prefix="/positions", tags=["positions"])


@router.get("/")
def list_positions(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(Position)
    if not include_inactive:
        q = q.filter(Position.is_active == True)
    return q.order_by(Position.name).all()


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_position(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    existing = db.query(Position).filter(Position.name == name).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(status_code=409, detail=f"Position '{name}' already exists")

    pos = Position(name=name, is_active=True)
    db.add(pos)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Position '{name}' already exists")
    db.refresh(pos)
    audit_log("position_create", current_user.username, details={"name": name})
    return pos


@router.patch("/{position_id}")
def update_position(
    position_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    pos = db.query(Position).filter(Position.id == position_id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found")

    if "name" in payload and payload["name"]:
        pos.name = payload["name"].strip()
    if "is_active" in payload:
        pos.is_active = bool(payload["is_active"])

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Position name already in use")
    db.refresh(pos)
    audit_log("position_update", current_user.username, details={"id": position_id})
    return pos


@router.delete("/{position_id}", status_code=status.HTTP_200_OK)
def delete_position(
    position_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    from app.models.employee import Employee
    pos = db.query(Position).filter(Position.id == position_id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found")

    in_use = db.query(Employee).filter(Employee.position == pos.name).first()
    if in_use:
        pos.is_active = False
        db.commit()
        audit_log("position_delete", current_user.username, details={"id": position_id, "deactivated": True})
        return {"detail": "Position deactivated (still in use)", "id": position_id}

    db.delete(pos)
    db.commit()
    audit_log("position_delete", current_user.username, details={"id": position_id, "deleted": True})
    return {"detail": "Deleted", "id": position_id}
