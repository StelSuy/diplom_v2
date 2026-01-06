from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Terminal(Base):
    __tablename__ = "terminals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    # Секрет терминала (Bearer-подобный ключ)
    api_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
