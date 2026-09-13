"""Tests for thegent.integrations.stale_detector — Stale Item Detector.

@trace WL-182
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from thegent.integrations.stale_detector import (
    StaleConfig,
    StaleItem,
    StaleItemDetector,
)


class TestStaleConfigCreation:
    """Test StaleConfig dataclass creation."""

    @pytest.mark.requirement("WL-182")
    def test_create_default_config(self) -> None:
        """Can create StaleConfig with default threshold."""
        config = StaleConfig()

        assert config.stale_after_days == 14

    @pytest.mark.requirement("WL-182")
    def test_create_custom_config(self) -> None:
        """Can create StaleConfig with custom threshold."""
        config = StaleConfig(stale_after_days=30)

        assert config.stale_after_days == 30


class TestStaleItemCreation:
    """Test StaleItem dataclass creation."""

    @pytest.mark.requirement("WL-182")
    def test_create_stale_item(self) -> None:
        """Can create a StaleItem."""
        now = datetime.now(UTC)
        old_time = now - timedelta(days=20)

        item = StaleItem(
            wl_id="WL-001",
            last_activity=old_time,
            age_days=20.0,
            connector="github",
        )

        assert item.wl_id == "WL-001"
        assert item.last_activity == old_time
        assert item.age_days == 20.0
        assert item.connector == "github"


class TestStaleItemDetectorInit:
    """Test StaleItemDetector initialization."""

    @pytest.mark.requirement("WL-182")
    def test_init_default_config(self) -> None:
        """Detector initializes with default config."""
        detector = StaleItemDetector()

        assert detector.config.stale_after_days == 14

    @pytest.mark.requirement("WL-182")
    def test_init_custom_config(self) -> None:
        """Detector initializes with custom config."""
        config = StaleConfig(stale_after_days=7)
        detector = StaleItemDetector(config)

        assert detector.config.stale_after_days == 7


class TestStaleItemDetectorIsStale:
    """Test StaleItemDetector.is_stale operations."""

    @pytest.mark.requirement("WL-182")
    def test_is_stale_old_item(self) -> None:
        """is_stale returns True for old items."""
        detector = StaleItemDetector(StaleConfig(stale_after_days=14))
        now = datetime.now(UTC)
        old_time = now - timedelta(days=20)

        assert detector.is_stale(old_time, now) is True

    @pytest.mark.requirement("WL-182")
    def test_is_stale_new_item(self) -> None:
        """is_stale returns False for recent items."""
        detector = StaleItemDetector(StaleConfig(stale_after_days=14))
        now = datetime.now(UTC)
        recent_time = now - timedelta(days=5)

        assert detector.is_stale(recent_time, now) is False

    @pytest.mark.requirement("WL-182")
    def test_is_stale_at_threshold(self) -> None:
        """is_stale returns True when age equals threshold."""
        detector = StaleItemDetector(StaleConfig(stale_after_days=14))
        now = datetime.now(UTC)
        threshold_time = now - timedelta(days=14)

        assert detector.is_stale(threshold_time, now) is True

    @pytest.mark.requirement("WL-182")
    def test_is_stale_just_below_threshold(self) -> None:
        """is_stale returns False when age just below threshold."""
        detector = StaleItemDetector(StaleConfig(stale_after_days=14))
        now = datetime.now(UTC)
        just_below_time = now - timedelta(days=13, hours=23)

        assert detector.is_stale(just_below_time, now) is False

    @pytest.mark.requirement("WL-182")
    def test_is_stale_with_default_now(self) -> None:
        """is_stale uses UTC now when not specified."""
        detector = StaleItemDetector(StaleConfig(stale_after_days=14))
        old_time = datetime.now(UTC) - timedelta(days=20)

        # Should not raise and should return True
        assert detector.is_stale(old_time) is True

    @pytest.mark.requirement("WL-182")
    def test_is_stale_naive_datetime(self) -> None:
        """is_stale handles naive datetimes."""
        detector = StaleItemDetector(StaleConfig(stale_after_days=14))
        now = datetime.now(UTC)
        old_time = datetime.now() - timedelta(days=20)  # naive

        # Should not raise
        result = detector.is_stale(old_time, now)
        assert isinstance(result, bool)


class TestStaleItemDetectorDetect:
    """Test StaleItemDetector.detect operations."""

    @pytest.mark.requirement("WL-182")
    def test_detect_all_stale(self) -> None:
        """detect returns all items if all are stale."""
        detector = StaleItemDetector(StaleConfig(stale_after_days=14))
        now = datetime.now(UTC)

        items = [
            {
                "wl_id": "WL-001",
                "last_activity": (now - timedelta(days=20)).isoformat(),
                "connector": "github",
            },
            {
                "wl_id": "WL-002",
                "last_activity": (now - timedelta(days=30)).isoformat(),
                "connector": "linear",
            },
        ]

        stale = detector.detect(items, now)

        assert len(stale) == 2
        assert stale[0].wl_id == "WL-001"
        assert stale[1].wl_id == "WL-002"

    @pytest.mark.requirement("WL-182")
    def test_detect_no_stale(self) -> None:
        """detect returns empty list if no items are stale."""
        detector = StaleItemDetector(StaleConfig(stale_after_days=14))
        now = datetime.now(UTC)

        items = [
            {
                "wl_id": "WL-001",
                "last_activity": (now - timedelta(days=5)).isoformat(),
                "connector": "github",
            },
            {
                "wl_id": "WL-002",
                "last_activity": (now - timedelta(days=10)).isoformat(),
                "connector": "linear",
            },
        ]

        stale = detector.detect(items, now)

        assert stale == []

    @pytest.mark.requirement("WL-182")
    def test_detect_mixed_stale(self) -> None:
        """detect returns only stale items when mixed."""
        detector = StaleItemDetector(StaleConfig(stale_after_days=14))
        now = datetime.now(UTC)

        items = [
            {
                "wl_id": "WL-001",
                "last_activity": (now - timedelta(days=5)).isoformat(),
                "connector": "github",
            },
            {
                "wl_id": "WL-002",
                "last_activity": (now - timedelta(days=20)).isoformat(),
                "connector": "linear",
            },
            {
                "wl_id": "WL-003",
                "last_activity": (now - timedelta(days=30)).isoformat(),
                "connector": "github",
            },
        ]

        stale = detector.detect(items, now)

        assert len(stale) == 2
        stale_ids = {item.wl_id for item in stale}
        assert "WL-002" in stale_ids
        assert "WL-003" in stale_ids
        assert "WL-001" not in stale_ids

    @pytest.mark.requirement("WL-182")
    def test_detect_with_datetime_objects(self) -> None:
        """detect handles datetime objects (not just ISO strings)."""
        detector = StaleItemDetector(StaleConfig(stale_after_days=14))
        now = datetime.now(UTC)

        items = [
            {
                "wl_id": "WL-001",
                "last_activity": now - timedelta(days=20),
                "connector": "github",
            },
        ]

        stale = detector.detect(items, now)

        assert len(stale) == 1

    @pytest.mark.requirement("WL-182")
    def test_detect_age_days_calculated(self) -> None:
        """detect calculates age_days correctly."""
        detector = StaleItemDetector(StaleConfig(stale_after_days=14))
        now = datetime.now(UTC)

        items = [
            {
                "wl_id": "WL-001",
                "last_activity": (now - timedelta(days=20)).isoformat(),
                "connector": "github",
            },
        ]

        stale = detector.detect(items, now)

        assert len(stale) == 1
        assert 19.99 < stale[0].age_days < 20.01

    @pytest.mark.requirement("WL-182")
    def test_detect_empty_list(self) -> None:
        """detect returns empty list for empty input."""
        detector = StaleItemDetector()
        now = datetime.now(UTC)

        stale = detector.detect([], now)

        assert stale == []


class TestStaleItemDetectorSummary:
    """Test StaleItemDetector.summary operations."""

    @pytest.mark.requirement("WL-182")
    def test_summary_empty_list(self) -> None:
        """summary returns zeros for empty list."""
        detector = StaleItemDetector()
        stale_items: list[StaleItem] = []

        summary = detector.summary(stale_items)

        assert summary["count"] == 0
        assert summary["oldest_days"] is None
        assert summary["connectors"] == []

    @pytest.mark.requirement("WL-182")
    def test_summary_single_item(self) -> None:
        """summary works with single item."""
        detector = StaleItemDetector()
        now = datetime.now(UTC)

        stale_items = [
            StaleItem(
                wl_id="WL-001",
                last_activity=now - timedelta(days=20),
                age_days=20.0,
                connector="github",
            ),
        ]

        summary = detector.summary(stale_items)

        assert summary["count"] == 1
        assert summary["oldest_days"] == 20.0
        assert summary["connectors"] == ["github"]

    @pytest.mark.requirement("WL-182")
    def test_summary_multiple_items(self) -> None:
        """summary tracks oldest and unique connectors."""
        detector = StaleItemDetector()
        now = datetime.now(UTC)

        stale_items = [
            StaleItem(
                wl_id="WL-001",
                last_activity=now - timedelta(days=20),
                age_days=20.0,
                connector="github",
            ),
            StaleItem(
                wl_id="WL-002",
                last_activity=now - timedelta(days=35),
                age_days=35.0,
                connector="linear",
            ),
            StaleItem(
                wl_id="WL-003",
                last_activity=now - timedelta(days=30),
                age_days=30.0,
                connector="github",
            ),
        ]

        summary = detector.summary(stale_items)

        assert summary["count"] == 3
        assert summary["oldest_days"] == 35.0
        assert set(summary["connectors"]) == {"github", "linear"}

    @pytest.mark.requirement("WL-182")
    def test_summary_connectors_sorted(self) -> None:
        """summary returns connectors in sorted order."""
        detector = StaleItemDetector()
        now = datetime.now(UTC)

        stale_items = [
            StaleItem(
                wl_id="WL-001",
                last_activity=now - timedelta(days=20),
                age_days=20.0,
                connector="z_connector",
            ),
            StaleItem(
                wl_id="WL-002",
                last_activity=now - timedelta(days=20),
                age_days=20.0,
                connector="a_connector",
            ),
        ]

        summary = detector.summary(stale_items)

        assert summary["connectors"] == ["a_connector", "z_connector"]
