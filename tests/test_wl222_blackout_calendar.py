"""Tests for WL-222: Blackout Calendar Support.

Verifies blackout window management, membership testing, and active window queries.

# @trace WL-222
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest


def _utc_dt(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


@pytest.mark.requirement("WL-222")
class TestBlackoutCalendar:
    """WL-222: Blackout calendar for operational scheduling."""

    def test_add_window_creates_blackout(self):
        """# @trace WL-222 — add() creates a blackout window."""
        from thegent.integrations.blackout_calendar import BlackoutCalendar

        cal = BlackoutCalendar()
        start = _utc_dt(2026, 2, 22, 10, 0)
        end = _utc_dt(2026, 2, 22, 12, 0)

        window = cal.add("maint", start, end)

        assert window.name == "maint"
        assert window.start == start
        assert window.end == end

    def test_add_window_duplicate_raises_error(self):
        """# @trace WL-222 — add() raises ValueError for duplicate name."""
        from thegent.integrations.blackout_calendar import BlackoutCalendar

        cal = BlackoutCalendar()
        start = _utc_dt(2026, 2, 22, 10, 0)
        end = _utc_dt(2026, 2, 22, 12, 0)

        cal.add("maint", start, end)

        with pytest.raises(ValueError, match="already exists"):
            cal.add("maint", start, end)

    def test_add_window_end_before_start_raises_error(self):
        """# @trace WL-222 — add() raises ValueError if end <= start."""
        from thegent.integrations.blackout_calendar import BlackoutCalendar

        cal = BlackoutCalendar()
        start = _utc_dt(2026, 2, 22, 12, 0)
        end = _utc_dt(2026, 2, 22, 10, 0)

        with pytest.raises(ValueError, match="after start time"):
            cal.add("bad", start, end)

    def test_add_window_end_equal_start_raises_error(self):
        """# @trace WL-222 — add() raises ValueError if end == start."""
        from thegent.integrations.blackout_calendar import BlackoutCalendar

        cal = BlackoutCalendar()
        dt = _utc_dt(2026, 2, 22, 10, 0)

        with pytest.raises(ValueError, match="after start time"):
            cal.add("bad", dt, dt)

    def test_is_blacked_out_true_inside_window(self):
        """# @trace WL-222 — is_blacked_out() returns True for dt inside window."""
        from thegent.integrations.blackout_calendar import BlackoutCalendar

        cal = BlackoutCalendar()
        start = _utc_dt(2026, 2, 22, 10, 0)
        end = _utc_dt(2026, 2, 22, 12, 0)
        cal.add("maint", start, end)

        test_dt = _utc_dt(2026, 2, 22, 11, 0)

        assert cal.is_blacked_out(test_dt) is True

    def test_is_blacked_out_false_outside_window(self):
        """# @trace WL-222 — is_blacked_out() returns False for dt outside window."""
        from thegent.integrations.blackout_calendar import BlackoutCalendar

        cal = BlackoutCalendar()
        start = _utc_dt(2026, 2, 22, 10, 0)
        end = _utc_dt(2026, 2, 22, 12, 0)
        cal.add("maint", start, end)

        test_dt = _utc_dt(2026, 2, 22, 13, 0)

        assert cal.is_blacked_out(test_dt) is False

    def test_is_blacked_out_false_before_window(self):
        """# @trace WL-222 — is_blacked_out() returns False for dt before window."""
        from thegent.integrations.blackout_calendar import BlackoutCalendar

        cal = BlackoutCalendar()
        start = _utc_dt(2026, 2, 22, 10, 0)
        end = _utc_dt(2026, 2, 22, 12, 0)
        cal.add("maint", start, end)

        test_dt = _utc_dt(2026, 2, 22, 9, 0)

        assert cal.is_blacked_out(test_dt) is False

    def test_is_blacked_out_true_at_start_time(self):
        """# @trace WL-222 — is_blacked_out() returns True for dt at start boundary."""
        from thegent.integrations.blackout_calendar import BlackoutCalendar

        cal = BlackoutCalendar()
        start = _utc_dt(2026, 2, 22, 10, 0)
        end = _utc_dt(2026, 2, 22, 12, 0)
        cal.add("maint", start, end)

        assert cal.is_blacked_out(start) is True

    def test_is_blacked_out_false_at_end_time(self):
        """# @trace WL-222 — is_blacked_out() returns False for dt at end boundary."""
        from thegent.integrations.blackout_calendar import BlackoutCalendar

        cal = BlackoutCalendar()
        start = _utc_dt(2026, 2, 22, 10, 0)
        end = _utc_dt(2026, 2, 22, 12, 0)
        cal.add("maint", start, end)

        assert cal.is_blacked_out(end) is False

    def test_is_blacked_out_multiple_windows(self):
        """# @trace WL-222 — is_blacked_out() returns True if dt in any window."""
        from thegent.integrations.blackout_calendar import BlackoutCalendar

        cal = BlackoutCalendar()
        cal.add("maint1", _utc_dt(2026, 2, 22, 10, 0), _utc_dt(2026, 2, 22, 12, 0))
        cal.add("maint2", _utc_dt(2026, 2, 22, 14, 0), _utc_dt(2026, 2, 22, 16, 0))

        assert cal.is_blacked_out(_utc_dt(2026, 2, 22, 11, 0)) is True
        assert cal.is_blacked_out(_utc_dt(2026, 2, 22, 15, 0)) is True
        assert cal.is_blacked_out(_utc_dt(2026, 2, 22, 13, 0)) is False

    def test_active_windows_returns_matching_windows(self):
        """# @trace WL-222 — active_windows() returns windows containing dt."""
        from thegent.integrations.blackout_calendar import BlackoutCalendar

        cal = BlackoutCalendar()
        cal.add("maint1", _utc_dt(2026, 2, 22, 10, 0), _utc_dt(2026, 2, 22, 12, 0))
        cal.add("maint2", _utc_dt(2026, 2, 22, 14, 0), _utc_dt(2026, 2, 22, 16, 0))

        active = cal.active_windows(_utc_dt(2026, 2, 22, 11, 0))

        assert len(active) == 1
        assert active[0].name == "maint1"

    def test_active_windows_no_matching_windows(self):
        """# @trace WL-222 — active_windows() returns empty list when no matches."""
        from thegent.integrations.blackout_calendar import BlackoutCalendar

        cal = BlackoutCalendar()
        cal.add("maint", _utc_dt(2026, 2, 22, 10, 0), _utc_dt(2026, 2, 22, 12, 0))

        active = cal.active_windows(_utc_dt(2026, 2, 22, 13, 0))

        assert active == []

    def test_active_windows_sorted_by_start_time(self):
        """# @trace WL-222 — active_windows() returns results sorted by start time."""
        from thegent.integrations.blackout_calendar import BlackoutCalendar

        cal = BlackoutCalendar()
        # Add in non-chronological order
        cal.add("maint3", _utc_dt(2026, 2, 22, 10, 0), _utc_dt(2026, 2, 22, 14, 0))
        cal.add("maint1", _utc_dt(2026, 2, 22, 10, 30), _utc_dt(2026, 2, 22, 12, 0))
        cal.add("maint2", _utc_dt(2026, 2, 22, 11, 0), _utc_dt(2026, 2, 22, 13, 0))

        active = cal.active_windows(_utc_dt(2026, 2, 22, 11, 30))

        names = [w.name for w in active]
        # Should be sorted by start time: maint3 (10:00), maint1 (10:30), maint2 (11:00)
        assert names == ["maint3", "maint1", "maint2"]

    def test_all_windows_returns_all(self):
        """# @trace WL-222 — all_windows() returns all windows."""
        from thegent.integrations.blackout_calendar import BlackoutCalendar

        cal = BlackoutCalendar()
        cal.add("maint1", _utc_dt(2026, 2, 22, 10, 0), _utc_dt(2026, 2, 22, 12, 0))
        cal.add("maint2", _utc_dt(2026, 2, 22, 14, 0), _utc_dt(2026, 2, 22, 16, 0))
        cal.add("maint3", _utc_dt(2026, 2, 22, 18, 0), _utc_dt(2026, 2, 22, 20, 0))

        all_windows = cal.all_windows()

        assert len(all_windows) == 3

    def test_all_windows_sorted_by_start_time(self):
        """# @trace WL-222 — all_windows() returns results sorted by start time."""
        from thegent.integrations.blackout_calendar import BlackoutCalendar

        cal = BlackoutCalendar()
        # Add in non-chronological order
        cal.add("maint3", _utc_dt(2026, 2, 22, 18, 0), _utc_dt(2026, 2, 22, 20, 0))
        cal.add("maint1", _utc_dt(2026, 2, 22, 10, 0), _utc_dt(2026, 2, 22, 12, 0))
        cal.add("maint2", _utc_dt(2026, 2, 22, 14, 0), _utc_dt(2026, 2, 22, 16, 0))

        all_windows = cal.all_windows()

        names = [w.name for w in all_windows]
        assert names == ["maint1", "maint2", "maint3"]

    def test_all_windows_empty_calendar(self):
        """# @trace WL-222 — all_windows() returns empty list for empty calendar."""
        from thegent.integrations.blackout_calendar import BlackoutCalendar

        cal = BlackoutCalendar()

        all_windows = cal.all_windows()

        assert all_windows == []
