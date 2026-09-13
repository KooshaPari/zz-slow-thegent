"""Hardening invariants for ``governance.agent_deployer`` — AUDIT-N+75.

15 invariants FR-GOV-AD-001 .. FR-GOV-AD-015 covering
TaskExecutionResult, DeploymentResult, CostControllerProtocol,
VerificationGateProtocol, and AgentDeployer (init, deploy, get_ready_batch).

Source: src/thegent/governance/agent_deployer.py

@trace AUDIT-N+75  FR-GOV-AD-001..015
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pytest

from thegent.governance.agent_deployer import (
    AgentDeployer,
    CostControllerProtocol,
    DeploymentResult,
    TaskExecutionResult,
    VerificationGateProtocol,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


class _FakeCostController:
    """Minimal CostControllerProtocol implementation for tests."""

    def __init__(
        self,
        *,
        can_spawn: bool = True,
        calls_remaining: int = 100,
    ) -> None:
        self._can_spawn = can_spawn
        self._calls_remaining = calls_remaining
        self.recorded_calls: list[tuple[str, str, float | None]] = []

    def record_call(self, dimension: str, agent: str, *, cost_usd: float | None = None) -> None:
        self.recorded_calls.append((dimension, agent, cost_usd))

    def can_spawn(self, estimated_calls: int = 1) -> bool:
        return self._can_spawn

    def get_tier(self) -> Any:
        return "default"

    def calls_remaining(self) -> int:
        return self._calls_remaining

    def get_today_usage(self) -> Any:
        return 0.0


@dataclass
class _FakeTask:
    """Minimal task object matching the attributes read by AgentDeployer."""

    task_id: str
    dependencies: list[str] = field(default_factory=list)
    prompt_template: str = "fix the code"
    estimated_cost_calls: int = 1
    dimension: str = ""
    agent_role: str = "workhorse"
    todo_spec: str = ""


@dataclass
class _FakePlan:
    """Minimal plan object matching the attributes read by AgentDeployer."""

    plan_id: str = "plan-1"
    dag_edges: dict[str, list[str]] | None = None
    tasks: list[_FakeTask] = field(default_factory=list)


# ---------------------------------------------------------------------------
# FR-GOV-AD-001
# ---------------------------------------------------------------------------


class TestFRGOVAD001TaskExecutionResultFieldDefaults:
    def test_defaults(self) -> None:
        result = TaskExecutionResult(task_id="t1", run_id="r1", exit_code=0)
        assert result.error == ""
        assert result.cost_usd is None
        assert result.agent_used == ""
        assert result.completed_at == ""

    def test_explicit_fields(self) -> None:
        result = TaskExecutionResult(
            task_id="t1",
            run_id="r1",
            exit_code=0,
            error="oops",
            cost_usd=0.5,
            agent_used="agent-a",
        )
        assert result.error == "oops"
        assert result.cost_usd == 0.5
        assert result.agent_used == "agent-a"


# ---------------------------------------------------------------------------
# FR-GOV-AD-002
# ---------------------------------------------------------------------------


class TestFRGOVAD002DeploymentResultFieldDefaults:
    def test_defaults(self) -> None:
        result = DeploymentResult(plan_id="p1", cycle_id="c1")
        assert result.tasks_attempted == 0
        assert result.tasks_completed == 0
        assert result.tasks_failed == 0
        assert result.total_calls_used == 0
        assert result.total_cost_usd == 0.0
        assert result.executions == []
        assert result.completed_at == ""


# ---------------------------------------------------------------------------
# FR-GOV-AD-003
# ---------------------------------------------------------------------------


class TestFRGOVAD003CostControllerProtocolMethodSignatures:
    def test_record_call_signature(self) -> None:
        import inspect

        sig = inspect.signature(CostControllerProtocol.record_call)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "dimension" in params
        assert "agent" in params
        assert "cost_usd" in params

    def test_can_spawn_signature(self) -> None:
        import inspect

        sig = inspect.signature(CostControllerProtocol.can_spawn)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "estimated_calls" in params

    def test_get_tier_signature(self) -> None:
        import inspect

        sig = inspect.signature(CostControllerProtocol.get_tier)
        assert "self" in list(sig.parameters.keys())

    def test_calls_remaining_signature(self) -> None:
        import inspect

        sig = inspect.signature(CostControllerProtocol.calls_remaining)
        assert "self" in list(sig.parameters.keys())

    def test_get_today_usage_signature(self) -> None:
        import inspect

        sig = inspect.signature(CostControllerProtocol.get_today_usage)
        assert "self" in list(sig.parameters.keys())


# ---------------------------------------------------------------------------
# FR-GOV-AD-004
# ---------------------------------------------------------------------------


class TestFRGOVAD004VerificationGateProtocolMethodSignatures:
    def test_verify_task_signature(self) -> None:
        import inspect

        sig = inspect.signature(VerificationGateProtocol.verify_task)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "task" in params
        assert "execution" in params
        assert "pre_scan" in params

    def test_should_reroll_signature(self) -> None:
        import inspect

        sig = inspect.signature(VerificationGateProtocol.should_reroll)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "attempts" in params


# ---------------------------------------------------------------------------
# FR-GOV-AD-005
# ---------------------------------------------------------------------------


class TestFRGOVAD005AgentDeployerInitValidParams:
    def test_valid_defaults(self) -> None:
        cc = _FakeCostController()
        deployer = AgentDeployer(cost_controller=cc)
        assert deployer.max_concurrent == 3
        assert deployer.lifecycle_mode == "soft"
        assert deployer.checker_agent_name == "antigravity"

    def test_valid_custom(self) -> None:
        cc = _FakeCostController()
        deployer = AgentDeployer(
            cost_controller=cc,
            max_concurrent=5,
            lifecycle_mode="strict",
            checker_agent_name="custom-checker",
        )
        assert deployer.max_concurrent == 5
        assert deployer.lifecycle_mode == "strict"
        assert deployer.checker_agent_name == "custom-checker"


# ---------------------------------------------------------------------------
# FR-GOV-AD-006
# ---------------------------------------------------------------------------


class TestFRGOVAD006AgentDeployerInitRejectsMaxConcurrentBelowOne:
    def test_zero(self) -> None:
        cc = _FakeCostController()
        with pytest.raises(ValueError, match="max_concurrent must be >= 1"):
            AgentDeployer(cost_controller=cc, max_concurrent=0)

    def test_negative(self) -> None:
        cc = _FakeCostController()
        with pytest.raises(ValueError, match="max_concurrent must be >= 1"):
            AgentDeployer(cost_controller=cc, max_concurrent=-3)


# ---------------------------------------------------------------------------
# FR-GOV-AD-007
# ---------------------------------------------------------------------------


class TestFRGOVAD007AgentDeployerInitRejectsEmptyLifecycleMode:
    def test_empty_string(self) -> None:
        cc = _FakeCostController()
        with pytest.raises(ValueError, match="non-empty string"):
            AgentDeployer(cost_controller=cc, lifecycle_mode="")

    def test_whitespace_only(self) -> None:
        cc = _FakeCostController()
        with pytest.raises(ValueError, match="non-empty string"):
            AgentDeployer(cost_controller=cc, lifecycle_mode="   ")


# ---------------------------------------------------------------------------
# FR-GOV-AD-008
# ---------------------------------------------------------------------------


class TestFRGOVAD008DeployEmptyPlanReturnsEmptyResult:
    def test_no_tasks(self) -> None:
        cc = _FakeCostController()
        deployer = AgentDeployer(cost_controller=cc)
        plan = _FakePlan(plan_id="empty-plan", tasks=[])
        result = deployer.deploy(plan, pre_scan=None, cycle_id="cycle-1")
        assert result.plan_id == "empty-plan"
        assert result.cycle_id == "cycle-1"
        assert result.tasks_attempted == 0
        assert result.tasks_completed == 0
        assert result.tasks_failed == 0
        assert result.executions == []


# ---------------------------------------------------------------------------
# FR-GOV-AD-009
# ---------------------------------------------------------------------------


class TestFRGOVAD009GetReadyBatchAllDepsSatisfied:
    def test_all_deps_met(self) -> None:
        cc = _FakeCostController()
        deployer = AgentDeployer(cost_controller=cc)
        task_a = _FakeTask(task_id="a", dependencies=[])
        task_b = _FakeTask(task_id="b", dependencies=["a"])
        plan = _FakePlan(tasks=[task_a, task_b])
        ready = deployer.get_ready_batch(plan, completed_task_ids={"a"})
        assert len(ready) == 1
        assert ready[0].task_id == "b"


# ---------------------------------------------------------------------------
# FR-GOV-AD-010
# ---------------------------------------------------------------------------


class TestFRGOVAD010GetReadyBatchDepsNotMet:
    def test_deps_not_met(self) -> None:
        cc = _FakeCostController()
        deployer = AgentDeployer(cost_controller=cc)
        task_a = _FakeTask(task_id="a", dependencies=[])
        task_b = _FakeTask(task_id="b", dependencies=["a", "c"])
        plan = _FakePlan(tasks=[task_a, task_b])
        # Only "a" completed, but b also depends on "c"
        ready = deployer.get_ready_batch(plan, completed_task_ids={"a"})
        assert len(ready) == 0


# ---------------------------------------------------------------------------
# FR-GOV-AD-011
# ---------------------------------------------------------------------------


class TestFRGOVAD011GetReadyBatchCompletedTaskExcluded:
    def test_completed_excluded(self) -> None:
        cc = _FakeCostController()
        deployer = AgentDeployer(cost_controller=cc)
        task_a = _FakeTask(task_id="a", dependencies=[])
        task_b = _FakeTask(task_id="b", dependencies=[])
        plan = _FakePlan(tasks=[task_a, task_b])
        ready = deployer.get_ready_batch(plan, completed_task_ids={"a"})
        task_ids = [t.task_id for t in ready]
        assert "a" not in task_ids
        assert "b" in task_ids


# ---------------------------------------------------------------------------
# FR-GOV-AD-012
# ---------------------------------------------------------------------------


class TestFRGOVAD012TaskExecutionResultStartedAtIsoFormat:
    def test_started_at_is_valid_iso(self) -> None:
        result = TaskExecutionResult(task_id="t1", run_id="r1", exit_code=0)
        # Should be parseable as ISO format
        parsed = datetime.fromisoformat(result.started_at)
        assert parsed.tzinfo is not None


# ---------------------------------------------------------------------------
# FR-GOV-AD-013
# ---------------------------------------------------------------------------


class TestFRGOVAD013DeploymentResultStartedAtIsoFormat:
    def test_started_at_is_valid_iso(self) -> None:
        result = DeploymentResult(plan_id="p1", cycle_id="c1")
        parsed = datetime.fromisoformat(result.started_at)
        assert parsed.tzinfo is not None


# ---------------------------------------------------------------------------
# FR-GOV-AD-014
# ---------------------------------------------------------------------------


class TestFRGOVAD014DeployRecordsCostOnSuccess:
    def test_records_cost(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cc = _FakeCostController()
        deployer = AgentDeployer(cost_controller=cc)

        task = _FakeTask(task_id="t1")
        plan = _FakePlan(tasks=[task])

        fake_execution = TaskExecutionResult(
            task_id="t1",
            run_id="run-ok",
            exit_code=0,
            cost_usd=0.12,
            agent_used="agent-x",
        )

        monkeypatch.setattr(deployer, "_execute_task", lambda t, c: fake_execution)
        result = deployer.deploy(plan, pre_scan=None, cycle_id="c1")

        assert result.total_cost_usd == 0.12
        assert result.tasks_completed == 1
        assert len(cc.recorded_calls) == 1
        assert cc.recorded_calls[0] == ("t1", "agent-x", 0.12)


# ---------------------------------------------------------------------------
# FR-GOV-AD-015
# ---------------------------------------------------------------------------


class TestFRGOVAD015DeployIncrementsTasksFailedOnNonZeroExit:
    def test_non_zero_exit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cc = _FakeCostController()
        deployer = AgentDeployer(cost_controller=cc)

        task = _FakeTask(task_id="t1")
        plan = _FakePlan(tasks=[task])

        failed_execution = TaskExecutionResult(
            task_id="t1",
            run_id="run-fail",
            exit_code=1,
            error="something broke",
        )

        monkeypatch.setattr(deployer, "_execute_task", lambda t, c: failed_execution)
        result = deployer.deploy(plan, pre_scan=None, cycle_id="c1")

        assert result.tasks_failed == 1
        assert result.tasks_completed == 0
        assert result.total_cost_usd == 0.0
        assert len(cc.recorded_calls) == 0
