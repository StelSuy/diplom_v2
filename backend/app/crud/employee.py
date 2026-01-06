from sqlalchemy.orm import Session
from app.models.employee import Employee


def get_by_id(db: Session, employee_id: int) -> Employee | None:
    return db.query(Employee).filter(Employee.id == employee_id).first()


def update_employee(db: Session, emp: Employee, data: dict) -> Employee:
    for k, v in data.items():
        if v is not None:
            setattr(emp, k, v)
    db.commit()
    db.refresh(emp)
    return emp
