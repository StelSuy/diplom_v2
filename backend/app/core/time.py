from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

WARSAW = ZoneInfo("Europe/Warsaw")


def ensure_utc(dt: datetime | None) -> datetime:
    """
    Приводит datetime к UTC-aware.
    - None -> now(UTC)
    - naive datetime -> считаем, что это локальное Europe/Warsaw, конвертим в UTC
    - aware datetime -> конвертим в UTC
    """
    if dt is None:
        return datetime.now(timezone.utc)

    if dt.tzinfo is None:
        # Наивный dt считаем локальным временем терминала/панели (Europe/Warsaw)
        dt = dt.replace(tzinfo=WARSAW)

    return dt.astimezone(timezone.utc)


def to_warsaw(dt: datetime) -> datetime:
    """
    UTC-aware -> Europe/Warsaw (для отображения)
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(WARSAW)


def to_utc(dt: datetime, assume_tz: ZoneInfo = WARSAW) -> datetime:
    """
    Конвертує будь-який datetime в UTC.
    
    Args:
        dt: datetime для конверсії
        assume_tz: timezone для naive datetime (default: Europe/Warsaw)
    
    Returns:
        UTC datetime
    """
    if dt.tzinfo is None:
        # Для naive datetime використовуємо assume_tz
        dt = dt.replace(tzinfo=assume_tz)
    return dt.astimezone(timezone.utc)


def local_date_str(dt: datetime) -> str:
    """Конвертує datetime в локальну дату (YYYY-MM-DD)"""
    return to_warsaw(dt).date().isoformat()
