"""Tests for thegent.integrations.maintenance_calendar — Connector maintenance calendar.

@trace WL-282
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from thegent.integrations.maintenance_calendar import (
    MaintenanceCalendar,
    MaintenanceWindow,
)


class TestMaintenanceWindow:
    """Test MaintenanceWindow dataclass."""

    @pytest.mark.requirement("WL-282")
    def test_maintenance_window_creation(self) -> None:
        """Can create a MaintenanceWindow with required fields."""
        start = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        end = datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC)
        window = MaintenanceWindow(
            connector="github",
            start=start,
            end=end,
            reason="Database maintenance",
        )

        assert window.connector == "github"
        assert window.start == start
        assert window.end == end
        assert window.reason == "Database maintenance"


class TestMaintenanceCalendar:
    """Test MaintenanceCalendar operations. @trace WL-282"""

    @pytest.fixture
    def calendar(self) -> MaintenanceCalendar:
        """Provide a MaintenanceCalendar instance."""
        return MaintenanceCalendar()

    @pytest.mark.requirement("WL-282")
    def test_add_window(self, calendar: MaintenanceCalendar) -> None:
        """Can add a maintenance window to the calendar."""
        window = MaintenanceWindow(
            connector="github",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Maintenance",
        )
        calendar.add_window(window)

        windows = calendar.upcoming_windows("github", after=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC))
        assert len(windows) == 1
        assert windows[0].connector == "github"

    @pytest.mark.requirement("WL-282")
    def test_is_in_maintenance_true(self, calendar: MaintenanceCalendar) -> None:
        """is_in_maintenance returns True when in active window."""
        window = MaintenanceWindow(
            connector="github",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Maintenance",
        )
        calendar.add_window(window)

        at = datetime(2024, 1, 1, 13, 0, 0, tzinfo=UTC)
        assert calendar.is_in_maintenance("github", at=at) is True

    @pytest.mark.requirement("WL-282")
    def test_is_in_maintenance_false_before(self, calendar: MaintenanceCalendar) -> None:
        """is_in_maintenance returns False before window."""
        window = MaintenanceWindow(
            connector="github",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Maintenance",
        )
        calendar.add_window(window)

        at = datetime(2024, 1, 1, 11, 0, 0, tzinfo=UTC)
        assert calendar.is_in_maintenance("github", at=at) is False

    @pytest.mark.requirement("WL-282")
    def test_is_in_maintenance_false_after(self, calendar: MaintenanceCalendar) -> None:
        """is_in_maintenance returns False after window."""
        window = MaintenanceWindow(
            connector="github",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Maintenance",
        )
        calendar.add_window(window)

        at = datetime(2024, 1, 1, 15, 0, 0, tzinfo=UTC)
        assert calendar.is_in_maintenance("github", at=at) is False

    @pytest.mark.requirement("WL-282")
    def test_is_in_maintenance_default_now(self, calendar: MaintenanceCalendar) -> None:
        """is_in_maintenance uses current UTC time by default."""
        window = MaintenanceWindow(
            connector="github",
            start=datetime(2000, 1, 1, 0, 0, 0, tzinfo=UTC),
            end=datetime(2000, 1, 1, 2, 0, 0, tzinfo=UTC),
            reason="Old maintenance",
        )
        calendar.add_window(window)

        # Window is in the past, should return False
        assert calendar.is_in_maintenance("github") is False

    @pytest.mark.requirement("WL-282")
    def test_is_in_maintenance_boundary_start(self, calendar: MaintenanceCalendar) -> None:
        """is_in_maintenance returns True at window start boundary."""
        window = MaintenanceWindow(
            connector="github",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Maintenance",
        )
        calendar.add_window(window)

        at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        assert calendar.is_in_maintenance("github", at=at) is True

    @pytest.mark.requirement("WL-282")
    def test_is_in_maintenance_boundary_end(self, calendar: MaintenanceCalendar) -> None:
        """is_in_maintenance returns True at window end boundary."""
        window = MaintenanceWindow(
            connector="github",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Maintenance",
        )
        calendar.add_window(window)

        at = datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC)
        assert calendar.is_in_maintenance("github", at=at) is True

    @pytest.mark.requirement("WL-282")
    def test_is_in_maintenance_wrong_connector(self, calendar: MaintenanceCalendar) -> None:
        """is_in_maintenance returns False for different connector."""
        window = MaintenanceWindow(
            connector="github",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Maintenance",
        )
        calendar.add_window(window)

        at = datetime(2024, 1, 1, 13, 0, 0, tzinfo=UTC)
        assert calendar.is_in_maintenance("linear", at=at) is False

    @pytest.mark.requirement("WL-282")
    def test_upcoming_windows_single(self, calendar: MaintenanceCalendar) -> None:
        """upcoming_windows returns single upcoming window."""
        window = MaintenanceWindow(
            connector="github",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Maintenance",
        )
        calendar.add_window(window)

        after = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        windows = calendar.upcoming_windows("github", after=after)

        assert len(windows) == 1
        assert windows[0].connector == "github"

    @pytest.mark.requirement("WL-282")
    def test_upcoming_windows_sorted(self, calendar: MaintenanceCalendar) -> None:
        """upcoming_windows returns windows sorted by start time."""
        window1 = MaintenanceWindow(
            connector="github",
            start=datetime(2024, 1, 2, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 2, 14, 0, 0, tzinfo=UTC),
            reason="Maintenance 2",
        )
        window2 = MaintenanceWindow(
            connector="github",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Maintenance 1",
        )
        calendar.add_window(window1)
        calendar.add_window(window2)

        after = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        windows = calendar.upcoming_windows("github", after=after)

        assert len(windows) == 2
        assert windows[0].start < windows[1].start

    @pytest.mark.requirement("WL-282")
    def test_upcoming_windows_filters_by_connector(self, calendar: MaintenanceCalendar) -> None:
        """upcoming_windows only returns windows for specified connector."""
        window_github = MaintenanceWindow(
            connector="github",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Github maintenance",
        )
        window_linear = MaintenanceWindow(
            connector="linear",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Linear maintenance",
        )
        calendar.add_window(window_github)
        calendar.add_window(window_linear)

        after = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        windows = calendar.upcoming_windows("github", after=after)

        assert len(windows) == 1
        assert windows[0].connector == "github"

    @pytest.mark.requirement("WL-282")
    def test_upcoming_windows_filters_by_after(self, calendar: MaintenanceCalendar) -> None:
        """upcoming_windows filters windows that start after 'after' time."""
        window_past = MaintenanceWindow(
            connector="github",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Past maintenance",
        )
        window_future = MaintenanceWindow(
            connector="github",
            start=datetime(2024, 1, 2, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 2, 14, 0, 0, tzinfo=UTC),
            reason="Future maintenance",
        )
        calendar.add_window(window_past)
        calendar.add_window(window_future)

        after = datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC)
        windows = calendar.upcoming_windows("github", after=after)

        assert len(windows) == 1
        assert windows[0].start == datetime(2024, 1, 2, 12, 0, 0, tzinfo=UTC)

    @pytest.mark.requirement("WL-282")
    def test_upcoming_windows_default_after_now(self, calendar: MaintenanceCalendar) -> None:
        """upcoming_windows uses current UTC time by default."""
        window = MaintenanceWindow(
            connector="github",
            start=datetime(2000, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2000, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Old maintenance",
        )
        calendar.add_window(window)

        windows = calendar.upcoming_windows("github")
        assert len(windows) == 0

    @pytest.mark.requirement("WL-282")
    def test_load_from_config_single_window(self, calendar: MaintenanceCalendar) -> None:
        """Can load maintenance windows from config dict."""
        config = [
            {
                "connector": "github",
                "start": "2024-01-01T12:00:00+00:00",
                "end": "2024-01-01T14:00:00+00:00",
                "reason": "Database maintenance",
            }
        ]
        calendar.load_from_config(config)

        after = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        windows = calendar.upcoming_windows("github", after=after)
        assert len(windows) == 1
        assert windows[0].connector == "github"
        assert windows[0].reason == "Database maintenance"

    @pytest.mark.requirement("WL-282")
    def test_load_from_config_multiple_windows(self, calendar: MaintenanceCalendar) -> None:
        """Can load multiple maintenance windows from config."""
        config = [
            {
                "connector": "github",
                "start": "2024-01-01T12:00:00+00:00",
                "end": "2024-01-01T14:00:00+00:00",
                "reason": "Maintenance 1",
            },
            {
                "connector": "linear",
                "start": "2024-01-02T12:00:00+00:00",
                "end": "2024-01-02T14:00:00+00:00",
                "reason": "Maintenance 2",
            },
        ]
        calendar.load_from_config(config)

        after = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        github_windows = calendar.upcoming_windows("github", after=after)
        linear_windows = calendar.upcoming_windows("linear", after=after)

        assert len(github_windows) == 1
        assert len(linear_windows) == 1

    @pytest.mark.requirement("WL-282")
    def test_load_from_config_missing_keys(self, calendar: MaintenanceCalendar) -> None:
        """load_from_config raises ValueError for missing required keys."""
        config = [
            {
                "connector": "github",
                "start": "2024-01-01T12:00:00+00:00",
            }
        ]

        with pytest.raises(ValueError, match="missing required keys"):
            calendar.load_from_config(config)

    @pytest.mark.requirement("WL-282")
    def test_load_from_config_invalid_datetime(self, calendar: MaintenanceCalendar) -> None:
        """load_from_config raises ValueError for invalid datetime format."""
        config = [
            {
                "connector": "github",
                "start": "not-a-datetime",
                "end": "2024-01-01T14:00:00+00:00",
                "reason": "Maintenance",
            }
        ]

        with pytest.raises(ValueError, match="Invalid datetime format"):
            calendar.load_from_config(config)

    @pytest.mark.requirement("WL-282")
    def test_list_connectors_empty(self, calendar: MaintenanceCalendar) -> None:
        """list_connectors returns empty list for empty calendar."""
        connectors = calendar.list_connectors()
        assert connectors == []

    @pytest.mark.requirement("WL-282")
    def test_list_connectors_single(self, calendar: MaintenanceCalendar) -> None:
        """list_connectors returns single connector."""
        window = MaintenanceWindow(
            connector="github",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Maintenance",
        )
        calendar.add_window(window)

        connectors = calendar.list_connectors()
        assert connectors == ["github"]

    @pytest.mark.requirement("WL-282")
    def test_list_connectors_multiple_sorted(self, calendar: MaintenanceCalendar) -> None:
        """list_connectors returns all connectors, sorted alphabetically."""
        window_github = MaintenanceWindow(
            connector="github",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Maintenance",
        )
        window_slack = MaintenanceWindow(
            connector="slack",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Maintenance",
        )
        window_linear = MaintenanceWindow(
            connector="linear",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Maintenance",
        )
        calendar.add_window(window_github)
        calendar.add_window(window_slack)
        calendar.add_window(window_linear)

        connectors = calendar.list_connectors()
        assert connectors == ["github", "linear", "slack"]

    @pytest.mark.requirement("WL-282")
    def test_list_connectors_duplicates_deduplicated(self, calendar: MaintenanceCalendar) -> None:
        """list_connectors returns unique connectors even with multiple windows."""
        window1 = MaintenanceWindow(
            connector="github",
            start=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 14, 0, 0, tzinfo=UTC),
            reason="Maintenance 1",
        )
        window2 = MaintenanceWindow(
            connector="github",
            start=datetime(2024, 1, 2, 12, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 2, 14, 0, 0, tzinfo=UTC),
            reason="Maintenance 2",
        )
        calendar.add_window(window1)
        calendar.add_window(window2)

        connectors = calendar.list_connectors()
        assert connectors == ["github"]
