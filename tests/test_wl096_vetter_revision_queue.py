"""Tests for WL-096: Vetter Revision Queue.

Covers:
- revision_requested verdict emitted when enable_revision_queue=True and rounds remain
- prompt_queue.enqueue() called with correct positional prompt text
- Enqueued prompt contains [VETTER REVISION REQUEST] header
- Enqueued prompt contains correct round number
- Enqueued prompt contains failed check IDs
- Enqueued prompt contains revision hint strings from check messages
- metadata.vetter_revision=True in enqueue call
- metadata.original_run_id=run_id in enqueue call
- metadata.round=n in enqueue call
- project_path forwarded from run_context to enqueue call
- round 0 -> revision requested (first attempt, rounds not yet used)
- round N-1 -> revision requested (last allowed revision)
- round N -> policy.on_fail applies (reject by default)
- round N with on_fail='escalate' -> ESCALATED verdict
- round N with on_fail='escalate' -> hitl_workflow called
- prompt_queue=None with revision enabled -> RuntimeError
- enable_revision_queue=False with failing checks -> REJECTED (no re-queue)
- revision_prompt on result contains correct round number
- revision_prompt on result contains failed check ID
- revision_prompt on result contains hint text
- multiple failing checks: all IDs in enqueued prompt
- multiple failing checks: all hint messages in enqueued prompt
- next_round in metadata is current_round + 1
- escalation event written to governance_events.jsonl on exhaustion + escalate

# @trace WL-096
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from thegent.govern.vetter.models import (
    VetterCheckResult,
    VetterPolicy,
    VetterVerdict,
)
from thegent.govern.vetter.orchestrator import VetterOrchestrator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _failing_check(name: str, message: str = "fix this") -> Any:
    """Async VetterCheck mock that always fails. # @trace WL-096"""
    check = MagicMock()
    check.name = name
    check.check = AsyncMock(return_value=VetterCheckResult(check_name=name, passed=False, message=message))
    return check


def _passing_check(name: str) -> Any:
    """Async VetterCheck mock that always passes. # @trace WL-096"""
    check = MagicMock()
    check.name = name
    check.check = AsyncMock(return_value=VetterCheckResult(check_name=name, passed=True))
    return check


def _make_queue() -> MagicMock:
    """Return a mock prompt queue with a tracked enqueue() method. # @trace WL-096"""
    q = MagicMock()
    q.enqueue = MagicMock()
    return q


def _make_orch(
    session_dir: Path,
    check_registry: dict[str, Any],
    prompt_queue: Any = None,
    hitl_workflow: Any = None,
) -> VetterOrchestrator:
    """Convenience factory for VetterOrchestrator. # @trace WL-096"""
    return VetterOrchestrator(
        session_dir=session_dir,
        check_registry=check_registry,
        prompt_queue=prompt_queue,
        hitl_workflow=hitl_workflow,
    )


# ---------------------------------------------------------------------------
# Test: verdict is REVISION_REQUESTED when rounds remain
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revision_requested_verdict_when_rounds_remain(tmp_path: Path) -> None:
    """Verdict is REVISION_REQUESTED when enable_revision_queue=True and rounds remain. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=3)

    result = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-001",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )

    assert result.verdict == VetterVerdict.REVISION_REQUESTED  # @trace WL-096


@pytest.mark.asyncio
async def test_enqueue_called_when_revision_requested(tmp_path: Path) -> None:
    """prompt_queue.enqueue() is called once when verdict is REVISION_REQUESTED. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=3)

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-002",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )

    queue.enqueue.assert_called_once()  # @trace WL-096


@pytest.mark.asyncio
async def test_enqueued_prompt_contains_revision_header(tmp_path: Path) -> None:
    """Enqueued prompt text starts with [VETTER REVISION REQUEST]. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=3)

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-003",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )

    prompt_text = queue.enqueue.call_args.args[0]
    assert "[VETTER REVISION REQUEST]" in prompt_text  # @trace WL-096


@pytest.mark.asyncio
async def test_enqueued_prompt_contains_correct_round_number(tmp_path: Path) -> None:
    """Enqueued prompt says 'Round: 2' when current_round=1. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=5)

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-004",
            "enable_revision_queue": True,
            "vetter_revision_round": 1,
        },
    )

    prompt_text = queue.enqueue.call_args.args[0]
    assert "Round: 2" in prompt_text  # @trace WL-096


@pytest.mark.asyncio
async def test_enqueued_prompt_contains_failed_check_id(tmp_path: Path) -> None:
    """Enqueued prompt contains the failed check name. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"style_check": _failing_check("style_check", "Too long")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["style_check"], max_revision_rounds=3)

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-005",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )

    prompt_text = queue.enqueue.call_args.args[0]
    assert "style_check" in prompt_text  # @trace WL-096


@pytest.mark.asyncio
async def test_enqueued_prompt_contains_hint_text(tmp_path: Path) -> None:
    """Enqueued prompt contains the revision hint from the check message. # @trace WL-096"""
    queue = _make_queue()
    hint = "Please split into smaller functions"
    orch = _make_orch(tmp_path, {"style": _failing_check("style", hint)}, prompt_queue=queue)
    policy = VetterPolicy(checks=["style"], max_revision_rounds=3)

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-006",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )

    prompt_text = queue.enqueue.call_args.args[0]
    assert hint in prompt_text  # @trace WL-096


@pytest.mark.asyncio
async def test_enqueue_metadata_vetter_revision_true(tmp_path: Path) -> None:
    """metadata.vetter_revision=True is passed to enqueue(). # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=3)

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-007",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )

    metadata = queue.enqueue.call_args.kwargs["metadata"]
    assert metadata["vetter_revision"] is True  # @trace WL-096


@pytest.mark.asyncio
async def test_enqueue_metadata_original_run_id(tmp_path: Path) -> None:
    """metadata.original_run_id matches the run_id from run_context. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=3)

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-008",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )

    metadata = queue.enqueue.call_args.kwargs["metadata"]
    assert metadata["original_run_id"] == "run-wl096-008"  # @trace WL-096


@pytest.mark.asyncio
async def test_enqueue_metadata_original_run_id_is_trimmed(tmp_path: Path) -> None:
    """metadata.original_run_id is canonicalized by trimming run_id whitespace. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=3)

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "  run-wl096-008b  ",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )

    metadata = queue.enqueue.call_args.kwargs["metadata"]
    assert metadata["original_run_id"] == "run-wl096-008b"  # @trace WL-096


@pytest.mark.asyncio
async def test_enqueue_metadata_round_is_next_round(tmp_path: Path) -> None:
    """metadata.round equals current_round + 1 (next round number). # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=5)

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-009",
            "enable_revision_queue": True,
            "vetter_revision_round": 2,
        },
    )

    metadata = queue.enqueue.call_args.kwargs["metadata"]
    assert metadata["round"] == 3  # current=2 -> next=3  # @trace WL-096


@pytest.mark.asyncio
async def test_enqueue_receives_project_path_from_run_context(tmp_path: Path) -> None:
    """project_path kwarg to enqueue() comes from run_context['project_path']. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=3)

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-010",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
            "project_path": "/projects/myapp",
        },
    )

    assert queue.enqueue.call_args.kwargs["project_path"] == "/projects/myapp"  # @trace WL-096


# ---------------------------------------------------------------------------
# Test: boundary conditions for round limits
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_round_zero_requests_revision(tmp_path: Path) -> None:
    """Round 0 (first attempt) produces REVISION_REQUESTED. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=1)

    result = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-011",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )

    assert result.verdict == VetterVerdict.REVISION_REQUESTED  # @trace WL-096
    queue.enqueue.assert_called_once()


@pytest.mark.asyncio
async def test_round_at_max_minus_one_requests_revision(tmp_path: Path) -> None:
    """Round max_revision_rounds-1 still produces REVISION_REQUESTED (last allowed). # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    max_rounds = 3
    policy = VetterPolicy(checks=["check"], max_revision_rounds=max_rounds)

    result = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-012",
            "enable_revision_queue": True,
            "vetter_revision_round": max_rounds - 1,  # round 2, max=3 -> still allowed
        },
    )

    assert result.verdict == VetterVerdict.REVISION_REQUESTED  # @trace WL-096
    queue.enqueue.assert_called_once()


@pytest.mark.asyncio
async def test_round_at_max_rejects_with_default_on_fail(tmp_path: Path) -> None:
    """When current_round >= max_revision_rounds, policy.on_fail='reject' -> REJECTED. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=2, on_fail="reject")

    result = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-013",
            "enable_revision_queue": True,
            "vetter_revision_round": 2,
        },
    )

    assert result.verdict == VetterVerdict.REJECTED  # @trace WL-096
    queue.enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_repeated_revision_requested_for_same_run_is_guarded_by_tracker_round(tmp_path: Path) -> None:
    """Second call for same run_id with stale round does not re-request revision. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=1, on_fail="reject")
    run_context = {
        "run_id": "run-wl096-013b",
        "enable_revision_queue": True,
        "vetter_revision_round": 0,
    }

    first = await orch.evaluate(result=MagicMock(), policy=policy, run_context=run_context)
    second = await orch.evaluate(result=MagicMock(), policy=policy, run_context=run_context)

    assert first.verdict == VetterVerdict.REVISION_REQUESTED
    assert second.verdict == VetterVerdict.REJECTED
    assert queue.enqueue.call_count == 1


@pytest.mark.asyncio
async def test_round_beyond_max_never_enqueues(tmp_path: Path) -> None:
    """Rounds strictly > max_revision_rounds never call enqueue(). # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=1)

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-014",
            "enable_revision_queue": True,
            "vetter_revision_round": 99,
        },
    )

    queue.enqueue.assert_not_called()  # @trace WL-096


# ---------------------------------------------------------------------------
# Test: policy.on_fail escalation path on round exhaustion
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_exhausted_rounds_on_fail_escalate_produces_escalated_verdict(tmp_path: Path) -> None:
    """Exhausted rounds with on_fail='escalate' -> ESCALATED verdict. # @trace WL-096"""
    queue = _make_queue()
    hitl = MagicMock()
    orch = _make_orch(
        tmp_path,
        {"check": _failing_check("check")},
        prompt_queue=queue,
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["check"], max_revision_rounds=1, on_fail="escalate")

    result = await orch.evaluate(
        result=MagicMock(output="some diff"),
        policy=policy,
        run_context={
            "run_id": "run-wl096-015",
            "enable_revision_queue": True,
            "vetter_revision_round": 1,
        },
    )

    assert result.verdict == VetterVerdict.ESCALATED  # @trace WL-096


@pytest.mark.asyncio
async def test_exhausted_rounds_on_fail_escalate_calls_hitl(tmp_path: Path) -> None:
    """Exhausted rounds with on_fail='escalate' -> hitl_workflow.await_approval() called. # @trace WL-096"""
    queue = _make_queue()
    hitl = MagicMock()
    orch = _make_orch(
        tmp_path,
        {"check": _failing_check("check")},
        prompt_queue=queue,
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["check"], max_revision_rounds=1, on_fail="escalate")

    await orch.evaluate(
        result=MagicMock(output="some diff"),
        policy=policy,
        run_context={
            "run_id": "run-wl096-016",
            "enable_revision_queue": True,
            "vetter_revision_round": 1,
        },
    )

    hitl.await_approval.assert_called_once()  # @trace WL-096


@pytest.mark.asyncio
async def test_exhausted_rounds_on_fail_escalate_does_not_enqueue(tmp_path: Path) -> None:
    """Exhausted rounds with on_fail='escalate' does NOT call enqueue(). # @trace WL-096"""
    queue = _make_queue()
    hitl = MagicMock()
    orch = _make_orch(
        tmp_path,
        {"check": _failing_check("check")},
        prompt_queue=queue,
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["check"], max_revision_rounds=1, on_fail="escalate")

    await orch.evaluate(
        result=MagicMock(output="some diff"),
        policy=policy,
        run_context={
            "run_id": "run-wl096-017",
            "enable_revision_queue": True,
            "vetter_revision_round": 1,
        },
    )

    queue.enqueue.assert_not_called()  # @trace WL-096


@pytest.mark.asyncio
async def test_exhausted_rounds_escalation_event_written_to_jsonl(tmp_path: Path) -> None:
    """Exhausted rounds with escalate writes vetter_escalation event to governance_events.jsonl. # @trace WL-096"""
    import json

    queue = _make_queue()
    hitl = MagicMock()
    orch = _make_orch(
        tmp_path,
        {"check": _failing_check("check")},
        prompt_queue=queue,
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["check"], max_revision_rounds=1, on_fail="escalate", escalation_lane="urgent")

    await orch.evaluate(
        result=MagicMock(output="some diff"),
        policy=policy,
        run_context={
            "run_id": "run-wl096-018",
            "enable_revision_queue": True,
            "vetter_revision_round": 1,
        },
    )

    lines = (tmp_path / "governance_events.jsonl").read_text(encoding="utf-8").strip().splitlines()
    event_types = [json.loads(line)["event_type"] for line in lines]
    assert "vetter_escalation" in event_types  # @trace WL-096


# ---------------------------------------------------------------------------
# Test: revision disabled / queue absent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revision_disabled_produces_rejected(tmp_path: Path) -> None:
    """When enable_revision_queue=False, failing checks produce REJECTED (no re-queue). # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=3)

    result = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-019",
            "enable_revision_queue": False,
            "vetter_revision_round": 0,
        },
    )

    assert result.verdict == VetterVerdict.REJECTED  # @trace WL-096
    queue.enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_revision_absent_from_context_produces_rejected(tmp_path: Path) -> None:
    """When enable_revision_queue is absent from run_context, failing checks produce REJECTED. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=3)

    result = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "run-wl096-020"},  # no enable_revision_queue key
    )

    assert result.verdict == VetterVerdict.REJECTED  # @trace WL-096
    queue.enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_prompt_queue_none_with_revision_enabled_raises(tmp_path: Path) -> None:
    """prompt_queue=None with revision enabled and rounds remaining raises RuntimeError. # @trace WL-096"""
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"check": _failing_check("check")},
        prompt_queue=None,  # no queue injected
    )
    policy = VetterPolicy(checks=["check"], max_revision_rounds=3)

    with pytest.raises(RuntimeError):  # @trace WL-096
        await orch.evaluate(
            result=MagicMock(),
            policy=policy,
            run_context={
                "run_id": "run-wl096-021",
                "enable_revision_queue": True,
                "vetter_revision_round": 0,
            },
        )


@pytest.mark.asyncio
async def test_revision_enabled_requires_non_empty_run_id(tmp_path: Path) -> None:
    """Revision enqueue fails loudly when run_id is missing. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=3)

    with pytest.raises(RuntimeError, match="non-empty run_id"):  # @trace WL-096
        await orch.evaluate(
            result=MagicMock(),
            policy=policy,
            run_context={
                "enable_revision_queue": True,
                "vetter_revision_round": 0,
            },
        )

    queue.enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_revision_enabled_rejects_whitespace_run_id(tmp_path: Path) -> None:
    """Revision enqueue fails loudly when run_id is whitespace-only. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=3)

    with pytest.raises(RuntimeError, match="non-empty run_id"):  # @trace WL-096
        await orch.evaluate(
            result=MagicMock(),
            policy=policy,
            run_context={
                "run_id": "   ",
                "enable_revision_queue": True,
                "vetter_revision_round": 0,
            },
        )

    queue.enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_revision_round_tracker_uses_normalized_run_id(tmp_path: Path) -> None:
    """Whitespace variations of the same run_id share revision round tracking. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=3)

    first = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "  run-wl096-normalized  ",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )
    assert first.verdict == VetterVerdict.REVISION_REQUESTED

    second = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-normalized",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )
    assert second.verdict == VetterVerdict.REVISION_REQUESTED

    second_metadata = queue.enqueue.call_args.kwargs["metadata"]
    assert second_metadata["round"] == 2


@pytest.mark.asyncio
async def test_revision_round_must_be_integer(tmp_path: Path) -> None:
    """Revision flow fails loudly when vetter_revision_round is not an integer. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=3)

    with pytest.raises(RuntimeError, match="must be an integer >= 0"):  # @trace WL-096
        await orch.evaluate(
            result=MagicMock(),
            policy=policy,
            run_context={
                "run_id": "run-wl096-bad-round-type",
                "enable_revision_queue": True,
                "vetter_revision_round": "2",
            },
        )

    queue.enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_revision_round_must_not_be_negative(tmp_path: Path) -> None:
    """Revision flow fails loudly when vetter_revision_round is negative. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=3)

    with pytest.raises(RuntimeError, match="must be an integer >= 0"):  # @trace WL-096
        await orch.evaluate(
            result=MagicMock(),
            policy=policy,
            run_context={
                "run_id": "run-wl096-bad-round-negative",
                "enable_revision_queue": True,
                "vetter_revision_round": -1,
            },
        )

    queue.enqueue.assert_not_called()


# ---------------------------------------------------------------------------
# Test: VetterResult.revision_prompt content
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revision_prompt_on_result_contains_round(tmp_path: Path) -> None:
    """VetterResult.revision_prompt contains the correct round number. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=5)

    result = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-022",
            "enable_revision_queue": True,
            "vetter_revision_round": 2,
        },
    )

    assert result.revision_prompt is not None
    assert "Round: 3" in result.revision_prompt  # @trace WL-096


@pytest.mark.asyncio
async def test_revision_prompt_on_result_contains_check_name(tmp_path: Path) -> None:
    """VetterResult.revision_prompt contains the failed check name. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(
        tmp_path, {"security_check": _failing_check("security_check", "No hardcoded secrets")}, prompt_queue=queue
    )
    policy = VetterPolicy(checks=["security_check"], max_revision_rounds=3)

    result = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-023",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )

    assert result.revision_prompt is not None
    assert "security_check" in result.revision_prompt  # @trace WL-096


@pytest.mark.asyncio
async def test_revision_prompt_on_result_contains_hint(tmp_path: Path) -> None:
    """VetterResult.revision_prompt contains the hint message from the failing check. # @trace WL-096"""
    queue = _make_queue()
    hint = "Use environment variables instead of literals"
    orch = _make_orch(tmp_path, {"secrets": _failing_check("secrets", hint)}, prompt_queue=queue)
    policy = VetterPolicy(checks=["secrets"], max_revision_rounds=3)

    result = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-024",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )

    assert result.revision_prompt is not None
    assert hint in result.revision_prompt  # @trace WL-096


# ---------------------------------------------------------------------------
# Test: multiple failing checks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_multiple_failing_checks_all_ids_in_enqueued_prompt(tmp_path: Path) -> None:
    """All failed check IDs appear in the enqueued revision prompt. # @trace WL-096"""
    queue = _make_queue()
    registry = {
        "linter": _failing_check("linter", "Fix lint errors"),
        "tests": _failing_check("tests", "Tests must pass"),
    }
    orch = _make_orch(tmp_path, registry, prompt_queue=queue)
    policy = VetterPolicy(checks=["linter", "tests"], max_revision_rounds=3)

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-025",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )

    prompt_text = queue.enqueue.call_args.args[0]
    assert "linter" in prompt_text  # @trace WL-096
    assert "tests" in prompt_text


@pytest.mark.asyncio
async def test_multiple_failing_checks_all_hints_in_enqueued_prompt(tmp_path: Path) -> None:
    """All hint messages from failing checks appear in the enqueued revision prompt. # @trace WL-096"""
    queue = _make_queue()
    hint_a = "Fix lint errors"
    hint_b = "Tests must pass"
    registry = {
        "linter": _failing_check("linter", hint_a),
        "tests": _failing_check("tests", hint_b),
    }
    orch = _make_orch(tmp_path, registry, prompt_queue=queue)
    policy = VetterPolicy(checks=["linter", "tests"], max_revision_rounds=3)

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-026",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )

    prompt_text = queue.enqueue.call_args.args[0]
    assert hint_a in prompt_text  # @trace WL-096
    assert hint_b in prompt_text


@pytest.mark.asyncio
async def test_passing_checks_not_in_failed_ids_of_prompt(tmp_path: Path) -> None:
    """Passing checks do NOT appear in the failed_checks section of the revision prompt. # @trace WL-096"""
    queue = _make_queue()
    registry = {
        "bad": _failing_check("bad", "Needs work"),
        "good": _passing_check("good"),
    }
    orch = _make_orch(tmp_path, registry, prompt_queue=queue)
    policy = VetterPolicy(checks=["bad", "good"], max_revision_rounds=3)

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-027",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )

    prompt_text = queue.enqueue.call_args.args[0]
    # "bad" must appear in the failed checks section
    assert "bad" in prompt_text  # @trace WL-096
    # "good" must NOT appear as a failed check (it passed)
    # The check: good should not be in "Failed checks:" line
    lines = prompt_text.splitlines()
    failed_line = next((l for l in lines if l.startswith("Failed checks:")), "")
    assert "good" not in failed_line


@pytest.mark.asyncio
async def test_enqueue_called_with_project_path_none_when_not_in_context(tmp_path: Path) -> None:
    """project_path kwarg is None when run_context has no project_path key. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=3)

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-028",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
            # no project_path
        },
    )

    assert queue.enqueue.call_args.kwargs["project_path"] is None  # @trace WL-096


@pytest.mark.asyncio
async def test_no_infinite_loop_max_rounds_zero(tmp_path: Path) -> None:
    """max_revision_rounds=0 means revision is never possible; always reject. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=0)

    result = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-029",
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )

    # 0 >= 0 so exhausted immediately -> reject
    assert result.verdict == VetterVerdict.REJECTED  # @trace WL-096
    queue.enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_metadata_complete_structure(tmp_path: Path) -> None:
    """All three required metadata keys are present and correct in enqueue call. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=5)

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "run-wl096-030",
            "enable_revision_queue": True,
            "vetter_revision_round": 3,
        },
    )

    metadata = queue.enqueue.call_args.kwargs["metadata"]
    assert set(metadata.keys()) >= {"vetter_revision", "original_run_id", "round"}  # @trace WL-096
    assert metadata["vetter_revision"] is True
    assert metadata["original_run_id"] == "run-wl096-030"
    assert metadata["round"] == 4  # 3 + 1


@pytest.mark.asyncio
async def test_exhausted_revision_path_does_not_requeue_without_new_round(tmp_path: Path) -> None:
    """Exhausted revision path cannot requeue unless a new round is provided. # @trace WL-096"""
    queue = _make_queue()
    orch = _make_orch(tmp_path, {"check": _failing_check("check")}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=1, on_fail="reject")
    exhausted_context = {
        "run_id": "run-wl096-regression-exhausted",
        "enable_revision_queue": True,
        "vetter_revision_round": 1,
    }

    first = await orch.evaluate(result=MagicMock(), policy=policy, run_context=exhausted_context)
    second = await orch.evaluate(result=MagicMock(), policy=policy, run_context=exhausted_context)

    assert first.verdict == VetterVerdict.REJECTED
    assert second.verdict == VetterVerdict.REJECTED
    queue.enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_revision_round_tracker_stays_monotonic_across_mixed_outcomes(tmp_path: Path) -> None:
    """Tracker never regresses for same run_id even when stale rounds are supplied. # @trace WL-096"""
    queue = _make_queue()
    failing = _failing_check("check", "needs revision")
    passing = _passing_check("check")
    orch = _make_orch(tmp_path, {"check": failing}, prompt_queue=queue)
    policy = VetterPolicy(checks=["check"], max_revision_rounds=2, on_fail="reject")
    run_id = "run-wl096-monotonic"

    first = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": run_id,
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )
    assert first.verdict == VetterVerdict.REVISION_REQUESTED
    assert queue.enqueue.call_args_list[0].kwargs["metadata"]["round"] == 1

    orch.check_registry["check"] = passing
    second = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": run_id,
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )
    assert second.verdict == VetterVerdict.APPROVED
    assert queue.enqueue.call_count == 1

    orch.check_registry["check"] = _failing_check("check", "needs second revision")
    third = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": run_id,
            "enable_revision_queue": True,
            "vetter_revision_round": 0,
        },
    )
    assert third.verdict == VetterVerdict.REVISION_REQUESTED
    assert queue.enqueue.call_count == 2
    assert queue.enqueue.call_args_list[1].kwargs["metadata"]["round"] == 2
