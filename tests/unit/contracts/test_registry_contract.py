"""WL-142 contract tests for ``thegent.contracts.registry``.

Pins the canonical surface that closes the WL-141 pre-existing
broken-import flag (the ROB-010 critical-lane downgrade guard in
``_phase_bg_evaluate_contract`` referenced
``thegent.contracts.registry.get_registry().is_compatible()`` which did
not exist). WL-142 introduces:

* ``ContractVersionInfo`` dataclass — single metadata shape consumed by
  governance commands and the L9 guard.
* ``ContractRegistry.list_versions()`` — drives the ``thegent contracts
  registry`` governance command.
* ``ContractRegistry.is_compatible(requested, current)`` — drives
  ROB-010.
* ``get_registry()`` and ``CONTRACT_REGISTRY`` singleton — module-level
  lookup surface.

These tests are the canonical invariant suite; any change to the
field set or method semantics requires updating them deliberately.
"""

from __future__ import annotations

import importlib
from dataclasses import fields, is_dataclass

import pytest

pytestmark = pytest.mark.unit


REGISTRY_MODULE = "thegent.contracts.registry"


# ---------------------------------------------------------------------------
# 1. Module exports — surface pinned.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def registry_mod():
    return importlib.import_module(REGISTRY_MODULE)


@pytest.mark.parametrize(
    "export_name",
    [
        "CONTRACT_SCHEMA_VERSION",
        "CONTRACT_REGISTRY",
        "ContractRegistry",
        "ContractVersion",
        "ContractVersionInfo",
        "get_registry",
    ],
)
def test_registry_module_exports(registry_mod, export_name: str) -> None:
    """Module must export every canonical name."""
    assert hasattr(registry_mod, export_name), f"missing export {export_name!r}"


def test_contract_schema_version_is_nonempty_string(registry_mod) -> None:
    """``CONTRACT_SCHEMA_VERSION`` is the canonical, non-empty schema tag."""
    assert isinstance(registry_mod.CONTRACT_SCHEMA_VERSION, str)
    assert registry_mod.CONTRACT_SCHEMA_VERSION


def test_get_registry_returns_singleton(registry_mod) -> None:
    """``get_registry()`` returns the module-level ``CONTRACT_REGISTRY``."""
    assert registry_mod.get_registry() is registry_mod.CONTRACT_REGISTRY


# ---------------------------------------------------------------------------
# 2. ContractVersionInfo dataclass — governance-command field set.
# ---------------------------------------------------------------------------


def test_contract_version_info_is_dataclass(registry_mod) -> None:
    """``ContractVersionInfo`` is a dataclass with frozen field set."""
    assert is_dataclass(registry_mod.ContractVersionInfo)


@pytest.mark.parametrize(
    "field_name",
    [
        "contract_id",
        "version",
        "description",
        "deprecated",
        "migration_window_end",
    ],
)
def test_contract_version_info_has_field(registry_mod, field_name: str) -> None:
    """Every governance / ROB-010 field must exist on the dataclass."""
    assert field_name in {f.name for f in fields(registry_mod.ContractVersionInfo)}


def test_contract_version_info_defaults(registry_mod) -> None:
    """Optional fields default sensibly so legacy dict-payload callers work."""
    info = registry_mod.ContractVersionInfo(contract_id="x", version="v1")
    assert info.description == ""
    assert info.deprecated is False
    assert info.migration_window_end is None


# ---------------------------------------------------------------------------
# 3. ContractRegistry methods — list_versions() + is_compatible().
# ---------------------------------------------------------------------------


def test_list_versions_is_nonempty(registry_mod) -> None:
    """Canonical registry must surface ≥ 1 entry at import time."""
    versions = registry_mod.CONTRACT_REGISTRY.list_versions()
    assert versions, "CONTRACT_REGISTRY.list_versions() returned empty"
    assert all(isinstance(v, registry_mod.ContractVersionInfo) for v in versions)


def test_list_versions_is_sorted_stably(registry_mod) -> None:
    """Output ordering is deterministic across calls."""
    a = registry_mod.CONTRACT_REGISTRY.list_versions()
    b = registry_mod.CONTRACT_REGISTRY.list_versions()
    assert [v.contract_id for v in a] == [v.contract_id for v in b]
    assert a == sorted(a, key=lambda v: (v.contract_id, v.version))


def test_canonical_csm_entry_is_present(registry_mod) -> None:
    """``csm`` entry at ``CONTRACT_SCHEMA_VERSION`` is registered."""
    versions = registry_mod.CONTRACT_REGISTRY.list_versions()
    assert any(v.contract_id == "csm" and v.version == registry_mod.CONTRACT_SCHEMA_VERSION for v in versions)


def test_is_compatible_same_version_returns_true(registry_mod) -> None:
    """``is_compatible(current, current) == True`` — exact-match pass."""
    assert registry_mod.CONTRACT_REGISTRY.is_compatible(
        registry_mod.CONTRACT_SCHEMA_VERSION, registry_mod.CONTRACT_SCHEMA_VERSION
    )


@pytest.mark.parametrize(
    "requested",
    [
        "contract-schema-v0",  # downgrade
        "contract-schema-v2",  # forward drift
        "not-a-version",  # unknown
        "",  # empty
    ],
)
def test_is_compatible_mismatch_returns_false(registry_mod, requested: str) -> None:
    """ROB-010 semantic: any non-current version is incompatible."""
    assert not registry_mod.CONTRACT_REGISTRY.is_compatible(requested, registry_mod.CONTRACT_SCHEMA_VERSION)


# ---------------------------------------------------------------------------
# 4. Back-compat shim — legacy ``register(name, dict)`` callers still work.
# ---------------------------------------------------------------------------


def test_register_dict_payload_promotes_to_version_info(registry_mod) -> None:
    """Legacy ``register(name, dict)`` callers must round-trip through
    ``ContractVersionInfo`` and surface via ``list_versions``."""
    fresh = registry_mod.ContractRegistry()
    fresh.register(
        "legacy",
        {
            "version": "v0",
            "description": "legacy entry",
            "deprecated": True,
            "migration_window_end": "2026-01-01",
        },
    )
    entries = fresh.list_versions()
    assert len(entries) == 1
    e = entries[0]
    assert e.contract_id == "legacy"
    assert e.version == "v0"
    assert e.description == "legacy entry"
    assert e.deprecated is True
    assert e.migration_window_end == "2026-01-01"


def test_get_returns_version_info(registry_mod) -> None:
    """``get(name)`` returns the stored ``ContractVersionInfo``."""
    info = registry_mod.CONTRACT_REGISTRY.get("csm")
    assert info is not None
    assert info.contract_id == "csm"
    assert info.version == registry_mod.CONTRACT_SCHEMA_VERSION


def test_get_unknown_returns_none(registry_mod) -> None:
    """Unknown name returns ``None`` (not KeyError)."""
    assert registry_mod.CONTRACT_REGISTRY.get("nonexistent-contract") is None


# ---------------------------------------------------------------------------
# 5. ``__all__`` — re-export parity.
# ---------------------------------------------------------------------------


def test_all_exports_match_module_attributes(registry_mod) -> None:
    """Every name in ``__all__`` must be reachable as a module attribute."""
    for name in registry_mod.__all__:
        assert hasattr(registry_mod, name), f"__all__ entry {name!r} missing"
