"""Tests for thegent.integrations.prod_readiness — Production readiness gate.

@trace WL-220
"""

from __future__ import annotations

import pytest

from thegent.integrations.prod_readiness import (
    ProductionReadinessGate,
    ReadinessCheck,
)


class TestReadinessCheck:
    """Test ReadinessCheck dataclass. @trace WL-220"""

    @pytest.mark.requirement("WL-220")
    def test_create_check_with_message(self) -> None:
        """Can create a ReadinessCheck with all fields."""
        check = ReadinessCheck(
            name="connector_auth",
            passed=True,
            message="All connectors authenticated",
        )

        assert check.name == "connector_auth"
        assert check.passed is True
        assert check.message == "All connectors authenticated"

    @pytest.mark.requirement("WL-220")
    def test_create_check_default_message(self) -> None:
        """Can create a ReadinessCheck with default empty message."""
        check = ReadinessCheck(name="monitoring_active", passed=False)

        assert check.name == "monitoring_active"
        assert check.passed is False
        assert check.message == ""


class TestProductionReadinessGate:
    """Test ProductionReadinessGate operations. @trace WL-220"""

    @pytest.fixture
    def gate(self) -> ProductionReadinessGate:
        """Provide a ProductionReadinessGate instance."""
        return ProductionReadinessGate()

    @pytest.mark.requirement("WL-220")
    def test_required_checks_classvar(self) -> None:
        """REQUIRED ClassVar has all 6 required check names."""
        assert len(ProductionReadinessGate.REQUIRED) == 6
        assert "connector_auth" in ProductionReadinessGate.REQUIRED
        assert "mapping_config" in ProductionReadinessGate.REQUIRED
        assert "startup_validation" in ProductionReadinessGate.REQUIRED
        assert "rollback_ready" in ProductionReadinessGate.REQUIRED
        assert "monitoring_active" in ProductionReadinessGate.REQUIRED
        assert "compliance_baseline" in ProductionReadinessGate.REQUIRED

    @pytest.mark.requirement("WL-220")
    def test_add_single_check(self, gate: ProductionReadinessGate) -> None:
        """Can add a single readiness check."""
        check = ReadinessCheck("connector_auth", passed=True)
        gate.add(check)

        # Verify by checking missing_checks doesn't include it
        missing = gate.missing_checks()
        assert "connector_auth" not in missing

    @pytest.mark.requirement("WL-220")
    def test_add_overwrites_previous(self, gate: ProductionReadinessGate) -> None:
        """Adding a check with same name overwrites previous."""
        gate.add(ReadinessCheck("connector_auth", passed=False))
        gate.add(ReadinessCheck("connector_auth", passed=True))

        failed = gate.failed_checks()
        assert "connector_auth" not in failed

    @pytest.mark.requirement("WL-220")
    def test_evaluate_false_when_empty(self, gate: ProductionReadinessGate) -> None:
        """evaluate returns False when no checks added."""
        assert gate.evaluate() is False

    @pytest.mark.requirement("WL-220")
    def test_evaluate_false_with_missing_checks(
        self, gate: ProductionReadinessGate
    ) -> None:
        """evaluate returns False when some required checks missing."""
        gate.add(ReadinessCheck("connector_auth", passed=True))
        gate.add(ReadinessCheck("mapping_config", passed=True))

        assert gate.evaluate() is False

    @pytest.mark.requirement("WL-220")
    def test_evaluate_false_when_check_fails(
        self, gate: ProductionReadinessGate
    ) -> None:
        """evaluate returns False when any check failed."""
        # Add all required checks
        for check_name in ProductionReadinessGate.REQUIRED:
            gate.add(ReadinessCheck(check_name, passed=True))

        # Fail one
        gate.add(ReadinessCheck("connector_auth", passed=False))

        assert gate.evaluate() is False

    @pytest.mark.requirement("WL-220")
    def test_evaluate_true_when_all_pass(self, gate: ProductionReadinessGate) -> None:
        """evaluate returns True when all required checks pass."""
        for check_name in ProductionReadinessGate.REQUIRED:
            gate.add(ReadinessCheck(check_name, passed=True))

        assert gate.evaluate() is True

    @pytest.mark.requirement("WL-220")
    def test_missing_checks_empty_when_all_added(
        self, gate: ProductionReadinessGate
    ) -> None:
        """missing_checks returns empty list when all checks added."""
        for check_name in ProductionReadinessGate.REQUIRED:
            gate.add(ReadinessCheck(check_name, passed=True))

        assert gate.missing_checks() == []

    @pytest.mark.requirement("WL-220")
    def test_missing_checks_returns_unaddedonly(
        self, gate: ProductionReadinessGate
    ) -> None:
        """missing_checks returns only checks not yet added."""
        gate.add(ReadinessCheck("connector_auth", passed=True))
        gate.add(ReadinessCheck("monitoring_active", passed=True))

        missing = gate.missing_checks()
        assert len(missing) == 4
        assert "connector_auth" not in missing
        assert "monitoring_active" not in missing

    @pytest.mark.requirement("WL-220")
    def test_failed_checks_empty_when_all_pass(
        self, gate: ProductionReadinessGate
    ) -> None:
        """failed_checks returns empty list when all pass."""
        for check_name in ProductionReadinessGate.REQUIRED:
            gate.add(ReadinessCheck(check_name, passed=True))

        assert gate.failed_checks() == []

    @pytest.mark.requirement("WL-220")
    def test_failed_checks_returns_failures_only(
        self, gate: ProductionReadinessGate
    ) -> None:
        """failed_checks returns only checks that failed."""
        gate.add(ReadinessCheck("connector_auth", passed=False))
        gate.add(ReadinessCheck("mapping_config", passed=True))
        gate.add(ReadinessCheck("startup_validation", passed=False))

        failed = gate.failed_checks()
        assert len(failed) == 2
        assert "connector_auth" in failed
        assert "startup_validation" in failed
        assert "mapping_config" not in failed

    @pytest.mark.requirement("WL-220")
    def test_report_when_ready(self, gate: ProductionReadinessGate) -> None:
        """report returns correct structure when ready."""
        for check_name in ProductionReadinessGate.REQUIRED:
            gate.add(ReadinessCheck(check_name, passed=True))

        report = gate.report()

        assert report["ready"] is True
        assert len(report["passed"]) == 6
        assert report["failed"] == []
        assert report["missing"] == []

    @pytest.mark.requirement("WL-220")
    def test_report_when_not_ready(self, gate: ProductionReadinessGate) -> None:
        """report returns correct structure when not ready."""
        gate.add(ReadinessCheck("connector_auth", passed=False))
        gate.add(ReadinessCheck("mapping_config", passed=True))

        report = gate.report()

        assert report["ready"] is False
        assert "mapping_config" in report["passed"]
        assert "connector_auth" in report["failed"]
        assert len(report["missing"]) == 4
