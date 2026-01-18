from app.db.session import engine
from app.db.base import Base

# Імпортуємо всі моделі ОДНИМ рядком
# щоб SQLAlchemy "побачив" всі таблиці
import app.models  # noqa: F401


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created")
