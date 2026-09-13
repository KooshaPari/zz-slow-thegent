"""Unit tests for GeoGuard (WP-35003)."""

import pytest

from thegent.security.geo_guard import GeoGuard, SovereigntyRule


@pytest.mark.unit
class TestGeoGuard:
    """GeoGuard (WP-35003)."""

    def test_eu_data_compliance(self) -> None:
        # @trace FR-SEC-001
        """EU data is blocked if outside EU regions."""
        guard = GeoGuard()

        # Valid region
        check1 = guard.validate_location("user-123", "PII_EU", "eu-west-1")
        assert check1.is_compliant is True

        # Restricted region
        check2 = guard.validate_location("user-123", "PII_EU", "us-east-1")
        assert check2.is_compliant is False
        assert any("us-east-1" in v for v in check2.violations)

    def test_custom_rule(self) -> None:
        # @trace FR-SEC-001
        """Can add and enforce custom sovereignty rules."""
        guard = GeoGuard()
        new_rule = SovereigntyRule(
            data_category="FINANCIAL_ASIA",
            allowed_regions={"ap-east-1", "ap-southeast-1"},
        )
        guard.add_rule(new_rule)

        check = guard.validate_location("tx-999", "FINANCIAL_ASIA", "eu-central-1")
        assert check.is_compliant is False
        assert "eu-central-1" in check.violations[0]

    def test_unknown_category_passes(self) -> None:
        # @trace FR-SEC-001
        """Unknown data categories pass by default if no rule exists."""
        guard = GeoGuard()
        check = guard.validate_location("file-001", "GENERAL_PUBLIC", "mars-base-1")
        assert check.is_compliant is True
