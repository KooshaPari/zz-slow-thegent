"""WL-182 stale item detector tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from thegent.integrations.stale_item_detector import (
    ItemActivity,
    StaleDetectorConfig,
    StaleItemDetector,
)


def test_wl182_detects_item_when_local_and_remote_are_stale() -> None:
    """# @trace WL-182"""
    now = datetime(2026, 2, 22, 12, 0, tzinfo=UTC)
    detector = StaleItemDetector(
        StaleDetectorConfig(local_threshold=timedelta(days=5), remote_threshold=timedelta(days=3))
    )
    results = detector.detect(
        [
            ItemActivity(
                item_id="WL-1820",
                last_local_movement_at=now - timedelta(days=7),
                last_remote_movement_at=now - timedelta(days=4),
            )
        ],
        now=now,
    )
    assert len(results) == 1
    assert results[0].item_id == "WL-1820"


def test_wl182_skips_when_local_is_recent_even_if_remote_is_old() -> None:
    """# @trace WL-182"""
    now = datetime(2026, 2, 22, 12, 0, tzinfo=UTC)
    detector = StaleItemDetector(
        StaleDetectorConfig(local_threshold=timedelta(days=5), remote_threshold=timedelta(days=3))
    )
    results = detector.detect(
        [
            ItemActivity(
                item_id="WL-1821",
                last_local_movement_at=now - timedelta(days=1),
                last_remote_movement_at=now - timedelta(days=10),
            )
        ],
        now=now,
    )
    assert results == []


def test_wl182_missing_movements_count_as_stale_when_thresholds_passed() -> None:
    """# @trace WL-182"""
    now = datetime(2026, 2, 22, 12, 0, tzinfo=UTC)
    detector = StaleItemDetector(
        StaleDetectorConfig(local_threshold=timedelta(days=5), remote_threshold=timedelta(days=3))
    )
    results = detector.detect(
        [ItemActivity(item_id="WL-1822", last_local_movement_at=None, last_remote_movement_at=None)],
        now=now,
    )
    assert len(results) == 1
    assert results[0].item_id == "WL-1822"


def test_wl182_rejects_future_timestamp() -> None:
    """# @trace WL-182"""
    now = datetime(2026, 2, 22, 12, 0, tzinfo=UTC)
    detector = StaleItemDetector(
        StaleDetectorConfig(local_threshold=timedelta(days=5), remote_threshold=timedelta(days=3))
    )
    with pytest.raises(ValueError, match="future"):
        detector.detect(
            [
                ItemActivity(
                    item_id="WL-1823",
                    last_local_movement_at=now + timedelta(minutes=1),
                    last_remote_movement_at=now - timedelta(days=4),
                )
            ],
            now=now,
        )


def test_wl182_requires_timezone_aware_timestamps() -> None:
    """# @trace WL-182"""
    now = datetime(2026, 2, 22, 12, 0, tzinfo=UTC)
    detector = StaleItemDetector(
        StaleDetectorConfig(local_threshold=timedelta(days=5), remote_threshold=timedelta(days=3))
    )
    with pytest.raises(ValueError, match="timezone-aware"):
        detector.detect(
            [
                ItemActivity(
                    item_id="WL-1824",
                    last_local_movement_at=datetime(2026, 2, 1, 12, 0),  # noqa: DTZ001 -- intentional naive timestamp to validate rejection
                    last_remote_movement_at=now - timedelta(days=6),
                )
            ],
            now=now,
        )
