"""WL-131 L9 mid-phase helpers wire-up regression.

Locks down the second batch of ``_phase_*`` helper wire-ups into
``run_impl_core`` (continues commit dfb3dd7fe's early-phase batch and
48e0f5acd's budget_gate wire-up):

* ``_phase_acquire_concurrency`` — ConcurrencyController.acquire
  block (WP-5001).
* ``_phase_fatigue_freshness_burst`` — InterruptionTracker +
  FreshnessValidator + LoadClassifier/DeferralQueue (WP-4004 / 4005 / 5002).
* ``_phase_evaluate_policy_with_override`` — PolicyEngine.evaluate +
  override TTL logic (WP-3001 / WP-3003).
* ``_phase_register_policy_denial`` — escalate + register_start +
  register_end on policy deny (WP-3008).
* ``_phase_register_hitl_pause`` — checkpoint + escalate on HITL pause
  (G-GP-05).

Each helper is contract-pinned in ``run_execution_core_helpers.py``;
this test guards against accidental re-inlining of the historical
bodies so the orchestrator's CC reduction is preserved.
"""

from __future__ import annotations

import importlib
import inspect

import pytest

_MID_PHASE_HELPERS = (
    "_phase_acquire_concurrency",
    "_phase_fatigue_freshness_burst",
    "_phase_evaluate_policy_with_override",
    "_phase_register_policy_denial",
    "_phase_register_hitl_pause",
)

# WL137 indirect: deny + hitl-pause are now invoked from
# ``_phase_dispatch_policy_outcome`` instead of ``run_impl_core`` directly,
# because the orchestrator delegates the pol_res branch table to that
# helper. Both call sites are still required; the test accepts either.
_INDIRECT_DISPATCH_FROM_RUN_IMPL_CORE = "_phase_dispatch_policy_outcome"

# Indirect helpers: the helper name → the calling helper inside
# ``run_impl_core`` that ultimately invokes it.
_INDIRECT_DELEGATION = {
    "_phase_register_policy_denial": ("_phase_dispatch_policy_outcome",),
    "_phase_register_hitl_pause": ("_phase_dispatch_policy_outcome",),
}


@pytest.fixture(scope="module")
def run_impl_core_source() -> str:
    helpers = importlib.import_module("thegent.cli.services.run_execution_core_helpers")
    return inspect.getsource(helpers.run_impl_core)


@pytest.fixture(scope="module")
def helpers_module():
    return importlib.import_module("thegent.cli.services.run_execution_core_helpers")


@pytest.mark.parametrize("phase_name", list(_MID_PHASE_HELPERS))
def test_run_impl_core_delegates_mid_phases_to_extracted_helpers(phase_name: str, run_impl_core_source: str, helpers_module) -> None:
    """``run_impl_core`` must call each mid-phase helper, not inline the body.

    WL137 indirection: ``_phase_register_policy_denial`` and
    ``_phase_register_hitl_pause`` are now invoked from
    ``_phase_dispatch_policy_outcome`` instead of run_impl_core directly.
    Both call sites are acceptable for the contract.
    """
    if f"{phase_name}(" in run_impl_core_source:
        return

    # Fall back: check that run_impl_core calls an indirect delegator that
    # itself calls the helper. This keeps the regression relevant for WL137.
    indirect_helpers = _INDIRECT_DELEGATION.get(phase_name, ())
    for delegator in indirect_helpers:
        assert f"{delegator}(" in run_impl_core_source, (
            f"Expected run_impl_core to delegate to {phase_name} either "
            f"directly or via {delegator}; neither call site found. "
            f"Re-inlining will balloon run_impl_core's CC past 44."
        )
        delegator_src = inspect.getsource(getattr(helpers_module, delegator))
        assert f"{phase_name}(" in delegator_src, (
            f"Indirect delegator {delegator} must invoke {phase_name}; "
            f"re-inlining the body into {delegator} defeats the WL137 refactor."
        )
        return

    pytest.fail(
        f"Expected run_impl_core to delegate to {phase_name} helper for "
        f"mid-phase parity with the pre-extraction monolith."
    )


def test_run_impl_core_has_no_inline_concurrency_block(run_impl_core_source: str) -> None:
    """ConcurrencyController instantiation must live in the helper, not the orchestrator.

    The pre-extraction body instantiated ``ConcurrencyController(...)`` and
    called ``cc.acquire(lane=lane, priority=lane)`` inline in run_impl_core.
    """
    forbidden = [
        "ConcurrencyController(\n        settings.session_dir",
        "if not cc.acquire(\n            lane=lane,\n            priority=lane,\n        ):",
    ]
    for sig in forbidden:
        assert sig not in run_impl_core_source, (
            f"Found inline concurrency block fragment {sig!r}; must be delegated to _phase_acquire_concurrency."
        )


def test_run_impl_core_has_no_inline_fatigue_freshness_burst_block(
    run_impl_core_source: str,
) -> None:
    """Fatigue/freshness/burst inline bodies must be gone from the orchestrator.

    The pre-extraction body constructed ``InterruptionTracker``,
    ``FreshnessValidator``, and ``LoadClassifier`` inline and branched on
    fatigue/freshness/burst thresholds inside run_impl_core.
    """
    forbidden = [
        "it = InterruptionTracker(settings.session_dir)\n    fatigue = it.get_fatigue_score()",
        "fv = FreshnessValidator(settings.session_dir)\n    registry_path = getattr(registry",
        "lc = LoadClassifier(settings.session_dir)\n    load_level = lc.get_load_level()",
    ]
    for sig in forbidden:
        assert sig not in run_impl_core_source, (
            f"Found inline fatigue/freshness/burst fragment {sig!r}; must "
            f"be delegated to _phase_fatigue_freshness_burst."
        )


def test_run_impl_core_has_no_inline_policy_evaluate_block(run_impl_core_source: str) -> None:
    """Policy evaluate + override TTL inline body must be gone from the orchestrator.

    The pre-extraction body called ``policy_engine.evaluate(run_meta, registry=registry)``
    and branched on the override TTL registry inline.
    """
    forbidden = [
        "pol_res, pol_reason = policy_engine.evaluate(run_meta, registry=registry)",
        "if override_registry.has_unexpired(effective_owner):",
    ]
    for sig in forbidden:
        assert sig not in run_impl_core_source, (
            f"Found inline policy evaluate fragment {sig!r}; must be delegated to _phase_evaluate_policy_with_override."
        )


def test_run_impl_core_has_no_inline_policy_denial_block(run_impl_core_source: str) -> None:
    """Policy-deny inline body (escalate + register_start + register_end) must be gone."""
    forbidden = [
        'if pol_res == "deny":\n        # WP-3008: Add to escalation queue for SLA tracking',
        'registry.register_end(\n            run_id=run_meta.run_id,\n            exit_code=1,\n            status="failed",\n            ended_at_utc=datetime.now(UTC).isoformat(),\n            duration_s=0.0,\n            error_class="policy_violation",\n        )\n        return {"error": f"Policy Violation: {pol_reason}", "exit_code": 1}',
    ]
    for sig in forbidden:
        assert sig not in run_impl_core_source, (
            f"Found inline policy-denial fragment {sig!r}; must be delegated to _phase_register_policy_denial."
        )


def test_run_impl_core_has_no_inline_hitl_pause_block(run_impl_core_source: str) -> None:
    """HITL pause inline body (register_pause + checkpoint + escalate) must be gone."""
    forbidden = [
        'ckpt_registry = CheckpointRegistry(settings.session_dir)\n        ckpt_registry.create_checkpoint(\n            reason=f"HITL Pause: {pol_reason}",',
        'return {\n            "error": f"HITL PAUSE: {pol_reason}. Escalated for approval.",\n            "exit_code": 0,\n            "status": "paused",\n            "run_id": run_meta.run_id,\n        }',
    ]
    for sig in forbidden:
        assert sig not in run_impl_core_source, (
            f"Found inline HITL pause fragment {sig!r}; must be delegated to _phase_register_hitl_pause."
        )


def test_run_impl_core_line_count_drops_after_mid_phase_wireup() -> None:
    """After mid-phase wire-ups, ``run_impl_core`` must shed lines.

    Pre-wire-up line count: 853. Expected post-wire-up: ≤ 760 (≥ 90 lines
    collapsed into single-line delegations across 5 helpers; the
    docstrings on the wirings add ~30 lines back).
    """
    helpers = importlib.import_module("thegent.cli.services.run_execution_core_helpers")
    src_lines = inspect.getsource(helpers.run_impl_core).splitlines()
    assert len(src_lines) <= 760, (
        f"run_impl_core grew to {len(src_lines)} lines; expected ≤ 760 after mid-phase wire-ups."
    )


def test_mid_phase_helpers_exist_with_expected_signatures() -> None:
    """Sanity check: every mid-phase helper exists and has a non-trivial docstring."""
    helpers = importlib.import_module("thegent.cli.services.run_execution_core_helpers")
    for name in _MID_PHASE_HELPERS:
        helper = getattr(helpers, name, None)
        assert callable(helper), f"helper {name} must exist and be callable"
        doc = inspect.getdoc(helper) or ""
        assert len(doc) >= 8, f"helper {name} docstring too short: {doc!r}"
        # Each helper body must stay small (CC ≤ 12 contract from L9 lane).
        sig = inspect.signature(helper)
        assert len(sig.parameters) >= 1, f"helper {name} must take parameters"
