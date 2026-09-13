"""Integration tests for WL-093: Vetter HITL Escalation.

Covers the full escalation path in VetterOrchestrator:
- verdict == ESCALATED triggers vetter_escalation event in governance_events.jsonl
- vetter_escalation event fields: event_type, status, escalation_lane, run_id, timestamp
- HITLApprovalWorkflow.await_approval() is called (emits await_approval event)
- await_approval event appears in govern list output (list_pending_approvals)
- RuntimeError raised when verdict is ESCALATED but hitl_workflow is None
- escalation_lane sourced from VetterPolicy.escalation_lane (defaults to "standard")
- VetterResult.escalation_reason is set on ESCALATED verdict
- Both vetter_decision and vetter_escalation events emitted per evaluate() call
- Multiple escalations accumulate correctly in governance_events.jsonl
- await_approval event has correct fields for govern list surfacing

# @trace WL-093
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import orjson as json
import pytest

from thegent.cli.services import governance as governance_service
from thegent.govern.vetter.models import (
    VetterCheckResult,
    VetterPolicy,
    VetterVerdict,
)
from thegent.govern.vetter.orchestrator import VetterOrchestrator
from thegent.governance.hitl import HITLApprovalWorkflow

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _failing_check(name: str, message: str = "failed") -> Any:
    """Return an async VetterCheck mock that always fails. # @trace WL-093"""
    check = MagicMock()
    check.name = name
    check.check = AsyncMock(return_value=VetterCheckResult(check_name=name, passed=False, message=message))
    return check


def _passing_check(name: str) -> Any:
    """Return an async VetterCheck mock that always passes. # @trace WL-093"""
    check = MagicMock()
    check.name = name
    check.check = AsyncMock(return_value=VetterCheckResult(check_name=name, passed=True))
    return check


def _make_hitl_mock() -> MagicMock:
    """Return a MagicMock hitl_workflow that records await_approval calls. # @trace WL-093"""
    hitl = MagicMock()
    hitl.await_approval = MagicMock(return_value={"success": True, "event_id": "hitl_test"})
    return hitl


def _load_events(session_dir: Path) -> list[dict[str, Any]]:
    """Read all events from governance_events.jsonl. # @trace WL-093"""
    path = session_dir / "governance_events.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _events_of_type(session_dir: Path, event_type: str) -> list[dict[str, Any]]:
    """Return all events of a given event_type. # @trace WL-093"""
    return [ev for ev in _load_events(session_dir) if ev.get("event_type") == event_type]


# ---------------------------------------------------------------------------
# 1. Escalated verdict triggers vetter_escalation event
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_escalated_verdict_emits_vetter_escalation_event(tmp_path: Path) -> None:
    """When verdict is ESCALATED, a vetter_escalation event is written to governance_events.jsonl.
    # @trace WL-093
    """
    bad = _failing_check("safety_check")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety_check": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety_check"], escalate_on=["safety_check"])
    await orch.evaluate(
        result=MagicMock(output="diff"),
        policy=policy,
        run_context={"run_id": "run-esc-001", "session_id": "sess-1"},
    )

    esc_events = _events_of_type(tmp_path, "vetter_escalation")
    assert len(esc_events) == 1, "Expected exactly one vetter_escalation event"


@pytest.mark.asyncio
async def test_escalation_event_has_correct_event_type(tmp_path: Path) -> None:
    """vetter_escalation event has event_type == 'vetter_escalation'. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-esc-002"})

    ev = _events_of_type(tmp_path, "vetter_escalation")[0]
    assert ev["event_type"] == "vetter_escalation"


@pytest.mark.asyncio
async def test_escalation_event_has_status_pending(tmp_path: Path) -> None:
    """vetter_escalation event has status == 'pending'. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-esc-003"})

    ev = _events_of_type(tmp_path, "vetter_escalation")[0]
    assert ev["status"] == "pending"


@pytest.mark.asyncio
async def test_escalation_event_has_run_id(tmp_path: Path) -> None:
    """vetter_escalation event has the correct run_id. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-esc-004"})

    ev = _events_of_type(tmp_path, "vetter_escalation")[0]
    assert ev["run_id"] == "run-esc-004"


@pytest.mark.asyncio
async def test_escalation_event_has_timestamp(tmp_path: Path) -> None:
    """vetter_escalation event has an ISO 8601 timestamp field. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-esc-005"})

    ev = _events_of_type(tmp_path, "vetter_escalation")[0]
    assert "timestamp" in ev
    assert isinstance(ev["timestamp"], str)
    assert "T" in ev["timestamp"]  # ISO 8601 format


@pytest.mark.asyncio
async def test_escalation_event_has_escalation_lane_from_policy(tmp_path: Path) -> None:
    """vetter_escalation event escalation_lane comes from policy.escalation_lane. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"], escalation_lane="critical")
    await orch.evaluate(
        result=MagicMock(output=""),
        policy=policy,
        run_context={"run_id": "run-esc-006"},
    )

    ev = _events_of_type(tmp_path, "vetter_escalation")[0]
    assert ev["escalation_lane"] == "critical"


@pytest.mark.asyncio
async def test_escalation_event_defaults_escalation_lane_to_standard(tmp_path: Path) -> None:
    """When policy has no escalation_lane override, vetter_escalation defaults to 'standard'. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    await orch.evaluate(
        result=MagicMock(output=""),
        policy=policy,
        run_context={"run_id": "run-esc-007"},
    )

    ev = _events_of_type(tmp_path, "vetter_escalation")[0]
    assert ev["escalation_lane"] == "standard"


@pytest.mark.asyncio
async def test_escalation_event_has_reason_field(tmp_path: Path) -> None:
    """vetter_escalation event has a non-empty reason field. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-esc-008"})

    ev = _events_of_type(tmp_path, "vetter_escalation")[0]
    assert "reason" in ev
    assert ev["reason"]  # non-empty string


@pytest.mark.asyncio
async def test_escalation_event_is_forwarded_to_optional_event_log(tmp_path: Path) -> None:
    """vetter_escalation event is emitted to event_log when configured. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    event_log = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
        event_log=event_log,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"], escalation_lane="critical")
    await orch.evaluate(
        result=MagicMock(output=""),
        policy=policy,
        run_context={"run_id": "run-esc-event-log"},
    )

    emitted_types = [call_args.args[0]["event_type"] for call_args in event_log.emit.call_args_list]
    assert "vetter_decision" in emitted_types
    assert "vetter_escalation" in emitted_types


# ---------------------------------------------------------------------------
# 2. HITLApprovalWorkflow.await_approval() is called
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hitl_await_approval_called_on_escalation(tmp_path: Path) -> None:
    """hitl_workflow.await_approval() is called when verdict is ESCALATED. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    await orch.evaluate(result=MagicMock(output="change_diff"), policy=policy, run_context={"run_id": "run-esc-009"})

    hitl.await_approval.assert_called_once()


@pytest.mark.asyncio
async def test_hitl_await_approval_called_with_correct_run_id(tmp_path: Path) -> None:
    """hitl_workflow.await_approval() receives the correct run_id. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    await orch.evaluate(
        result=MagicMock(output=""),
        policy=policy,
        run_context={"run_id": "run-esc-010"},
    )

    call_kwargs = hitl.await_approval.call_args.kwargs
    assert call_kwargs["run_id"] == "run-esc-010"


@pytest.mark.asyncio
async def test_hitl_await_approval_called_with_vetter_escalation_policy(tmp_path: Path) -> None:
    """hitl_workflow.await_approval() receives policy='vetter_escalation'. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-esc-011"})

    call_kwargs = hitl.await_approval.call_args.kwargs
    assert call_kwargs["policy"] == "vetter_escalation"


@pytest.mark.asyncio
async def test_hitl_await_approval_called_with_post_execution_checkpoint(tmp_path: Path) -> None:
    """hitl_workflow.await_approval() uses checkpoint='post_execution'. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-esc-012"})

    call_kwargs = hitl.await_approval.call_args.kwargs
    assert call_kwargs["checkpoint"] == "post_execution"


@pytest.mark.asyncio
async def test_hitl_await_approval_passes_unified_diff(tmp_path: Path) -> None:
    """hitl_workflow.await_approval() receives unified_diff from result.output. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    diff_text = "diff --git a/foo.py b/foo.py\n+added line"
    await orch.evaluate(
        result=MagicMock(output=diff_text),
        policy=policy,
        run_context={"run_id": "run-esc-013"},
    )

    call_kwargs = hitl.await_approval.call_args.kwargs
    assert call_kwargs["unified_diff"] == diff_text


@pytest.mark.asyncio
async def test_hitl_not_called_when_verdict_is_approved(tmp_path: Path) -> None:
    """hitl_workflow.await_approval() is NOT called when all checks pass. # @trace WL-093"""
    good = _passing_check("style")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"style": good},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["style"], escalate_on=[])
    await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-esc-014"})

    hitl.await_approval.assert_not_called()


@pytest.mark.asyncio
async def test_hitl_not_called_when_verdict_is_rejected_no_escalate_on(tmp_path: Path) -> None:
    """hitl_workflow.await_approval() is NOT called on rejection when check not in escalate_on. # @trace WL-093"""
    bad = _failing_check("style")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"style": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["style"], escalate_on=[])  # style not in escalate_on
    await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-esc-015"})

    hitl.await_approval.assert_not_called()


# ---------------------------------------------------------------------------
# 3. RuntimeError when hitl_workflow is None and verdict is ESCALATED
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_escalated_verdict_without_hitl_raises_runtime_error(tmp_path: Path) -> None:
    """When verdict is ESCALATED but hitl_workflow is None, RuntimeError is raised. # @trace WL-093"""
    bad = _failing_check("safety")
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=None,  # not wired
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])

    with pytest.raises(RuntimeError, match="hitl_workflow"):
        await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-esc-016"})


# ---------------------------------------------------------------------------
# 4. govern list surfacing: await_approval event appears via HITLApprovalWorkflow
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_escalation_emits_await_approval_event_surfaced_by_govern_list(
    tmp_path: Path,
) -> None:
    """After escalation, HITLApprovalWorkflow.list_pending() returns the blocking event.
    This confirms escalation events appear in thegent govern list output. # @trace WL-093
    """
    bad = _failing_check("safety")
    # Use a real HITLApprovalWorkflow wired to the same session_dir
    real_hitl = HITLApprovalWorkflow(session_dir=tmp_path)
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=real_hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    await orch.evaluate(
        result=MagicMock(output="some diff"),
        policy=policy,
        run_context={"run_id": "run-esc-017", "session_id": "sess-x"},
    )

    # govern list surfaces await_approval events with status=pending
    pending = real_hitl.list_pending()
    run_ids = {p["run_id"] for p in pending}
    assert "run-esc-017" in run_ids, "Escalation must appear in govern list pending output"


@pytest.mark.asyncio
async def test_escalation_await_approval_event_has_status_pending(tmp_path: Path) -> None:
    """The await_approval event emitted during escalation has status='pending'. # @trace WL-093"""
    bad = _failing_check("safety")
    real_hitl = HITLApprovalWorkflow(session_dir=tmp_path)
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=real_hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    await orch.evaluate(
        result=MagicMock(output=""),
        policy=policy,
        run_context={"run_id": "run-esc-018"},
    )

    pending = real_hitl.list_pending()
    matching = [p for p in pending if p["run_id"] == "run-esc-018"]
    assert len(matching) == 1
    assert matching[0]["status"] == "pending"


@pytest.mark.asyncio
async def test_govern_list_shows_escalation_event_type_await_approval(tmp_path: Path) -> None:
    """govern list entry for escalation has event_type='await_approval'. # @trace WL-093"""
    bad = _failing_check("safety")
    real_hitl = HITLApprovalWorkflow(session_dir=tmp_path)
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=real_hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    await orch.evaluate(
        result=MagicMock(output=""),
        policy=policy,
        run_context={"run_id": "run-esc-019"},
    )

    pending = real_hitl.list_pending()
    matching = [p for p in pending if p["run_id"] == "run-esc-019"]
    assert matching[0]["event_type"] == "await_approval"


# ---------------------------------------------------------------------------
# 5. Both vetter_decision and vetter_escalation events emitted per evaluate()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_escalation_emits_both_decision_and_escalation_events(tmp_path: Path) -> None:
    """evaluate() with escalation emits vetter_decision AND vetter_escalation events. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-esc-020"})

    all_events = _load_events(tmp_path)
    event_types = {ev["event_type"] for ev in all_events}
    assert "vetter_decision" in event_types
    assert "vetter_escalation" in event_types


@pytest.mark.asyncio
async def test_escalation_vetter_decision_event_has_escalated_verdict(tmp_path: Path) -> None:
    """The vetter_decision event has verdict='escalated' when check triggers escalation. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-esc-021"})

    decision_events = _events_of_type(tmp_path, "vetter_decision")
    assert len(decision_events) == 1
    assert decision_events[0]["verdict"] == "escalated"


@pytest.mark.asyncio
async def test_escalation_decision_event_emitted_before_escalation_event(tmp_path: Path) -> None:
    """vetter_decision is emitted before vetter_escalation (line order). # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-esc-022"})

    all_events = _load_events(tmp_path)
    types_in_order = [ev["event_type"] for ev in all_events]
    decision_idx = types_in_order.index("vetter_decision")
    escalation_idx = types_in_order.index("vetter_escalation")
    assert decision_idx < escalation_idx, "vetter_decision must precede vetter_escalation"


# ---------------------------------------------------------------------------
# 6. VetterResult fields on ESCALATED verdict
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_escalated_result_has_escalated_verdict(tmp_path: Path) -> None:
    """VetterResult.verdict is ESCALATED when escalation fires. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    result = await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-esc-023"})

    assert result.verdict == VetterVerdict.ESCALATED


@pytest.mark.asyncio
async def test_escalated_result_has_escalation_reason(tmp_path: Path) -> None:
    """VetterResult.escalation_reason is a non-empty string when escalation fires. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    result = await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-esc-024"})

    assert result.escalation_reason is not None
    assert len(result.escalation_reason) > 0


@pytest.mark.asyncio
async def test_escalated_result_escalation_reason_names_failed_check(tmp_path: Path) -> None:
    """VetterResult.escalation_reason mentions the failed check name. # @trace WL-093"""
    bad = _failing_check("my_safety_check")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"my_safety_check": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["my_safety_check"], escalate_on=["my_safety_check"])
    result = await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-esc-025"})

    assert "my_safety_check" in (result.escalation_reason or "")


@pytest.mark.asyncio
async def test_non_escalated_result_has_no_escalation_reason(tmp_path: Path) -> None:
    """VetterResult.escalation_reason is None when verdict is APPROVED. # @trace WL-093"""
    good = _passing_check("style")
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"style": good},
    )
    policy = VetterPolicy(checks=["style"])
    result = await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-esc-026"})

    assert result.escalation_reason is None


# ---------------------------------------------------------------------------
# 7. Multiple escalations accumulate correctly
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_multiple_escalations_each_emit_own_events(tmp_path: Path) -> None:
    """Two separate escalating evaluate() calls produce two vetter_escalation events. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])

    await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-multi-esc-1"})
    await orch.evaluate(result=MagicMock(output=""), policy=policy, run_context={"run_id": "run-multi-esc-2"})

    esc_events = _events_of_type(tmp_path, "vetter_escalation")
    assert len(esc_events) == 2
    run_ids = {ev["run_id"] for ev in esc_events}
    assert "run-multi-esc-1" in run_ids
    assert "run-multi-esc-2" in run_ids


@pytest.mark.asyncio
async def test_multiple_escalations_govern_list_shows_all_pending(tmp_path: Path) -> None:
    """After two escalations, govern list returns both pending entries. # @trace WL-093"""
    bad = _failing_check("safety")
    real_hitl = HITLApprovalWorkflow(session_dir=tmp_path)
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=real_hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])

    await orch.evaluate(
        result=MagicMock(output=""),
        policy=policy,
        run_context={"run_id": "run-govlist-1"},
    )
    await orch.evaluate(
        result=MagicMock(output=""),
        policy=policy,
        run_context={"run_id": "run-govlist-2"},
    )

    pending = real_hitl.list_pending()
    run_ids = {p["run_id"] for p in pending}
    assert "run-govlist-1" in run_ids
    assert "run-govlist-2" in run_ids


# ---------------------------------------------------------------------------
# 8. Partial escalate_on: only matching failures escalate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_only_checks_in_escalate_on_trigger_escalation(tmp_path: Path) -> None:
    """Only failed checks listed in escalate_on produce ESCALATED verdict. # @trace WL-093"""
    bad_style = _failing_check("style")  # NOT in escalate_on
    bad_safety = _failing_check("safety")  # IN escalate_on
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"style": bad_style, "safety": bad_safety},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["style", "safety"], escalate_on=["safety"])
    result = await orch.evaluate(
        result=MagicMock(output=""),
        policy=policy,
        run_context={"run_id": "run-partial-esc"},
    )

    assert result.verdict == VetterVerdict.ESCALATED
    hitl.await_approval.assert_called_once()


@pytest.mark.asyncio
async def test_failed_check_not_in_escalate_on_yields_rejected_not_escalated(tmp_path: Path) -> None:
    """When a check fails but is not in escalate_on, verdict is REJECTED not ESCALATED. # @trace WL-093"""
    bad_style = _failing_check("style")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"style": bad_style},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["style"], escalate_on=["safety"])  # style not listed
    result = await orch.evaluate(
        result=MagicMock(output=""),
        policy=policy,
        run_context={"run_id": "run-no-esc"},
    )

    assert result.verdict == VetterVerdict.REJECTED
    hitl.await_approval.assert_not_called()
    assert len(_events_of_type(tmp_path, "vetter_escalation")) == 0


# ---------------------------------------------------------------------------
# 9. session_id propagated into vetter_escalation event
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_escalation_event_has_session_id_from_run_context(tmp_path: Path) -> None:
    """vetter_escalation event carries session_id from run_context. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    await orch.evaluate(
        result=MagicMock(output=""),
        policy=policy,
        run_context={"run_id": "run-sess-esc", "session_id": "sess-abc-123"},
    )

    ev = _events_of_type(tmp_path, "vetter_escalation")[0]
    assert ev.get("session_id") == "sess-abc-123"


@pytest.mark.asyncio
async def test_escalated_decision_is_queryable_via_govern_list_pending_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Escalations surface through existing govern_list_pending_impl path. # @trace WL-093"""
    bad = _failing_check("safety")
    hitl = HITLApprovalWorkflow(session_dir=tmp_path)
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"], escalation_lane="critical")

    await orch.evaluate(
        result=MagicMock(output="diff --git a/x b/x\n+danger"),
        policy=policy,
        run_context={"run_id": "run-govern-list-esc", "session_id": "sess-govern-list"},
    )

    monkeypatch.setattr(governance_service, "_session_dir", lambda: tmp_path)
    pending = governance_service.govern_list_pending_impl()
    matching = [item for item in pending if item.get("run_id") == "run-govern-list-esc"]
    assert len(matching) == 1
    assert matching[0]["event_type"] == "await_approval"
    assert "lane" in matching[0]
    assert "status" in matching[0]
    assert matching[0]["lane"] == "standard"
    assert matching[0]["status"] == "pending"
    assert matching[0]["policy"] == "vetter_escalation"


@pytest.mark.asyncio
async def test_escalation_event_payload_shape_is_json_serializable_for_audit_log(tmp_path: Path) -> None:
    """Escalation event payload shape is stable and JSON serializable for audit-log sinks. # @trace WL-093"""
    bad = _failing_check("safety", "policy violation")
    hitl = _make_hitl_mock()
    event_log = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
        event_log=event_log,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"], escalation_lane="critical")

    await orch.evaluate(
        result=MagicMock(output="diff --git a/a.py b/a.py\n+unsafe"),
        policy=policy,
        run_context={"run_id": "run-esc-audit-shape", "session_id": "sess-audit-shape"},
    )

    escalation_event = next(
        call_args.args[0]
        for call_args in event_log.emit.call_args_list
        if call_args.args[0].get("event_type") == "vetter_escalation"
    )
    expected_keys = {
        "event_type",
        "timestamp",
        "session_id",
        "run_id",
        "status",
        "escalation_lane",
        "reason",
    }
    assert set(escalation_event.keys()) == expected_keys
    assert escalation_event["event_type"] == "vetter_escalation"
    assert escalation_event["run_id"] == "run-esc-audit-shape"
    assert escalation_event["status"] == "pending"
    assert escalation_event["escalation_lane"] == "critical"
    assert isinstance(escalation_event["reason"], str)
    json.dumps(escalation_event).decode()


@pytest.mark.asyncio
async def test_escalation_reason_is_deterministic_and_matches_event_reason(tmp_path: Path) -> None:
    """Escalation reason is stable for audit trails and matches emitted event reason. # @trace WL-093"""
    alpha = _failing_check("alpha", "alpha failed")
    zeta = _failing_check("zeta", "zeta failed")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"alpha": alpha, "zeta": zeta},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(
        checks=["zeta", "alpha"],
        escalate_on=["zeta", "alpha"],
        escalation_lane="critical",
    )

    result = await orch.evaluate(
        result=MagicMock(output="diff --git a/a.py b/a.py\n+unsafe"),
        policy=policy,
        run_context={"run_id": "run-esc-reason-stable", "session_id": "sess-reason-stable"},
    )

    assert result.verdict == VetterVerdict.ESCALATED
    reason = result.escalation_reason or ""
    assert "failed_checks=alpha,zeta" in reason
    assert "policy_escalate_on=alpha,zeta" in reason
    assert "policy_lane=critical" in reason

    escalation_event = _events_of_type(tmp_path, "vetter_escalation")[0]
    assert escalation_event["reason"] == reason


@pytest.mark.asyncio
async def test_escalation_reason_deduplicates_policy_escalate_on_for_audit_stability(tmp_path: Path) -> None:
    """Escalation reason de-duplicates and sorts policy_escalate_on values. # @trace WL-093"""
    bad = _failing_check("safety", "unsafe output")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(
        checks=["safety"],
        escalate_on=["safety", "safety"],
        escalation_lane="critical",
    )

    result = await orch.evaluate(
        result=MagicMock(output="diff --git a/a.py b/a.py\n+unsafe"),
        policy=policy,
        run_context={"run_id": "run-esc-reason-dedup", "session_id": "sess-reason-dedup"},
    )

    reason = result.escalation_reason or ""
    assert "policy_escalate_on=safety" in reason
    assert "policy_escalate_on=safety,safety" not in reason


@pytest.mark.asyncio
async def test_escalation_reason_uses_explicit_none_when_policy_escalate_on_empty(tmp_path: Path) -> None:
    """Escalation reason uses explicit <none> when policy_escalate_on is empty. # @trace WL-093"""
    bad = _failing_check("quality", "quality gate failed")
    hitl = _make_hitl_mock()
    queue = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"quality": bad},
        hitl_workflow=hitl,
        prompt_queue=queue,
    )
    policy = VetterPolicy(
        checks=["quality"],
        escalate_on=[],
        max_revision_rounds=0,
        on_fail="escalate",
        escalation_lane="critical",
    )

    result = await orch.evaluate(
        result=MagicMock(output="diff --git a/a.py b/a.py\n+bad"),
        policy=policy,
        run_context={
            "run_id": "run-esc-empty-escalate-on",
            "session_id": "sess-esc-empty-escalate-on",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )

    assert result.verdict == VetterVerdict.ESCALATED
    reason = result.escalation_reason or ""
    assert "policy_escalate_on=<none>" in reason


@pytest.mark.asyncio
async def test_escalation_event_normalizes_session_id_whitespace(tmp_path: Path) -> None:
    """Escalation event payload trims session_id for canonical audit keys. # @trace WL-093"""
    bad = _failing_check("safety", "unsafe output")
    hitl = _make_hitl_mock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": bad},
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])

    await orch.evaluate(
        result=MagicMock(output="diff --git a/a.py b/a.py\n+unsafe"),
        policy=policy,
        run_context={"run_id": "run-esc-session-normalized", "session_id": "  sess-trimmed  "},
    )

    escalation_event = _events_of_type(tmp_path, "vetter_escalation")[0]
    assert escalation_event["session_id"] == "sess-trimmed"
