"""Tests for thegent.integrations.maintenance_banner — Maintenance banner propagation.

@trace WL-229
"""

from __future__ import annotations

import pytest

from thegent.integrations.maintenance_banner import (
    MaintenanceBanner,
    MaintenanceBannerPropagator,
)


class TestMaintenanceBanner:
    """Test MaintenanceBanner dataclass. @trace WL-229"""

    @pytest.mark.requirement("WL-229")
    def test_create_banner_with_defaults(self) -> None:
        """Can create a MaintenanceBanner with default values."""
        banner = MaintenanceBanner(message="System maintenance in progress")

        assert banner.message == "System maintenance in progress"
        assert banner.active is False
        assert banner.severity == "info"

    @pytest.mark.requirement("WL-229")
    def test_create_banner_with_all_fields(self) -> None:
        """Can create a MaintenanceBanner with all fields specified."""
        banner = MaintenanceBanner(
            message="Critical maintenance", active=True, severity="critical"
        )

        assert banner.message == "Critical maintenance"
        assert banner.active is True
        assert banner.severity == "critical"

    @pytest.mark.requirement("WL-229")
    def test_banner_severity_levels(self) -> None:
        """Can create banners with all valid severity levels."""
        for severity in ["info", "warning", "critical"]:
            banner = MaintenanceBanner(message="Test", severity=severity)
            assert banner.severity == severity


class TestMaintenanceBannerPropagator:
    """Test MaintenanceBannerPropagator operations. @trace WL-229"""

    @pytest.fixture
    def propagator(self) -> MaintenanceBannerPropagator:
        """Provide a fresh propagator."""
        return MaintenanceBannerPropagator()

    @pytest.mark.requirement("WL-229")
    def test_set_banner(self, propagator: MaintenanceBannerPropagator) -> None:
        """Can set a maintenance banner."""
        result = propagator.set_banner("System maintenance in progress")

        assert result.message == "System maintenance in progress"
        assert result.severity == "info"
        assert result.active is False

    @pytest.mark.requirement("WL-229")
    def test_set_banner_with_severity(
        self, propagator: MaintenanceBannerPropagator
    ) -> None:
        """Can set a banner with custom severity."""
        result = propagator.set_banner("Critical outage", severity="critical")

        assert result.message == "Critical outage"
        assert result.severity == "critical"

    @pytest.mark.requirement("WL-229")
    def test_set_banner_invalid_severity(
        self, propagator: MaintenanceBannerPropagator
    ) -> None:
        """set_banner raises ValueError for invalid severity."""
        with pytest.raises(ValueError, match="Invalid severity"):
            propagator.set_banner("Test", severity="invalid")

    @pytest.mark.requirement("WL-229")
    def test_activate_banner(self, propagator: MaintenanceBannerPropagator) -> None:
        """Can activate a banner."""
        propagator.set_banner("Maintenance window")
        propagator.activate()

        assert propagator.is_active() is True

    @pytest.mark.requirement("WL-229")
    def test_activate_without_set_raises(
        self, propagator: MaintenanceBannerPropagator
    ) -> None:
        """activate raises RuntimeError if no banner is set."""
        with pytest.raises(RuntimeError, match="No banner has been set"):
            propagator.activate()

    @pytest.mark.requirement("WL-229")
    def test_deactivate_banner(self, propagator: MaintenanceBannerPropagator) -> None:
        """Can deactivate a banner."""
        propagator.set_banner("Maintenance window")
        propagator.activate()
        assert propagator.is_active() is True

        propagator.deactivate()
        assert propagator.is_active() is False

    @pytest.mark.requirement("WL-229")
    def test_deactivate_without_set_raises(
        self, propagator: MaintenanceBannerPropagator
    ) -> None:
        """deactivate raises RuntimeError if no banner is set."""
        with pytest.raises(RuntimeError, match="No banner has been set"):
            propagator.deactivate()

    @pytest.mark.requirement("WL-229")
    def test_is_active_false_when_not_set(
        self, propagator: MaintenanceBannerPropagator
    ) -> None:
        """is_active returns False when no banner is set."""
        assert propagator.is_active() is False

    @pytest.mark.requirement("WL-229")
    def test_is_active_false_when_inactive(
        self, propagator: MaintenanceBannerPropagator
    ) -> None:
        """is_active returns False when banner is set but inactive."""
        propagator.set_banner("Maintenance")
        assert propagator.is_active() is False

    @pytest.mark.requirement("WL-229")
    def test_current_none_when_not_set(
        self, propagator: MaintenanceBannerPropagator
    ) -> None:
        """current returns None when no banner is set."""
        assert propagator.current() is None

    @pytest.mark.requirement("WL-229")
    def test_current_returns_banner(
        self, propagator: MaintenanceBannerPropagator
    ) -> None:
        """current returns the set banner."""
        propagator.set_banner("Test banner", severity="warning")

        current = propagator.current()
        assert current is not None
        assert current.message == "Test banner"
        assert current.severity == "warning"

    @pytest.mark.requirement("WL-229")
    def test_update_banner_replaces(
        self, propagator: MaintenanceBannerPropagator
    ) -> None:
        """Setting a new banner replaces the previous one."""
        propagator.set_banner("Old message")
        propagator.set_banner("New message", severity="critical")

        current = propagator.current()
        assert current is not None
        assert current.message == "New message"
        assert current.severity == "critical"

    @pytest.mark.requirement("WL-229")
    def test_lifecycle_set_activate_deactivate(
        self, propagator: MaintenanceBannerPropagator
    ) -> None:
        """Complete lifecycle: set -> activate -> deactivate."""
        # Initially inactive
        assert propagator.is_active() is False
        assert propagator.current() is None

        # Set banner
        propagator.set_banner("Maintenance", severity="info")
        assert propagator.is_active() is False
        assert propagator.current() is not None

        # Activate
        propagator.activate()
        assert propagator.is_active() is True
        assert propagator.current().active is True

        # Deactivate
        propagator.deactivate()
        assert propagator.is_active() is False
        assert propagator.current().active is False
