from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List, Optional

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.event import Event


class Terminal(Base):
    __tablename__ = "terminals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    # Секрет терміналу (Bearer-подібний ключ)
    api_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)

    # ВИПРАВЛЕНО: lazy="dynamic" застарілий в SQLAlchemy 2.0 для Mapped[] — замінено на lazy="select"
    events: Mapped[List["Event"]] = relationship("Event", back_populates="terminal", lazy="select")
