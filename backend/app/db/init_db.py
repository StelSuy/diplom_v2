# app/db/init_db.py
from __future__ import annotations

from app.db.session import engine, SessionLocal
from app.db.base import Base

# ✅ Імпортуємо моделі ТУТ, а не в Base (щоб SQLAlchemy побачив таблиці)
import app.models  # noqa: F401

from app.core.seed import seed_demo_data


def init_db() -> dict:
    print("== init_db: creating tables ==")
    Base.metadata.create_all(bind=engine)

    print("== init_db: seeding demo data (if needed) ==")
    db = SessionLocal()
    try:
        created = seed_demo_data(db)
        print("Seed result:", created)
        return created
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("✅ Tables created (and seed done if needed)")
