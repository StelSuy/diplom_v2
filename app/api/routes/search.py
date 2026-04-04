"""Search route — live employee search."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.employee import Employee
from app.models.user import User

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/employees")
def search_employees(
    q: str = Query("", description="Search query"),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = db.query(Employee)
    if q:
        like = f"%{q}%"
        query = query.filter(
            Employee.full_name.ilike(like) |
            Employee.nfc_uid.ilike(like) |
            Employee.position.ilike(like)
        )
    employees = query.order_by(Employee.full_name).limit(limit).all()
    return [
        {
            "id": e.id,
            "full_name": e.full_name,
            "nfc_uid": e.nfc_uid,
            "position": e.position,
            "is_active": e.is_active,
        }
        for e in employees
    ]
