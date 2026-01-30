"""
Database session management and engine configuration.
"""
import logging
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import settings

logger = logging.getLogger(__name__)


def _create_engine() -> Engine:
    """
    Create and configure SQLAlchemy engine.
    
    Returns:
        Configured SQLAlchemy engine
    """
    database_url = settings.database_url
    
    # Engine configuration
    engine_kwargs = {
        "echo": settings.sql_echo,
        "pool_pre_ping": True,  # Verify connections before using
        "pool_recycle": settings.db_pool_recycle,
    }
    
    # Use connection pooling for MySQL/PostgreSQL, NullPool for SQLite
    if "sqlite" in database_url:
        engine_kwargs["poolclass"] = NullPool
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        logger.warning("Using SQLite - not recommended for production")
    else:
        engine_kwargs["poolclass"] = QueuePool
        engine_kwargs["pool_size"] = settings.db_pool_size
        engine_kwargs["max_overflow"] = settings.db_max_overflow
    
    engine = create_engine(database_url, **engine_kwargs)
    
    # Log engine configuration
    logger.info(f"Database engine created: {engine.url.drivername}")
    logger.info(f"Pool size: {engine.pool.size() if hasattr(engine.pool, 'size') else 'N/A'}")
    
    return engine


# Create global engine instance
engine = _create_engine()

# Create session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# Database session dependency
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    
    Yields:
        SQLAlchemy session
        
    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Event listeners for connection handling
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign keys for SQLite connections."""
    if "sqlite" in str(engine.url):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@event.listens_for(Engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log when connection is checked out from pool (debug only)."""
    if settings.debug and settings.sql_echo:
        logger.debug("Connection checked out from pool")


@event.listens_for(Engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log when connection is returned to pool (debug only)."""
    if settings.debug and settings.sql_echo:
        logger.debug("Connection returned to pool")
