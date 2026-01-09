from app.db.session import engine
from app.db.base import Base
from app.models import user, employee, terminal, event, schedule  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
