# app/crud/schedule.py
from __future__ import annotations

import re
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.schedule import Schedule


_CODE_HOURS_RE = re.compile(r"^\s*(\d{1,2})\s*-\s*(\d{1,2})\s*$")


def _normalize_hhmm(value: str) -> str:
    """
    Приймає '5', '05', '5:00', '05:00' -> повертає 'HH:MM'
    """
    v = value.strip()
    if ":" not in v:
        # тільки години
        h = int(v)
        if h < 0 or h > 23:
            raise ValueError("Hour must be 0..23")
        return f"{h:02d}:00"

    h_str, m_str = v.split(":", 1)
    h = int(h_str)
    m = int(m_str)
    if h < 0 or h > 23:
        raise ValueError("Hour must be 0..23")
    if m < 0 or m > 59:
        raise ValueError("Minute must be 0..59")
    return f"{h:02d}:{m:02d}"


def _derive_time_from_code(code: str) -> tuple[str, str]:
    """
    Підтримка форматів:
    - '5-7'  -> 05:00..07:00
    - '05-17' -> 05:00..17:00
    """
    m = _CODE_HOURS_RE.match(code or "")
    if not m:
        raise ValueError("Invalid code format. Use 'H-H' (example: '5-7') or send start_hhmm/end_hhmm.")
    start_h = m.group(1)
    end_h = m.group(2)
    start = _normalize_hhmm(start_h)
    end = _normalize_hhmm(end_h)
    return start, end


def get_range(db: Session, date_from: date, date_to: date, employee_id: Optional[int] = None):
    q = db.query(Schedule).filter(Schedule.day >= date_from, Schedule.day <= date_to)
    if employee_id is not None:
        q = q.filter(Schedule.employee_id == employee_id)
    return q.all()


def upsert_cell(
    db: Session,
    employee_id: int,
    day: date,
    code: Optional[str],
    start_hhmm: Optional[str] = None,
    end_hhmm: Optional[str] = None,
) -> Schedule:
    """
    Вставляє/оновлює комірку розкладу.
    Якщо start/end не передані, але є code у форматі '5-7' — конвертуємо в HH:MM.
    Якщо code порожній/None — видаляємо запис (очистити комірку).
    """
    # Якщо користувач "очистив" комірку
    if code is None or str(code).strip() == "":
        existing = (
            db.query(Schedule)
            .filter(Schedule.employee_id == employee_id, Schedule.day == day)
            .first()
        )
        if existing:
            db.delete(existing)
            db.commit()
        # Повернемо "порожній" об'єкт (або можна підняти 204 у роуті)
        return Schedule(employee_id=employee_id, day=day, start_hhmm="00:00", end_hhmm="00:00", code="")

    # Нормалізація часу
    if start_hhmm and end_hhmm:
        start = _normalize_hhmm(start_hhmm)
        end = _normalize_hhmm(end_hhmm)
    else:
        # Беремо з code
        start, end = _derive_time_from_code(str(code))

    row = (
        db.query(Schedule)
        .filter(Schedule.employee_id == employee_id, Schedule.day == day)
        .first()
    )

    if row is None:
        row = Schedule(
            employee_id=employee_id,
            day=day,
            start_hhmm=start,
            end_hhmm=end,
            code=str(code).strip(),
        )
        db.add(row)
    else:
        row.start_hhmm = start
        row.end_hhmm = end
        row.code = str(code).strip()

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # Краще 400 з текстом, а не 500
        raise ValueError(f"Schedule cell invalid: {e.orig}")

    db.refresh(row)
    return row
