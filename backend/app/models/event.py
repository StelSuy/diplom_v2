from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from app.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), index=True)
    terminal_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("terminals.id"), index=True, nullable=True)

    # IN / OUT
    direction: Mapped[str] = mapped_column(String(8), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True)

    is_manual: Mapped[bool] = mapped_column(Boolean, default=False, comment="Чи створена подія вручну")
    created_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="Коментар до ручної події")
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)
