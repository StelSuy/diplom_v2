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


def local_date_str(dt: datetime) -> str:
    return to_warsaw(dt).date().isoformat()
