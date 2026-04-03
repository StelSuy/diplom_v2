from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeOut, EmployeeUpdate
from app.crud import employee as employee_crud
from app.security.audit import audit_log

# БАГ №1 ВИПРАВЛЕНО: вилучено get_current_user — require_admin тепер повертає User
router = APIRouter(prefix="/employees", tags=["employees"])


@router.post("/", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    # Перевірка унікальності NFC UID перед INSERT
    if payload.nfc_uid:
        existing = db.query(Employee).filter(Employee.nfc_uid == payload.nfc_uid).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Співробітник з NFC UID '{payload.nfc_uid}' вже існує (ID: {existing.id}, {existing.full_name})"
            )

    emp = Employee(
        full_name=payload.full_name,
        nfc_uid=payload.nfc_uid,
        position=getattr(payload, "position", None),
        comment=getattr(payload, "comment", None),
        is_active=True,
    )
    db.add(emp)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        err_str = str(e.orig)
        if "nfc_uid" in err_str or "Duplicate entry" in err_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"NFC UID '{payload.nfc_uid}' вже використовується іншим співробітником"
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Помилка БД: {err_str}")

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

    # Перевірка унікальності NFC UID при зміні
    if "nfc_uid" in data and data["nfc_uid"] and data["nfc_uid"] != emp.nfc_uid:
        dup = db.query(Employee).filter(
            Employee.nfc_uid == data["nfc_uid"],
            Employee.id != employee_id
        ).first()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"NFC UID '{data['nfc_uid']}' вже використовується співробітником ID:{dup.id} ({dup.full_name})"
            )

    try:
        result = employee_crud.update_employee(db, emp, data)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Помилка унікальності: {str(e.orig)}"
        )

    audit_log("employee_update", current_user.username, details={
        "employee_id": employee_id, "changes": data,
    })
    return result
