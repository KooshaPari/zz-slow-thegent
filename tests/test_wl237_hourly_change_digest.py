"""Tests for WL-237: Hourly Change Digest.

Tests cover:
- ChangeEntry dataclass creation
- HourlyChangeDigest change recording with automatic hour derivation
- Change retrieval by hour
- Hourly digest summarization by change type
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from thegent.integrations.hourly_change_digest import (
    ChangeEntry,
    HourlyChangeDigest,
)


def _aware_datetime(*args, **kwargs):
    if "tzinfo" in kwargs:
        return datetime(*args, **kwargs)  # noqa: DTZ001 -- tzinfo is already supplied by caller branch guard
    return datetime(*args, tzinfo=UTC, **kwargs)


@pytest.mark.requirement("WL-237")
class TestChangeEntry:
    """Tests for the ChangeEntry dataclass."""

    def test_change_entry_creation(self) -> None:
        """Test creating a ChangeEntry."""
        entry = ChangeEntry(
            item_id="item-123",
            change_type="updated",
            hour="2026-02-22T15",
        )
        assert entry.item_id == "item-123"
        assert entry.change_type == "updated"
        assert entry.hour == "2026-02-22T15"

    def test_change_entry_attributes(self) -> None:
        """Test all ChangeEntry attributes are accessible."""
        entry = ChangeEntry(
            item_id="test-id",
            change_type="created",
            hour="2026-02-22T10",
        )
        assert hasattr(entry, "item_id")
        assert hasattr(entry, "change_type")
        assert hasattr(entry, "hour")


@pytest.mark.requirement("WL-237")
class TestHourlyChangeDigest:
    """Tests for the HourlyChangeDigest class."""

    def test_create_empty_digest(self) -> None:
        """Test creating an empty digest."""
        digest = HourlyChangeDigest()
        assert digest.get_hour("2026-02-22T15") == []

    @patch("thegent.integrations.hourly_change_digest.datetime")
    def test_record_change(self, mock_datetime) -> None:
        """Test recording a change with automatic hour derivation."""
        mock_now = datetime(2026, 2, 22, 15, 30, 45, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = _aware_datetime

        digest = HourlyChangeDigest()
        entry = digest.record("item-1", "created")

        assert entry.item_id == "item-1"
        assert entry.change_type == "created"
        assert entry.hour == "2026-02-22T15"

    @patch("thegent.integrations.hourly_change_digest.datetime")
    def test_record_multiple_changes_same_hour(self, mock_datetime) -> None:
        """Test recording multiple changes in the same hour."""
        mock_now = datetime(2026, 2, 22, 14, 15, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = _aware_datetime

        digest = HourlyChangeDigest()
        digest.record("item-1", "created")
        digest.record("item-2", "updated")
        digest.record("item-3", "deleted")

        hour_entries = digest.get_hour("2026-02-22T14")
        assert len(hour_entries) == 3

    def test_get_hour_empty(self) -> None:
        """Test getting an hour with no entries returns empty list."""
        digest = HourlyChangeDigest()
        result = digest.get_hour("2026-02-22T99")
        assert result == []

    def test_get_hour_returns_entries(self) -> None:
        """Test getting an hour returns the recorded entries."""
        digest = HourlyChangeDigest()
        entry1 = ChangeEntry("item-1", "created", "2026-02-22T15")
        entry2 = ChangeEntry("item-2", "updated", "2026-02-22T15")

        digest._by_hour["2026-02-22T15"] = [entry1, entry2]

        result = digest.get_hour("2026-02-22T15")
        assert len(result) == 2
        assert entry1 in result
        assert entry2 in result

    def test_digest_empty_hour(self) -> None:
        """Test digest for an empty hour returns empty dict."""
        digest = HourlyChangeDigest()
        result = digest.digest("2026-02-22T15")
        assert result == {}

    def test_digest_single_change_type(self) -> None:
        """Test digest with entries of a single type."""
        digest = HourlyChangeDigest()
        digest._by_hour["2026-02-22T15"] = [
            ChangeEntry("item-1", "created", "2026-02-22T15"),
            ChangeEntry("item-2", "created", "2026-02-22T15"),
            ChangeEntry("item-3", "created", "2026-02-22T15"),
        ]

        result = digest.digest("2026-02-22T15")
        assert result == {"created": 3}

    def test_digest_multiple_change_types(self) -> None:
        """Test digest with entries of multiple types."""
        digest = HourlyChangeDigest()
        digest._by_hour["2026-02-22T15"] = [
            ChangeEntry("item-1", "created", "2026-02-22T15"),
            ChangeEntry("item-2", "created", "2026-02-22T15"),
            ChangeEntry("item-3", "updated", "2026-02-22T15"),
            ChangeEntry("item-4", "deleted", "2026-02-22T15"),
            ChangeEntry("item-5", "updated", "2026-02-22T15"),
        ]

        result = digest.digest("2026-02-22T15")
        assert result == {"created": 2, "updated": 2, "deleted": 1}

    def test_digest_hour_isolation(self) -> None:
        """Test that digest only counts changes from the specified hour."""
        digest = HourlyChangeDigest()
        digest._by_hour["2026-02-22T14"] = [
            ChangeEntry("item-1", "created", "2026-02-22T14"),
            ChangeEntry("item-2", "created", "2026-02-22T14"),
        ]
        digest._by_hour["2026-02-22T15"] = [
            ChangeEntry("item-3", "created", "2026-02-22T15"),
            ChangeEntry("item-4", "updated", "2026-02-22T15"),
        ]

        result_14 = digest.digest("2026-02-22T14")
        result_15 = digest.digest("2026-02-22T15")

        assert result_14 == {"created": 2}
        assert result_15 == {"created": 1, "updated": 1}

    @patch("thegent.integrations.hourly_change_digest.datetime")
    def test_full_workflow(self, mock_datetime) -> None:
        """Test a complete workflow with recording and digestion."""
        mock_now = datetime(2026, 2, 22, 16, 45, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = _aware_datetime

        digest = HourlyChangeDigest()
        digest.record("item-1", "created")
        digest.record("item-2", "created")
        digest.record("item-3", "updated")

        hour_entries = digest.get_hour("2026-02-22T16")
        assert len(hour_entries) == 3

        summary = digest.digest("2026-02-22T16")
        assert summary == {"created": 2, "updated": 1}

    def test_hour_format_consistency(self) -> None:
        """Test that recorded hour format is consistent."""
        digest = HourlyChangeDigest()
        entry1 = ChangeEntry("item-1", "created", "2026-02-22T12")
        entry2 = ChangeEntry("item-2", "updated", "2026-02-22T12")

        digest._by_hour["2026-02-22T12"] = [entry1, entry2]

        # Verify both entries use the same hour format
        for entry in digest.get_hour("2026-02-22T12"):
            assert entry.hour == "2026-02-22T12"
