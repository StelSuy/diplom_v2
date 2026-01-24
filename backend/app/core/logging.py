# app/core/logging.py
import logging
import sys
from typing import Any

from app.core.config import settings


def setup_logging():
    """
    Настройка логирования для приложения.
    """
    log_level = logging.DEBUG if settings.debug else logging.INFO
    
    # Формат логов
    log_format = "%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Основной handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Корневой logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
    
    # Отключаем лишний вывод от библиотек
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)
    
    # Логи SQLAlchemy только при явном SQL_ECHO
    if not settings.debug:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Получить logger с заданным именем.
    """
    return logging.getLogger(name)
