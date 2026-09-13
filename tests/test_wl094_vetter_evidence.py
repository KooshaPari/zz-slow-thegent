"""Integration tests for WL-094: EvidenceStore.append wired into VetterOrchestrator.evaluate().

Tests verify:
- EvidenceStore.append is called with exact required arguments on every evaluate() call
- kind="agent_decision", actor="vetter_orchestrator", resource="session:{sid}/run:{rid}"
- payload contains verdict, failed_checks (list), passed_checks (list), duration_ms
- Hash chain integrity passes after every append (single and multi-call chains)
- Tamper-evident chain is maintained across multiple vetting decisions
- Evidence is NOT appended when evidence_store is None (pure isolation path)
- All four verdicts (approved/rejected/escalated/revision_requested) produce correct evidence

All tests use the real EvidenceStore (not mocks) to exercise the tamper-evident chain.
Mock evidence_store tests appear only where isolating exact call arguments.

# @trace WL-094
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
from thegent.governance.compliance import ComplianceEvidence, EvidenceStore

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _passing_check(name: str) -> Any:
    """Async VetterCheck mock that always passes. # @trace WL-094"""
    check = MagicMock()
    check.name = name
    check.check = AsyncMock(return_value=VetterCheckResult(check_name=name, passed=True))
    return check


def _failing_check(name: str, message: str = "failed") -> Any:
    """Async VetterCheck mock that always fails. # @trace WL-094"""
    check = MagicMock()
    check.name = name
    check.check = AsyncMock(return_value=VetterCheckResult(check_name=name, passed=False, message=message))
    return check


def _make_store(tmp_path: Path, filename: str = "evidence.jsonl") -> EvidenceStore:
    """Create a fresh EvidenceStore under tmp_path. # @trace WL-094"""
    return EvidenceStore(store_path=tmp_path / filename)


def _make_orch(
    session_dir: Path,
    registry: dict[str, Any],
    evidence_store: EvidenceStore | None,
) -> VetterOrchestrator:
    """Construct VetterOrchestrator with given evidence_store. # @trace WL-094"""
    return VetterOrchestrator(
        session_dir=session_dir,
        check_registry=registry,
        evidence_store=evidence_store,
    )


# ---------------------------------------------------------------------------
# 1. Evidence appended on approved verdict
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evidence_appended_on_approved_verdict(tmp_path: Path) -> None:
    """Real EvidenceStore receives one record when evaluate() returns approved. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {"alpha": _passing_check("alpha")},
        store,
    )
    policy = VetterPolicy(checks=["alpha"])
    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "run-001", "session_id": "sess-001"},
    )
    records = store.list_all()
    assert len(records) == 1
    assert records[0].kind == "agent_decision"


# ---------------------------------------------------------------------------
# 2. Evidence appended on rejected verdict
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evidence_appended_on_rejected_verdict(tmp_path: Path) -> None:
    """Real EvidenceStore receives one record when evaluate() returns rejected. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {"bad": _failing_check("bad")},
        store,
    )
    policy = VetterPolicy(checks=["bad"])
    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "run-002", "session_id": "sess-001"},
    )
    records = store.list_all()
    assert len(records) == 1
    assert records[0].payload["verdict"] == "rejected"


# ---------------------------------------------------------------------------
# 3. actor field is always "vetter_orchestrator"
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evidence_actor_is_vetter_orchestrator(tmp_path: Path) -> None:
    """Evidence record actor is exactly 'vetter_orchestrator'. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {"alpha": _passing_check("alpha")},
        store,
    )
    policy = VetterPolicy(checks=["alpha"])
    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "r1", "session_id": "s1"},
    )
    record = store.list_all()[0]
    assert record.actor == "vetter_orchestrator"


# ---------------------------------------------------------------------------
# 4. resource format is "session:{sid}/run:{rid}"
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evidence_resource_format(tmp_path: Path) -> None:
    """Evidence resource is formatted as 'session:{sid}/run:{rid}'. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {"alpha": _passing_check("alpha")},
        store,
    )
    policy = VetterPolicy(checks=["alpha"])
    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "run-xyz", "session_id": "sess-abc"},
    )
    record = store.list_all()[0]
    assert record.resource == "session:sess-abc/run:run-xyz"


# ---------------------------------------------------------------------------
# 5. payload contains verdict
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evidence_payload_contains_verdict(tmp_path: Path) -> None:
    """Evidence payload.verdict matches VetterResult.verdict.value. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {"alpha": _passing_check("alpha")},
        store,
    )
    policy = VetterPolicy(checks=["alpha"])
    result = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "r1", "session_id": "s1"},
    )
    record = store.list_all()[0]
    assert record.payload["verdict"] == result.verdict.value


# ---------------------------------------------------------------------------
# 6. payload contains passed_checks list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evidence_payload_contains_passed_checks(tmp_path: Path) -> None:
    """Evidence payload.passed_checks is a list of check names that passed. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {"good": _passing_check("good"), "bad": _failing_check("bad")},
        store,
    )
    policy = VetterPolicy(checks=["good", "bad"])
    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "r1", "session_id": "s1"},
    )
    record = store.list_all()[0]
    assert "passed_checks" in record.payload
    assert "good" in record.payload["passed_checks"]
    assert "bad" not in record.payload["passed_checks"]


# ---------------------------------------------------------------------------
# 7. payload contains failed_checks list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evidence_payload_contains_failed_checks(tmp_path: Path) -> None:
    """Evidence payload.failed_checks is a list of check names that failed. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {"bad1": _failing_check("bad1"), "bad2": _failing_check("bad2")},
        store,
    )
    policy = VetterPolicy(checks=["bad1", "bad2"])
    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "r1", "session_id": "s1"},
    )
    record = store.list_all()[0]
    assert "failed_checks" in record.payload
    assert "bad1" in record.payload["failed_checks"]
    assert "bad2" in record.payload["failed_checks"]


@pytest.mark.asyncio
async def test_evidence_payload_failed_passed_checks_capture_exact_details(tmp_path: Path) -> None:
    """Mixed check outcomes preserve exact failed/passed check-name details. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {
            "alpha": _passing_check("alpha"),
            "beta": _failing_check("beta"),
            "gamma": _passing_check("gamma"),
            "delta": _failing_check("delta"),
        },
        store,
    )
    policy = VetterPolicy(checks=["alpha", "beta", "gamma", "delta"])
    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "run-detail", "session_id": "sess-detail"},
    )

    payload = store.list_all()[0].payload
    assert payload["passed_checks"] == ["alpha", "gamma"]
    assert payload["failed_checks"] == ["beta", "delta"]


@pytest.mark.asyncio
async def test_evidence_payload_failed_passed_checks_empty_side_is_explicit(tmp_path: Path) -> None:
    """All-pass verdict writes empty failed_checks list and non-empty passed_checks. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {"ok1": _passing_check("ok1"), "ok2": _passing_check("ok2")},
        store,
    )
    policy = VetterPolicy(checks=["ok1", "ok2"])
    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "run-all-pass", "session_id": "sess-all-pass"},
    )

    payload = store.list_all()[0].payload
    assert payload["passed_checks"] == ["ok1", "ok2"]
    assert payload["failed_checks"] == []


# ---------------------------------------------------------------------------
# 8. payload contains duration_ms as int
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evidence_payload_contains_duration_ms(tmp_path: Path) -> None:
    """Evidence payload.duration_ms is a non-negative integer. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {"alpha": _passing_check("alpha")},
        store,
    )
    policy = VetterPolicy(checks=["alpha"])
    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "r1", "session_id": "s1"},
    )
    record = store.list_all()[0]
    assert "duration_ms" in record.payload
    assert isinstance(record.payload["duration_ms"], int)
    assert record.payload["duration_ms"] >= 0


# ---------------------------------------------------------------------------
# 9. Hash chain integrity passes after a single append
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hash_chain_integrity_single_append(tmp_path: Path) -> None:
    """Hash chain integrity passes after one evidence append. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {"alpha": _passing_check("alpha")},
        store,
    )
    policy = VetterPolicy(checks=["alpha"])
    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "r1", "session_id": "s1"},
    )
    assert store.verify_integrity() is True


# ---------------------------------------------------------------------------
# 10. Hash chain integrity passes after multiple appends (same orchestrator)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hash_chain_integrity_multiple_appends_same_orch(tmp_path: Path) -> None:
    """Hash chain integrity passes after 5 evaluate() calls via same orchestrator. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {"alpha": _passing_check("alpha")},
        store,
    )
    policy = VetterPolicy(checks=["alpha"])
    for i in range(5):
        await orch.evaluate(
            result=MagicMock(),
            policy=policy,
            run_context={"run_id": f"run-{i:03d}", "session_id": "sess-multi"},
        )
    assert store.verify_integrity() is True
    assert len(store.list_all()) == 5


# ---------------------------------------------------------------------------
# 11. Hash chain integrity with mixed verdicts
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hash_chain_integrity_mixed_verdicts(tmp_path: Path) -> None:
    """Hash chain integrity holds across approved/rejected/approved decisions. # @trace WL-094"""
    store = _make_store(tmp_path)
    pass_registry = {"alpha": _passing_check("alpha")}
    fail_registry = {"bad": _failing_check("bad")}

    orch_pass = _make_orch(tmp_path, pass_registry, store)
    orch_fail = _make_orch(tmp_path, fail_registry, store)

    await orch_pass.evaluate(
        result=MagicMock(),
        policy=VetterPolicy(checks=["alpha"]),
        run_context={"run_id": "r1", "session_id": "s1"},
    )
    await orch_fail.evaluate(
        result=MagicMock(),
        policy=VetterPolicy(checks=["bad"]),
        run_context={"run_id": "r2", "session_id": "s1"},
    )
    await orch_pass.evaluate(
        result=MagicMock(),
        policy=VetterPolicy(checks=["alpha"]),
        run_context={"run_id": "r3", "session_id": "s1"},
    )

    records = store.list_all()
    assert len(records) == 3
    verdicts = [r.payload["verdict"] for r in records]
    assert verdicts == ["approved", "rejected", "approved"]
    assert store.verify_integrity() is True


# ---------------------------------------------------------------------------
# 12. Hash chain is tamper-evident — modified record breaks integrity
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hash_chain_tamper_detection(tmp_path: Path) -> None:
    """Manually altering stored JSONL breaks verify_integrity(). # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {"alpha": _passing_check("alpha")},
        store,
    )
    policy = VetterPolicy(checks=["alpha"])
    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "r-tamper", "session_id": "s1"},
    )
    assert store.verify_integrity() is True

    # Tamper: overwrite the file with corrupted content
    store_path = store.store_path
    original = store_path.read_text(encoding="utf-8")
    # Flip a character in the middle of the entry_hash
    lines = original.strip().splitlines()
    corrupted_line = lines[0].replace('"approved"', '"rejected"')
    store_path.write_text(corrupted_line + "\n", encoding="utf-8")

    assert store.verify_integrity() is False


# ---------------------------------------------------------------------------
# 13. Evidence NOT appended when evidence_store is None
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_evidence_appended_when_store_is_none(tmp_path: Path) -> None:
    """When evidence_store=None, no evidence store interaction occurs. # @trace WL-094"""
    orch = _make_orch(
        tmp_path,
        {"alpha": _passing_check("alpha")},
        None,
    )
    policy = VetterPolicy(checks=["alpha"])
    # Should complete without error
    result = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "r1", "session_id": "s1"},
    )
    assert result.verdict == VetterVerdict.APPROVED
    # No evidence file created (since no store was provided)
    evidence_file = tmp_path / "evidence.jsonl"
    assert not evidence_file.exists()


# ---------------------------------------------------------------------------
# 14. Evidence record kind is always "agent_decision"
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evidence_kind_is_agent_decision(tmp_path: Path) -> None:
    """Every appended record has kind='agent_decision'. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {"alpha": _passing_check("alpha"), "bad": _failing_check("bad")},
        store,
    )

    await orch.evaluate(
        result=MagicMock(),
        policy=VetterPolicy(checks=["alpha"]),
        run_context={"run_id": "r1", "session_id": "s1"},
    )
    await orch.evaluate(
        result=MagicMock(),
        policy=VetterPolicy(checks=["bad"]),
        run_context={"run_id": "r2", "session_id": "s1"},
    )

    records = store.list_all()
    assert all(r.kind == "agent_decision" for r in records)


# ---------------------------------------------------------------------------
# 15. One evidence record per evaluate() call (count matches call count)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_one_evidence_record_per_evaluate_call(tmp_path: Path) -> None:
    """evaluate() appends exactly one evidence record per call. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {"alpha": _passing_check("alpha")},
        store,
    )
    policy = VetterPolicy(checks=["alpha"])

    for call_num in range(7):
        await orch.evaluate(
            result=MagicMock(),
            policy=policy,
            run_context={"run_id": f"run-{call_num}", "session_id": "s-count"},
        )
        assert len(store.list_all()) == call_num + 1


# ---------------------------------------------------------------------------
# 16. Mock-based: append called with exact kwargs (argument contract)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_append_called_with_exact_kwargs(tmp_path: Path) -> None:
    """_append_evidence calls evidence_store.append with exact required kwargs. # @trace WL-094"""
    mock_store = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"alpha": _passing_check("alpha")},
        evidence_store=mock_store,
    )
    policy = VetterPolicy(checks=["alpha"])
    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "run-kwarg", "session_id": "sess-kwarg"},
    )

    mock_store.append.assert_called_once()
    kwargs = mock_store.append.call_args.kwargs
    assert kwargs["kind"] == "agent_decision"
    assert kwargs["actor"] == "vetter_orchestrator"
    assert kwargs["resource"] == "session:sess-kwarg/run:run-kwarg"
    assert "verdict" in kwargs["payload"]
    assert "failed_checks" in kwargs["payload"]
    assert "passed_checks" in kwargs["payload"]
    assert "duration_ms" in kwargs["payload"]


@pytest.mark.asyncio
async def test_append_raises_when_evidence_integrity_check_fails(tmp_path: Path) -> None:
    """evaluate() fails loudly when evidence_store.verify_integrity() returns False. # @trace WL-094"""
    mock_store = MagicMock()
    mock_store.verify_integrity.return_value = False
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"alpha": _passing_check("alpha")},
        evidence_store=mock_store,
    )
    policy = VetterPolicy(checks=["alpha"])

    with pytest.raises(RuntimeError, match="hash-chain integrity failed"):
        await orch.evaluate(
            result=MagicMock(),
            policy=policy,
            run_context={"run_id": "run-integrity-fail", "session_id": "sess-kwarg"},
        )

    mock_store.append.assert_called_once()
    mock_store.verify_integrity.assert_called_once()


@pytest.mark.asyncio
async def test_append_raises_with_missing_run_id(tmp_path: Path) -> None:
    """evaluate() fails loudly when evidence append would run without run_id. # @trace WL-094"""
    mock_store = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"alpha": _passing_check("alpha")},
        evidence_store=mock_store,
    )
    policy = VetterPolicy(checks=["alpha"])

    with pytest.raises(RuntimeError, match="non-empty run_id"):
        await orch.evaluate(
            result=MagicMock(),
            policy=policy,
            run_context={"session_id": "sess-missing-run"},
        )

    mock_store.append.assert_not_called()


@pytest.mark.asyncio
async def test_append_raises_with_missing_session_id(tmp_path: Path) -> None:
    """evaluate() fails loudly when evidence append would run without session_id. # @trace WL-094"""
    mock_store = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"alpha": _passing_check("alpha")},
        evidence_store=mock_store,
    )
    policy = VetterPolicy(checks=["alpha"])

    with pytest.raises(RuntimeError, match="non-empty session_id"):
        await orch.evaluate(
            result=MagicMock(),
            policy=policy,
            run_context={"run_id": "run-missing-session"},
        )

    mock_store.append.assert_not_called()


@pytest.mark.asyncio
async def test_append_raises_with_whitespace_run_id(tmp_path: Path) -> None:
    """Whitespace-only run_id is rejected before evidence append. # @trace WL-094"""
    mock_store = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"alpha": _passing_check("alpha")},
        evidence_store=mock_store,
    )
    policy = VetterPolicy(checks=["alpha"])

    with pytest.raises(RuntimeError, match="non-empty run_id"):
        await orch.evaluate(
            result=MagicMock(),
            policy=policy,
            run_context={"run_id": "   ", "session_id": "sess-whitespace-run"},
        )

    mock_store.append.assert_not_called()


@pytest.mark.asyncio
async def test_append_normalizes_resource_ids_before_write(tmp_path: Path) -> None:
    """Evidence resource trims run_id/session_id before append for canonical audit keys. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {"alpha": _passing_check("alpha")},
        store,
    )
    policy = VetterPolicy(checks=["alpha"])

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "  run-094-trim  ", "session_id": "  sess-094-trim  "},
    )

    record = store.list_all()[0]
    assert record.resource == "session:sess-094-trim/run:run-094-trim"


# ---------------------------------------------------------------------------
# 17. Hash chain persists across separate EvidenceStore instances
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hash_chain_persists_across_store_instances(tmp_path: Path) -> None:
    """Hash chain integrity holds when a new EvidenceStore re-opens the same file. # @trace WL-094"""
    store_path = tmp_path / "persistent_evidence.jsonl"

    # First store writes 3 records
    store1 = EvidenceStore(store_path=store_path)
    orch1 = _make_orch(tmp_path, {"alpha": _passing_check("alpha")}, store1)
    policy = VetterPolicy(checks=["alpha"])
    for i in range(3):
        await orch1.evaluate(
            result=MagicMock(),
            policy=policy,
            run_context={"run_id": f"r{i}", "session_id": "s1"},
        )

    # A new store instance re-opens the same file — should verify OK
    store2 = EvidenceStore(store_path=store_path)
    assert store2.verify_integrity() is True
    assert len(store2.list_all()) == 3


# ---------------------------------------------------------------------------
# 18. Escalated verdict produces evidence with verdict="escalated"
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evidence_appended_for_escalated_verdict(tmp_path: Path) -> None:
    """Evidence is appended even when verdict is escalated, with correct payload. # @trace WL-094"""
    store = _make_store(tmp_path)
    hitl = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"safety": _failing_check("safety")},
        evidence_store=store,
        hitl_workflow=hitl,
    )
    policy = VetterPolicy(checks=["safety"], escalate_on=["safety"])
    result = await orch.evaluate(
        result=MagicMock(output="diff"),
        policy=policy,
        run_context={"run_id": "r-esc", "session_id": "s-esc", "owner": "alice"},
    )

    assert result.verdict == VetterVerdict.ESCALATED
    records = store.list_all()
    assert len(records) == 1
    assert records[0].payload["verdict"] == "escalated"
    assert "safety" in records[0].payload["failed_checks"]
    assert store.verify_integrity() is True


# ---------------------------------------------------------------------------
# 19. Revision-requested verdict produces evidence with correct payload
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evidence_appended_for_revision_requested_verdict(tmp_path: Path) -> None:
    """Evidence is appended when verdict is revision_requested. # @trace WL-094"""
    store = _make_store(tmp_path)
    queue = MagicMock()
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry={"style": _failing_check("style", "Too long")},
        evidence_store=store,
        prompt_queue=queue,
    )
    policy = VetterPolicy(checks=["style"], max_revision_rounds=3)
    result = await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={
            "run_id": "r-rev",
            "session_id": "s-rev",
            "enable_revision_queue": True,
            "vetter_revision_round": 1,
        },
    )

    assert result.verdict == VetterVerdict.REVISION_REQUESTED
    records = store.list_all()
    assert len(records) == 1
    assert records[0].payload["verdict"] == "revision_requested"
    assert "style" in records[0].payload["failed_checks"]
    assert store.verify_integrity() is True


# ---------------------------------------------------------------------------
# 20. verdict/duration payload shape for all terminal verdicts
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("policy", "registry", "run_context", "expected_verdict", "needs_hitl"),
    [
        (
            VetterPolicy(checks=["pass"]),
            {"pass": _passing_check("pass")},
            {"run_id": "payload-approved", "session_id": "sess-v"},
            VetterVerdict.APPROVED,
            False,
        ),
        (
            VetterPolicy(checks=["fail"]),
            {"fail": _failing_check("fail")},
            {"run_id": "payload-rejected", "session_id": "sess-v"},
            VetterVerdict.REJECTED,
            False,
        ),
        (
            VetterPolicy(checks=["esc"], escalate_on=["esc"], escalation_lane="critical"),
            {"esc": _failing_check("esc")},
            {"run_id": "payload-escalated", "session_id": "sess-v", "owner": "alice"},
            VetterVerdict.ESCALATED,
            True,
        ),
        (
            VetterPolicy(checks=["rev"], max_revision_rounds=2),
            {"rev": _failing_check("rev", "fix this")},
            {
                "run_id": "payload-revision",
                "session_id": "sess-v",
                "enable_revision_queue": True,
                "vetter_revision_round": 0,
            },
            VetterVerdict.REVISION_REQUESTED,
            False,
        ),
    ],
)
async def test_evidence_payload_contains_verdict_and_duration_for_all_verdicts(
    tmp_path: Path,
    policy: VetterPolicy,
    registry: dict[str, Any],
    run_context: dict[str, Any],
    expected_verdict: VetterVerdict,
    needs_hitl: bool,
) -> None:
    """Each verdict appends payload with exact verdict and non-negative duration_ms. # @trace WL-094"""
    store = _make_store(tmp_path)
    queue = MagicMock()
    hitl = MagicMock() if needs_hitl else None
    orch = VetterOrchestrator(
        session_dir=tmp_path,
        check_registry=registry,
        evidence_store=store,
        prompt_queue=queue,
        hitl_workflow=hitl,
    )

    result = await orch.evaluate(result=MagicMock(output="diff"), policy=policy, run_context=run_context)
    assert result.verdict == expected_verdict

    record = store.list_all()[0]
    assert record.payload["verdict"] == expected_verdict.value
    assert isinstance(record.payload["duration_ms"], int)
    assert record.payload["duration_ms"] >= 0


# ---------------------------------------------------------------------------
# 21. Long chain (20 calls) maintains integrity
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hash_chain_integrity_long_chain_20_calls(tmp_path: Path) -> None:
    """Hash chain integrity holds across 20 consecutive evaluate() calls. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {"alpha": _passing_check("alpha"), "bad": _failing_check("bad")},
        store,
    )

    for i in range(20):
        check_name = "alpha" if i % 2 == 0 else "bad"
        await orch.evaluate(
            result=MagicMock(),
            policy=VetterPolicy(checks=[check_name]),
            run_context={"run_id": f"run-{i:03d}", "session_id": "sess-long"},
        )

    records = store.list_all()
    assert len(records) == 20
    assert store.verify_integrity() is True


# ---------------------------------------------------------------------------
# 22. Evidence record fields conform to ComplianceEvidence schema
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evidence_record_is_valid_compliance_evidence(tmp_path: Path) -> None:
    """Appended record deserializes as a valid ComplianceEvidence instance. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {"alpha": _passing_check("alpha")},
        store,
    )
    policy = VetterPolicy(checks=["alpha"])
    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "r-schema", "session_id": "s-schema"},
    )
    records = store.list_all()
    assert len(records) == 1
    record = records[0]
    assert isinstance(record, ComplianceEvidence)
    assert record.evidence_id  # non-empty
    assert record.timestamp_utc  # non-empty
    assert record.entry_hash  # non-empty
    assert record.prev_hash == ""  # first record has empty prev_hash


@pytest.mark.asyncio
async def test_evidence_append_order_matches_evaluate_order_across_runs(tmp_path: Path) -> None:
    """Evidence append order is stable across multiple evaluate() calls. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(
        tmp_path,
        {
            "alpha": _passing_check("alpha"),
            "beta": _failing_check("beta", "needs fix"),
        },
        store,
    )

    call_sequence = [
        ("run-order-001", VetterPolicy(checks=["alpha"])),
        ("run-order-002", VetterPolicy(checks=["beta"])),
        ("run-order-003", VetterPolicy(checks=["alpha"])),
        ("run-order-004", VetterPolicy(checks=["beta"])),
    ]
    for run_id, policy in call_sequence:
        await orch.evaluate(
            result=MagicMock(),
            policy=policy,
            run_context={"run_id": run_id, "session_id": "sess-order"},
        )

    records = store.list_all()
    resources = [record.resource for record in records]
    assert resources == [
        "session:sess-order/run:run-order-001",
        "session:sess-order/run:run-order-002",
        "session:sess-order/run:run-order-003",
        "session:sess-order/run:run-order-004",
    ]


@pytest.mark.asyncio
async def test_evidence_payload_reflects_fail_fast_executed_checks_only(tmp_path: Path) -> None:
    """Fail-fast short-circuit is reflected in evidence payload check lists. # @trace WL-094"""
    store = _make_store(tmp_path)
    first_bad = _failing_check("first_bad", "stop early")
    second_good = _passing_check("second_good")
    orch = _make_orch(
        tmp_path,
        {"first_bad": first_bad, "second_good": second_good},
        store,
    )
    policy = VetterPolicy(checks=["first_bad", "second_good"], fail_fast=True)

    await orch.evaluate(
        result=MagicMock(),
        policy=policy,
        run_context={"run_id": "run-fail-fast-evidence", "session_id": "sess-fail-fast"},
    )

    first_bad.check.assert_awaited_once()
    second_good.check.assert_not_awaited()
    payload = store.list_all()[0].payload
    assert payload["failed_checks"] == ["first_bad"]
    assert payload["passed_checks"] == []


@pytest.mark.asyncio
async def test_evidence_append_rejects_whitespace_only_session_id(tmp_path: Path) -> None:
    """Whitespace-only session_id is rejected before evidence append. # @trace WL-094"""
    store = _make_store(tmp_path)
    orch = _make_orch(tmp_path, {"alpha": _passing_check("alpha")}, store)
    policy = VetterPolicy(checks=["alpha"])

    with pytest.raises(RuntimeError, match="non-empty session_id"):
        await orch.evaluate(
            result=MagicMock(),
            policy=policy,
            run_context={"run_id": "run-session-whitespace", "session_id": "   "},
        )
