from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.schemas.terminal import TerminalRegisterRequest




def get_all(db: Session, only_active: bool = True) -> list[Employee]:
    q = db.query(Employee)
    if only_active:
        q = q.filter(Employee.is_active == True)  # noqa: E712
    return q.order_by(Employee.full_name.asc()).all()


def get_by_id(db: Session, employee_id: int) -> Employee | None:
    return db.query(Employee).filter(Employee.id == employee_id).first()


def get_by_uid(db: Session, uid: str) -> Employee | None:
    u = (uid or "").strip().upper()
    return db.query(Employee).filter(Employee.nfc_uid == u).first()


def update_employee(db: Session, emp: Employee, data: dict) -> Employee:
    for k, v in data.items():
        if v is not None:
            setattr(emp, k, v)
    db.commit()
    db.refresh(emp)
    return emp


def create_employee_from_terminal_registration(db: Session, payload: TerminalRegisterRequest) -> Employee:
    uid = payload.uid.strip().upper()

    existing = db.query(Employee).filter(Employee.nfc_uid == uid).first()
    if existing:
        return existing

    emp = Employee(
        full_name=payload.full_name.strip(),
        nfc_uid=uid,
        is_active=True
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp
