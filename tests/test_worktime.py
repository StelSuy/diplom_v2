"""
Юніт-тести для app/services/worktime.py

Покривають:
- build_intervals(): нормальні інтервали, аномалії, авто-закриття, розбивка по дням
- split_interval_seconds_by_local_day(): однодобові і міжнічні інтервали
- hms_from_seconds(): форматування
- iter_local_days(): ітерація по датах
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from app.services.worktime import (
    WorkInterval,
    WorktimeAnomaly,
    build_intervals,
    hms_from_seconds,
    iter_local_days,
    split_interval_seconds_by_local_day,
)
from app.core.time import WARSAW


# ─── Helpers ─────────────────────────────────────────────────────────────────

def utc(year, month, day, hour=0, minute=0, second=0) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


def warsaw(year, month, day, hour=0, minute=0, second=0) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=WARSAW)


class FakeEvent:
    def __init__(self, direction: str, ts: datetime):
        self.direction = direction
        self.ts = ts


def events(*pairs) -> list[FakeEvent]:
    """Зручний конструктор: events(('IN', utc(...)), ('OUT', utc(...)))"""
    return [FakeEvent(d, t) for d, t in pairs]


# ─── hms_from_seconds ────────────────────────────────────────────────────────

class TestHmsFromSeconds:
    def test_zero(self):
        assert hms_from_seconds(0) == "00:00:00"

    def test_one_second(self):
        assert hms_from_seconds(1) == "00:00:01"

    def test_one_minute(self):
        assert hms_from_seconds(60) == "00:01:00"

    def test_one_hour(self):
        assert hms_from_seconds(3600) == "01:00:00"

    def test_mixed(self):
        assert hms_from_seconds(3661) == "01:01:01"

    def test_over_24_hours(self):
        assert hms_from_seconds(90000) == "25:00:00"

    def test_negative_clamps_to_zero(self):
        assert hms_from_seconds(-100) == "00:00:00"

    def test_large_value(self):
        result = hms_from_seconds(86400)  # 24 год
        assert result == "24:00:00"


# ─── iter_local_days ─────────────────────────────────────────────────────────

class TestIterLocalDays:
    def test_single_day(self):
        d = date(2024, 1, 15)
        result = list(iter_local_days(d, d))
        assert result == [d]

    def test_three_days(self):
        result = list(iter_local_days(date(2024, 3, 1), date(2024, 3, 3)))
        assert result == [date(2024, 3, 1), date(2024, 3, 2), date(2024, 3, 3)]

    def test_month_boundary(self):
        result = list(iter_local_days(date(2024, 1, 30), date(2024, 2, 1)))
        assert len(result) == 3
        assert result[-1] == date(2024, 2, 1)

    def test_from_after_to_returns_empty(self):
        result = list(iter_local_days(date(2024, 5, 10), date(2024, 5, 9)))
        assert result == []


# ─── split_interval_seconds_by_local_day ────────────────────────────────────

class TestSplitIntervalByDay:
    def test_same_day_single_bucket(self):
        in_utc = warsaw(2024, 6, 1, 9, 0).astimezone(timezone.utc)
        out_utc = warsaw(2024, 6, 1, 17, 0).astimezone(timezone.utc)
        result = split_interval_seconds_by_local_day(in_utc, out_utc)
        assert len(result) == 1
        assert result.get("2024-06-01") == 8 * 3600

    def test_cross_midnight_splits_into_two_days(self):
        in_utc = warsaw(2024, 6, 1, 22, 0).astimezone(timezone.utc)
        out_utc = warsaw(2024, 6, 2, 2, 0).astimezone(timezone.utc)
        result = split_interval_seconds_by_local_day(in_utc, out_utc)
        assert len(result) == 2
        assert result["2024-06-01"] == 2 * 3600   # 22:00–00:00
        assert result["2024-06-02"] == 2 * 3600   # 00:00–02:00

    def test_cross_two_midnights(self):
        in_utc = warsaw(2024, 6, 1, 23, 0).astimezone(timezone.utc)
        out_utc = warsaw(2024, 6, 3, 1, 0).astimezone(timezone.utc)
        result = split_interval_seconds_by_local_day(in_utc, out_utc)
        assert "2024-06-01" in result
        assert "2024-06-02" in result
        assert "2024-06-03" in result
        total = sum(result.values())
        expected = int((out_utc - in_utc).total_seconds())
        assert abs(total - expected) <= 1  # ±1 сек через округлення

    def test_zero_duration_returns_empty(self):
        t = warsaw(2024, 6, 1, 10, 0).astimezone(timezone.utc)
        result = split_interval_seconds_by_local_day(t, t)
        assert result == {}

    def test_out_before_in_returns_empty(self):
        in_utc = warsaw(2024, 6, 1, 12, 0).astimezone(timezone.utc)
        out_utc = warsaw(2024, 6, 1, 10, 0).astimezone(timezone.utc)
        result = split_interval_seconds_by_local_day(in_utc, out_utc)
        assert result == {}

    def test_naive_datetimes_treated_as_utc(self):
        in_utc = datetime(2024, 6, 1, 6, 0, 0)   # naive → UTC
        out_utc = datetime(2024, 6, 1, 14, 0, 0)
        result = split_interval_seconds_by_local_day(in_utc, out_utc)
        assert sum(result.values()) == 8 * 3600

    def test_total_seconds_match_duration(self):
        in_utc = warsaw(2024, 1, 15, 8, 30).astimezone(timezone.utc)
        out_utc = warsaw(2024, 1, 15, 17, 45).astimezone(timezone.utc)
        result = split_interval_seconds_by_local_day(in_utc, out_utc)
        expected = int((out_utc - in_utc).total_seconds())
        assert sum(result.values()) == expected


# ─── build_intervals — нормальні сценарії ────────────────────────────────────

class TestBuildIntervalsNormal:
    def test_single_in_out_pair(self):
        evs = events(
            ("IN",  utc(2024, 6, 1, 8, 0)),
            ("OUT", utc(2024, 6, 1, 17, 0)),
        )
        intervals, anomalies, has_open = build_intervals(evs, auto_close=False)
        assert len(intervals) == 1
        assert len(anomalies) == 0
        assert has_open is False
        assert intervals[0].in_utc == utc(2024, 6, 1, 8, 0)
        assert intervals[0].out_utc == utc(2024, 6, 1, 17, 0)
        assert intervals[0].auto_closed is False

    def test_multiple_pairs(self):
        evs = events(
            ("IN",  utc(2024, 6, 1, 8, 0)),
            ("OUT", utc(2024, 6, 1, 12, 0)),
            ("IN",  utc(2024, 6, 1, 13, 0)),
            ("OUT", utc(2024, 6, 1, 17, 0)),
        )
        intervals, anomalies, has_open = build_intervals(evs, auto_close=False)
        assert len(intervals) == 2
        assert len(anomalies) == 0
        assert has_open is False

    def test_interval_duration_correct(self):
        evs = events(
            ("IN",  utc(2024, 6, 1, 9, 0)),
            ("OUT", utc(2024, 6, 1, 11, 30)),
        )
        intervals, _, _ = build_intervals(evs, auto_close=False)
        duration = (intervals[0].out_utc - intervals[0].in_utc).total_seconds()
        assert duration == 2.5 * 3600

    def test_case_insensitive_direction(self):
        evs = events(
            ("in",  utc(2024, 6, 1, 9, 0)),
            ("out", utc(2024, 6, 1, 17, 0)),
        )
        intervals, anomalies, _ = build_intervals(evs, auto_close=False)
        assert len(intervals) == 1
        assert len(anomalies) == 0

    def test_naive_ts_treated_as_utc(self):
        in_naive = datetime(2024, 6, 1, 8, 0)
        out_naive = datetime(2024, 6, 1, 17, 0)
        evs = events(("IN", in_naive), ("OUT", out_naive))
        intervals, anomalies, _ = build_intervals(evs, auto_close=False)
        assert len(intervals) == 1
        assert len(anomalies) == 0


# ─── build_intervals — аномалії ──────────────────────────────────────────────

class TestBuildIntervalsAnomalies:
    def test_out_without_in_is_orphan_out(self):
        evs = events(("OUT", utc(2024, 6, 1, 10, 0)))
        intervals, anomalies, has_open = build_intervals(evs, auto_close=False)
        assert len(intervals) == 0
        assert len(anomalies) == 1
        assert anomalies[0].code == "ORPHAN_OUT"
        assert has_open is False

    def test_duplicate_in_creates_anomaly(self):
        evs = events(
            ("IN", utc(2024, 6, 1, 8, 0)),
            ("IN", utc(2024, 6, 1, 9, 0)),   # дублікат
        )
        intervals, anomalies, has_open = build_intervals(evs, auto_close=False)
        assert any(a.code == "DUPLICATE_IN" for a in anomalies)
        assert has_open is True

    def test_duplicate_in_replaces_open_in(self):
        """Другий IN замінює перший — інтервал відраховується від другого IN."""
        evs = events(
            ("IN",  utc(2024, 6, 1, 8, 0)),
            ("IN",  utc(2024, 6, 1, 9, 0)),   # замінює
            ("OUT", utc(2024, 6, 1, 17, 0)),
        )
        intervals, anomalies, _ = build_intervals(evs, auto_close=False)
        assert len(intervals) == 1
        assert intervals[0].in_utc == utc(2024, 6, 1, 9, 0)

    def test_out_before_in_is_anomaly(self):
        evs = events(
            ("IN",  utc(2024, 6, 1, 10, 0)),
            ("OUT", utc(2024, 6, 1, 9, 0)),   # раніше за IN
        )
        intervals, anomalies, _ = build_intervals(evs, auto_close=False)
        assert any(a.code == "OUT_BEFORE_IN" for a in anomalies)
        assert len(intervals) == 0

    def test_unknown_direction_is_anomaly(self):
        evs = events(("UNKNOWN", utc(2024, 6, 1, 10, 0)))
        _, anomalies, _ = build_intervals(evs, auto_close=False)
        assert any(a.code == "UNKNOWN_DIRECTION" for a in anomalies)

    def test_empty_events_returns_empty(self):
        intervals, anomalies, has_open = build_intervals([], auto_close=False)
        assert intervals == []
        assert anomalies == []
        assert has_open is False

    def test_multiple_anomalies_collected(self):
        evs = events(
            ("OUT", utc(2024, 6, 1, 7, 0)),   # ORPHAN_OUT
            ("IN",  utc(2024, 6, 1, 8, 0)),
            ("IN",  utc(2024, 6, 1, 9, 0)),   # DUPLICATE_IN
        )
        _, anomalies, _ = build_intervals(evs, auto_close=False)
        codes = [a.code for a in anomalies]
        assert "ORPHAN_OUT" in codes
        assert "DUPLICATE_IN" in codes


# ─── build_intervals — auto_close ────────────────────────────────────────────

class TestBuildIntervalsAutoClose:
    def test_open_shift_auto_closed(self):
        evs = events(("IN", utc(2024, 6, 1, 8, 0)))
        now = utc(2024, 6, 1, 12, 0)
        intervals, _, has_open = build_intervals(evs, auto_close=True, now_utc=now)
        assert has_open is True
        assert len(intervals) == 1
        assert intervals[0].auto_closed is True

    def test_auto_close_at_day_end(self):
        """Авто-закриття не пізніше кінця локального дня."""
        # Зміна відкрита вранці, now — наступний день
        evs = events(("IN", warsaw(2024, 6, 1, 8, 0).astimezone(timezone.utc)))
        now = utc(2024, 6, 2, 10, 0)   # наступний день
        intervals, _, _ = build_intervals(
            evs, auto_close=True, auto_close_at_day_end=True, now_utc=now
        )
        # Закривається не пізніше 23:59:59 2024-06-01 по Варшаві
        close_warsaw = intervals[0].out_utc.astimezone(WARSAW)
        assert close_warsaw.date() == date(2024, 6, 1)

    def test_open_shift_without_auto_close(self):
        evs = events(("IN", utc(2024, 6, 1, 8, 0)))
        intervals, _, has_open = build_intervals(evs, auto_close=False)
        assert has_open is True
        assert len(intervals) == 0  # інтервал не генерується

    def test_closed_shift_not_auto_closed(self):
        evs = events(
            ("IN",  utc(2024, 6, 1, 8, 0)),
            ("OUT", utc(2024, 6, 1, 17, 0)),
        )
        intervals, _, has_open = build_intervals(evs, auto_close=True, now_utc=utc(2024, 6, 1, 20, 0))
        assert has_open is False
        assert intervals[0].auto_closed is False

    def test_auto_close_uses_now_not_future(self):
        """Авто-закриття не може бути після now_utc."""
        evs = events(("IN", utc(2024, 6, 1, 8, 0)))
        now = utc(2024, 6, 1, 10, 0)
        intervals, _, _ = build_intervals(evs, auto_close=True, now_utc=now)
        assert intervals[0].out_utc <= now


# ─── build_intervals — реалістичні сценарії ──────────────────────────────────

class TestBuildIntervalsRealistic:
    def test_full_work_week(self):
        """Пн–Пт, 8 год/день — 5 нормальних інтервалів."""
        evs = []
        for day in range(1, 6):
            evs.append(FakeEvent("IN",  warsaw(2024, 1, day + 6, 8, 0).astimezone(timezone.utc)))
            evs.append(FakeEvent("OUT", warsaw(2024, 1, day + 6, 16, 0).astimezone(timezone.utc)))
        intervals, anomalies, has_open = build_intervals(evs, auto_close=False)
        assert len(intervals) == 5
        assert len(anomalies) == 0
        assert has_open is False

    def test_overnight_shift_single_interval(self):
        """Нічна зміна: IN 23:00, OUT 07:00 наступного дня."""
        evs = events(
            ("IN",  warsaw(2024, 6, 1, 23, 0).astimezone(timezone.utc)),
            ("OUT", warsaw(2024, 6, 2,  7, 0).astimezone(timezone.utc)),
        )
        intervals, anomalies, _ = build_intervals(evs, auto_close=False)
        assert len(intervals) == 1
        assert len(anomalies) == 0
        duration = (intervals[0].out_utc - intervals[0].in_utc).total_seconds()
        assert duration == 8 * 3600

    def test_forgotten_checkout_then_next_day_in(self):
        """Забули вийти → DUPLICATE_IN наступного дня."""
        evs = events(
            ("IN",  warsaw(2024, 6, 1, 8, 0).astimezone(timezone.utc)),
            # OUT забули
            ("IN",  warsaw(2024, 6, 2, 8, 0).astimezone(timezone.utc)),
            ("OUT", warsaw(2024, 6, 2, 16, 0).astimezone(timezone.utc)),
        )
        intervals, anomalies, has_open = build_intervals(evs, auto_close=False)
        assert any(a.code == "DUPLICATE_IN" for a in anomalies)
        # Останній інтервал — 2-й день
        assert len(intervals) == 1
        assert intervals[0].in_utc.astimezone(WARSAW).date() == date(2024, 6, 2)

    def test_anomaly_ts_utc_preserved(self):
        """Аномалія зберігає правильний UTC timestamp."""
        orphan_ts = utc(2024, 6, 1, 10, 0)
        evs = events(("OUT", orphan_ts))
        _, anomalies, _ = build_intervals(evs, auto_close=False)
        assert anomalies[0].ts_utc == orphan_ts
