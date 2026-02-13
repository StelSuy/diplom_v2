from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeOut, EmployeeUpdate
from app.crud import employee as employee_crud
from app.security.audit import audit_log

# БАГ №1 ВИПРАВЛЕНО: вилучено get_current_user — require_admin тепер повертає User
router = APIRouter(prefix="/employees", tags=["employees"])


@router.post("/", response_model=EmployeeOut)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    emp = Employee(
        full_name=payload.full_name,
        nfc_uid=payload.nfc_uid,
        position=getattr(payload, "position", None),
        comment=getattr(payload, "comment", None),
        is_active=True,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)

    audit_log("employee_create", current_user.username, details={
        "employee_id": emp.id, "full_name": emp.full_name, "nfc_uid": emp.nfc_uid,
    })
    return emp


@router.get("/", response_model=list[EmployeeOut])
def list_employees(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(Employee).order_by(Employee.id).all()


@router.get("/{employee_id}", response_model=EmployeeOut)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    emp = employee_crud.get_by_id(db, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.patch("/{employee_id}", response_model=EmployeeOut)
def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    emp = employee_crud.get_by_id(db, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    data = payload.model_dump(exclude_unset=True)  # pydantic v2
    result = employee_crud.update_employee(db, emp, data)

    audit_log("employee_update", current_user.username, details={
        "employee_id": employee_id, "changes": data,
    })
    return result
