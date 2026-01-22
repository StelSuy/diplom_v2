from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable

from app.core.time import WARSAW, to_warsaw


@dataclass(frozen=True)
class WorktimeAnomaly:
    code: str
    ts_utc: datetime | None = None
    details: str | None = None


@dataclass(frozen=True)
class WorkInterval:
    in_utc: datetime
    out_utc: datetime
    auto_closed: bool = False


def _day_end_utc_for_local_day(local_day: date) -> datetime:
    """Local 23:59:59.999999 -> UTC."""
    end_local = datetime.combine(local_day, time.max).replace(tzinfo=WARSAW)
    return end_local.astimezone(timezone.utc)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def build_intervals(
    events: Iterable,
    *,
    auto_close: bool = True,
    auto_close_at_day_end: bool = True,
    now_utc: datetime | None = None,
) -> tuple[list[WorkInterval], list[WorktimeAnomaly], bool]:
    """Turn raw IN/OUT events into normalized intervals.

    Rules:
    - Sort order is assumed chronological.
    - Duplicate IN while already "open" => anomaly; we keep the latest IN as the new start.
    - OUT without open IN => anomaly; ignored.
    - If there is open IN at the end:
        - if auto_close: close at min(now_utc, end_of_local_day) (if auto_close_at_day_end)
        - otherwise interval is not emitted.

    Returns: (intervals, anomalies, has_open_shift)
    """
    now_utc = now_utc or _now_utc()

    intervals: list[WorkInterval] = []
    anomalies: list[WorktimeAnomaly] = []

    open_in: datetime | None = None
    open_in_local_day: date | None = None

    for ev in events:
        direction = str(getattr(ev, "direction", "") or "").upper().strip()
        ts: datetime = getattr(ev, "ts")

        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        else:
            ts = ts.astimezone(timezone.utc)

        if direction == "IN":
            if open_in is not None:
                anomalies.append(
                    WorktimeAnomaly(
                        code="DUPLICATE_IN",
                        ts_utc=ts,
                        details="IN while previous shift is still open; replacing open IN",
                    )
                )
            open_in = ts
            open_in_local_day = to_warsaw(ts).date()

        elif direction == "OUT":
            if open_in is None:
                anomalies.append(
                    WorktimeAnomaly(
                        code="ORPHAN_OUT",
                        ts_utc=ts,
                        details="OUT without preceding IN; ignored",
                    )
                )
                continue

            if ts < open_in:
                anomalies.append(
                    WorktimeAnomaly(
                        code="OUT_BEFORE_IN",
                        ts_utc=ts,
                        details="OUT earlier than current open IN; ignored",
                    )
                )
                continue

            intervals.append(WorkInterval(in_utc=open_in, out_utc=ts, auto_closed=False))
            open_in = None
            open_in_local_day = None

        else:
            anomalies.append(
                WorktimeAnomaly(
                    code="UNKNOWN_DIRECTION",
                    ts_utc=ts,
                    details=f"direction={direction!r}",
                )
            )

    has_open = open_in is not None
    if has_open and auto_close and open_in is not None:
        # Close open shift at the earlier of:
        # - now (for "today" / live demos)
        # - end of the local day of the IN (to keep historical reporting stable)
        close_at = now_utc
        if auto_close_at_day_end and open_in_local_day is not None:
            close_at = min(close_at, _day_end_utc_for_local_day(open_in_local_day))

        if close_at >= open_in:
            intervals.append(WorkInterval(in_utc=open_in, out_utc=close_at, auto_closed=True))
        else:
            anomalies.append(
                WorktimeAnomaly(
                    code="AUTO_CLOSE_INVALID",
                    ts_utc=close_at,
                    details="auto-close time is earlier than IN",
                )
            )

    return intervals, anomalies, has_open


def split_interval_seconds_by_local_day(in_utc: datetime, out_utc: datetime) -> dict[str, int]:
    """Split a single interval into buckets by local (Europe/Warsaw) day.

    Returns: {"YYYY-MM-DD": seconds}
    """
    if in_utc.tzinfo is None:
        in_utc = in_utc.replace(tzinfo=timezone.utc)
    else:
        in_utc = in_utc.astimezone(timezone.utc)

    if out_utc.tzinfo is None:
        out_utc = out_utc.replace(tzinfo=timezone.utc)
    else:
        out_utc = out_utc.astimezone(timezone.utc)

    if out_utc <= in_utc:
        return {}

    start_local = to_warsaw(in_utc)
    end_local = to_warsaw(out_utc)

    buckets: dict[str, int] = {}

    cur_local = start_local
    while cur_local.date() < end_local.date():
        next_midnight_local = datetime.combine(cur_local.date() + timedelta(days=1), time.min).replace(tzinfo=WARSAW)
        seg_end_local = next_midnight_local

        seg_start_utc = cur_local.astimezone(timezone.utc)
        seg_end_utc = seg_end_local.astimezone(timezone.utc)
        sec = int((seg_end_utc - seg_start_utc).total_seconds())
        if sec > 0:
            buckets[cur_local.date().isoformat()] = buckets.get(cur_local.date().isoformat(), 0) + sec

        cur_local = seg_end_local

    # last segment
    seg_start_utc = cur_local.astimezone(timezone.utc)
    seg_end_utc = end_local.astimezone(timezone.utc)
    sec = int((seg_end_utc - seg_start_utc).total_seconds())
    if sec > 0:
        buckets[end_local.date().isoformat()] = buckets.get(end_local.date().isoformat(), 0) + sec

    return buckets


def hms_from_seconds(total_seconds: int) -> str:
    if total_seconds < 0:
        total_seconds = 0
    hh = total_seconds // 3600
    mm = (total_seconds % 3600) // 60
    ss = total_seconds % 60
    return f"{hh:02d}:{mm:02d}:{ss:02d}"


def iter_local_days(from_date: date, to_date: date):
    cur = from_date
    while cur <= to_date:
        yield cur
        cur = date.fromordinal(cur.toordinal() + 1)
