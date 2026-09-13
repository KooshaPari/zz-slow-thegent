"""WL-142 L9 ROB-010 critical-lane stability regression suite.

Locks down the WL-142 governance/stability pass that closes the
explicit pre-existing-broken-import flag from the WL-141 session
(``_phase_bg_evaluate_contract`` referenced
``thegent.contracts.registry.get_registry().is_compatible()`` which
did not exist — would have crashed any critical-lane bg dispatch in
production).

Coverage:

* ``_phase_bg_evaluate_contract`` resolves every import without
  ``ImportError`` (the latent crash).
* ROB-010 critical-lane happy path: ``lane='critical'`` with the
  canonical ``CONTRACT_SCHEMA_VERSION`` returns ``(None, version)``.
* ROB-010 critical-lane downgrade path: ``lane='critical'`` with a
  non-current version returns an error payload tagged with the
  ROB-010 message and the ``run_id`` of the caller.
* Standard-lane acceptance: any ``contract_version`` returns
  ``(None, requested_version)`` (ROB-010 only blocks critical).
* Wire-up regression: ``bg_impl_core`` still delegates to
  ``_phase_bg_evaluate_contract``.
* Registry integration: ``is_compatible`` is wired to the canonical
  ``CONTRACT_REGISTRY`` singleton.
"""

from __future__ import annotations

import importlib
import inspect

import pytest

pytestmark = pytest.mark.unit


HELPERS_MODULE = "thegent.cli.services.run_execution_core_helpers"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def helpers_module():
    return importlib.import_module(HELPERS_MODULE)


@pytest.fixture(scope="module")
def bg_impl_core_source(helpers_module) -> str:
    return inspect.getsource(helpers_module.bg_impl_core)


# ---------------------------------------------------------------------------
# 1. Import resolution — the latent crash that WL-142 fixes.
# ---------------------------------------------------------------------------


def test_phase_bg_evaluate_contract_resolves_imports(helpers_module) -> None:
    """Calling the helper must NOT raise ``ImportError`` for the
    ``thegent.contracts.registry.get_registry`` symbol (the WL-141
    pre-existing bug).

    The fix adds ``get_registry()`` and ``is_compatible()`` to
    ``thegent.contracts.registry``; the critical-lane branch in
    ``_phase_bg_evaluate_contract`` now resolves cleanly.
    """
    # Drive both branches: standard and critical. The critical branch
    # used to blow up with ``ImportError: cannot import name 'get_registry'``
    # at the ``from thegent.contracts.registry import get_registry`` line.
    err_std, _requested_std = helpers_module._phase_bg_evaluate_contract(
        contract_version="contract-schema-v0",
        lane="standard",
        rid="run-import-std",
    )
    err_crit, _requested_crit = helpers_module._phase_bg_evaluate_contract(
        contract_version="contract-schema-v0",
        lane="critical",
        rid="run-import-crit",
    )
    # Both branches resolve without ImportError. Standard returns None
    # error; critical returns the ROB-010 error payload.
    assert err_std is None
    assert err_crit is not None
    assert "ROB-010" in err_crit["error"]


# ---------------------------------------------------------------------------
# 2. ROB-010 happy path — critical lane with canonical version.
# ---------------------------------------------------------------------------


def test_rob010_happy_path(helpers_module) -> None:
    """``lane='critical'`` + canonical ``CONTRACT_SCHEMA_VERSION`` → no error.

    This is the path that would never have been reached in production
    because the previous broken import crashed *before* the version
    comparison ran. Now the helper returns ``(None, current_version)``
    and the caller proceeds.
    """
    from thegent.contracts.registry import CONTRACT_SCHEMA_VERSION

    err, requested = helpers_module._phase_bg_evaluate_contract(
        contract_version=None,  # → falls back to CONTRACT_SCHEMA_VERSION
        lane="critical",
        rid="run-happy",
    )
    assert err is None
    assert requested == CONTRACT_SCHEMA_VERSION


def test_rob010_happy_path_explicit_canonical(helpers_module) -> None:
    """Same path, but the caller passes the canonical version explicitly."""
    from thegent.contracts.registry import CONTRACT_SCHEMA_VERSION

    err, requested = helpers_module._phase_bg_evaluate_contract(
        contract_version=CONTRACT_SCHEMA_VERSION,
        lane="critical",
        rid="run-happy-explicit",
    )
    assert err is None
    assert requested == CONTRACT_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# 3. ROB-010 downgrade path — critical lane with non-current version.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rogue_version",
    [
        "contract-schema-v0",  # classic downgrade
        "contract-schema-v2",  # forward drift (also blocked)
        "not-a-version",  # unknown
    ],
)
def test_rob010_downgrade_returns_error(helpers_module, rogue_version: str) -> None:
    """``lane='critical'`` + non-current version → ROB-010 error payload.

    The error must be a dict with ``exit_code=1``, the canonical
    ``session_id='failed'`` marker, the caller's ``run_id``, the
    ROB-010 message, and the remediation hint.
    """
    err, requested = helpers_module._phase_bg_evaluate_contract(
        contract_version=rogue_version,
        lane="critical",
        rid="run-rob010",
    )
    assert err is not None
    assert err["exit_code"] == 1
    assert err["session_id"] == "failed"
    assert err["run_id"] == "run-rob010"
    assert "ROB-010" in err["error"]
    assert rogue_version in err["error"]
    assert "remediation" in err
    # Requested version is always echoed back so callers can log it.
    assert requested == rogue_version


# ---------------------------------------------------------------------------
# 4. Standard lane — ROB-010 must NOT trigger.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "any_version",
    [
        "contract-schema-v0",
        "contract-schema-v2",
        "anything",
        None,  # canonical fallback
    ],
)
def test_standard_lane_accepts_any_version(helpers_module, any_version) -> None:
    """ROB-010 is scoped to the critical lane only. Standard lanes
    accept arbitrary ``contract_version`` strings (the migrator handles
    rejection if needed).
    """
    err, requested = helpers_module._phase_bg_evaluate_contract(
        contract_version=any_version,
        lane="standard",
        rid="run-std",
    )
    assert err is None
    if any_version is None:
        from thegent.contracts.registry import CONTRACT_SCHEMA_VERSION

        assert requested == CONTRACT_SCHEMA_VERSION
    else:
        assert requested == any_version


# ---------------------------------------------------------------------------
# 5. Wire-up regression — bg_impl_core delegates to the helper.
# ---------------------------------------------------------------------------


def test_bg_impl_core_delegates_to_phase_bg_evaluate_contract(
    bg_impl_core_source: str,
) -> None:
    """``bg_impl_core`` must call ``_phase_bg_evaluate_contract(...)``.

    Guards against accidental re-inlining that would silently drop the
    ROB-010 guard and reintroduce the latent bug.
    """
    assert "_phase_bg_evaluate_contract(" in bg_impl_core_source


# ---------------------------------------------------------------------------
# 6. Registry integration — ``is_compatible`` is wired through the singleton.
# ---------------------------------------------------------------------------


def test_registry_singleton_is_used_by_helper(helpers_module) -> None:
    """The helper must consult the canonical ``CONTRACT_REGISTRY``,
    not a fresh local instance.

    We invert ``CONTRACT_REGISTRY.is_compatible`` for the duration of
    one call: ``is_compatible('contract-schema-v0', current)`` flips
    from ``False`` to ``True``. The critical-lane branch must then
    fall through to ``return None, requested_version`` (no error
    payload) — proving the helper consulted the patched singleton.

    Implementation note: ``patch.object`` replaces the bound name on
    the instance; the dataclass class method is shadowed while the
    patch is active, then restored.
    """
    from unittest.mock import patch

    from thegent.contracts.registry import (
        CONTRACT_REGISTRY,
    )

    # Capture the real method BEFORE patching so the stub does not
    # recurse into the patched MagicMock.
    real = CONTRACT_REGISTRY.is_compatible
    invoked: list[tuple[str, str]] = []

    def stub(requested: str, current: str) -> bool:
        invoked.append((requested, current))
        return not real(requested, current)

    with patch.object(CONTRACT_REGISTRY, "is_compatible", side_effect=stub):
        # Critical lane + non-current version → without the inverted
        # stub this returns a ROB-010 error; with the inverted stub
        # the singleton now considers v0 "compatible" so the helper
        # returns None and proves the singleton was consulted.
        err, requested = helpers_module._phase_bg_evaluate_contract(
            contract_version="contract-schema-v0",
            lane="critical",
            rid="run-stub",
        )
    assert invoked, "helper did not consult the singleton"
    assert err is None, f"expected None (stub flipped v0 to compatible), got {err!r}"
    assert requested == "contract-schema-v0"


# ---------------------------------------------------------------------------
# 7. Behavioural spot — error payload preserves canonical keys.
# ---------------------------------------------------------------------------


def test_rob010_error_payload_keys(helpers_module) -> None:
    """The error payload must carry every canonical key the rest of the
    run-execution pipeline expects. Pinned by audit, prevents
    downstream ``KeyError`` regressions if the payload shape drifts.
    """
    err, _ = helpers_module._phase_bg_evaluate_contract(
        contract_version="contract-schema-v0",
        lane="critical",
        rid="run-shape",
    )
    assert err is not None
    expected = {"error", "exit_code", "session_id", "run_id", "remediation"}
    assert expected <= set(err.keys())
