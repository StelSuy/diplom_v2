from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    WARSAW = ZoneInfo("Europe/Warsaw")
except ZoneInfoNotFoundError:
    # On Windows, zoneinfo requires the 'tzdata' package.
    # Run: pip install tzdata
    raise RuntimeError(
        "Timezone data not found. Install the missing package:\n"
        "    pip install tzdata\n"
        "or re-run:  pip install -r requirements.txt"
    )


def ensure_utc(dt: datetime | None) -> datetime:
    """
    Приводить datetime до UTC-aware.
    - None          -> now(UTC)
    - naive datetime -> вважається Europe/Warsaw, конвертується в UTC
    - aware datetime -> конвертується в UTC
    """
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=WARSAW)
    return dt.astimezone(timezone.utc)


def to_warsaw(dt: datetime) -> datetime:
    """UTC-aware -> Europe/Warsaw (для відображення)"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(WARSAW)


def to_utc(dt: datetime) -> datetime:
    """Конвертує будь-який datetime в UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def local_date_str(dt: datetime) -> str:
    return to_warsaw(dt).date().isoformat()
