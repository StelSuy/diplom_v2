# РўСѓС‚ РїРѕС‚РѕРј CRUD РґР»СЏ РіСЂР°С„РёРєРѕРІ
from __future__ import annotations

from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.schedule import Schedule


def get_range(db: Session, date_from: date, date_to: date, employee_id: int | None = None) -> list[Schedule]:
    q = db.query(Schedule).filter(and_(Schedule.day >= date_from, Schedule.day <= date_to))
    if employee_id is not None:
        q = q.filter(Schedule.employee_id == employee_id)
    return q.all()


def upsert_cell(
    db: Session,
    employee_id: int,
    day: date,
    start_hhmm: str | None,
    end_hhmm: str | None,
    code: str | None,
) -> Schedule:
    row = (
        db.query(Schedule)
        .filter(Schedule.employee_id == employee_id, Schedule.day == day)
        .first()
    )
    if row is None:
        row = Schedule(employee_id=employee_id, day=day)
        db.add(row)

    # Если всё пусто — удаляем запись
    if not start_hhmm and not end_hhmm and not code:
        if row.id is not None:
            db.delete(row)
            db.commit()
        return Schedule(employee_id=employee_id, day=day, start_hhmm=None, end_hhmm=None, code=None)

    row.start_hhmm = start_hhmm
    row.end_hhmm = end_hhmm
    row.code = code

    db.commit()
    db.refresh(row)
    return row
