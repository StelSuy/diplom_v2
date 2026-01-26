# app/db/session.py
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def _make_engine():
    """
    Створює SQLAlchemy engine з production-готовими налаштуваннями.
    
    Використовує:
    - computed_database_url (автоматична збірка з компонентів або прямий URL)
    - pool settings для оптимальної роботи з MySQL
    - pool_pre_ping для перевірки з'єднань
    """
    db_url = settings.computed_database_url
    
    # Логування (без паролю в production)
    if settings.app_debug:
        logger.info(f"Connecting to database: {db_url}")
    else:
        # Приховуємо пароль в production
        safe_url = db_url.split('@')[1] if '@' in db_url else db_url
        logger.info(f"Connecting to database: ...@{safe_url}")
    
    return create_engine(
        db_url,
        echo=settings.sql_echo,
        pool_pre_ping=True,  # Перевірка з'єднань перед використанням
        pool_recycle=settings.db_pool_recycle,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        # Додаткові production-налаштування
        pool_timeout=30,  # Timeout для отримання з'єднання з пулу
        connect_args={
            "connect_timeout": 10  # Timeout для підключення до БД
        }
    )


try:
    engine = _make_engine()
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency для FastAPI.
    
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
