"""
conftest.py — глобальні налаштування pytest для всіх юніт-тестів.

Встановлює мінімальні змінні оточення ДО того, як будь-який модуль
з app/ спробує зчитати Settings() — інакше pydantic_settings впаде
з ValidationError через відсутність DATABASE_URL або JWT_SECRET.
"""
import os

# Мінімальний набір env-змінних для тестів (не потребують реальної БД)
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_temp.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-that-is-long-enough-for-jwt-hs256")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("ADMIN_PASSWORD", "testpassword123")
os.environ.setdefault("LOG_LEVEL", "WARNING")
