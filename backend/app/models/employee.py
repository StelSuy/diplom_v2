from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING, List

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.event import Event


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    full_name: Mapped[str] = mapped_column(String(128), index=True)
    nfc_uid: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    # NEW: public key для challenge-response (Base64 DER)
    public_key_b64: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    position: Mapped[str | None] = mapped_column(String(64), nullable=True)
    comment: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ВИПРАВЛЕНО: lazy="dynamic" застарілий в SQLAlchemy 2.0 для Mapped[] — замінено на lazy="select"
    events: Mapped[List["Event"]] = relationship("Event", back_populates="employee", lazy="select")
