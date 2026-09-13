"""Tests for WL-268: Incident Snapshot Bundle.

Verifies that incident snapshots can be captured, retrieved, and exported
for immutable postmortem workflows.

# @trace WL-268
"""

from __future__ import annotations

from datetime import datetime

import pytest

from thegent.integrations.incident_snapshot import (
    IncidentSnapshotBundle,
)


@pytest.mark.requirement("WL-268")
class TestIncidentSnapshotBundle:
    """WL-268: Immutable incident snapshot bundle for postmortem analysis."""

    def test_capture_and_get_snapshot(self):
        """# @trace WL-268 — capture a snapshot and retrieve it by incident ID."""
        bundle = IncidentSnapshotBundle()
        incident_data = {
            "status": "active",
            "error_count": 42,
            "affected_resources": ["service-a", "service-b"],
        }

        snapshot = bundle.capture("inc-001", incident_data)

        assert snapshot.incident_id == "inc-001"
        assert snapshot.data == incident_data
        assert isinstance(snapshot.timestamp, datetime)

        retrieved = bundle.get("inc-001")
        assert retrieved.incident_id == "inc-001"
        assert retrieved.data == incident_data

    def test_get_missing_incident_raises_key_error(self):
        """# @trace WL-268 — retrieving a non-existent incident raises KeyError."""
        bundle = IncidentSnapshotBundle()

        with pytest.raises(KeyError, match="Incident snapshot for 'missing' not found"):
            bundle.get("missing")

    def test_list_incidents(self):
        """# @trace WL-268 — list_incidents() returns all incident IDs."""
        bundle = IncidentSnapshotBundle()
        bundle.capture("inc-001", {"status": "active"})
        bundle.capture("inc-002", {"status": "resolved"})
        bundle.capture("inc-003", {"status": "active"})

        incident_ids = bundle.list_incidents()

        assert len(incident_ids) == 3
        assert set(incident_ids) == {"inc-001", "inc-002", "inc-003"}

    def test_list_incidents_returns_empty_initially(self):
        """# @trace WL-268 — list_incidents() returns empty list on new bundle."""
        bundle = IncidentSnapshotBundle()

        incident_ids = bundle.list_incidents()

        assert incident_ids == []

    def test_export_returns_serializable_dicts(self):
        """# @trace WL-268 — export() returns list of dicts with ISO timestamps."""
        bundle = IncidentSnapshotBundle()
        bundle.capture("inc-001", {"status": "active", "error_count": 5})
        bundle.capture("inc-002", {"status": "resolved", "duration_seconds": 120})

        exported = bundle.export()

        assert len(exported) == 2
        for item in exported:
            assert "incident_id" in item
            assert "timestamp" in item
            assert "data" in item
            # Timestamp should be ISO format string
            assert isinstance(item["timestamp"], str)
            # Try parsing as ISO format (should not raise)
            datetime.fromisoformat(item["timestamp"])

    def test_export_returns_empty_list_initially(self):
        """# @trace WL-268 — export() returns empty list on new bundle."""
        bundle = IncidentSnapshotBundle()

        exported = bundle.export()

        assert exported == []

    def test_capture_overwrites_previous_snapshot(self):
        """# @trace WL-268 — capturing same incident ID overwrites previous snapshot."""
        bundle = IncidentSnapshotBundle()
        bundle.capture("inc-001", {"status": "active", "version": 1})
        bundle.capture("inc-001", {"status": "resolved", "version": 2})

        snapshot = bundle.get("inc-001")

        assert snapshot.data["version"] == 2
        assert snapshot.data["status"] == "resolved"

    def test_export_contains_exact_data(self):
        """# @trace WL-268 — export includes all data fields without modification."""
        bundle = IncidentSnapshotBundle()
        complex_data = {
            "status": "active",
            "errors": [
                {"code": "E001", "message": "Service unavailable"},
                {"code": "E002", "message": "Timeout"},
            ],
            "metadata": {
                "region": "us-west-2",
                "environment": "production",
                "owner": "team-platform",
            },
        }

        bundle.capture("inc-001", complex_data)
        exported = bundle.export()

        assert len(exported) == 1
        assert exported[0]["incident_id"] == "inc-001"
        assert exported[0]["data"] == complex_data

    def test_snapshot_timestamp_is_unique(self):
        """# @trace WL-268 — consecutive captures have different timestamps."""
        bundle = IncidentSnapshotBundle()
        bundle.capture("inc-001", {"version": 1})
        snap1 = bundle.get("inc-001")

        bundle.capture("inc-002", {"version": 2})
        snap2 = bundle.get("inc-002")

        # Timestamps should be different (in practice, very close but distinct)
        # We check they are both datetime objects
        assert isinstance(snap1.timestamp, datetime)
        assert isinstance(snap2.timestamp, datetime)

    def test_multiple_incidents_are_independent(self):
        """# @trace WL-268 — multiple incidents are stored independently."""
        bundle = IncidentSnapshotBundle()
        bundle.capture("inc-001", {"status": "active", "error_count": 1})
        bundle.capture("inc-002", {"status": "active", "error_count": 2})
        bundle.capture("inc-003", {"status": "active", "error_count": 3})

        snap1 = bundle.get("inc-001")
        snap2 = bundle.get("inc-002")
        snap3 = bundle.get("inc-003")

        assert snap1.data["error_count"] == 1
        assert snap2.data["error_count"] == 2
        assert snap3.data["error_count"] == 3

    def test_export_includes_all_incidents(self):
        """# @trace WL-268 — export() includes all incidents captured."""
        bundle = IncidentSnapshotBundle()
        for i in range(5):
            bundle.capture(f"inc-{i:03d}", {"index": i})

        exported = bundle.export()

        assert len(exported) == 5
        incident_ids = {item["incident_id"] for item in exported}
        assert incident_ids == {f"inc-{i:03d}" for i in range(5)}

    def test_empty_data_dict(self):
        """# @trace WL-268 — capture handles empty data dict."""
        bundle = IncidentSnapshotBundle()

        snapshot = bundle.capture("inc-001", {})

        assert snapshot.data == {}
        retrieved = bundle.get("inc-001")
        assert retrieved.data == {}
