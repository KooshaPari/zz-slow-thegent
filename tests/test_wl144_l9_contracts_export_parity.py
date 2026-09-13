"""WL144 — L9 contract: ``thegent.contracts`` ↔ ``thegent.contracts.registry`` parity.

ROB-010 regression suite for the L9 (Complexity Management) lane.
This test pins the canonical ROB-010 surface so that
``from thegent.contracts import X`` and
``from thegent.contracts.registry import X`` resolve to the **same**
object for every governance-relevant symbol.

Why this exists
---------------
During the WL142/WL143 trajectory we discovered that ``thegent/contracts/__init__.py``
was an auto-generated stub that re-exported the legacy ``ADAPTER_REGISTRY`` /
``CSMPhase`` / ``CanonicalStructuredMessage`` symbols from ``adapters.py`` /
``csm.py`` but never re-exported the canonical ROB-010 governance surface
(``get_registry``, ``CONTRACT_SCHEMA_VERSION``, ``ContractRegistry``, ...).
That meant callers using ``from thegent.contracts import get_registry``
would crash with ``ImportError``, while callers using
``from thegent.contracts.registry import get_registry`` got the real
``ContractRegistry`` instance.

WL144 closes that gap by promoting ``thegent/contracts/__init__.py`` to a
proper canonical re-export layer that pins the ROB-010 surface and
preserves every legacy symbol for back-compat. This test asserts both
parity (every shared symbol is the same object) and back-compat
(every legacy symbol still resolves).

These tests intentionally do NOT touch ``thegent/agents/cliproxy_manager.py``
(preserve unrelated worktree changes — that file has a known merge conflict
preserved at ``/tmp/cliproxy_conflict_preserved.py``).
"""

from __future__ import annotations

import importlib
import inspect

import pytest

# ---------------------------------------------------------------------------
# Canonical ROB-010 surface — MUST be the SAME object via either import path
# ---------------------------------------------------------------------------


def test_get_registry_is_same_object_via_both_paths():
    """``get_registry`` must be ``thegent.contracts.registry.get_registry``."""
    from thegent.contracts import get_registry as pkg_get_registry
    from thegent.contracts.registry import get_registry as mod_get_registry

    assert pkg_get_registry is mod_get_registry, (
        "L9 REGRESSION: thegent.contracts.get_registry is not "
        "thegent.contracts.registry.get_registry — the canonical ROB-010 "
        "surface has diverged again. Re-pin src/thegent/contracts/__init__.py."
    )


def test_get_registry_singleton_returns_same_instance_each_call():
    from thegent.contracts import get_registry
    from thegent.contracts.registry import get_registry as mod_get_registry

    r1 = get_registry()
    r2 = get_registry()
    r3 = mod_get_registry()
    assert r1 is r2 is r3, "get_registry() must return a singleton"


def test_contract_schema_version_is_same_string_via_both_paths():
    from thegent.contracts import CONTRACT_SCHEMA_VERSION as pkg_csv  # noqa: N811
    from thegent.contracts.registry import (
        CONTRACT_SCHEMA_VERSION as mod_csv,  # noqa: N811
    )

    assert pkg_csv == mod_csv == "csm-v1", f"L9 REGRESSION: schema version drift — pkg={pkg_csv!r} mod={mod_csv!r}"


def test_contract_registry_class_is_same_via_both_paths():
    from thegent.contracts import ContractRegistry as pkg_class  # noqa: N813
    from thegent.contracts.registry import ContractRegistry as mod_class  # noqa: N813

    assert pkg_class is mod_class


def test_contract_registry_is_a_class():
    from thegent.contracts.registry import ContractRegistry

    assert inspect.isclass(ContractRegistry)


def test_contract_version_class_is_same_via_both_paths():
    from thegent.contracts import ContractVersion as pkg_class  # noqa: N813
    from thegent.contracts.registry import ContractVersion as mod_class  # noqa: N813

    assert pkg_class is mod_class


def test_contract_version_info_class_is_same_via_both_paths():
    from thegent.contracts import ContractVersionInfo as pkg_class  # noqa: N813
    from thegent.contracts.registry import (
        ContractVersionInfo as mod_class,  # noqa: N813
    )

    assert pkg_class is mod_class


def test_contract_registry_module_instance_is_same_via_both_paths():
    from thegent.contracts import CONTRACT_REGISTRY as pkg_inst  # noqa: N811
    from thegent.contracts.registry import CONTRACT_REGISTRY as mod_inst  # noqa: N811

    assert pkg_inst is mod_inst
    # And the module-level CONTRACT_REGISTRY must match the singleton
    from thegent.contracts import get_registry

    assert pkg_inst is get_registry()


def test_is_compatible_is_method_not_free_function():
    """``is_compatible`` lives on the ContractRegistry class, not at module scope."""
    import thegent.contracts as pkg

    # Must NOT be a module-level free function (we removed it intentionally).
    assert "is_compatible" not in vars(pkg), "is_compatible leaked to module scope — it must remain a method only."
    # Must be a method on the class and the instance.
    from thegent.contracts import ContractRegistry, get_registry

    assert hasattr(ContractRegistry, "is_compatible")
    assert callable(ContractRegistry.is_compatible)
    assert hasattr(get_registry(), "is_compatible")


def test_is_compatible_returns_expected_values():
    from thegent.contracts import CONTRACT_SCHEMA_VERSION, get_registry

    r = get_registry()
    assert r.is_compatible(CONTRACT_SCHEMA_VERSION, CONTRACT_SCHEMA_VERSION) is True
    assert r.is_compatible("contract-schema-v0", CONTRACT_SCHEMA_VERSION) is False
    # Forward-version is rejected (no future planning permitted).
    assert r.is_compatible("contract-schema-v99", CONTRACT_SCHEMA_VERSION) is False


# ---------------------------------------------------------------------------
# Back-compat surface — every legacy symbol MUST still resolve
# ---------------------------------------------------------------------------


def test_backcompat_adapter_registry_resolves():
    """The legacy ``ADAPTER_REGISTRY`` symbol must still resolve."""
    from thegent.contracts import ADAPTER_REGISTRY

    # Could be either a class (with classmethod access) or an instance;
    # both shapes must work because callers use ``ADAPTER_REGISTRY.keys()``
    # or ``ADAPTER_REGISTRY.register(...)`` polymorphically.
    assert ADAPTER_REGISTRY is not None


def test_backcompat_adapter_result_resolves():
    from thegent.contracts import AdapterResult

    assert inspect.isclass(AdapterResult)


def test_backcompat_output_adapter_resolves():
    from thegent.contracts import OutputAdapter

    assert inspect.isclass(OutputAdapter)


def test_backcompat_get_adapter_resolves():
    from thegent.contracts import get_adapter

    assert callable(get_adapter)


def test_backcompat_normalize_output_resolves():
    from thegent.contracts import normalize_output

    assert callable(normalize_output)


def test_backcompat_csm_phase_resolves():
    from thegent.contracts import CSMPhase

    # Enum or class — both are valid shapes; just must be a class-like.
    assert CSMPhase is not None
    assert hasattr(CSMPhase, "__members__") or inspect.isclass(CSMPhase)


def test_backcompat_csm_status_resolves():
    from thegent.contracts import CSMStatus

    assert CSMStatus is not None
    assert hasattr(CSMStatus, "__members__") or inspect.isclass(CSMStatus)


def test_backcompat_canonical_structured_message_resolves():
    from thegent.contracts import CanonicalStructuredMessage

    assert inspect.isclass(CanonicalStructuredMessage)


# ---------------------------------------------------------------------------
# Contract registry behaviour pinned at the package boundary
# ---------------------------------------------------------------------------


def test_package_get_registry_lists_csm_v1():
    from thegent.contracts import CONTRACT_SCHEMA_VERSION, get_registry

    versions = get_registry().list_versions()
    ids = [v.contract_id for v in versions]
    assert "csm" in ids, f"CSM contract missing from registry: {ids}"
    # The listed version must match the canonical schema constant.
    csm_versions = [v.version for v in versions if v.contract_id == "csm"]
    assert CONTRACT_SCHEMA_VERSION in csm_versions


def test_package_module_parity_holds_after_reload():
    """Reload the package and the module — symbols must STILL be the same object."""
    import thegent.contracts as pkg
    import thegent.contracts.registry as mod

    # Reload the registry first (to get a fresh singleton), then the package.
    importlib.reload(mod)
    importlib.reload(pkg)

    from thegent.contracts import get_registry as pkg_get_registry
    from thegent.contracts.registry import get_registry as mod_get_registry

    assert pkg_get_registry is mod_get_registry


def test_dunder_all_lists_canonical_surface():
    """The ``__all__`` must enumerate the canonical surface explicitly."""
    import thegent.contracts as pkg

    canonical = {
        "CONTRACT_REGISTRY",
        "CONTRACT_SCHEMA_VERSION",
        "ContractRegistry",
        "ContractVersion",
        "ContractVersionInfo",
        "get_registry",
    }
    backcompat = {
        "ADAPTER_REGISTRY",
        "AdapterResult",
        "OutputAdapter",
        "get_adapter",
        "normalize_output",
        "CSMPhase",
        "CSMStatus",
        "CanonicalStructuredMessage",
    }
    declared = set(pkg.__all__)
    missing_canonical = canonical - declared
    missing_backcompat = backcompat - declared
    assert not missing_canonical, f"Missing canonical exports in __all__: {missing_canonical}"
    assert not missing_backcompat, f"Missing back-compat exports in __all__: {missing_backcompat}"
    # ``is_compatible`` must NOT be in __all__ — it is a method, not a free function.
    assert "is_compatible" not in declared, "is_compatible leaked into __all__ — must remain method-only."


# ---------------------------------------------------------------------------
# Governance commands must continue to import the canonical surface
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "module_name",
    [
        "thegent.cli.governance.governance_policy_cmds",
        "thegent.cli.governance.governance_policy_core_cmds",
        "thegent.cli.governance.governance_policy_contracts_cmds",
    ],
)
def test_governance_modules_can_resolve_get_registry(module_name):
    """Each governance command module must be able to import ``get_registry``.

    WL142 locked the import sites to
    ``from thegent.contracts.registry import get_registry`` inside the
    command functions. The imports are lazy (inside the function body),
    not at module top-level, so we verify two things instead:

    1. The module loads without error.
    2. The module source pins the canonical import line
       ``from thegent.contracts.registry import get_registry``.

    Together these guarantee the WL142 import pinning survived the
    WL144 re-export layer changes.
    """
    importlib.import_module(module_name)
    mod_source = importlib.import_module(module_name).__file__
    assert mod_source is not None
    with open(mod_source, encoding="utf-8") as fh:
        source = fh.read()

    assert "from thegent.contracts.registry import get_registry" in source, (
        f"{module_name} no longer pins the canonical ROB-010 surface "
        f"(missing `from thegent.contracts.registry import get_registry`). "
        f"Re-pin WL142 import site."
    )

    # And actually verify that the canonical surface resolves at runtime.
    from thegent.contracts.registry import get_registry as canonical_get_registry

    assert callable(canonical_get_registry)
    assert canonical_get_registry() is not None


# ---------------------------------------------------------------------------
# Divergence guard: package-level stub removal
# ---------------------------------------------------------------------------


def test_package_no_longer_exposes_adapter_registry_class_directly():
    """The package ``ADAPTER_REGISTRY`` must expose the canonical AdapterRegistry instance.

    After WL144 the legacy ``ADAPTER_REGISTRY`` symbol must resolve to the
    canonical instance from ``thegent/contracts/adapters.py`` and retain
    its duck-type surface: ``.register(name, adapter)``, ``.get(name)``,
    ``.list_adapters()``. We pin those three methods here because they are
    the contract legacy callers depend on (the prior ``__init__.py`` stub
    documented ``.keys()`` / ``.register()`` / ``.get(...)`` but the
    canonical class actually exposes ``.list_adapters()`` instead of
    ``.keys()``; WL144 makes the contract explicit).
    """
    from thegent.contracts import ADAPTER_REGISTRY
    from thegent.contracts.adapters import ADAPTER_REGISTRY as canonical  # noqa: N811

    assert ADAPTER_REGISTRY is canonical, (
        "ADAPTER_REGISTRY has diverged from the canonical instance — "
        "WL144 must re-export it from thegent.contracts.adapters."
    )

    # Canonical duck-type surface that legacy callers depend on.
    for method_name in ("register", "get", "list_adapters"):
        assert hasattr(ADAPTER_REGISTRY, method_name), (
            f"ADAPTER_REGISTRY lost method {method_name!r} — legacy callers will break."
        )
        assert callable(getattr(ADAPTER_REGISTRY, method_name))

    # Back-compat surface (HEAD's stub-era classmethod API).
    assert hasattr(ADAPTER_REGISTRY, "keys"), (
        "ADAPTER_REGISTRY.keys() must remain callable for back-compat "
        "with the stub-era API consumed by tests/test_contract_conformance.py."
    )
    assert ADAPTER_REGISTRY.keys() == ADAPTER_REGISTRY.list_adapters(), (
        "ADAPTER_REGISTRY.keys() must mirror list_adapters() — they are documented aliases (WL144 contract)."
    )
    assert hasattr(ADAPTER_REGISTRY, "__getitem__"), (
        "ADAPTER_REGISTRY[name] subscript access must remain for back-compat "
        "with the stub-era API consumed by tests/test_contract_conformance.py."
    )


def test_canonical_surface_is_import_order_independent():
    """The canonical surface must not depend on import order.

    If a legacy module happens to be imported first, ``thegent.contracts``
    must still resolve the ROB-010 symbols from the registry module.
    """
    # Force-import the legacy modules first.
    # Now re-import the package and check.
    import thegent.contracts as pkg
    import thegent.contracts.adapters  # noqa: F401
    import thegent.contracts.csm  # noqa: F401
    import thegent.contracts.registry as reg

    assert pkg.get_registry is reg.get_registry
    assert pkg.CONTRACT_SCHEMA_VERSION == reg.CONTRACT_SCHEMA_VERSION
    assert pkg.ContractRegistry is reg.ContractRegistry
    assert pkg.CONTRACT_REGISTRY is reg.CONTRACT_REGISTRY
