# app/core/seed.py
from __future__ import annotations

import secrets
from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect

from app.models.terminal import Terminal
from app.models.employee import Employee

DEFAULT_TERMINAL_ID = 1
DEFAULT_EMPLOYEE_UID = "TEST-EMP-0001"


def _model_columns(model) -> set[str]:
    return {c.key for c in inspect(model).mapper.column_attrs}


def _filter_kwargs(model, data: dict) -> dict:
    cols = _model_columns(model)
    return {k: v for k, v in data.items() if k in cols}


def _gen_api_key() -> str:
    # стабільний формат, без спецсимволів, зручний для копіювання
    return secrets.token_urlsafe(32)


def seed_demo_data(db: Session) -> dict:
    created = {"terminal": False, "employee": False}

    # -----------------
    # Terminal #1
    # -----------------
    terminal = db.get(Terminal, DEFAULT_TERMINAL_ID)
    if terminal is None:
        term_cols = _model_columns(Terminal)

        term_data = {
            "id": DEFAULT_TERMINAL_ID,
            "name": "Terminal #1",
            "title": "Terminal #1",
            "is_active": True,
            "active": True,
            "location": "Demo",
        }

        # якщо в моделі є api_key — заповнюємо
        if "api_key" in term_cols:
            term_data["api_key"] = _gen_api_key()

        term_kwargs = _filter_kwargs(Terminal, term_data)
        terminal = Terminal(**term_kwargs)
        db.add(terminal)
        created["terminal"] = True

    # -----------------
    # Test Employee
    # -----------------
    emp_cols = _model_columns(Employee)
    uid_field = "nfc_uid" if "nfc_uid" in emp_cols else ("uid" if "uid" in emp_cols else None)

    employee = None
    if uid_field is not None:
        employee = db.query(Employee).filter(getattr(Employee, uid_field) == DEFAULT_EMPLOYEE_UID).first()

    if employee is None:
        emp_data = {
            "full_name": "Test Employee",
            "first_name": "Test",
            "last_name": "Employee",
            "position": "Demo",
            "comment": "Auto-seeded for demo",
            "is_active": True,
            "active": True,
            "public_key_b64": None,
        }
        if uid_field:
            emp_data[uid_field] = DEFAULT_EMPLOYEE_UID

        emp_kwargs = _filter_kwargs(Employee, emp_data)
        employee = Employee(**emp_kwargs)
        db.add(employee)
        created["employee"] = True

    if created["terminal"] or created["employee"]:
        db.commit()

    return created
