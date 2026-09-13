"""Unit tests for orchestration lane model (WP-1002, FR-019).

Traces to: FR-019 (Adaptive load controls with critical lane protection).
"""

from __future__ import annotations

from thegent.orchestration.execution.lanes import (
    LANE_PRIORITIES,
    LANE_URGENCY,
    URGENCY_CRITICAL,
    URGENCY_HIGH,
    URGENCY_LOW,
    URGENCY_NORMAL,
    Lane,
    LaneModel,
)


class TestLaneModel:
    """Priority and urgency lane model."""

    def test_critical_has_highest_priority(self) -> None:
        assert LaneModel.get_priority("critical") == 0

    def test_standard_priority(self) -> None:
        assert LaneModel.get_priority("standard") == 10

    def test_recovery_priority(self) -> None:
        assert LaneModel.get_priority("recovery") == 20

    def test_background_has_lowest_priority(self) -> None:
        assert LaneModel.get_priority("background") == 100

    def test_unknown_lane_default_priority(self) -> None:
        assert LaneModel.get_priority("unknown") == 50

    def test_empty_lane_default_priority(self) -> None:
        assert LaneModel.get_priority("") == 50

    def test_case_insensitive(self) -> None:
        assert LaneModel.get_priority("CRITICAL") == 0
        assert LaneModel.get_priority("Standard") == 10


class TestLaneUrgency:
    """Urgency tier mapping."""

    def test_critical_urgency(self) -> None:
        assert LaneModel.get_urgency("critical") == URGENCY_CRITICAL

    def test_standard_urgency(self) -> None:
        assert LaneModel.get_urgency("standard") == URGENCY_NORMAL

    def test_recovery_urgency(self) -> None:
        assert LaneModel.get_urgency("recovery") == URGENCY_HIGH

    def test_background_urgency(self) -> None:
        assert LaneModel.get_urgency("background") == URGENCY_LOW


class TestCriticalLaneProtection:
    """FR-019: Critical lane bypasses overload rejection."""

    def test_critical_is_protected(self) -> None:
        assert LaneModel.is_protected("critical") is True

    def test_standard_not_protected(self) -> None:
        assert LaneModel.is_protected("standard") is False

    def test_recovery_not_protected(self) -> None:
        assert LaneModel.is_protected("recovery") is False

    def test_background_not_protected(self) -> None:
        assert LaneModel.is_protected("background") is False


class TestSortTasks:
    """Task ordering by lane priority."""

    def test_critical_before_standard(self) -> None:
        tasks = [
            {"lane": "standard", "started_at_utc": "2025-01-01T00:00:00Z"},
            {"lane": "critical", "started_at_utc": "2025-01-01T00:01:00Z"},
        ]
        sorted_tasks = LaneModel.sort_tasks(tasks)
        assert sorted_tasks[0]["lane"] == "critical"

    def test_standard_before_background(self) -> None:
        tasks = [
            {"lane": "background", "started_at_utc": "2025-01-01T00:00:00Z"},
            {"lane": "standard", "started_at_utc": "2025-01-01T00:01:00Z"},
        ]
        sorted_tasks = LaneModel.sort_tasks(tasks)
        assert sorted_tasks[0]["lane"] == "standard"

    def test_same_lane_sorted_by_time(self) -> None:
        tasks = [
            {"lane": "standard", "started_at_utc": "2025-01-01T00:01:00Z"},
            {"lane": "standard", "started_at_utc": "2025-01-01T00:00:00Z"},
        ]
        sorted_tasks = LaneModel.sort_tasks(tasks)
        assert sorted_tasks[0]["started_at_utc"] == "2025-01-01T00:00:00Z"

    def test_default_lane_standard(self) -> None:
        tasks = [{"started_at_utc": "2025-01-01T00:00:00Z"}]
        sorted_tasks = LaneModel.sort_tasks(tasks)
        assert len(sorted_tasks) == 1


class TestCheckCapacity:
    """FR-019: Reserved slots for critical lane; starvation prevention."""

    def test_critical_always_has_capacity(self) -> None:
        assert LaneModel.check_capacity("critical", active_count=99, total_capacity=10)
        assert LaneModel.check_capacity("critical", active_count=0, total_capacity=1)

    def test_standard_has_capacity_when_slots_available(self) -> None:
        assert LaneModel.check_capacity("standard", active_count=5, total_capacity=10)
        assert LaneModel.check_capacity("standard", active_count=7, total_capacity=10)

    def test_standard_no_capacity_when_reserved_exhausted(self) -> None:
        # capacity=10, reserved=2 -> available=8 for non-critical; 8 active = at limit
        assert LaneModel.check_capacity("standard", active_count=7, total_capacity=10)
        assert not LaneModel.check_capacity("standard", active_count=8, total_capacity=10)

    def test_small_capacity_floor(self) -> None:
        assert LaneModel.check_capacity("standard", active_count=0, total_capacity=1)


class TestLaneEnum:
    """Canonical lane enum."""

    def test_lane_values(self) -> None:
        assert Lane.CRITICAL == "critical"
        assert Lane.STANDARD == "standard"
        assert Lane.RECOVERY == "recovery"
        assert Lane.BACKGROUND == "background"


class TestConstants:
    """Module constants."""

    def test_lane_priorities_has_expected_keys(self) -> None:
        assert "critical" in LANE_PRIORITIES
        assert "standard" in LANE_PRIORITIES
        assert LANE_PRIORITIES["critical"] == 0

    def test_lane_urgency_has_expected_keys(self) -> None:
        assert "critical" in LANE_URGENCY
        assert LANE_URGENCY["critical"] == URGENCY_CRITICAL
