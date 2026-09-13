"""Tests for WL-207: Full-Rescan Scheduler.

# @trace WL-207
"""

from __future__ import annotations

import pytest

from thegent.integrations.rescan_scheduler import RescanConfig, RescanScheduler


class TestRescanConfig:
    """WL-207: RescanConfig dataclass."""

    @pytest.mark.requirement("WL-207")
    def test_default_config(self):
        """# @trace WL-207 — RescanConfig has correct defaults."""
        config = RescanConfig()

        assert config.full_rescan_every_n_cycles == 10
        assert config.incremental_by_default is True

    @pytest.mark.requirement("WL-207")
    def test_custom_config(self):
        """# @trace WL-207 — RescanConfig accepts custom values."""
        config = RescanConfig(
            full_rescan_every_n_cycles=5, incremental_by_default=False
        )

        assert config.full_rescan_every_n_cycles == 5
        assert config.incremental_by_default is False


class TestRescanScheduler:
    """WL-207: RescanScheduler class."""

    @pytest.mark.requirement("WL-207")
    def test_scheduler_with_default_config(self):
        """# @trace WL-207 — RescanScheduler initializes with default config."""
        scheduler = RescanScheduler()

        assert scheduler.config is not None
        assert scheduler.config.full_rescan_every_n_cycles == 10

    @pytest.mark.requirement("WL-207")
    def test_scheduler_with_custom_config(self):
        """# @trace WL-207 — RescanScheduler accepts custom config."""
        config = RescanConfig(full_rescan_every_n_cycles=5)
        scheduler = RescanScheduler(config=config)

        assert scheduler.config.full_rescan_every_n_cycles == 5

    @pytest.mark.requirement("WL-207")
    def test_should_full_rescan_at_interval_boundaries(self):
        """# @trace WL-207 — should_full_rescan returns True at interval boundaries."""
        scheduler = RescanScheduler(RescanConfig(full_rescan_every_n_cycles=10))

        # Full rescan at cycle 10, 20, 30, etc.
        assert scheduler.should_full_rescan(10) is True
        assert scheduler.should_full_rescan(20) is True
        assert scheduler.should_full_rescan(30) is True

    @pytest.mark.requirement("WL-207")
    def test_should_full_rescan_between_boundaries(self):
        """# @trace WL-207 — should_full_rescan returns False between boundaries."""
        scheduler = RescanScheduler(RescanConfig(full_rescan_every_n_cycles=10))

        # Incremental cycles
        assert scheduler.should_full_rescan(1) is False
        assert scheduler.should_full_rescan(5) is False
        assert scheduler.should_full_rescan(9) is False
        assert scheduler.should_full_rescan(11) is False

    @pytest.mark.requirement("WL-207")
    def test_should_full_rescan_custom_interval(self):
        """# @trace WL-207 — should_full_rescan respects custom interval."""
        scheduler = RescanScheduler(RescanConfig(full_rescan_every_n_cycles=5))

        # Full rescan at cycle 5, 10, 15, etc.
        assert scheduler.should_full_rescan(5) is True
        assert scheduler.should_full_rescan(10) is True
        assert scheduler.should_full_rescan(3) is False
        assert scheduler.should_full_rescan(7) is False

    @pytest.mark.requirement("WL-207")
    def test_should_full_rescan_invalid_cycle_number(self):
        """# @trace WL-207 — should_full_rescan raises ValueError for invalid cycle."""
        scheduler = RescanScheduler()

        with pytest.raises(ValueError, match="cycle_number must be >= 1"):
            scheduler.should_full_rescan(0)

        with pytest.raises(ValueError, match="cycle_number must be >= 1"):
            scheduler.should_full_rescan(-5)

    @pytest.mark.requirement("WL-207")
    def test_next_full_rescan_cycle_from_start(self):
        """# @trace WL-207 — next_full_rescan_cycle from cycle 1."""
        scheduler = RescanScheduler(RescanConfig(full_rescan_every_n_cycles=10))

        assert scheduler.next_full_rescan_cycle(1) == 10
        assert scheduler.next_full_rescan_cycle(5) == 10
        assert scheduler.next_full_rescan_cycle(9) == 10

    @pytest.mark.requirement("WL-207")
    def test_next_full_rescan_cycle_from_boundary(self):
        """# @trace WL-207 — next_full_rescan_cycle from boundary."""
        scheduler = RescanScheduler(RescanConfig(full_rescan_every_n_cycles=10))

        assert scheduler.next_full_rescan_cycle(10) == 20
        assert scheduler.next_full_rescan_cycle(20) == 30
        assert scheduler.next_full_rescan_cycle(25) == 30

    @pytest.mark.requirement("WL-207")
    def test_next_full_rescan_cycle_custom_interval(self):
        """# @trace WL-207 — next_full_rescan_cycle with custom interval."""
        scheduler = RescanScheduler(RescanConfig(full_rescan_every_n_cycles=7))

        assert scheduler.next_full_rescan_cycle(1) == 7
        assert scheduler.next_full_rescan_cycle(7) == 14
        assert scheduler.next_full_rescan_cycle(8) == 14
        assert scheduler.next_full_rescan_cycle(13) == 14

    @pytest.mark.requirement("WL-207")
    def test_next_full_rescan_cycle_invalid_cycle(self):
        """# @trace WL-207 — next_full_rescan_cycle raises ValueError for invalid cycle."""
        scheduler = RescanScheduler()

        with pytest.raises(ValueError, match="current_cycle must be >= 1"):
            scheduler.next_full_rescan_cycle(0)

        with pytest.raises(ValueError, match="current_cycle must be >= 1"):
            scheduler.next_full_rescan_cycle(-1)
