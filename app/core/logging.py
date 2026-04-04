"""
Centralized logging configuration.
"""
import logging
import sys
from typing import Optional

from app.core.config import settings


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Configure application-wide logging.
    
    Args:
        log_level: Override default log level from settings
        
    Returns:
        Root logger instance
    """
    level_name = log_level or settings.log_level
    level = getattr(logging, level_name.upper(), logging.INFO)
    
    # Log format
    log_format = "%(asctime)s [%(levelname)-8s] %(name)s:%(lineno)d - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    
    # Suppress noisy libraries in production
    if settings.is_production:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("multipart").setLevel(logging.WARNING)
        logging.getLogger("watchfiles").setLevel(logging.WARNING)
    
    # SQLAlchemy logging
    if settings.sql_echo:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
