from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List
import enum

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.audit_log import AuditLog


class UserRole(str, enum.Enum):
    """Ролі користувачів у системі"""
    ADMIN = "admin"          # Повний доступ
    MANAGER = "manager"      # Перегляд + редагування графіків
    HR = "hr"                # Тільки перегляд + звіти
    EMPLOYEE = "employee"    # Особистий кабінет


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(
        Enum(UserRole, native_enum=False, length=20),
        default=UserRole.EMPLOYEE.value,
        nullable=False
    )

    created_events: Mapped[List["Event"]] = relationship("Event", back_populates="created_by", lazy="select")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="admin", lazy="select")

