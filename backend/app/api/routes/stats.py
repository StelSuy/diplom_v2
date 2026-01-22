from __future__ import annotations

from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.crud import event as event_crud
from app.core.time import to_warsaw
from app.schemas.stats import EmployeeDailyStats, DailyWorkStat, WorktimeAnomaly, WeekWorkStat, MonthWorkStat
from app.services.worktime import build_intervals, split_interval_seconds_by_local_day, hms_from_seconds, iter_local_days

router = APIRouter(prefix="/stats", dependencies=[Depends(require_admin)])


@router.get("/employee/{employee_id}")
def employee_stats(employee_id: int, db: Session = Depends(get_db)):
    events = event_crud.list_events_for_employee(db, employee_id)
    if not events:
        raise HTTPException(status_code=404, detail="No events for employee")

    intervals, anomalies, has_open = build_intervals(events, auto_close=True, auto_close_at_day_end=True)

    total_seconds = 0
    intervals_out = []
    for it in intervals:
        dur = int((it.out_utc - it.in_utc).total_seconds())
        if dur < 0:
            dur = 0
        total_seconds += dur
        intervals_out.append(
            {
                "in_utc": it.in_utc.isoformat(),
                "out_utc": it.out_utc.isoformat(),
                "in_local": to_warsaw(it.in_utc).isoformat(),
                "out_local": to_warsaw(it.out_utc).isoformat(),
                "minutes": int(dur // 60),
                "auto_closed": bool(it.auto_closed),
            }
        )

    return {
        "employee_id": employee_id,
        "total_minutes": int(total_seconds // 60),
        "total_hms": hms_from_seconds(int(total_seconds)),
        "intervals": intervals_out,
        "has_open_shift": bool(has_open),
        "anomalies": [
            {
                "code": a.code,
                "ts_utc": a.ts_utc.isoformat() if a.ts_utc else None,
                "ts_local": to_warsaw(a.ts_utc).isoformat() if a.ts_utc else None,
                "details": a.details,
            }
            for a in anomalies
        ],
        "events": [
            {
                "id": ev.id,
                "direction": ev.direction,
                "ts_utc": ev.ts.isoformat(),
                "ts_local": to_warsaw(ev.ts).isoformat(),
                "terminal_id": ev.terminal_id,
            }
            for ev in events
        ],
    }


@router.get("/employee/{employee_id}/daily", response_model=EmployeeDailyStats)
def employee_daily_stats(
    employee_id: int,
    db: Session = Depends(get_db),
    from_date: date = Query(..., description="YYYY-MM-DD (local Europe/Warsaw date)"),
    to_date: date = Query(..., description="YYYY-MM-DD (local Europe/Warsaw date)"),
):
    events = event_crud.list_events_for_employee(db, employee_id)
    if not events:
        raise HTTPException(status_code=404, detail="No events for employee")

    intervals, anomalies, has_open = build_intervals(events, auto_close=True, auto_close_at_day_end=True)

    # --- aggregate per local day ---
    day_work_seconds: dict[str, int] = {}
    day_first_in: dict[str, datetime] = {}
    day_last_out: dict[str, datetime] = {}
    day_auto_closed: dict[str, bool] = {}

    for it in intervals:
        in_local = to_warsaw(it.in_utc)
        out_local = to_warsaw(it.out_utc)

        # split seconds by local day (handles cross-midnight)
        buckets = split_interval_seconds_by_local_day(it.in_utc, it.out_utc)
        for day_key, sec in buckets.items():
            day_work_seconds[day_key] = day_work_seconds.get(day_key, 0) + int(sec)

        # first_in attaches to IN local day
        in_day = in_local.date().isoformat()
        if in_day not in day_first_in or it.in_utc < day_first_in[in_day]:
            day_first_in[in_day] = it.in_utc

        # last_out attaches to OUT local day
        out_day = out_local.date().isoformat()
        if out_day not in day_last_out or it.out_utc > day_last_out[out_day]:
            day_last_out[out_day] = it.out_utc

        if it.auto_closed:
            day_auto_closed[in_day] = True

    # anomalies bucketed by local day (for UI diagnostics)
    anomalies_by_day: dict[str, list[WorktimeAnomaly]] = {}
    for a in anomalies:
        if not a.ts_utc:
            continue
        day_key = to_warsaw(a.ts_utc).date().isoformat()
        anomalies_by_day.setdefault(day_key, []).append(
            WorktimeAnomaly(
                code=a.code,
                ts_utc=a.ts_utc.isoformat() if a.ts_utc else None,
                ts_local=to_warsaw(a.ts_utc).isoformat() if a.ts_utc else None,
                details=a.details,
            )
        )

    # open_shift is only meaningful for the IN day of the last open interval
    open_shift_day: str | None = None
    if has_open:
        for it in reversed(intervals):
            if it.auto_closed:
                open_shift_day = to_warsaw(it.in_utc).date().isoformat()
                break

    items: list[DailyWorkStat] = []
    range_total_seconds = 0

    for d in iter_local_days(from_date, to_date):
        key = d.isoformat()
        ws = int(day_work_seconds.get(key, 0))
        range_total_seconds += ws

        first_in = day_first_in.get(key)
        last_out = day_last_out.get(key)
        open_shift = (open_shift_day == key)

        items.append(
            DailyWorkStat(
                date_local=key,
                worked_minutes=int(ws // 60),
                worked_seconds=ws,
                worked_hms=hms_from_seconds(ws),
                first_in_local=to_warsaw(first_in).isoformat() if first_in else None,
                last_out_local=None if open_shift else (to_warsaw(last_out).isoformat() if last_out else None),
                open_shift=open_shift,
                auto_closed=bool(day_auto_closed.get(key, False)),
                anomalies=anomalies_by_day.get(key, []),
            )
        )

    # --- week / month aggregates ---
    weeks: list[WeekWorkStat] = []
    months_map: dict[str, int] = {}

    cur = from_date
    while cur <= to_date:
        week_start = cur - timedelta(days=cur.weekday())  # Monday
        week_end = week_start + timedelta(days=6)         # Sunday

        a = max(week_start, from_date)
        b = min(week_end, to_date)

        total = 0
        t = a
        while t <= b:
            total += int(day_work_seconds.get(t.isoformat(), 0))
            t = date.fromordinal(t.toordinal() + 1)

        weeks.append(
            WeekWorkStat(
                week_start_local=week_start.isoformat(),
                week_end_local=week_end.isoformat(),
                worked_minutes=int(total // 60),
                worked_hms=hms_from_seconds(int(total)),
            )
        )
        cur = week_end + timedelta(days=1)

    for d in iter_local_days(from_date, to_date):
        ym = d.strftime("%Y-%m")
        months_map[ym] = months_map.get(ym, 0) + int(day_work_seconds.get(d.isoformat(), 0))

    months = [
        MonthWorkStat(month=k, worked_minutes=int(v // 60), worked_hms=hms_from_seconds(int(v)))
        for k, v in sorted(months_map.items())
    ]

    return EmployeeDailyStats(
        employee_id=employee_id,
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat(),
        items=items,
        total_minutes=int(range_total_seconds // 60),
        total_hms=hms_from_seconds(int(range_total_seconds)),
        weeks=weeks,
        months=months,
    )
