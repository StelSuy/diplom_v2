#!/usr/bin/env python3
"""
Database initialization script.

This script:
1. Creates all tables if they don't exist
2. Seeds demo data
3. Can be run multiple times safely
"""
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import engine
from app.db.base import Base
from app.db.session import SessionLocal
from app.core.seed import seed_demo_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def init_db():
    """Initialize database schema and seed data."""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created successfully")
        
        logger.info("Seeding demo data...")
        db = SessionLocal()
        try:
            result = seed_demo_data(db)
            logger.info(f"✓ Demo data seeded: {result}")
        finally:
            db.close()
        
        logger.info("✓ Database initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        logger.exception("Full error:")
        return False


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("Starting database initialization...")
    logger.info("="*60)
    
    success = init_db()
    
    logger.info("="*60)
    if success:
        logger.info("✓ ALL DONE!")
        logger.info("\nYou can now run the server:")
        logger.info("  Windows: run_dev.bat")
        logger.info("  Linux/Mac: ./run_dev.sh")
    else:
        logger.error("✗ FAILED!")
        logger.error("\nPlease check:")
        logger.error("  1. Database connection in .env")
        logger.error("  2. Database exists and is accessible")
        logger.error("  3. User has proper permissions")
        sys.exit(1)
    logger.info("="*60)
