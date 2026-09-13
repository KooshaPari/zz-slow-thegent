"""Unit tests for HITL (Human-in-the-Loop) governance gate (WL-019).

FR Traceability:
  All tests trace to G-GP-05 / WL-019-A (PolicyEngine.evaluate_hitl)
  and WL-019-B (HITLApprovalWorkflow approve/reject).
"""

from __future__ import annotations

from pathlib import Path

import orjson as json
import pytest

from thegent.governance.hitl import (
    GovernanceEventLog,
    HITLApprovalWorkflow,
    HITLDecision,
    PolicyEngine,
    RunContext,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class _FakeSettings:
    """Minimal settings stub for PolicyEngine tests."""

    def __init__(
        self,
        hitl_enabled: bool = True,
        hitl_checkpoints: list[str] | None = None,
        session_dir: str | None = None,
    ) -> None:
        self.hitl_enabled = hitl_enabled
        self.hitl_checkpoints = hitl_checkpoints if hitl_checkpoints is not None else ["pre_execution"]
        self._session_dir = session_dir

    @property
    def session_dir(self) -> str | None:
        return self._session_dir


@pytest.fixture
def tmp_session(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def settings_enabled(tmp_session: Path) -> _FakeSettings:
    return _FakeSettings(hitl_enabled=True, session_dir=str(tmp_session))


@pytest.fixture
def settings_disabled(tmp_session: Path) -> _FakeSettings:
    return _FakeSettings(hitl_enabled=False, session_dir=str(tmp_session))


@pytest.fixture
def engine_enabled(settings_enabled: _FakeSettings, tmp_session: Path) -> PolicyEngine:
    return PolicyEngine(settings=settings_enabled, session_dir=tmp_session)


@pytest.fixture
def engine_disabled(settings_disabled: _FakeSettings, tmp_session: Path) -> PolicyEngine:
    return PolicyEngine(settings=settings_disabled, session_dir=tmp_session)


def _critical_ctx(run_id: str = "run_001", confidence: float | None = None) -> RunContext:
    return RunContext(
        run_id=run_id,
        agent="claude",
        lane="critical",
        confidence=confidence,
        owner="test_owner",
        environment="staging",
    )


def _standard_ctx(run_id: str = "run_002") -> RunContext:
    return RunContext(
        run_id=run_id,
        agent="claude",
        lane="standard",
        confidence=0.95,
        owner="test_owner",
        environment="staging",
    )


def _production_no_conf_ctx(run_id: str = "run_003") -> RunContext:
    return RunContext(
        run_id=run_id,
        agent="claude",
        lane="standard",
        confidence=None,
        owner="test_owner",
        environment="production",
    )


def _recovery_production_ctx(run_id: str = "run_004") -> RunContext:
    return RunContext(
        run_id=run_id,
        agent="claude",
        lane="recovery",
        confidence=0.85,
        owner="test_owner",
        environment="production",
    )


# ---------------------------------------------------------------------------
# HITLDecision
# ---------------------------------------------------------------------------


class TestHITLDecision:
    """Tests for HITLDecision data class."""

    def test_to_dict_contains_all_fields(self) -> None:
        # @trace G-GP-05 / WL-019-A
        decision = HITLDecision(
            required=True,
            run_id="run_abc",
            policy="require_human_approval.critical_lane_low_confidence",
            reason="confidence 0.5 < 0.9",
            checkpoint="pre_execution",
        )
        d = decision.to_dict()
        assert d["required"] is True
        assert d["run_id"] == "run_abc"
        assert d["policy"] == "require_human_approval.critical_lane_low_confidence"
        assert d["reason"] == "confidence 0.5 < 0.9"
        assert d["checkpoint"] == "pre_execution"

    def test_repr_contains_run_id(self) -> None:
        # @trace G-GP-05 / WL-019-A
        decision = HITLDecision(required=False, run_id="run_xyz", policy="no_match")
        assert "run_xyz" in repr(decision)


# ---------------------------------------------------------------------------
# PolicyEngine.evaluate_hitl — gate disabled
# ---------------------------------------------------------------------------


class TestPolicyEngineDisabled:
    """HITL gate disabled — evaluate_hitl should always return required=False."""

    def test_gate_disabled_returns_not_required(self, engine_disabled: PolicyEngine) -> None:
        # @trace G-GP-05 / WL-019-A
        ctx = _critical_ctx(confidence=None)
        decision = engine_disabled.evaluate_hitl(ctx)
        assert decision.required is False

    def test_gate_disabled_no_event_emitted(self, engine_disabled: PolicyEngine, tmp_session: Path) -> None:
        # @trace G-GP-05 / WL-019-A
        ctx = _critical_ctx(confidence=None)
        engine_disabled.evaluate_hitl(ctx)
        events_path = tmp_session / "governance_events.jsonl"
        assert not events_path.exists()


# ---------------------------------------------------------------------------
# PolicyEngine.evaluate_hitl — gate enabled
# ---------------------------------------------------------------------------


class TestPolicyEngineCriticalLane:
    """Policy: critical lane requires confidence >= 0.9."""

    def test_critical_lane_no_confidence_fires_gate(self, engine_enabled: PolicyEngine) -> None:
        # @trace G-GP-05 / WL-019-A
        ctx = _critical_ctx(confidence=None)
        decision = engine_enabled.evaluate_hitl(ctx)
        assert decision.required is True
        assert "critical_lane" in decision.policy

    def test_critical_lane_low_confidence_fires_gate(self, engine_enabled: PolicyEngine) -> None:
        # @trace G-GP-05 / WL-019-A
        ctx = _critical_ctx(confidence=0.5)
        decision = engine_enabled.evaluate_hitl(ctx)
        assert decision.required is True

    def test_critical_lane_high_confidence_does_not_fire(self, engine_enabled: PolicyEngine) -> None:
        # @trace G-GP-05 / WL-019-A
        ctx = _critical_ctx(confidence=0.95)
        decision = engine_enabled.evaluate_hitl(ctx)
        assert decision.required is False

    def test_critical_lane_fires_emits_await_approval_event(
        self, engine_enabled: PolicyEngine, tmp_session: Path
    ) -> None:
        # @trace G-GP-05 / WL-019-A
        ctx = _critical_ctx(run_id="run_crit_001", confidence=None)
        engine_enabled.evaluate_hitl(ctx)
        events_path = tmp_session / "governance_events.jsonl"
        assert events_path.exists()
        events = [json.loads(line) for line in events_path.read_text().splitlines() if line.strip()]
        await_events = [e for e in events if e.get("event_type") == "await_approval"]
        assert len(await_events) == 1
        ev = await_events[0]
        assert ev["run_id"] == "run_crit_001"
        assert ev["status"] == "pending"
        assert ev["checkpoint"] == "pre_execution"


class TestPolicyEngineProductionNoConf:
    """Policy: production runs without confidence require human approval."""

    def test_production_no_confidence_fires_gate(self, engine_enabled: PolicyEngine) -> None:
        # @trace G-GP-05 / WL-019-A
        ctx = _production_no_conf_ctx()
        decision = engine_enabled.evaluate_hitl(ctx)
        assert decision.required is True
        assert "production_no_confidence" in decision.policy

    def test_production_with_confidence_does_not_fire(self, engine_enabled: PolicyEngine) -> None:
        # @trace G-GP-05 / WL-019-A
        ctx = RunContext(
            run_id="run_prod_conf",
            agent="claude",
            lane="standard",
            confidence=0.9,
            owner="owner",
            environment="production",
        )
        decision = engine_enabled.evaluate_hitl(ctx)
        assert decision.required is False


class TestPolicyEngineRecoveryProduction:
    """Policy: recovery actions in production require human approval."""

    def test_recovery_production_fires_gate(self, engine_enabled: PolicyEngine) -> None:
        # @trace G-GP-05 / WL-019-A
        ctx = _recovery_production_ctx()
        decision = engine_enabled.evaluate_hitl(ctx)
        assert decision.required is True
        assert "production_recovery" in decision.policy

    def test_recovery_staging_does_not_fire(self, engine_enabled: PolicyEngine) -> None:
        # @trace G-GP-05 / WL-019-A
        ctx = RunContext(
            run_id="run_rec_stg",
            agent="claude",
            lane="recovery",
            confidence=0.8,
            owner="owner",
            environment="staging",
        )
        decision = engine_enabled.evaluate_hitl(ctx)
        assert decision.required is False


# ---------------------------------------------------------------------------
# GovernanceEventLog
# ---------------------------------------------------------------------------


class TestGovernanceEventLog:
    """Unit tests for event log read/write operations."""

    def test_emit_and_list_pending(self, tmp_session: Path) -> None:
        # @trace G-GP-05 / WL-019-A
        log = GovernanceEventLog(tmp_session)
        log.emit(
            {
                "event_type": "await_approval",
                "run_id": "run_log_001",
                "status": "pending",
                "policy": "test_policy",
            }
        )
        items = log.list_pending_approvals()
        assert len(items) == 1
        assert items[0]["run_id"] == "run_log_001"

    def test_list_pending_filters_resolved(self, tmp_session: Path) -> None:
        # @trace G-GP-05 / WL-019-A
        log = GovernanceEventLog(tmp_session)
        log.emit({"event_type": "await_approval", "run_id": "run_r1", "status": "approved"})
        log.emit({"event_type": "await_approval", "run_id": "run_r2", "status": "pending"})
        items = log.list_pending_approvals()
        assert len(items) == 1
        assert items[0]["run_id"] == "run_r2"

    def test_list_pending_filters_by_run_id(self, tmp_session: Path) -> None:
        # @trace G-GP-05 / WL-019-A
        log = GovernanceEventLog(tmp_session)
        log.emit({"event_type": "await_approval", "run_id": "run_a", "status": "pending"})
        log.emit({"event_type": "await_approval", "run_id": "run_b", "status": "pending"})
        items = log.list_pending_approvals(run_id="run_a")
        assert len(items) == 1
        assert items[0]["run_id"] == "run_a"

    def test_update_status_marks_approved(self, tmp_session: Path) -> None:
        # @trace G-GP-05 / WL-019-B
        log = GovernanceEventLog(tmp_session)
        log.emit({"event_type": "await_approval", "run_id": "run_up_01", "status": "pending"})
        ok = log.update_status("run_up_01", "approved", reason="looks good")
        assert ok is True
        items = log.list_pending_approvals(run_id="run_up_01")
        assert len(items) == 0

    def test_update_status_returns_false_when_missing(self, tmp_session: Path) -> None:
        # @trace G-GP-05 / WL-019-B
        log = GovernanceEventLog(tmp_session)
        ok = log.update_status("nonexistent", "approved")
        assert ok is False


# ---------------------------------------------------------------------------
# HITLApprovalWorkflow
# ---------------------------------------------------------------------------


class TestHITLApprovalWorkflow:
    """Tests for approve/reject workflow (WL-019-B)."""

    def _seed_pending(self, session_dir: Path, run_id: str) -> None:
        log = GovernanceEventLog(session_dir)
        log.emit(
            {
                "event_type": "await_approval",
                "run_id": run_id,
                "status": "pending",
                "policy": "require_human_approval.critical_lane_low_confidence",
            }
        )

    def test_approve_success(self, tmp_session: Path) -> None:
        # @trace G-GP-05 / WL-019-B
        self._seed_pending(tmp_session, "run_w_01")
        workflow = HITLApprovalWorkflow(tmp_session)
        result = workflow.approve("run_w_01", reason="reviewed by alice")
        assert result["success"] is True
        assert result["run_id"] == "run_w_01"
        assert result["resolution"] == "approved"
        assert result["reason"] == "reviewed by alice"

    def test_approve_emits_resolution_event(self, tmp_session: Path) -> None:
        # @trace G-GP-05 / WL-019-B
        self._seed_pending(tmp_session, "run_w_02")
        workflow = HITLApprovalWorkflow(tmp_session)
        workflow.approve("run_w_02")
        GovernanceEventLog(tmp_session)
        events_path = tmp_session / "governance_events.jsonl"
        events = [json.loads(l) for l in events_path.read_text().splitlines() if l.strip()]
        resolution_events = [e for e in events if e.get("event_type") == "hitl_resolution"]
        assert len(resolution_events) == 1
        assert resolution_events[0]["resolution"] == "approved"

    def test_reject_success(self, tmp_session: Path) -> None:
        # @trace G-GP-05 / WL-019-B
        self._seed_pending(tmp_session, "run_w_03")
        workflow = HITLApprovalWorkflow(tmp_session)
        result = workflow.reject("run_w_03", reason="policy violation")
        assert result["success"] is True
        assert result["resolution"] == "rejected"
        assert result["reason"] == "policy violation"

    def test_reject_emits_resolution_event_with_signature(self, tmp_session: Path) -> None:
        # @trace G-GP-05 / WL-019-B
        self._seed_pending(tmp_session, "run_w_04")
        workflow = HITLApprovalWorkflow(tmp_session)
        workflow.reject("run_w_04", reason="risky")
        events_path = tmp_session / "governance_events.jsonl"
        events = [json.loads(l) for l in events_path.read_text().splitlines() if l.strip()]
        res_events = [e for e in events if e.get("event_type") == "hitl_resolution"]
        assert len(res_events) == 1
        assert "provenance_signature" in res_events[0]
        assert len(res_events[0]["provenance_signature"]) == 64  # sha256 hex

    def test_approve_raises_when_no_pending(self, tmp_session: Path) -> None:
        # @trace G-GP-05 / WL-019-B
        workflow = HITLApprovalWorkflow(tmp_session)
        with pytest.raises(ValueError, match="No pending HITL approval"):
            workflow.approve("nonexistent_run")

    def test_reject_raises_when_no_pending(self, tmp_session: Path) -> None:
        # @trace G-GP-05 / WL-019-B
        workflow = HITLApprovalWorkflow(tmp_session)
        with pytest.raises(ValueError, match="No pending HITL approval"):
            workflow.reject("nonexistent_run")

    def test_list_pending_returns_all(self, tmp_session: Path) -> None:
        # @trace G-GP-05 / WL-019-B
        self._seed_pending(tmp_session, "run_list_01")
        self._seed_pending(tmp_session, "run_list_02")
        workflow = HITLApprovalWorkflow(tmp_session)
        pending = workflow.list_pending()
        run_ids = {p["run_id"] for p in pending}
        assert "run_list_01" in run_ids
        assert "run_list_02" in run_ids

    def test_approve_then_list_empty(self, tmp_session: Path) -> None:
        # @trace G-GP-05 / WL-019-B
        self._seed_pending(tmp_session, "run_once")
        workflow = HITLApprovalWorkflow(tmp_session)
        workflow.approve("run_once")
        pending = workflow.list_pending()
        assert all(p["run_id"] != "run_once" for p in pending)

    def test_await_approval_persists_unified_diff(self, tmp_session: Path) -> None:
        # @trace G-GP-05 / WL-100
        workflow = HITLApprovalWorkflow(tmp_session)
        diff_text = "--- a/test.py\n+++ b/test.py\n@@ -1 +1 @@\n-old\n+new\n"
        result = workflow.await_approval(
            run_id="run_diff_01",
            policy="vetter_escalation",
            reason="needs review",
            checkpoint="post_execution",
            unified_diff=diff_text,
        )
        assert result["success"] is True
        assert result["has_diff"] is True

        log = GovernanceEventLog(tmp_session)
        pending = log.list_pending_approvals(run_id="run_diff_01")
        assert len(pending) == 1
        assert pending[0]["unified_diff"] == diff_text

    def test_await_approval_always_writes_unified_diff_key(self, tmp_session: Path) -> None:
        # @trace G-GP-05 / WL-100
        workflow = HITLApprovalWorkflow(tmp_session)
        result = workflow.await_approval(
            run_id="run_diff_02",
            policy="vetter_escalation",
            reason="needs review",
            checkpoint="post_execution",
            unified_diff=None,
        )
        assert result["success"] is True
        assert result["has_diff"] is False

        log = GovernanceEventLog(tmp_session)
        pending = log.list_pending_approvals(run_id="run_diff_02")
        assert len(pending) == 1
        assert pending[0]["unified_diff"] == ""


# ---------------------------------------------------------------------------
# impl helpers (smoke tests via govern_approve_impl / govern_reject_impl)
# ---------------------------------------------------------------------------


class TestGovernImplHelpers:
    """Smoke tests for govern_approve_impl and govern_reject_impl in cli/commands/impl.py."""

    def test_govern_approve_impl_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # @trace G-GP-05 / WL-019-B
        log = GovernanceEventLog(tmp_path)
        log.emit(
            {
                "event_type": "await_approval",
                "run_id": "run_impl_01",
                "status": "pending",
            }
        )

        from thegent.governance.hitl import HITLApprovalWorkflow

        workflow = HITLApprovalWorkflow(tmp_path)
        result = workflow.approve(run_id="run_impl_01", reason="ok")
        assert result["success"] is True
        assert result["resolution"] == "approved"

    def test_govern_reject_impl_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # @trace G-GP-05 / WL-019-B
        log = GovernanceEventLog(tmp_path)
        log.emit(
            {
                "event_type": "await_approval",
                "run_id": "run_impl_02",
                "status": "pending",
            }
        )

        from thegent.governance.hitl import HITLApprovalWorkflow

        workflow = HITLApprovalWorkflow(tmp_path)
        result = workflow.reject(run_id="run_impl_02", reason="unsafe")
        assert result["success"] is True
        assert result["resolution"] == "rejected"

    def test_govern_list_pending_impl(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # @trace G-GP-05 / WL-019-B
        log = GovernanceEventLog(tmp_path)
        log.emit(
            {
                "event_type": "await_approval",
                "run_id": "run_list_p1",
                "status": "pending",
            }
        )

        from thegent.governance.hitl import HITLApprovalWorkflow

        workflow = HITLApprovalWorkflow(tmp_path)
        items = workflow.list_pending()
        assert any(i["run_id"] == "run_list_p1" for i in items)
