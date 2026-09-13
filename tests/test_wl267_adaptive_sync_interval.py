"""Tests for WL-267: Adaptive Sync Interval Controller.

Verifies that sync intervals can be dynamically increased, decreased, and reset
within configured bounds.

# @trace WL-267
"""

from __future__ import annotations

import pytest

from thegent.integrations.adaptive_sync_interval import (
    AdaptiveSyncIntervalController,
    SyncIntervalConfig,
)


@pytest.mark.requirement("WL-267")
class TestAdaptiveSyncIntervalController:
    """WL-267: Dynamic sync interval adjustment based on system conditions."""

    def test_default_config(self):
        """# @trace WL-267 — default config has min, max, and current intervals."""
        config = SyncIntervalConfig()

        assert config.min_seconds == 60.0
        assert config.max_seconds == 3600.0
        assert config.current_seconds == 300.0

    def test_increase_interval_by_factor(self):
        """# @trace WL-267 — increase() doubles the interval by default."""
        config = SyncIntervalConfig(
            min_seconds=60.0, max_seconds=3600.0, current_seconds=300.0
        )

        increased = AdaptiveSyncIntervalController.increase(config, factor=2.0)

        assert increased.current_seconds == 600.0
        assert increased.min_seconds == 60.0
        assert increased.max_seconds == 3600.0

    def test_increase_respects_max_bound(self):
        """# @trace WL-267 — increase() caps at max_seconds."""
        config = SyncIntervalConfig(
            min_seconds=60.0, max_seconds=3600.0, current_seconds=3000.0
        )

        increased = AdaptiveSyncIntervalController.increase(config, factor=2.0)

        assert increased.current_seconds == 3600.0  # Capped at max

    def test_increase_with_custom_factor(self):
        """# @trace WL-267 — increase() uses custom factor."""
        config = SyncIntervalConfig(current_seconds=100.0)

        increased = AdaptiveSyncIntervalController.increase(config, factor=1.5)

        assert increased.current_seconds == 150.0

    def test_decrease_interval_by_factor(self):
        """# @trace WL-267 — decrease() halves the interval by default."""
        config = SyncIntervalConfig(
            min_seconds=60.0, max_seconds=3600.0, current_seconds=300.0
        )

        decreased = AdaptiveSyncIntervalController.decrease(config, factor=2.0)

        assert decreased.current_seconds == 150.0
        assert decreased.min_seconds == 60.0
        assert decreased.max_seconds == 3600.0

    def test_decrease_respects_min_bound(self):
        """# @trace WL-267 — decrease() caps at min_seconds."""
        config = SyncIntervalConfig(
            min_seconds=60.0, max_seconds=3600.0, current_seconds=100.0
        )

        decreased = AdaptiveSyncIntervalController.decrease(config, factor=2.0)

        assert decreased.current_seconds == 60.0  # Capped at min

    def test_decrease_with_custom_factor(self):
        """# @trace WL-267 — decrease() uses custom factor."""
        config = SyncIntervalConfig(current_seconds=300.0)

        decreased = AdaptiveSyncIntervalController.decrease(config, factor=3.0)

        assert decreased.current_seconds == 100.0

    def test_reset_to_midpoint(self):
        """# @trace WL-267 — reset() returns interval to (min + max) / 2."""
        config = SyncIntervalConfig(
            min_seconds=60.0, max_seconds=3600.0, current_seconds=100.0
        )

        reset = AdaptiveSyncIntervalController.reset(config)

        expected_midpoint = (60.0 + 3600.0) / 2.0
        assert reset.current_seconds == expected_midpoint
        assert reset.min_seconds == 60.0
        assert reset.max_seconds == 3600.0

    def test_reset_with_asymmetric_bounds(self):
        """# @trace WL-267 — reset() computes midpoint correctly with custom bounds."""
        config = SyncIntervalConfig(
            min_seconds=100.0, max_seconds=500.0, current_seconds=250.0
        )

        reset = AdaptiveSyncIntervalController.reset(config)

        expected_midpoint = (100.0 + 500.0) / 2.0
        assert reset.current_seconds == expected_midpoint

    def test_increase_then_decrease_returns_to_original(self):
        """# @trace WL-267 — increase(2x) then decrease(2x) restores original interval."""
        original = SyncIntervalConfig(current_seconds=300.0)

        increased = AdaptiveSyncIntervalController.increase(original, factor=2.0)
        restored = AdaptiveSyncIntervalController.decrease(increased, factor=2.0)

        assert restored.current_seconds == original.current_seconds

    def test_multiple_increases_stack(self):
        """# @trace WL-267 — multiple increases stack (2x then 2x = 4x)."""
        config = SyncIntervalConfig(current_seconds=100.0)

        step1 = AdaptiveSyncIntervalController.increase(config, factor=2.0)
        step2 = AdaptiveSyncIntervalController.increase(step1, factor=2.0)

        assert step2.current_seconds == 400.0

    def test_original_config_is_not_mutated(self):
        """# @trace WL-267 — increase/decrease/reset return new configs; original unchanged."""
        config = SyncIntervalConfig(current_seconds=300.0)

        _increased = AdaptiveSyncIntervalController.increase(config)
        _decreased = AdaptiveSyncIntervalController.decrease(config)
        _reset = AdaptiveSyncIntervalController.reset(config)

        assert config.current_seconds == 300.0  # Original unchanged

    def test_decrease_with_very_small_interval(self):
        """# @trace WL-267 — decrease() on min_seconds stays at min."""
        config = SyncIntervalConfig(
            min_seconds=60.0, max_seconds=3600.0, current_seconds=60.0
        )

        decreased = AdaptiveSyncIntervalController.decrease(config, factor=2.0)

        assert decreased.current_seconds == 60.0

    def test_fractional_intervals(self):
        """# @trace WL-267 — increase/decrease handle fractional intervals."""
        config = SyncIntervalConfig(current_seconds=50.5)

        increased = AdaptiveSyncIntervalController.increase(config, factor=2.0)

        assert increased.current_seconds == 101.0
