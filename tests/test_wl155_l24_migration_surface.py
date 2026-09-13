"""WL155 — L24 Migration: hardening tests for the canonical surface.

Seals the contracts-migration module end-to-end:

* ``MigrationController(registry=...)`` accepts a fresh registry and
  resolves ``registry=None`` to ``CONTRACT_REGISTRY``.
* ``evaluate_version`` returns the canonical dict shape (``allowed``,
  ``status``, ``contract``, ``version``, ``reason``,
  ``migration_days_left``) and respects active / deprecated-no-window /
  deprecated-within-window / deprecated-window-expired / unknown /
  malformed-window branches.
* ``get_preferred_version`` returns the lexicographically highest active
  version registered for a contract; falls back to the deprecated pool
  if every entry is deprecated; returns ``"unknown"`` for un-registered
  contracts.
* The ``migrations`` queue + ``run()`` drain pair is reversible to
  callers (returns the count applied, empties the queue, idempotent
  on the empty queue).
* ``ContractRegistry`` preserves the legacy ``_versions`` alias for
  test fixtures that bypass ``__init__`` via ``__new__``, plus the
  polymorphic ``register(name, dict)`` / ``register(version_info)``
  shims.
* Re-export: ``thegent.contracts.registry.ContractVersion`` is the same
  object as ``ContractVersionInfo``.

These tests intentionally do NOT touch ``thegent/agents/cliproxy_manager.py``
or the cliproxy merge-conflict preservation area.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from thegent.contracts.migration import MigrationController
from thegent.contracts.registry import (
    CONTRACT_REGISTRY,
    CONTRACT_SCHEMA_VERSION,
    ContractRegistry,
    ContractVersion,
    ContractVersionInfo,
    get_registry,
)

# ---------------------------------------------------------------------------
# Helpers (mirrors the test_.._migration.py pattern)
# ---------------------------------------------------------------------------


def _make_registry_with_versions(*versions: ContractVersionInfo) -> ContractRegistry:
    """Build a ContractRegistry populated only with the given versions."""
    reg = ContractRegistry.__new__(ContractRegistry)
    reg._versions = {}
    for v in versions:
        reg.register(v)
    return reg


def _iso(days_from_now: int) -> str:
    return (datetime.now(UTC) + timedelta(days=days_from_now)).isoformat()


# ---------------------------------------------------------------------------
# MigrationController.evaluate_version shape + branches
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMigrationControllerEvaluateVersionShape:
    """The evaluate_version return dict exposes every required key."""

    def test_returns_expected_keys(self) -> None:
        # @trace FR-CTR-010
        cv = ContractVersion(contract_id="csm", version="csm-v1", description="active")
        reg = _make_registry_with_versions(cv)
        mc = MigrationController(registry=reg)
        result = mc.evaluate_version("csm", "csm-v1")
        for key in (
            "allowed",
            "status",
            "contract",
            "version",
            "reason",
            "migration_days_left",
        ):
            assert key in result, f"missing key: {key}"

    def test_active_status_set(self) -> None:
        cv = ContractVersion(contract_id="csm", version="csm-v1", description="active")
        reg = _make_registry_with_versions(cv)
        mc = MigrationController(registry=reg)
        result = mc.evaluate_version("csm", "csm-v1")
        assert result["status"] == "active"
        assert result["allowed"] is True
        assert result["migration_days_left"] == 0

    def test_unknown_status_for_unregistered_version(self) -> None:
        reg = _make_registry_with_versions()
        mc = MigrationController(registry=reg)
        result = mc.evaluate_version("nope", "v0")
        assert result["status"] == "unknown"
        assert result["allowed"] is False
        assert result["reason"]
        assert "not registered" in result["reason"].lower()

    def test_deprecated_no_window(self) -> None:
        cv = ContractVersion(
            contract_id="csm",
            version="csm-v0",
            description="old",
            deprecated=True,
        )
        reg = _make_registry_with_versions(cv)
        mc = MigrationController(registry=reg)
        result = mc.evaluate_version("csm", "csm-v0")
        assert result["status"] == "deprecated"
        assert result["allowed"] is True
        assert result["migration_days_left"] == 0

    def test_deprecated_within_window(self) -> None:
        cv = ContractVersion(
            contract_id="csm",
            version="csm-v0",
            description="old",
            deprecated=True,
            migration_window_end=_iso(30),
        )
        reg = _make_registry_with_versions(cv)
        mc = MigrationController(registry=reg)
        result = mc.evaluate_version("csm", "csm-v0")
        assert result["status"] == "deprecated"
        assert result["allowed"] is True
        # Allow a small clock-skew window between the helper and the
        # controller when computing days remaining.
        assert 29.0 <= result["migration_days_left"] <= 30.0

    def test_deprecated_window_expired(self) -> None:
        cv = ContractVersion(
            contract_id="csm",
            version="csm-v0",
            description="old",
            deprecated=True,
            migration_window_end=_iso(-10),
        )
        reg = _make_registry_with_versions(cv)
        mc = MigrationController(registry=reg)
        result = mc.evaluate_version("csm", "csm-v0")
        assert result["status"] == "expired"
        assert result["allowed"] is False
        assert result["migration_days_left"] < 0
        assert result["migration_days_left"] >= -10.5

    def test_malformed_migration_window_falls_back_to_allowed(self) -> None:
        cv = ContractVersion(
            contract_id="csm",
            version="csm-v0",
            description="old",
            deprecated=True,
            migration_window_end="not-a-date",
        )
        reg = _make_registry_with_versions(cv)
        mc = MigrationController(registry=reg)
        result = mc.evaluate_version("csm", "csm-v0")
        assert result["status"] == "deprecated"
        assert result["allowed"] is True
        assert result["migration_days_left"] == 0

    def test_naive_datetime_window_treated_as_utc(self) -> None:
        cv = ContractVersion(
            contract_id="csm",
            version="csm-v0",
            description="old",
            deprecated=True,
            migration_window_end=(datetime.now(UTC) + timedelta(days=2))
            .replace(tzinfo=None)
            .isoformat(),
        )
        reg = _make_registry_with_versions(cv)
        mc = MigrationController(registry=reg)
        result = mc.evaluate_version("csm", "csm-v0")
        # Naive datetimes become UTC, so the window is in the future →
        # allowed with positive days_left.
        assert result["allowed"] is True


# ---------------------------------------------------------------------------
# MigrationController.get_preferred_version
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMigrationControllerGetPreferredVersion:
    """Pinned behavior for get_preferred_version()."""

    def test_preferred_with_only_active(self) -> None:
        cv = ContractVersion(contract_id="csm", version="csm-v1", description="active")
        reg = _make_registry_with_versions(cv)
        mc = MigrationController(registry=reg)
        assert mc.get_preferred_version("csm") == "csm-v1"

    def test_preferred_unknown_contract(self) -> None:
        reg = _make_registry_with_versions()
        mc = MigrationController(registry=reg)
        assert mc.get_preferred_version("nope") == "unknown"

    def test_preferred_picks_highest_active_over_deprecated(self) -> None:
        v_old = ContractVersion(
            contract_id="csm",
            version="csm-v0",
            description="old",
            deprecated=True,
        )
        v_new = ContractVersion(
            contract_id="csm", version="csm-v1", description="active"
        )
        reg = _make_registry_with_versions(v_old, v_new)
        mc = MigrationController(registry=reg)
        assert mc.get_preferred_version("csm") == "csm-v1"

    def test_preferred_falls_back_to_highest_when_all_deprecated(self) -> None:
        v_a = ContractVersion(
            contract_id="csm",
            version="csm-v0",
            description="old",
            deprecated=True,
        )
        v_b = ContractVersion(
            contract_id="csm",
            version="csm-v1",
            description="also old",
            deprecated=True,
        )
        reg = _make_registry_with_versions(v_a, v_b)
        mc = MigrationController(registry=reg)
        # Lexicographic highest wins the fallback.
        assert mc.get_preferred_version("csm") == "csm-v1"

    def test_preferred_ignores_other_contract_ids(self) -> None:
        v_other = ContractVersion(
            contract_id="other", version="other-v9", description="x"
        )
        v_csm = ContractVersion(
            contract_id="csm", version="csm-v1", description="active"
        )
        reg = _make_registry_with_versions(v_other, v_csm)
        mc = MigrationController(registry=reg)
        assert mc.get_preferred_version("csm") == "csm-v1"


# ---------------------------------------------------------------------------
# MigrationController queue + run
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMigrationControllerQueueAndRun:
    """Drain semantics for the migrations queue."""

    def test_default_queue_is_empty(self) -> None:
        mc = MigrationController()
        assert mc.migrations == []

    def test_queue_migration_appends(self) -> None:
        mc = MigrationController()
        mc.queue_migration({"contract": "csm", "to": "csm-v1"})
        assert mc.migrations == [{"contract": "csm", "to": "csm-v1"}]

    def test_run_returns_count_and_empties_queue(self) -> None:
        mc = MigrationController()
        mc.queue_migration({"contract": "csm", "to": "csm-v1"})
        mc.queue_migration({"contract": "csm", "to": "csm-v0-deprecation"})
        applied = mc.run()
        assert applied == 2
        assert mc.migrations == []

    def test_run_on_empty_queue_returns_zero(self) -> None:
        mc = MigrationController()
        assert mc.run() == 0
        assert mc.run() == 0  # idempotent

    def test_run_does_not_touch_registry(self) -> None:
        cv = ContractVersion(contract_id="csm", version="csm-v1", description="active")
        reg = _make_registry_with_versions(cv)
        mc = MigrationController(registry=reg)
        mc.queue_migration({"contract": "csm", "to": "csm-v1"})
        before = reg.list_versions()
        mc.run()
        assert reg.list_versions() == before


# ---------------------------------------------------------------------------
# Default registry resolution
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMigrationControllerDefaultRegistry:
    """``registry=None`` resolves to ``CONTRACT_REGISTRY``."""

    def test_default_registry_attribute(self) -> None:
        mc = MigrationController()
        assert mc.registry is CONTRACT_REGISTRY

    def test_default_registry_lookup_for_csm(self) -> None:
        # The canonical registry ships pre-populated with csm@csm-v1.
        mc = MigrationController()
        result = mc.evaluate_version("csm", CONTRACT_SCHEMA_VERSION)
        assert result["allowed"] is True
        assert result["status"] == "active"

    def test_explicit_none_after_default(self) -> None:
        # Passing ``registry=None`` explicitly must yield the same singleton.
        mc = MigrationController(registry=None)
        assert mc.registry is CONTRACT_REGISTRY
        assert mc.get_preferred_version("csm") == CONTRACT_SCHEMA_VERSION

    def test_get_registry_singleton_is_same_object(self) -> None:
        assert get_registry() is CONTRACT_REGISTRY


# ---------------------------------------------------------------------------
# Registry back-compat
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestContractRegistryBackCompat:
    """Pins the legacy ``_versions`` alias + polymorphic register."""

    def test_versions_alias_is_same_dict_as_contracts(self) -> None:
        reg = ContractRegistry()
        reg.register("csm", {"version": "csm-v1", "description": "active"})
        assert reg._versions is reg._contracts
        assert reg.list_versions() and "csm" in reg._versions

    def test_register_accepts_version_info_positional(self) -> None:
        reg = ContractRegistry()
        cv = ContractVersion(contract_id="csm", version="csm-v1", description="active")
        reg.register(cv)
        info = reg.get("csm")
        assert info is not None
        assert info.version == "csm-v1"

    def test_register_accepts_name_and_dict(self) -> None:
        reg = ContractRegistry()
        reg.register("legacy", {"version": "task-tool-18", "description": "d"})
        assert reg.get("legacy").version == "task-tool-18"

    def test_register_with_none_is_noop(self) -> None:
        reg = ContractRegistry()
        reg.register(None, None)
        assert reg.list_versions() == []

    def test_register_contract_version_method(self) -> None:
        reg = ContractRegistry()
        cv = ContractVersion(
            contract_id="csm",
            version="csm-v2",
            description="future",
            deprecated=False,
        )
        reg.register_contract_version(cv)
        assert reg.get("csm").version == "csm-v2"

    def test_test_helper_sets_versions_alias_works(self) -> None:
        # This is exactly the helper pattern used in
        # tests/test_unit_contracts_migration.py.
        reg = ContractRegistry.__new__(ContractRegistry)
        reg._versions = {}
        cv = ContractVersion(contract_id="csm", version="csm-v1", description="active")
        reg.register(cv)
        # list_versions must surface the registration whether the alias
        # or the canonical storage was used.
        assert any(v.version == "csm-v1" for v in reg.list_versions())


# ---------------------------------------------------------------------------
# ContractVersion alias
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestContractVersionAlias:
    """``ContractVersion`` is the canonical ``ContractVersionInfo`` dataclass."""

    def test_contract_version_is_contract_version_info(self) -> None:
        assert ContractVersion is ContractVersionInfo

    def test_contract_version_constructs_with_contract_id(self) -> None:
        cv = ContractVersion(contract_id="csm", version="csm-v1", description="x")
        assert cv.contract_id == "csm"
        assert cv.version == "csm-v1"
        assert cv.deprecated is False
        assert cv.migration_window_end is None
