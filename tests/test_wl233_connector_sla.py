"""Tests for thegent.integrations.connector_sla — Connector SLA tracking.

@trace WL-233
"""

from __future__ import annotations

import pytest

from thegent.integrations.connector_sla import (
    ConnectorSLATracker,
    SLARecord,
)


class TestSLARecord:
    """Test SLARecord dataclass. @trace WL-233"""

    @pytest.mark.requirement("WL-233")
    def test_create_record_with_defaults(self) -> None:
        """Can create an SLARecord with default actual_ms."""
        record = SLARecord(connector_id="github", target_ms=1000.0)

        assert record.connector_id == "github"
        assert record.target_ms == 1000.0
        assert record.actual_ms is None

    @pytest.mark.requirement("WL-233")
    def test_create_record_with_actual(self) -> None:
        """Can create an SLARecord with actual_ms specified."""
        record = SLARecord(connector_id="github", target_ms=1000.0, actual_ms=950.0)

        assert record.connector_id == "github"
        assert record.target_ms == 1000.0
        assert record.actual_ms == 950.0


class TestConnectorSLATracker:
    """Test ConnectorSLATracker operations. @trace WL-233"""

    @pytest.fixture
    def tracker(self) -> ConnectorSLATracker:
        """Provide a fresh tracker."""
        return ConnectorSLATracker()

    @pytest.mark.requirement("WL-233")
    def test_set_target(self, tracker: ConnectorSLATracker) -> None:
        """Can set an SLA target for a connector."""
        result = tracker.set_target("github", 1000.0)

        assert result.connector_id == "github"
        assert result.target_ms == 1000.0
        assert result.actual_ms is None

    @pytest.mark.requirement("WL-233")
    def test_set_target_invalid_zero(self, tracker: ConnectorSLATracker) -> None:
        """set_target raises ValueError for zero target."""
        with pytest.raises(ValueError, match="positive"):
            tracker.set_target("github", 0.0)

    @pytest.mark.requirement("WL-233")
    def test_set_target_invalid_negative(self, tracker: ConnectorSLATracker) -> None:
        """set_target raises ValueError for negative target."""
        with pytest.raises(ValueError, match="positive"):
            tracker.set_target("github", -100.0)

    @pytest.mark.requirement("WL-233")
    def test_record_actual(self, tracker: ConnectorSLATracker) -> None:
        """Can record actual latency for a connector."""
        tracker.set_target("github", 1000.0)
        tracker.record_actual("github", 950.0)

        record = tracker.all_records()[0]
        assert record.actual_ms == 950.0

    @pytest.mark.requirement("WL-233")
    def test_record_actual_no_target_raises(self, tracker: ConnectorSLATracker) -> None:
        """record_actual raises KeyError if connector has no target."""
        with pytest.raises(KeyError, match="no SLA target"):
            tracker.record_actual("github", 950.0)

    @pytest.mark.requirement("WL-233")
    def test_record_actual_negative_raises(self, tracker: ConnectorSLATracker) -> None:
        """record_actual raises ValueError for negative latency."""
        tracker.set_target("github", 1000.0)

        with pytest.raises(ValueError, match="cannot be negative"):
            tracker.record_actual("github", -100.0)

    @pytest.mark.requirement("WL-233")
    def test_is_breached_when_not_recorded(self, tracker: ConnectorSLATracker) -> None:
        """is_breached returns False when actual not recorded."""
        tracker.set_target("github", 1000.0)

        assert tracker.is_breached("github") is False

    @pytest.mark.requirement("WL-233")
    def test_is_breached_within_sla(self, tracker: ConnectorSLATracker) -> None:
        """is_breached returns False when actual <= target."""
        tracker.set_target("github", 1000.0)
        tracker.record_actual("github", 950.0)

        assert tracker.is_breached("github") is False

    @pytest.mark.requirement("WL-233")
    def test_is_breached_at_sla_boundary(self, tracker: ConnectorSLATracker) -> None:
        """is_breached returns False when actual == target."""
        tracker.set_target("github", 1000.0)
        tracker.record_actual("github", 1000.0)

        assert tracker.is_breached("github") is False

    @pytest.mark.requirement("WL-233")
    def test_is_breached_exceeds_sla(self, tracker: ConnectorSLATracker) -> None:
        """is_breached returns True when actual > target."""
        tracker.set_target("github", 1000.0)
        tracker.record_actual("github", 1050.0)

        assert tracker.is_breached("github") is True

    @pytest.mark.requirement("WL-233")
    def test_is_breached_unregistered_raises(
        self, tracker: ConnectorSLATracker
    ) -> None:
        """is_breached raises KeyError for unregistered connector."""
        with pytest.raises(KeyError, match="not found"):
            tracker.is_breached("unknown")

    @pytest.mark.requirement("WL-233")
    def test_breached_empty_tracker(self, tracker: ConnectorSLATracker) -> None:
        """breached returns empty list for empty tracker."""
        assert tracker.breached() == []

    @pytest.mark.requirement("WL-233")
    def test_breached_no_breaches(self, tracker: ConnectorSLATracker) -> None:
        """breached returns empty list when no connectors are breached."""
        tracker.set_target("github", 1000.0)
        tracker.record_actual("github", 950.0)

        tracker.set_target("linear", 500.0)
        tracker.record_actual("linear", 400.0)

        assert tracker.breached() == []

    @pytest.mark.requirement("WL-233")
    def test_breached_some_breaches(self, tracker: ConnectorSLATracker) -> None:
        """breached returns only breached records."""
        tracker.set_target("github", 1000.0)
        tracker.record_actual("github", 950.0)

        tracker.set_target("linear", 500.0)
        tracker.record_actual("linear", 600.0)

        tracker.set_target("jira", 2000.0)
        tracker.record_actual("jira", 2500.0)

        breached = tracker.breached()
        breached_ids = {r.connector_id for r in breached}

        assert breached_ids == {"linear", "jira"}
        assert len(breached) == 2

    @pytest.mark.requirement("WL-233")
    def test_all_records_empty(self, tracker: ConnectorSLATracker) -> None:
        """all_records returns empty list for empty tracker."""
        assert tracker.all_records() == []

    @pytest.mark.requirement("WL-233")
    def test_all_records_returns_all(self, tracker: ConnectorSLATracker) -> None:
        """all_records returns all SLA records."""
        tracker.set_target("github", 1000.0)
        tracker.set_target("linear", 500.0)
        tracker.set_target("jira", 2000.0)

        records = tracker.all_records()
        ids = {r.connector_id for r in records}

        assert ids == {"github", "linear", "jira"}
        assert len(records) == 3

    @pytest.mark.requirement("WL-233")
    def test_all_records_includes_recorded_and_unrecorded(
        self, tracker: ConnectorSLATracker
    ) -> None:
        """all_records includes both recorded and unrecorded actuals."""
        tracker.set_target("github", 1000.0)
        tracker.record_actual("github", 950.0)

        tracker.set_target("linear", 500.0)
        # Don't record actual for linear

        records = tracker.all_records()
        github_record = next(r for r in records if r.connector_id == "github")
        linear_record = next(r for r in records if r.connector_id == "linear")

        assert github_record.actual_ms == 950.0
        assert linear_record.actual_ms is None

    @pytest.mark.requirement("WL-233")
    def test_update_target(self, tracker: ConnectorSLATracker) -> None:
        """Can update an existing target."""
        tracker.set_target("github", 1000.0)
        tracker.set_target("github", 500.0)

        record = tracker.all_records()[0]
        assert record.target_ms == 500.0

    @pytest.mark.requirement("WL-233")
    def test_multiple_operations(self, tracker: ConnectorSLATracker) -> None:
        """Can perform multiple operations in sequence."""
        # Set targets
        tracker.set_target("github", 1000.0)
        tracker.set_target("linear", 500.0)

        # Record some actuals
        tracker.record_actual("github", 950.0)
        tracker.record_actual("linear", 600.0)

        # Check status
        assert tracker.is_breached("github") is False
        assert tracker.is_breached("linear") is True
        assert len(tracker.breached()) == 1
        assert len(tracker.all_records()) == 2
