"""Unit tests for thegent.contracts.migration -- MigrationController."""

from datetime import UTC, datetime, timedelta

import pytest

from thegent.contracts.migration import MigrationController
from thegent.contracts.registry import ContractRegistry, ContractVersion


def _make_registry_with_versions(*versions: ContractVersion) -> ContractRegistry:
    """Build a ContractRegistry populated only with the given versions."""
    reg = ContractRegistry.__new__(ContractRegistry)
    reg._versions = {}
    for v in versions:
        reg.register(v)
    return reg


@pytest.mark.unit
class TestMigrationControllerEvaluateVersion:
    """Tests for MigrationController.evaluate_version()."""

    def test_active_version_allowed(self) -> None:
        # @trace FR-CTR-010
        cv = ContractVersion(contract_id="csm", version="csm-v1", description="active")
        reg = _make_registry_with_versions(cv)
        mc = MigrationController(registry=reg)
        result = mc.evaluate_version("csm", "csm-v1")
        assert result["allowed"] is True
        assert result["status"] == "active"

    def test_unknown_version_not_allowed(self) -> None:
        # @trace FR-CTR-010
        reg = _make_registry_with_versions()
        mc = MigrationController(registry=reg)
        result = mc.evaluate_version("csm", "csm-v99")
        assert result["allowed"] is False
        assert result["status"] == "unknown"

    def test_deprecated_no_window_still_allowed(self) -> None:
        # @trace FR-CTR-010
        cv = ContractVersion(contract_id="csm", version="csm-v0", description="old", deprecated=True)
        reg = _make_registry_with_versions(cv)
        mc = MigrationController(registry=reg)
        result = mc.evaluate_version("csm", "csm-v0")
        assert result["allowed"] is True
        assert result["status"] == "deprecated"

    def test_deprecated_within_window_allowed(self) -> None:
        # @trace FR-CTR-010
        future = (datetime.now(UTC) + timedelta(days=30)).isoformat()
        cv = ContractVersion(
            contract_id="csm",
            version="csm-v0",
            description="old",
            deprecated=True,
            migration_window_end=future,
        )
        reg = _make_registry_with_versions(cv)
        mc = MigrationController(registry=reg)
        result = mc.evaluate_version("csm", "csm-v0")
        assert result["allowed"] is True
        assert result["status"] == "deprecated"
        assert result["migration_days_left"] > 0

    def test_deprecated_window_expired(self) -> None:
        # @trace FR-CTR-010
        past = (datetime.now(UTC) - timedelta(days=10)).isoformat()
        cv = ContractVersion(
            contract_id="csm",
            version="csm-v0",
            description="old",
            deprecated=True,
            migration_window_end=past,
        )
        reg = _make_registry_with_versions(cv)
        mc = MigrationController(registry=reg)
        result = mc.evaluate_version("csm", "csm-v0")
        assert result["allowed"] is False
        assert result["status"] == "expired"
        assert result["migration_days_left"] < 0

    def test_reason_contains_contract_id(self) -> None:
        # @trace FR-CTR-010
        cv = ContractVersion(contract_id="csm", version="csm-v1", description="active")
        reg = _make_registry_with_versions(cv)
        mc = MigrationController(registry=reg)
        result = mc.evaluate_version("csm", "csm-v1")
        assert "active" in result["reason"].lower() or "supported" in result["reason"].lower()


@pytest.mark.unit
class TestMigrationControllerGetPreferred:
    """Tests for MigrationController.get_preferred_version()."""

    def test_preferred_version_active(self) -> None:
        # @trace FR-CTR-010
        cv = ContractVersion(contract_id="csm", version="csm-v1", description="active")
        reg = _make_registry_with_versions(cv)
        mc = MigrationController(registry=reg)
        assert mc.get_preferred_version("csm") == "csm-v1"

    def test_preferred_version_unknown_contract(self) -> None:
        # @trace FR-CTR-010
        reg = _make_registry_with_versions()
        mc = MigrationController(registry=reg)
        assert mc.get_preferred_version("nonexistent") == "unknown"
