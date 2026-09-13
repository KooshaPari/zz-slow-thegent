"""Unit tests for VetterOrchestrator.evaluate() — WL-092.

Covers:
- Constructor with None/omitted deps
- evaluate() with all checks passing -> "approved"
- evaluate() with one check failing -> "rejected"
- evaluate() with fail_fast=True stops after first failure
- evaluate() emits vetter_decision event to governance_events.jsonl
- Event has correct fields: event_type, timestamp, verdict, failed_checks, passed_checks, duration_ms
- duration_ms is a positive integer
- Mock checks used for all isolation
- run_id extracted from run_context or generated
- Multiple checks aggregated correctly
- Session_dir governance_events.jsonl created if absent

# @trace WL-092
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import orjson as json
import pytest

from thegent.govern.vetter.models import (
    VetterCheckResult,
    VetterPolicy,
    VetterResult,
    VetterVerdict,
)
from thegent.govern.vetter.orchestrator import VetterOrchestrator

# ---------------------------------------------------------------------------
# Helpers: mock check factories
# ---------------------------------------------------------------------------


def _passing_check(name: str) -> Any:
    """Return an async VetterCheck mock that always passes. # @trace WL-092"""
    check = MagicMock()
    check.name = name
    check.check = AsyncMock(return_value=VetterCheckResult(check_name=name, passed=True))
    return check


def _failing_check(name: str, message: str = "failed") -> Any:
    """Return an async VetterCheck mock that always fails. # @trace WL-092"""
    check = MagicMock()
    check.name = name
    check.check = AsyncMock(return_value=VetterCheckResult(check_name=name, passed=False, message=message))
    return check


def _make_policy(
    check_names: list[str],
    fail_fast: bool = False,
) -> VetterPolicy:
    """Construct a VetterPolicy with given check names and fail_fast. # @trace WL-092"""
    return VetterPolicy(checks=check_names, fail_fast=fail_fast)


def _make_orchestrator(
    session_dir: Path,
    check_registry: dict[str, Any] | None = None,
) -> VetterOrchestrator:
    """Construct VetterOrchestrator with all optional deps as None. # @trace WL-092"""
    return VetterOrchestrator(
        session_dir=session_dir,
        check_registry=check_registry or {},
    )


# ---------------------------------------------------------------------------
# Constructor tests
# ---------------------------------------------------------------------------


def test_constructor_with_none_deps(tmp_path: Path) -> None:
    """VetterOrchestrator constructs without error when all deps are None. # @trace WL-092"""
    orch = VetterOrchestrator(session_dir=tmp_path)
    assert orch.session_dir == tmp_path


def test_constructor_stores_session_dir(tmp_path: Path) -> None:
    """session_dir is stored on the instance. # @trace WL-092"""
    orch = VetterOrchestrator(session_dir=tmp_path)
    assert orch.session_dir is tmp_path


def test_constructor_evidence_store_default_none(tmp_path: Path) -> None:
    """evidence_store defaults to None. # @trace WL-092"""
    orch = VetterOrchestrator(session_dir=tmp_path)
    assert orch.evidence_store is None


def test_constructor_hitl_workflow_default_none(tmp_path: Path) -> None:
    """hitl_workflow defaults to None. # @trace WL-092"""
    orch = VetterOrchestrator(session_dir=tmp_path)
    assert orch.hitl_workflow is None


def test_constructor_event_log_default_none(tmp_path: Path) -> None:
    """event_log defaults to None. # @trace WL-092"""
    orch = VetterOrchestrator(session_dir=tmp_path)
    assert orch.event_log is None


def test_constructor_prompt_queue_default_none(tmp_path: Path) -> None:
    """prompt_queue defaults to None. # @trace WL-092"""
    orch = VetterOrchestrator(session_dir=tmp_path)
    assert orch.prompt_queue is None


def test_constructor_federated_policy_default_none(tmp_path: Path) -> None:
    """federated_policy defaults to None. # @trace WL-092"""
    orch = VetterOrchestrator(session_dir=tmp_path)
    assert orch.federated_policy is None


def test_constructor_accepts_all_deps(tmp_path: Path) -> None:
    """Constructor accepts non-None values for all optional deps. # @trace WL-092"""
    mock_evidence = MagicMock()
    mock_hitl = MagicMock()
    mock_log = MagicMock()
    mock_queue = MagicMock()
    mock_policy = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        evidence_store=mock_evidence,
        hitl_workflow=mock_hitl,
        event_log=mock_log,
        prompt_queue=mock_queue,
        federated_policy=mock_policy,
    )
    assert orch.evidence_store is mock_evidence
    assert orch.hitl_workflow is mock_hitl
    assert orch.event_log is mock_log
    assert orch.prompt_queue is mock_queue
    assert orch.federated_policy is mock_policy


# ---------------------------------------------------------------------------
# evaluate() — all checks passing -> approved
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evaluate_all_pass_returns_approved(tmp_path: Path) -> None:
    """All checks passing produces VetterVerdict.APPROVED. # @trace WL-092"""
    check_a = _passing_check("alpha")
    check_b = _passing_check("beta")
    registry = {"alpha": check_a, "beta": check_b}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["alpha", "beta"])
    result = await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-001"})
    assert result.verdict == VetterVerdict.APPROVED


@pytest.mark.asyncio
async def test_evaluate_all_pass_no_failed_checks(tmp_path: Path) -> None:
    """When all checks pass, check_results contains no failed entries. # @trace WL-092"""
    check_a = _passing_check("alpha")
    registry = {"alpha": check_a}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["alpha"])
    result = await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-002"})
    failed = [cr for cr in result.check_results if not cr.passed]
    assert len(failed) == 0


@pytest.mark.asyncio
async def test_evaluate_all_pass_all_checks_present(tmp_path: Path) -> None:
    """When all checks pass, all check names appear in check_results. # @trace WL-092"""
    check_a = _passing_check("alpha")
    check_b = _passing_check("beta")
    registry = {"alpha": check_a, "beta": check_b}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["alpha", "beta"])
    result = await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-003"})
    names = [cr.check_name for cr in result.check_results]
    assert "alpha" in names
    assert "beta" in names


@pytest.mark.asyncio
async def test_evaluate_single_passing_check_approved(tmp_path: Path) -> None:
    """Single passing check produces approved verdict. # @trace WL-092"""
    registry = {"only": _passing_check("only")}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["only"])
    result = await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-004"})
    assert result.verdict == VetterVerdict.APPROVED


# ---------------------------------------------------------------------------
# evaluate() — one check failing -> rejected
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evaluate_one_fail_returns_rejected(tmp_path: Path) -> None:
    """One failing check produces VetterVerdict.REJECTED. # @trace WL-092"""
    registry = {"bad": _failing_check("bad")}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["bad"])
    result = await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-010"})
    assert result.verdict == VetterVerdict.REJECTED


@pytest.mark.asyncio
async def test_evaluate_mixed_checks_rejected_when_any_fails(tmp_path: Path) -> None:
    """Mix of pass/fail checks produces rejected verdict. # @trace WL-092"""
    registry = {
        "good": _passing_check("good"),
        "bad": _failing_check("bad"),
    }
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["good", "bad"])
    result = await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-011"})
    assert result.verdict == VetterVerdict.REJECTED


@pytest.mark.asyncio
async def test_evaluate_failed_check_appears_in_results(tmp_path: Path) -> None:
    """Failed check name appears in check_results with passed=False. # @trace WL-092"""
    registry = {"bad": _failing_check("bad", "something wrong")}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["bad"])
    result = await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-012"})
    failed = [cr for cr in result.check_results if not cr.passed]
    assert len(failed) == 1
    assert failed[0].check_name == "bad"
    assert failed[0].message == "something wrong"


@pytest.mark.asyncio
async def test_evaluate_multiple_failures_all_recorded(tmp_path: Path) -> None:
    """Multiple failing checks are all recorded in check_results. # @trace WL-092"""
    registry = {
        "fail1": _failing_check("fail1"),
        "fail2": _failing_check("fail2"),
    }
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["fail1", "fail2"])
    result = await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-013"})
    failed_names = {cr.check_name for cr in result.check_results if not cr.passed}
    assert "fail1" in failed_names
    assert "fail2" in failed_names


# ---------------------------------------------------------------------------
# evaluate() — fail_fast stops after first failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evaluate_fail_fast_stops_after_first_failure(tmp_path: Path) -> None:
    """With fail_fast=True, only one check is called after first failure. # @trace WL-092"""
    check_bad = _failing_check("bad")
    check_never = _passing_check("never_called")
    registry = {"bad": check_bad, "never_called": check_never}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["bad", "never_called"], fail_fast=True)
    result = await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-020"})
    # never_called check should not have been invoked
    check_never.check.assert_not_called()
    assert result.verdict == VetterVerdict.REJECTED


@pytest.mark.asyncio
async def test_evaluate_fail_fast_result_contains_only_run_checks(tmp_path: Path) -> None:
    """With fail_fast=True, only checks actually run appear in check_results. # @trace WL-092"""
    check_bad = _failing_check("bad")
    check_never = _passing_check("never_called")
    registry = {"bad": check_bad, "never_called": check_never}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["bad", "never_called"], fail_fast=True)
    result = await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-021"})
    check_names = [cr.check_name for cr in result.check_results]
    assert "bad" in check_names
    assert "never_called" not in check_names


@pytest.mark.asyncio
async def test_evaluate_no_fail_fast_runs_all_checks(tmp_path: Path) -> None:
    """Without fail_fast, all checks run even after a failure. # @trace WL-092"""
    check_bad = _failing_check("bad")
    check_after = _passing_check("after")
    registry = {"bad": check_bad, "after": check_after}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["bad", "after"], fail_fast=False)
    await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-022"})
    check_after.check.assert_called_once()


@pytest.mark.asyncio
async def test_evaluate_fail_fast_false_is_default(tmp_path: Path) -> None:
    """fail_fast defaults to False; all checks run even after failure. # @trace WL-092"""
    check_bad = _failing_check("bad")
    check_after = _passing_check("after")
    registry = {"bad": check_bad, "after": check_after}
    orch = _make_orchestrator(tmp_path, registry)
    policy = VetterPolicy(checks=["bad", "after"])  # no fail_fast arg
    await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-023"})
    check_after.check.assert_called_once()


# ---------------------------------------------------------------------------
# evaluate() — emits vetter_decision event to governance_events.jsonl
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evaluate_creates_governance_events_file(tmp_path: Path) -> None:
    """evaluate() creates governance_events.jsonl in session_dir. # @trace WL-092"""
    registry = {"alpha": _passing_check("alpha")}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["alpha"])
    await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-030"})
    events_file = tmp_path / "governance_events.jsonl"
    assert events_file.exists()


@pytest.mark.asyncio
async def test_evaluate_emits_vetter_decision_event_type(tmp_path: Path) -> None:
    """Emitted event has event_type == 'vetter_decision'. # @trace WL-092"""
    registry = {"alpha": _passing_check("alpha")}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["alpha"])
    await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-031"})
    events_file = tmp_path / "governance_events.jsonl"
    event = json.loads(events_file.read_text().strip().splitlines()[0])
    assert event["event_type"] == "vetter_decision"


@pytest.mark.asyncio
async def test_evaluate_event_has_verdict_field(tmp_path: Path) -> None:
    """Emitted vetter_decision event has a verdict field. # @trace WL-092"""
    registry = {"alpha": _passing_check("alpha")}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["alpha"])
    await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-032"})
    event = json.loads((tmp_path / "governance_events.jsonl").read_text().strip())
    assert "verdict" in event
    assert event["verdict"] == "approved"


@pytest.mark.asyncio
async def test_evaluate_event_has_failed_checks_field(tmp_path: Path) -> None:
    """Emitted event has a failed_checks list. # @trace WL-092"""
    registry = {"bad": _failing_check("bad")}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["bad"])
    await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-033"})
    event = json.loads((tmp_path / "governance_events.jsonl").read_text().strip())
    assert "failed_checks" in event
    assert "bad" in event["failed_checks"]


@pytest.mark.asyncio
async def test_evaluate_event_has_passed_checks_field(tmp_path: Path) -> None:
    """Emitted event has a passed_checks list. # @trace WL-092"""
    registry = {"good": _passing_check("good")}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["good"])
    await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-034"})
    event = json.loads((tmp_path / "governance_events.jsonl").read_text().strip())
    assert "passed_checks" in event
    assert "good" in event["passed_checks"]


@pytest.mark.asyncio
async def test_evaluate_event_has_timestamp(tmp_path: Path) -> None:
    """Emitted event has a timestamp field (ISO 8601 string). # @trace WL-092"""
    registry = {"alpha": _passing_check("alpha")}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["alpha"])
    await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-035"})
    event = json.loads((tmp_path / "governance_events.jsonl").read_text().strip())
    assert "timestamp" in event
    assert isinstance(event["timestamp"], str)
    assert "T" in event["timestamp"]  # ISO 8601 format contains 'T'


@pytest.mark.asyncio
async def test_evaluate_event_has_duration_ms(tmp_path: Path) -> None:
    """Emitted event has duration_ms as an integer >= 0. # @trace WL-092"""
    registry = {"alpha": _passing_check("alpha")}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["alpha"])
    await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-036"})
    event = json.loads((tmp_path / "governance_events.jsonl").read_text().strip())
    assert "duration_ms" in event
    assert isinstance(event["duration_ms"], int)
    assert event["duration_ms"] >= 0


@pytest.mark.asyncio
async def test_evaluate_duration_ms_is_positive_for_real_work(tmp_path: Path) -> None:
    """duration_ms is a non-negative integer reflecting actual elapsed time. # @trace WL-092"""
    registry = {"alpha": _passing_check("alpha")}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["alpha"])
    before = time.monotonic()
    result = await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-037"})
    elapsed_ms = int((time.monotonic() - before) * 1000)
    # duration_ms should not exceed total wall clock time + small margin
    assert result.duration_ms >= 0
    assert result.duration_ms <= elapsed_ms + 50


# ---------------------------------------------------------------------------
# VetterResult fields
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evaluate_returns_vetter_result(tmp_path: Path) -> None:
    """evaluate() returns a VetterResult instance. # @trace WL-092"""
    registry = {"alpha": _passing_check("alpha")}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["alpha"])
    result = await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-040"})
    assert isinstance(result, VetterResult)


@pytest.mark.asyncio
async def test_evaluate_result_has_run_id(tmp_path: Path) -> None:
    """VetterResult.run_id matches run_context run_id. # @trace WL-092"""
    registry = {"alpha": _passing_check("alpha")}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["alpha"])
    result = await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-041"})
    assert result.run_id == "run-041"


@pytest.mark.asyncio
async def test_evaluate_result_has_check_results(tmp_path: Path) -> None:
    """VetterResult.check_results is a list of VetterCheckResult. # @trace WL-092"""
    registry = {"alpha": _passing_check("alpha")}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["alpha"])
    result = await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-042"})
    assert isinstance(result.check_results, list)
    assert all(isinstance(cr, VetterCheckResult) for cr in result.check_results)


@pytest.mark.asyncio
async def test_evaluate_result_has_duration_ms(tmp_path: Path) -> None:
    """VetterResult exposes duration_ms attribute. # @trace WL-092"""
    registry = {"alpha": _passing_check("alpha")}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["alpha"])
    result = await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-043"})
    assert hasattr(result, "duration_ms")
    assert isinstance(result.duration_ms, int)


# ---------------------------------------------------------------------------
# Multiple evaluate() calls append to governance_events.jsonl
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evaluate_appends_multiple_events(tmp_path: Path) -> None:
    """Multiple evaluate() calls produce one event per call in the JSONL file. # @trace WL-092"""
    registry = {"alpha": _passing_check("alpha")}
    orch = _make_orchestrator(tmp_path, registry)
    policy = _make_policy(["alpha"])
    await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-050"})
    await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-051"})
    lines = (tmp_path / "governance_events.jsonl").read_text().strip().splitlines()
    assert len(lines) == 2
    e0 = json.loads(lines[0])
    e1 = json.loads(lines[1])
    assert e0["event_type"] == "vetter_decision"
    assert e1["event_type"] == "vetter_decision"


# ---------------------------------------------------------------------------
# Empty check list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evaluate_empty_checks_returns_approved(tmp_path: Path) -> None:
    """No checks in policy -> verdict is approved (vacuously). # @trace WL-092"""
    orch = _make_orchestrator(tmp_path, {})
    policy = VetterPolicy(checks=[])
    result = await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-060"})
    assert result.verdict == VetterVerdict.APPROVED


@pytest.mark.asyncio
async def test_evaluate_empty_checks_emits_event(tmp_path: Path) -> None:
    """No checks still emits a vetter_decision event. # @trace WL-092"""
    orch = _make_orchestrator(tmp_path, {})
    policy = VetterPolicy(checks=[])
    await orch.evaluate(result=MagicMock(), policy=policy, run_context={"run_id": "run-061"})
    event = json.loads((tmp_path / "governance_events.jsonl").read_text().strip())
    assert event["event_type"] == "vetter_decision"
    assert event["passed_checks"] == []
    assert event["failed_checks"] == []


# ---------------------------------------------------------------------------
# WL-093/WL-094/WL-096 extension slices
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evaluate_escalated_emits_vetter_escalation_and_calls_hitl(tmp_path: Path) -> None:
    """Escalation path emits event + calls HITL workflow await_approval. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    result = await orch.evaluate(
        result=MagicMock(output="diff --git a/x b/x\n+change"),
        policy=policy,
        run_context={"run_id": "run-esc", "session_id": "sess-1", "owner": "alice"},
    )

    assert result.verdict == VetterVerdict.ESCALATED
    hitl.await_approval.assert_called_once()

    lines = (tmp_path / "governance_events.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    escalation_event = json.loads(lines[1])
    assert escalation_event["event_type"] == "vetter_escalation"
    assert escalation_event["run_id"] == "run-esc"
    assert escalation_event["status"] == "pending"


@pytest.mark.asyncio
async def test_evaluate_appends_evidence_on_every_call(tmp_path: Path) -> None:
    """evaluate() appends agent_decision evidence when evidence_store is configured. # @trace WL-094"""
    evidence = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"alpha": _passing_check("alpha")},
        evidence_store=evidence,
    )
    policy = VetterPolicy(checks=["alpha"])

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "run-ev", "session_id": "sess-ev"},
    )

    evidence.append.assert_called_once()
    kwargs = evidence.append.call_args.kwargs
    assert kwargs["kind"] == "agent_decision"
    assert kwargs["actor"] == "vetter_orchestrator"
    assert kwargs["resource"] == "session:sess-ev/run:run-ev"
    assert kwargs["payload"]["verdict"] == "approved"


@pytest.mark.asyncio
async def test_evaluate_revision_requested_enqueues_prompt(tmp_path: Path) -> None:
    """Revision queue path is opt-in via run_context flag. # @trace WL-096"""
    bad = _failing_check("style", "Please split this into smaller functions")
    queue = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"style": bad},
        prompt_queue=queue,
    )
    policy = VetterPolicy(checks=["style"], max_revision_rounds=3)

    result = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-rev",
            "enable_revision_queue": True,
            "vetter_revision_round": 1,
            "project_path": "/tmp/demo-project",
        },
    )

    assert result.verdict == VetterVerdict.REVISION_REQUESTED
    assert result.revision_prompt is not None
    assert "Round: 2" in (result.revision_prompt or "")
    queue.enqueue.assert_called_once()
    enqueue_args = queue.enqueue.call_args
    assert "[VETTER REVISION REQUEST]" in enqueue_args.args[0]
    assert enqueue_args.kwargs["project_path"] == "/tmp/demo-project"
    assert enqueue_args.kwargs["metadata"] == {
        "vetter_revision": True,
        "original_run_id": "run-rev",
        "round": 2,
    }


@pytest.mark.asyncio
async def test_evaluate_revision_round_cap_falls_back_to_rejected(tmp_path: Path) -> None:
    """When revision rounds are exhausted, verdict falls back to rejected. # @trace WL-096"""
    bad = _failing_check("style", "need updates")
    queue = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"style": bad},
        prompt_queue=queue,
    )
    policy = VetterPolicy(checks=["style"], max_revision_rounds=1)

    result = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-rev-cap",
            "enable_revision_queue": True,
            "vetter_revision_round": 1,
        },
    )

    assert result.verdict == VetterVerdict.REJECTED
    queue.enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_evaluate_revision_round_cap_escalates_when_policy_on_fail_escalate(tmp_path: Path) -> None:
    """Exhausted revision rounds use policy.on_fail='escalate' path. # @trace WL-096"""
    bad = _failing_check("style", "need updates")
    queue = MagicMock()
    hitl = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"style": bad},
        prompt_queue=queue,
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(
        checks=["style"],
        max_revision_rounds=1,
        on_fail="escalate",
        escalation_lane="critical",
    )

    result = await orch.evaluate(
        result=MagicMock(output="diff --git a/x b/x\n+change"),
        policy=policy,
        run_context={
            "run_id": "run-rev-cap-esc",
            "enable_revision_queue": True,
            "vetter_revision_round": 1,
        },
    )

    assert result.verdict == VetterVerdict.ESCALATED
    queue.enqueue.assert_not_called()
    hitl.await_approval.assert_called_once()
    lines = (tmp_path / "governance_events.jsonl").read_text(encoding="utf-8").strip().splitlines()
    escalation_event = json.loads(lines[-1])
    assert escalation_event["event_type"] == "vetter_escalation"
    assert escalation_event["escalation_lane"] == "critical"


@pytest.mark.asyncio
async def test_repeated_calls_without_round_bump_do_not_revision_loop_forever(tmp_path: Path) -> None:
    """Repeated evaluate() calls for same run_id stop at max_revision_rounds. # @trace WL-096"""
    bad = _failing_check("style", "need updates")
    queue = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"style": bad},
        prompt_queue=queue,
    )
    policy = VetterPolicy(checks=["style"], max_revision_rounds=2)

    verdicts: list[VetterVerdict] = []
    for _ in range(4):
        result = await orch.evaluate(
            result=MagicMock(),
            policy=policy,
            run_context={
                "run_id": "run-rev-repeat",
                "enable_revision_queue": True,
            },
        )
        verdicts.append(result.verdict)

    assert verdicts == [
        VetterVerdict.REVISION_REQUESTED,
        VetterVerdict.REVISION_REQUESTED,
        VetterVerdict.REJECTED,
        VetterVerdict.REJECTED,
    ]
    assert queue.enqueue.call_count == 2


@pytest.mark.asyncio
async def test_repeated_calls_without_round_bump_escalate_once_cap_reached(tmp_path: Path) -> None:
    """Escalation policy activates after revision cap even across repeated calls. # @trace WL-096"""
    bad = _failing_check("style", "need updates")
    queue = MagicMock()
    hitl = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"style": bad},
        prompt_queue=queue,
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["style"], max_revision_rounds=1, on_fail="escalate")

    first = await orch.evaluate(
        result=MagicMock(output="diff --git a/x b/x\n+change"),
        policy=policy,
        run_context={"run_id": "run-rev-repeat-esc", "enable_revision_queue": True},
    )
    second = await orch.evaluate(
        result=MagicMock(output="diff --git a/x b/x\n+change"),
        policy=policy,
        run_context={"run_id": "run-rev-repeat-esc", "enable_revision_queue": True},
    )
    third = await orch.evaluate(
        result=MagicMock(output="diff --git a/x b/x\n+change"),
        policy=policy,
        run_context={"run_id": "run-rev-repeat-esc", "enable_revision_queue": True},
    )

    assert first.verdict == VetterVerdict.REVISION_REQUESTED
    assert second.verdict == VetterVerdict.ESCALATED
    assert third.verdict == VetterVerdict.ESCALATED
    assert queue.enqueue.call_count == 1
    assert hitl.await_approval.call_count == 2


@pytest.mark.asyncio
async def test_evaluate_emits_event_to_optional_event_log(tmp_path: Path) -> None:
    """When event_log is configured, vetter_decision event is emitted there too. # @trace WL-093"""
    event_log = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"alpha": _passing_check("alpha")},
        event_log=event_log,
    )
    policy = VetterPolicy(checks=["alpha"])

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "run-event-log", "session_id": "sess-1"},
    )

    event_log.emit.assert_called_once()
    emitted = event_log.emit.call_args.args[0]
    assert emitted["event_type"] == "vetter_decision"
    assert emitted["run_id"] == "run-event-log"
