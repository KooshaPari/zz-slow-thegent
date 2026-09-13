"""WL-132 L9 post-mid + pre-failure helpers wire-up regression.

Continues L9 orchestrator decomposition after WL-131 (mid-phase) and
commits dfb3dd7fe / 48e0f5acd (early-phase). The eight helpers wired
here collapse the pre-success postlude into single delegations:

Post-mid (2):
* ``_phase_load_l3_memory_context`` — MemoryManager.load_context injection
* ``_phase_setup_shadow_workspace`` — ShadowWorkspace.create + env export

Pre-failure (6):
* ``_phase_acquire_resource_leases`` — FileLeaseRegistry.claim_lease loop
* ``_phase_release_resource_leases`` — FileLeaseRegistry.release_lease loop
* ``_phase_finalize_shadow`` — auto-merge + destroy on status
* ``_phase_estimate_run_cost`` — CostEstimator.estimate dispatch
* ``_phase_register_run_end`` — RunRegistry.register_end call
* ``_phase_record_success_postlude`` — trust record + lint + MAIF artifact

Each helper is contract-pinned in ``run_execution_core_helpers.py``;
this test guards against accidental re-inlining of the historical
bodies so the orchestrator's CC reduction is preserved.
"""

from __future__ import annotations

import importlib
import inspect

import pytest

_POST_MID_AND_PRE_FAILURE_HELPERS = (
    "_phase_load_l3_memory_context",
    "_phase_setup_shadow_workspace",
    "_phase_acquire_resource_leases",
    "_phase_release_resource_leases",
    "_phase_finalize_shadow",
    "_phase_estimate_run_cost",
    "_phase_register_run_end",
    "_phase_record_success_postlude",
)

# WL137 indirect: ``_phase_release_resource_leases`` is now invoked from
# ``_phase_run_under_keepalive`` (the keepalive context's ``finally``
# clause) instead of being called inline by ``run_impl_core``. Both call
# sites remain valid for the contract.
_INDIRECT_DELEGATION = {
    "_phase_release_resource_leases": ("_phase_run_under_keepalive",),
}


@pytest.fixture(scope="module")
def run_impl_core_source() -> str:
    helpers = importlib.import_module("thegent.cli.services.run_execution_core_helpers")
    return inspect.getsource(helpers.run_impl_core)


@pytest.fixture(scope="module")
def helpers_module():
    return importlib.import_module("thegent.cli.services.run_execution_core_helpers")


@pytest.mark.parametrize("phase_name", list(_POST_MID_AND_PRE_FAILURE_HELPERS))
def test_run_impl_core_delegates_to_phase_helpers(
    phase_name: str, run_impl_core_source: str, helpers_module
) -> None:
    """``run_impl_core`` must call each post-mid / pre-failure helper, not inline the body.

    WL137 indirection: ``_phase_release_resource_leases`` is invoked from
    ``_phase_run_under_keepalive`` instead of directly from
    ``run_impl_core``. Both call sites remain valid for the contract.
    """
    if f"{phase_name}(" in run_impl_core_source:
        return

    indirect_helpers = _INDIRECT_DELEGATION.get(phase_name, ())
    for delegator in indirect_helpers:
        assert f"{delegator}(" in run_impl_core_source, (
            f"Expected run_impl_core to delegate to {phase_name} either "
            f"directly or via {delegator}; neither call site found."
        )
        delegator_src = inspect.getsource(getattr(helpers_module, delegator))
        assert f"{phase_name}(" in delegator_src, (
            f"Indirect delegator {delegator} must invoke {phase_name}; "
            f"re-inlining the body defeats the WL137 refactor."
        )
        return

    pytest.fail(
        f"Expected run_impl_core to delegate to {phase_name} helper for "
        f"post-mid / pre-failure parity with the pre-extraction monolith."
    )


def test_run_impl_core_has_no_inline_l3_memory_block(run_impl_core_source: str) -> None:
    """L3 memory inline body must be gone from the orchestrator.

    The pre-extraction body called ``MemoryManager().load_context(...)``
    inline inside run_impl_core and built ``ctx_block`` by hand.
    """
    forbidden = [
        "from thegent.memory.memory_manager import MemoryManager as _MemoryManager\n\n    try:\n        _mem_mgr = _MemoryManager()",
        '_mem_ctx = _asyncio.get_event_loop().run_until_complete(_mem_mgr.load_context(agent or "unknown"))',
        'ctx_block = "\\n".join(f"- {c}" for c in _mem_ctx[:5])',
    ]
    for sig in forbidden:
        assert sig not in run_impl_core_source, (
            f"Found inline L3 memory fragment {sig!r}; must be delegated to _phase_load_l3_memory_context."
        )


def test_run_impl_core_has_no_inline_shadow_setup_block(
    run_impl_core_source: str,
) -> None:
    """Shadow workspace inline body must be gone from the orchestrator."""
    forbidden = [
        "shadow_ws = ShadowWorkspace(original_cwd, run_meta.run_id)\n            if shadow_ws.create():\n                agent_cwd = shadow_ws.shadow_root\n                shadow_env = shadow_ws.get_env()",
        'shadow_ws = None\n        except ImportError as _shadow_exc:\n            _log.debug(\n                "shadow workspace module unavailable in this revision',
    ]
    for sig in forbidden:
        assert sig not in run_impl_core_source, (
            f"Found inline shadow workspace setup fragment {sig!r}; must be delegated to _phase_setup_shadow_workspace."
        )


def test_run_impl_core_has_no_inline_lease_acquire_block(
    run_impl_core_source: str,
) -> None:
    """Resource lease acquire inline body must be gone from the orchestrator."""
    forbidden = [
        'lease_registry = FileLeaseRegistry(settings.session_dir / "leases")\n        for resource in lock:\n            path = Path(resource)',
        "token = lease_registry.claim_lease(path, run_meta.run_id, ttl=int(effective_timeout))",
        'return {"error": f"Resource {resource} is locked by another agent.", "exit_code": 1}',
    ]
    for sig in forbidden:
        assert sig not in run_impl_core_source, (
            f"Found inline lease acquire fragment {sig!r}; must be delegated to _phase_acquire_resource_leases."
        )


def test_run_impl_core_has_no_inline_lease_release_block(
    run_impl_core_source: str,
) -> None:
    """Resource lease release inline body must be gone from the orchestrator."""
    forbidden = [
        'lease_registry = FileLeaseRegistry(settings.session_dir / "leases")\n            for path, token in locked_tokens:\n                lease_registry.release_lease(path, run_meta.run_id, token)\n                _log.info("Released lease for %s", path)',
    ]
    for sig in forbidden:
        assert sig not in run_impl_core_source, (
            f"Found inline lease release fragment {sig!r}; must be delegated to _phase_release_resource_leases."
        )


def test_run_impl_core_has_no_inline_shadow_finalize_block(
    run_impl_core_source: str,
) -> None:
    """Shadow finalize inline body (auto-merge + destroy on success and failure) must be gone."""
    forbidden = [
        'if shadow_ws and bool(getattr(settings, "shadow_workspaces_auto_merge", False)):\n            if shadow_ws.merge_back():',
        "if shadow_ws:\n            shadow_ws.destroy()",
    ]
    for sig in forbidden:
        assert sig not in run_impl_core_source, (
            f"Found inline shadow finalize fragment {sig!r}; must be delegated to _phase_finalize_shadow."
        )


def test_run_impl_core_has_no_inline_estimate_run_cost_block(
    run_impl_core_source: str,
) -> None:
    """Cost estimate inline body must be gone from the orchestrator."""
    forbidden = [
        "if settings.cost_tracking or settings.cost_tracking_enabled:\n        try:\n            from thegent.cost.aggregator import CostEstimator\n\n            est = CostEstimator()",
        "if not settings.cost_tracking_enabled:\n        return None\n        try:\n            from thegent.cost.aggregator import CostEstimator\n\n            est = CostEstimator()",
        'cost_usd = est.estimate(\n                model=run_meta.model,\n                prompt_length=len(run_meta.prompt or ""),\n            )',
    ]
    for sig in forbidden:
        assert sig not in run_impl_core_source, (
            f"Found inline cost estimate fragment {sig!r}; must be delegated to _phase_estimate_run_cost."
        )


def test_run_impl_core_has_no_inline_register_run_end_block(
    run_impl_core_source: str,
) -> None:
    """Register-end inline body must be gone from the orchestrator."""
    forbidden = [
        "registry.register_end(\n        run_id=run_meta.run_id,\n        exit_code=exit_code,\n        status=status,\n        ended_at_utc=datetime.now(UTC).isoformat(),\n        duration_s=duration,\n        error_class=error_class,\n        cost_usd=cost_usd,\n    )",
    ]
    for sig in forbidden:
        assert sig not in run_impl_core_source, (
            f"Found inline register_run_end fragment {sig!r}; must be delegated to _phase_register_run_end."
        )


def test_run_impl_core_has_no_inline_success_postlude_block(
    run_impl_core_source: str,
) -> None:
    """Success postlude inline body must be gone from the orchestrator.

    The pre-extraction body did trust_boundary.record_environment + evidence
    lint + MAIF artifact generation inline; they all live in
    ``_phase_record_success_postlude`` now.
    """
    forbidden = [
        'if status == "completed":\n        trust_boundary.record_environment(settings.environment.lower())',
        "linter = EvidenceLinter(settings.session_dir)\n            lint_issues = linter.lint(norm_res.csm)",
        "artifact = auditor.generate_maif_artifact(run_meta, output=result.stdout if result else None)\n        auditor.persist_maif_artifact(settings.session_dir, artifact)",
    ]
    for sig in forbidden:
        assert sig not in run_impl_core_source, (
            f"Found inline success postlude fragment {sig!r}; must be delegated to _phase_record_success_postlude."
        )


def test_run_impl_core_line_count_drops_after_wl132_wireup() -> None:
    """After WL-131 + WL-132 wire-ups, ``run_impl_core`` must shed more lines.

    Pre-WL-130 line count: 853 (per test_wl131). After WL-131: ≤ 760. After
    WL-132 (this test): ≤ 670 (≥ 90 additional lines collapsed into the
    8 new delegations, with ~30 lines of helper-call wiring added back).
    """
    helpers = importlib.import_module("thegent.cli.services.run_execution_core_helpers")
    src_lines = inspect.getsource(helpers.run_impl_core).splitlines()
    assert len(src_lines) <= 670, (
        f"run_impl_core grew to {len(src_lines)} lines; expected ≤ 670 after WL-132 wire-ups."
    )


def test_post_mid_and_pre_failure_helpers_exist_with_expected_signatures() -> None:
    """Sanity check: every WL-132 helper exists and has a non-trivial docstring."""
    helpers = importlib.import_module("thegent.cli.services.run_execution_core_helpers")
    for name in _POST_MID_AND_PRE_FAILURE_HELPERS:
        helper = getattr(helpers, name, None)
        assert callable(helper), f"helper {name} must exist and be callable"
        doc = inspect.getdoc(helper) or ""
        assert len(doc) >= 8, f"helper {name} docstring too short: {doc!r}"
        sig = inspect.signature(helper)
        assert len(sig.parameters) >= 1, f"helper {name} must take parameters"
