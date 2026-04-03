# app/core/seed.py
from __future__ import annotations

import logging
import secrets

from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect

from app.models.terminal import Terminal
from app.models.employee import Employee
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

DEFAULT_TERMINAL_ID = 1
DEFAULT_EMPLOYEE_UID = "TEST-EMP-0001"


def _model_columns(model) -> set[str]:
    return {c.key for c in inspect(model).mapper.column_attrs}


def _filter_kwargs(model, data: dict) -> dict:
    cols = _model_columns(model)
    return {k: v for k, v in data.items() if k in cols}


def _gen_api_key() -> str:
    return secrets.token_urlsafe(32)


# ─────────────────────────────────────────────────────────────────────────────
#  Admin user
# ─────────────────────────────────────────────────────────────────────────────

def seed_admin(db: Session) -> bool:
    """
    Створює адмін-користувача в таблиці users, якщо його ще немає.
    Ім'я та пароль беруться з .env (ADMIN_USERNAME / ADMIN_PASSWORD).
    Повертає True якщо створено, False якщо вже існує.
    """
    from app.core.config import settings
    from app.core.security import hash_password

    existing = db.query(User).filter(
        User.username == settings.admin_username
    ).first()

    if existing:
        logger.debug(f"Admin user '{settings.admin_username}' already exists — skipping.")
        return False

    admin = User(
        username=settings.admin_username,
        password_hash=hash_password(settings.admin_password),
        role=UserRole.ADMIN.value,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    logger.info(
        f"✔ Admin user created: username='{settings.admin_username}' "
        f"role='{UserRole.ADMIN.value}' (id={admin.id})"
    )
    return True


# ─────────────────────────────────────────────────────────────────────────────
#  Demo data (terminal + test employee)
# ─────────────────────────────────────────────────────────────────────────────

def seed_demo_data(db: Session) -> dict:
    created = {"terminal": False, "employee": False}

    # Terminal #1
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
        if "api_key" in term_cols:
            term_data["api_key"] = _gen_api_key()
        terminal = Terminal(**_filter_kwargs(Terminal, term_data))
        db.add(terminal)
        created["terminal"] = True

    # Test Employee
    emp_cols = _model_columns(Employee)
    uid_field = (
        "nfc_uid" if "nfc_uid" in emp_cols
        else ("uid" if "uid" in emp_cols else None)
    )
    employee = None
    if uid_field:
        employee = db.query(Employee).filter(
            getattr(Employee, uid_field) == DEFAULT_EMPLOYEE_UID
        ).first()

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
        employee = Employee(**_filter_kwargs(Employee, emp_data))
        db.add(employee)
        created["employee"] = True

    if created["terminal"] or created["employee"]:
        db.commit()

    return created
