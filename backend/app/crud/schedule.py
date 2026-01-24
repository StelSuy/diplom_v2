# app/crud/schedule.py
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Optional
from calendar import monthrange

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.schedule import Schedule


_CODE_HOURS_RE = re.compile(r"^\s*(\d{1,2})\s*-\s*(\d{1,2})\s*$")


def _normalize_hhmm(value: str) -> str:
    """
    Нормалізує час: приймає '5', '05', '5:00', '05:00' -> повертає 'ГГ:ХХ'
    """
    v = value.strip()
    if ":" not in v:
        # тільки години
        h = int(v)
        if h < 0 or h > 23:
            raise ValueError("Година має бути 0..23")
        return f"{h:02d}:00"

    h_str, m_str = v.split(":", 1)
    h = int(h_str)
    m = int(m_str)
    if h < 0 or h > 23:
        raise ValueError("Година має бути 0..23")
    if m < 0 or m > 59:
        raise ValueError("Хвилина має бути 0..59")
    return f"{h:02d}:{m:02d}"


def _derive_time_from_code(code: str) -> tuple[str, str]:
    """
    Підтримка форматів:
    - '5-7'  -> 05:00..07:00
    - '05-17' -> 05:00..17:00
    """
    m = _CODE_HOURS_RE.match(code or "")
    if not m:
        raise ValueError("Неправильний формат коду. Використовуйте 'Г-Г' (приклад: '5-7') або вкажіть start_hhmm/end_hhmm.")
    start_h = m.group(1)
    end_h = m.group(2)
    start = _normalize_hhmm(start_h)
    end = _normalize_hhmm(end_h)
    return start, end


def get_range(db: Session, date_from: date, date_to: date, employee_id: Optional[int] = None):
    """Отримати графік за період"""
    q = db.query(Schedule).filter(Schedule.day >= date_from, Schedule.day <= date_to)
    if employee_id is not None:
        q = q.filter(Schedule.employee_id == employee_id)
    return q.order_by(Schedule.day, Schedule.employee_id).all()


def get_or_create_empty_schedules(
    db: Session,
    employee_id: int,
    year: int,
    month: int
) -> list[Schedule]:
    """
    Отримати або створити пусті графіки для працівника на весь місяць.
    Якщо графіку немає - створюється пустий запис (00:00-00:00, code=None)
    """
    from app.crud.employee import get_by_id
    
    # Перевіряємо чи існує працівник
    employee = get_by_id(db, employee_id)
    if not employee:
        raise ValueError(f"Працівник з ID {employee_id} не знайдений")
    
    # Отримуємо перший і останній день місяця
    _, last_day = monthrange(year, month)
    date_from = date(year, month, 1)
    date_to = date(year, month, last_day)
    
    # Отримуємо існуючі записи
    existing = get_range(db, date_from, date_to, employee_id)
    existing_days = {rec.day for rec in existing}
    
    # Створюємо пусті записи для днів без графіку
    created = []
    current_day = date_from
    while current_day <= date_to:
        if current_day not in existing_days:
            new_schedule = Schedule(
                employee_id=employee_id,
                day=current_day,
                start_hhmm="00:00",
                end_hhmm="00:00",
                code=None
            )
            db.add(new_schedule)
            created.append(new_schedule)
        current_day += timedelta(days=1)
    
    if created:
        db.commit()
        for rec in created:
            db.refresh(rec)
    
    # Повертаємо всі записи за місяць
    return get_range(db, date_from, date_to, employee_id)


def ensure_all_employees_have_schedules(
    db: Session,
    year: int,
    month: int
) -> dict[int, int]:
    """
    Створити пусті графіки для ВСІХ працівників на місяць.
    Повертає словник {employee_id: кількість_створених_записів}
    """
    from app.crud.employee import get_all
    
    employees = get_all(db)
    result = {}
    
    for employee in employees:
        schedules_before = len(get_or_create_empty_schedules(db, employee.id, year, month))
        _, last_day = monthrange(year, month)
        date_from = date(year, month, 1)
        date_to = date(year, month, last_day)
        existing_count = len(get_range(db, date_from, date_to, employee.id))
        
        created_count = existing_count - (schedules_before - existing_count)
        result[employee.id] = max(0, created_count)
    
    return result


def upsert_cell(
    db: Session,
    employee_id: int,
    day: date,
    code: Optional[str],
    start_hhmm: Optional[str] = None,
    end_hhmm: Optional[str] = None,
) -> Schedule:
    """
    Вставляє/оновлює комірку графіку.
    
    Логіка:
    1. Якщо code пустий/None І start/end пусті -> ВИДАЛЯЄМО запис
    2. Якщо є start AND end -> використовуємо їх
    3. Якщо є code в форматі '5-7' -> конвертуємо в ГГ:ХХ
    4. Інакше -> помилка валідації
    
    ВАЖЛИВО: При видаленні повертаємо None, а не фейковий об'єкт!
    """
    # Нормалізуємо вхідні дані
    code_clean = str(code).strip() if code else ""
    start_clean = str(start_hhmm).strip() if start_hhmm else ""
    end_clean = str(end_hhmm).strip() if end_hhmm else ""
    
    # Перевіряємо існуючий запис
    existing = (
        db.query(Schedule)
        .filter(Schedule.employee_id == employee_id, Schedule.day == day)
        .first()
    )

    # Випадок 1: Очищення комірки (пустий код і пустий час)
    if not code_clean and not start_clean and not end_clean:
        if existing:
            db.delete(existing)
            db.commit()
        # Створюємо тимчасовий об'єкт для відповіді (НЕ зберігаємо в БД!)
        deleted_obj = Schedule(
            employee_id=employee_id,
            day=day,
            start_hhmm="",
            end_hhmm="",
            code=""
        )
        deleted_obj.id = None
        return deleted_obj

    # Випадок 1.5: Пустий графік (00:00-00:00 без коду) - це теж очищення
    if not code_clean and start_clean == "00:00" and end_clean == "00:00":
        if existing:
            # Оновлюємо на пустий графік
            existing.start_hhmm = "00:00"
            existing.end_hhmm = "00:00"
            existing.code = None
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Створюємо новий пустий графік
            row = Schedule(
                employee_id=employee_id,
                day=day,
                start_hhmm="00:00",
                end_hhmm="00:00",
                code=None,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return row
    
    # Випадок 2: Є явні start і end
    if start_clean and end_clean:
        try:
            start = _normalize_hhmm(start_clean)
            end = _normalize_hhmm(end_clean)
        except ValueError as e:
            raise ValueError(f"Неправильний формат часу: {e}")

        # Випадок 3: Парсимо з code (якщо це формат Г-Г) або використовуємо як є
    elif code_clean:
        # Спробуємо розпарсити як Г-Г формат
        m = _CODE_HOURS_RE.match(code_clean)
        if m:
            # Це формат типу "5-7", парсимо в час
            try:
                start, end = _derive_time_from_code(code_clean)
            except ValueError as e:
                raise ValueError(f"Неправильний формат коду: {e}")
        else:
            # Це довільний код (В, ОФ, Л тощо) - використовуємо 00:00-00:00
            start = "00:00"
            end = "00:00"
    
    # Випадок 4: Недостатньо даних
    else:
        raise ValueError("Вкажіть start_hhmm+end_hhmm АБО code в форматі 'Г-Г'")

        # Перевіряємо логіку часу (тільки якщо це не 00:00-00:00 для кодів типу В, Л)
    if start >= end and not (start == "00:00" and end == "00:00"):
        raise ValueError(f"start_hhmm ({start}) має бути раніше ніж end_hhmm ({end})")
    
    # Оновлення або створення
    if existing:
        existing.start_hhmm = start
        existing.end_hhmm = end
        existing.code = code_clean
        row = existing
    else:
        row = Schedule(
            employee_id=employee_id,
            day=day,
            start_hhmm=start,
            end_hhmm=end,
            code=code_clean,
        )
        db.add(row)
    
    try:
        db.commit()
        db.refresh(row)
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Порушення обмеження БД: {e.orig}")
    
    return row


def delete_cell(db: Session, employee_id: int, day: date) -> bool:
    """Видаляє комірку графіку. Повертає True якщо щось видалено."""
    existing = (
        db.query(Schedule)
        .filter(Schedule.employee_id == employee_id, Schedule.day == day)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        return True
    return False
