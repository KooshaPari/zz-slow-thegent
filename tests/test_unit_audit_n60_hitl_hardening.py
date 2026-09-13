"""AUDIT-N+60: governance/hitl hardening spec (SOTA pass-37).

15 invariants FR-GOV-HL-001..015 covering GovernanceEventLog init,
path guard, emit, list_pending_approvals, update_status,
HITLApprovalWorkflow approve/reject, HITLManager request/approve,
corrupt-line resilience, and canonical ``__all__``.

Source: src/thegent/governance/hitl.py

@trace AUDIT-N+60  FR-GOV-HL-001..015
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from thegent.governance import hitl as _mod
from thegent.governance.hitl import (
    GovernanceEventLog,
    HITLApprovalWorkflow,
    HITLDecision,
    HITLManager,
    PolicyEngine,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# FR-GOV-HL-001 -- GovernanceEventLog is constructible with absolute session_dir
# ---------------------------------------------------------------------------


class TestGELInit:
    """FR-GOV-HL-001: ``GovernanceEventLog(session_dir)`` stores paths."""

    def test_init_sets_session_dir(self, tmp_path: Path) -> None:
        gel = GovernanceEventLog(tmp_path)
        assert gel.session_dir == tmp_path

    def test_init_sets_events_path(self, tmp_path: Path) -> None:
        gel = GovernanceEventLog(tmp_path)
        assert gel.events_path == tmp_path / "governance_events.jsonl"


# ---------------------------------------------------------------------------
# FR-GOV-HL-002 -- GovernanceEventLog rejects relative session_dir
# ---------------------------------------------------------------------------


class TestGELPathGuard:
    """FR-GOV-HL-002: ``session_dir`` must be absolute."""

    def test_rejects_relative_path(self) -> None:
        with pytest.raises(ValueError, match="absolute"):
            GovernanceEventLog(Path("relative/session"))

    def test_accepts_absolute_path(self, tmp_path: Path) -> None:
        gel = GovernanceEventLog(tmp_path)
        assert gel.session_dir.is_absolute()


# ---------------------------------------------------------------------------
# FR-GOV-HL-003 -- HITLApprovalWorkflow is constructible with absolute session_dir
# ---------------------------------------------------------------------------


class TestWorkflowInit:
    """FR-GOV-HL-003: ``HITLApprovalWorkflow(session_dir)`` stores paths."""

    def test_init_sets_session_dir(self, tmp_path: Path) -> None:
        wf = HITLApprovalWorkflow(tmp_path)
        assert wf.session_dir == tmp_path


# ---------------------------------------------------------------------------
# FR-GOV-HL-004 -- HITLApprovalWorkflow rejects relative session_dir
# ---------------------------------------------------------------------------


class TestWorkflowPathGuard:
    """FR-GOV-HL-004: ``session_dir`` must be absolute."""

    def test_rejects_relative_path(self) -> None:
        with pytest.raises(ValueError, match="absolute"):
            HITLApprovalWorkflow(Path("relative/session"))

    def test_accepts_absolute_path(self, tmp_path: Path) -> None:
        wf = HITLApprovalWorkflow(tmp_path)
        assert wf.session_dir.is_absolute()


# ---------------------------------------------------------------------------
# FR-GOV-HL-005 -- GovernanceEventLog.emit() creates parent directories
# ---------------------------------------------------------------------------


class TestGLEmit:
    """FR-GOV-HL-005: ``emit`` creates parent dirs and writes JSONL."""

    def test_emit_creates_session_dir(self, tmp_path: Path) -> None:
        session = tmp_path / "nested" / "dir"
        gel = GovernanceEventLog(session)
        gel.emit({"event_type": "test", "key": "value"})
        assert session.is_dir()

    def test_emit_writes_jsonl(self, tmp_path: Path) -> None:
        gel = GovernanceEventLog(tmp_path)
        gel.emit({"event_type": "test", "key": "value"})
        lines = gel.events_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        ev = json.loads(lines[0])
        assert ev["event_type"] == "test"
        assert ev["key"] == "value"


# ---------------------------------------------------------------------------
# FR-GOV-HL-006 -- GovernanceEventLog.list_pending_approvals() returns [] when no file
# ---------------------------------------------------------------------------


class TestGELListPending:
    """FR-GOV-HL-006: ``list_pending_approvals`` returns [] when file doesn't exist."""

    def test_returns_empty_when_no_file(self, tmp_path: Path) -> None:
        gel = GovernanceEventLog(tmp_path)
        assert gel.list_pending_approvals() == []

    def test_returns_empty_when_filtered_run_id_not_found(self, tmp_path: Path) -> None:
        gel = GovernanceEventLog(tmp_path)
        gel.emit(
            {
                "event_type": "await_approval",
                "run_id": "run-1",
                "status": "pending",
            }
        )
        assert gel.list_pending_approvals(run_id="nonexistent") == []


# ---------------------------------------------------------------------------
# FR-GOV-HL-007 -- GovernanceEventLog.list_pending_approvals() skips corrupt JSONL lines
# ---------------------------------------------------------------------------


class TestGELCorruptResilience:
    """FR-GOV-HL-007: corrupt JSONL lines are skipped, not fatal."""

    def test_skips_corrupt_line(self, tmp_path: Path) -> None:
        gel = GovernanceEventLog(tmp_path)
        gel.events_path.write_text(
            '{bad json\n{"event_type": "await_approval", "run_id": "r1", "status": "pending"}\n',
            encoding="utf-8",
        )
        pending = gel.list_pending_approvals()
        assert len(pending) == 1
        assert pending[0]["run_id"] == "r1"

    def test_all_corrupt_returns_empty(self, tmp_path: Path) -> None:
        gel = GovernanceEventLog(tmp_path)
        gel.events_path.write_text("{bad\n{also bad\n", encoding="utf-8")
        assert gel.list_pending_approvals() == []


# ---------------------------------------------------------------------------
# FR-GOV-HL-008 -- GovernanceEventLog.update_status() returns False when no file
# ---------------------------------------------------------------------------


class TestGELUpdateStatus:
    """FR-GOV-HL-008: ``update_status`` returns False when file doesn't exist."""

    def test_returns_false_when_no_file(self, tmp_path: Path) -> None:
        gel = GovernanceEventLog(tmp_path)
        assert gel.update_status("run-1", "approved") is False


# ---------------------------------------------------------------------------
# FR-GOV-HL-009 -- GovernanceEventLog.update_status() updates pending to approved
# ---------------------------------------------------------------------------


class TestGELUpdateStatusApproved:
    """FR-GOV-HL-009: ``update_status`` flips pending -> approved."""

    def test_updates_pending_to_approved(self, tmp_path: Path) -> None:
        gel = GovernanceEventLog(tmp_path)
        gel.emit(
            {
                "event_type": "await_approval",
                "run_id": "run-1",
                "status": "pending",
            }
        )
        result = gel.update_status("run-1", "approved", reason="looks good")
        assert result is True
        pending = gel.list_pending_approvals()
        assert len(pending) == 0
        # Verify the event was updated
        all_events = gel.events_path.read_text(encoding="utf-8").strip().splitlines()
        ev = json.loads(all_events[0])
        assert ev["status"] == "approved"
        assert ev["resolution_reason"] == "looks good"

    def test_returns_false_when_no_pending_match(self, tmp_path: Path) -> None:
        gel = GovernanceEventLog(tmp_path)
        gel.emit(
            {
                "event_type": "await_approval",
                "run_id": "run-1",
                "status": "pending",
            }
        )
        assert gel.update_status("nonexistent", "approved") is False


# ---------------------------------------------------------------------------
# FR-GOV-HL-010 -- HITLApprovalWorkflow.approve() raises ValueError for no pending
# ---------------------------------------------------------------------------


class TestWorkflowApprove:
    """FR-GOV-HL-010: ``approve`` raises ``ValueError`` when no pending found."""

    def test_raises_when_no_pending(self, tmp_path: Path) -> None:
        wf = HITLApprovalWorkflow(tmp_path)
        with pytest.raises(ValueError, match="No pending HITL approval"):
            wf.approve("nonexistent-run")


# ---------------------------------------------------------------------------
# FR-GOV-HL-011 -- HITLApprovalWorkflow.reject() raises ValueError for no pending
# ---------------------------------------------------------------------------


class TestWorkflowReject:
    """FR-GOV-HL-011: ``reject`` raises ``ValueError`` when no pending found."""

    def test_raises_when_no_pending(self, tmp_path: Path) -> None:
        wf = HITLApprovalWorkflow(tmp_path)
        with pytest.raises(ValueError, match="No pending HITL approval"):
            wf.reject("nonexistent-run")

    def test_successful_reject(self, tmp_path: Path) -> None:
        wf = HITLApprovalWorkflow(tmp_path)
        wf.await_approval(
            run_id="run-x",
            policy="test_policy",
            reason="test reason",
        )
        result = wf.reject("run-x", reason="not now")
        assert result["success"] is True
        assert result["resolution"] == "rejected"


# ---------------------------------------------------------------------------
# FR-GOV-HL-012 -- HITLManager.request_approval() returns the request_id
# ---------------------------------------------------------------------------


class TestManagerRequestApproval:
    """FR-GOV-HL-012: ``request_approval`` returns the request_id."""

    def test_returns_request_id(self) -> None:
        mgr = HITLManager()
        rid = mgr.request_approval("req-1", "deploy", {"service": "api"})
        assert rid == "req-1"

    def test_not_approved_after_request(self) -> None:
        mgr = HITLManager()
        mgr.request_approval("req-1", "deploy", {})
        assert mgr.is_approved("req-1") is False


# ---------------------------------------------------------------------------
# FR-GOV-HL-013 -- HITLManager.is_approved() returns False before approval
# ---------------------------------------------------------------------------


class TestManagerIsApproved:
    """FR-GOV-HL-013: ``is_approved`` returns False before explicit approval."""

    def test_false_for_unknown_id(self) -> None:
        mgr = HITLManager()
        assert mgr.is_approved("unknown") is False

    def test_false_after_request(self) -> None:
        mgr = HITLManager()
        mgr.request_approval("req-2", "patch", {})
        assert mgr.is_approved("req-2") is False

    def test_true_after_approve(self) -> None:
        mgr = HITLManager()
        mgr.request_approval("req-3", "patch", {})
        mgr.approve("req-3")
        assert mgr.is_approved("req-3") is True


# ---------------------------------------------------------------------------
# FR-GOV-HL-014 -- __all__ exports HITLDecision
# ---------------------------------------------------------------------------


class TestAllExportsDecision:
    """FR-GOV-HL-014: ``__all__`` includes ``HITLDecision``."""

    def test_all_exports_hitl_decision(self) -> None:
        assert "HITLDecision" in _mod.__all__

    def test_module_exports_hitl_decision(self) -> None:
        assert _mod.HITLDecision is HITLDecision


# ---------------------------------------------------------------------------
# FR-GOV-HL-015 -- __all__ exports PolicyEngine
# ---------------------------------------------------------------------------


class TestAllExportsPolicyEngine:
    """FR-GOV-HL-015: ``__all__`` includes ``PolicyEngine``."""

    def test_all_exports_policy_engine(self) -> None:
        assert "PolicyEngine" in _mod.__all__

    def test_module_exports_policy_engine(self) -> None:
        assert _mod.PolicyEngine is PolicyEngine
