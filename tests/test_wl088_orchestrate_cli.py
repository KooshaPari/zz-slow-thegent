"""Tests for WL-088: thegent orchestrate plan / run CLI commands.

# @trace WL-088
# @trace FR-ORC-088
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _make_mock_plan(
    goal: str = "test goal",
    *,
    node_count: int = 2,
) -> MagicMock:
    """Build a mock OrchestrationPlan-like object."""
    import uuid
    from datetime import UTC, datetime

    nodes = []
    prev_id = None
    for i in range(node_count):
        node = MagicMock()
        node.id = str(uuid.uuid4())
        node.task = f"Task {i + 1} for: {goal}"
        node.depends_on = [prev_id] if prev_id else []
        node.status = "pending"
        node.result = None
        node.error = None
        node.metadata = {
            "agent_hint": "coder" if i == 0 else None,
            "budget_tokens": 500 if i == 0 else None,
        }
        nodes.append(node)
        prev_id = node.id

    plan = MagicMock()
    plan.id = str(uuid.uuid4())
    plan.goal = goal
    plan.nodes = nodes
    plan.created_at = datetime.now(UTC)
    plan.done_ids = set()
    plan.failed_ids = set()
    return plan


# ---------------------------------------------------------------------------
# Unit tests for orchestrate_plan_impl
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-ORC-088")
class TestOrchestratePlanImpl:
    """Unit tests for orchestrate_plan_impl."""

    # @trace WL-088
    def test_returns_expected_keys(self) -> None:
        """orchestrate_plan_impl must return dict with required keys."""
        mock_plan = _make_mock_plan("build a login page", node_count=3)

        with patch("thegent.agents.plangent.LLMPlangentPlanner") as MockPlanner:
            instance = MockPlanner.return_value
            instance.decompose_to_orchestration_plan = AsyncMock(return_value=mock_plan)

            from thegent.cli.commands.impl import orchestrate_plan_impl

            result = orchestrate_plan_impl("build a login page")

        assert "plan_id" in result
        assert "goal" in result
        assert "node_count" in result
        assert "nodes" in result
        assert "created_at" in result

    # @trace WL-088
    def test_node_count_matches(self) -> None:
        """node_count in result must equal the number of plan nodes."""
        mock_plan = _make_mock_plan("deploy api", node_count=4)

        with patch("thegent.agents.plangent.LLMPlangentPlanner") as MockPlanner:
            instance = MockPlanner.return_value
            instance.decompose_to_orchestration_plan = AsyncMock(return_value=mock_plan)

            from thegent.cli.commands.impl import orchestrate_plan_impl

            result = orchestrate_plan_impl("deploy api")

        assert result["node_count"] == 4
        assert len(result["nodes"]) == 4

    # @trace WL-088
    def test_node_dict_has_required_keys(self) -> None:
        """Each node dict must have id, task, depends_on, agent_hint, budget_tokens, status."""
        mock_plan = _make_mock_plan("refactor service", node_count=2)

        with patch("thegent.agents.plangent.LLMPlangentPlanner") as MockPlanner:
            instance = MockPlanner.return_value
            instance.decompose_to_orchestration_plan = AsyncMock(return_value=mock_plan)

            from thegent.cli.commands.impl import orchestrate_plan_impl

            result = orchestrate_plan_impl("refactor service")

        for node in result["nodes"]:
            assert "id" in node
            assert "task" in node
            assert "depends_on" in node
            assert "agent_hint" in node
            assert "budget_tokens" in node
            assert "status" in node

    # @trace WL-088
    def test_empty_goal_raises_value_error(self) -> None:
        """Empty goal string must raise ValueError immediately."""
        from thegent.cli.commands.impl import orchestrate_plan_impl

        with pytest.raises(ValueError, match="non-empty"):
            orchestrate_plan_impl("")

    # @trace WL-088
    def test_whitespace_only_goal_raises_value_error(self) -> None:
        """Whitespace-only goal must raise ValueError."""
        from thegent.cli.commands.impl import orchestrate_plan_impl

        with pytest.raises(ValueError, match="non-empty"):
            orchestrate_plan_impl("   ")

    # @trace WL-088
    def test_goal_forwarded_to_planner(self) -> None:
        """The goal must be passed (stripped) to decompose_to_orchestration_plan."""
        mock_plan = _make_mock_plan("  my goal  ", node_count=1)

        with patch("thegent.agents.plangent.LLMPlangentPlanner") as MockPlanner:
            instance = MockPlanner.return_value
            instance.decompose_to_orchestration_plan = AsyncMock(return_value=mock_plan)

            from thegent.cli.commands.impl import orchestrate_plan_impl

            orchestrate_plan_impl("  my goal  ")

        instance.decompose_to_orchestration_plan.assert_awaited_once_with("my goal", 3)

    # @trace WL-088
    def test_custom_max_depth_forwarded(self) -> None:
        """max_depth option must be forwarded to decompose_to_orchestration_plan."""
        mock_plan = _make_mock_plan("deep goal", node_count=1)

        with patch("thegent.agents.plangent.LLMPlangentPlanner") as MockPlanner:
            instance = MockPlanner.return_value
            instance.decompose_to_orchestration_plan = AsyncMock(return_value=mock_plan)

            from thegent.cli.commands.impl import orchestrate_plan_impl

            orchestrate_plan_impl("deep goal", max_depth=7)

        instance.decompose_to_orchestration_plan.assert_awaited_once_with("deep goal", 7)

    # @trace WL-088
    def test_model_passed_to_planner_constructor(self) -> None:
        """The model parameter must be forwarded to LLMPlangentPlanner.__init__."""
        mock_plan = _make_mock_plan("goal", node_count=1)

        with patch("thegent.agents.plangent.LLMPlangentPlanner") as MockPlanner:
            instance = MockPlanner.return_value
            instance.decompose_to_orchestration_plan = AsyncMock(return_value=mock_plan)

            from thegent.cli.commands.impl import orchestrate_plan_impl

            orchestrate_plan_impl("goal", model="gemini-flash")

        MockPlanner.assert_called_once_with(model="gemini-flash", timeout_s=30.0)

    # @trace WL-088
    def test_timeout_passed_to_planner_constructor(self) -> None:
        """The timeout_s parameter must be forwarded to LLMPlangentPlanner."""
        mock_plan = _make_mock_plan("goal", node_count=1)

        with patch("thegent.agents.plangent.LLMPlangentPlanner") as MockPlanner:
            instance = MockPlanner.return_value
            instance.decompose_to_orchestration_plan = AsyncMock(return_value=mock_plan)

            from thegent.cli.commands.impl import orchestrate_plan_impl

            orchestrate_plan_impl("goal", timeout_s=60.0)

        MockPlanner.assert_called_once_with(model="claude-haiku-4.5", timeout_s=60.0)

    # @trace WL-088
    def test_plan_id_in_result(self) -> None:
        """plan_id in result must match the mock plan's id."""
        mock_plan = _make_mock_plan("check id", node_count=1)
        expected_id = mock_plan.id

        with patch("thegent.agents.plangent.LLMPlangentPlanner") as MockPlanner:
            instance = MockPlanner.return_value
            instance.decompose_to_orchestration_plan = AsyncMock(return_value=mock_plan)

            from thegent.cli.commands.impl import orchestrate_plan_impl

            result = orchestrate_plan_impl("check id")

        assert result["plan_id"] == expected_id


# ---------------------------------------------------------------------------
# Unit tests for orchestrate_run_impl
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-ORC-088")
class TestOrchestrateRunImpl:
    """Unit tests for orchestrate_run_impl."""

    # @trace WL-088
    def test_returns_expected_keys(self) -> None:
        """orchestrate_run_impl must return dict with required keys."""
        mock_plan = _make_mock_plan("run a pipeline", node_count=2)
        # Mark nodes as done post-execution simulation
        for node in mock_plan.nodes:
            node.status = "done"
            node.result = "completed"
        mock_plan.done_ids = {n.id for n in mock_plan.nodes}
        mock_plan.failed_ids = set()

        with (
            patch("thegent.agents.plangent.LLMPlangentPlanner") as MockPlanner,
            patch("thegent.agents.plangent.PlangentExecutor") as MockExecutor,
        ):
            instance = MockPlanner.return_value
            instance.decompose_to_orchestration_plan = AsyncMock(return_value=mock_plan)
            exec_instance = MockExecutor.return_value
            exec_instance.execute.return_value = mock_plan

            from thegent.cli.commands.impl import orchestrate_run_impl

            result = orchestrate_run_impl("run a pipeline")

        assert "plan_id" in result
        assert "goal" in result
        assert "success_count" in result
        assert "failure_count" in result
        assert "all_passed" in result
        assert "errors" in result
        assert "events" in result
        assert "nodes" in result

    # @trace WL-088
    def test_empty_goal_raises_value_error(self) -> None:
        """Empty goal must raise ValueError without calling planner."""
        from thegent.cli.commands.impl import orchestrate_run_impl

        with pytest.raises(ValueError, match="non-empty"):
            orchestrate_run_impl("")

    # @trace WL-088
    def test_all_passed_when_all_nodes_done(self) -> None:
        """all_passed must be True when all nodes status is 'done'."""
        mock_plan = _make_mock_plan("passing run", node_count=2)
        for node in mock_plan.nodes:
            node.status = "done"
            node.result = "ok"
        mock_plan.done_ids = {n.id for n in mock_plan.nodes}
        mock_plan.failed_ids = set()

        with (
            patch("thegent.agents.plangent.LLMPlangentPlanner") as MockPlanner,
            patch("thegent.agents.plangent.PlangentExecutor") as MockExecutor,
        ):
            instance = MockPlanner.return_value
            instance.decompose_to_orchestration_plan = AsyncMock(return_value=mock_plan)
            MockExecutor.return_value.execute.return_value = mock_plan

            from thegent.cli.commands.impl import orchestrate_run_impl

            result = orchestrate_run_impl("passing run")

        assert result["all_passed"] is True
        assert result["success_count"] == 2
        assert result["failure_count"] == 0

    # @trace WL-088
    def test_all_passed_false_when_node_failed(self) -> None:
        """all_passed must be False when at least one node fails."""
        mock_plan = _make_mock_plan("failing run", node_count=2)
        mock_plan.nodes[0].status = "done"
        mock_plan.nodes[0].result = "ok"
        mock_plan.nodes[1].status = "failed"
        mock_plan.nodes[1].error = "agent error"
        mock_plan.done_ids = {mock_plan.nodes[0].id}
        mock_plan.failed_ids = {mock_plan.nodes[1].id}

        with (
            patch("thegent.agents.plangent.LLMPlangentPlanner") as MockPlanner,
            patch("thegent.agents.plangent.PlangentExecutor") as MockExecutor,
        ):
            instance = MockPlanner.return_value
            instance.decompose_to_orchestration_plan = AsyncMock(return_value=mock_plan)
            MockExecutor.return_value.execute.return_value = mock_plan

            from thegent.cli.commands.impl import orchestrate_run_impl

            result = orchestrate_run_impl("failing run")

        assert result["all_passed"] is False
        assert result["failure_count"] == 1
        assert "agent error" in result["errors"]

    # @trace WL-088
    def test_nodes_list_includes_all_nodes(self) -> None:
        """nodes list must include every node from the executed plan."""
        mock_plan = _make_mock_plan("multi node", node_count=3)
        for node in mock_plan.nodes:
            node.status = "done"
            node.result = "ok"
        mock_plan.done_ids = {n.id for n in mock_plan.nodes}
        mock_plan.failed_ids = set()

        with (
            patch("thegent.agents.plangent.LLMPlangentPlanner") as MockPlanner,
            patch("thegent.agents.plangent.PlangentExecutor") as MockExecutor,
        ):
            instance = MockPlanner.return_value
            instance.decompose_to_orchestration_plan = AsyncMock(return_value=mock_plan)
            MockExecutor.return_value.execute.return_value = mock_plan

            from thegent.cli.commands.impl import orchestrate_run_impl

            result = orchestrate_run_impl("multi node")

        assert len(result["nodes"]) == 3

    # @trace WL-088
    def test_fail_fast_forwarded_to_executor(self) -> None:
        """fail_fast option must be forwarded to PlangentExecutor constructor."""
        mock_plan = _make_mock_plan("ff test", node_count=1)
        for node in mock_plan.nodes:
            node.status = "done"
            node.result = "ok"
        mock_plan.done_ids = {n.id for n in mock_plan.nodes}
        mock_plan.failed_ids = set()

        with (
            patch("thegent.agents.plangent.LLMPlangentPlanner") as MockPlanner,
            patch("thegent.agents.plangent.PlangentExecutor") as MockExecutor,
        ):
            instance = MockPlanner.return_value
            instance.decompose_to_orchestration_plan = AsyncMock(return_value=mock_plan)
            MockExecutor.return_value.execute.return_value = mock_plan

            from thegent.cli.commands.impl import orchestrate_run_impl

            orchestrate_run_impl("ff test", fail_fast=True)

        MockExecutor.assert_called_once_with(fail_fast=True)


# ---------------------------------------------------------------------------
# CLI integration tests via typer.testing.CliRunner
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-ORC-088")
class TestOrchestrateCLIPlan:
    """CLI integration tests for `thegent orchestrate plan`."""

    # @trace WL-088
    def test_plan_command_exits_zero_on_success(self, runner: CliRunner) -> None:
        """orchestrate plan must exit 0 on success."""
        from thegent.cli.apps.orchestrate import app

        mock_result: dict[str, Any] = {
            "plan_id": "plan-abc",
            "goal": "build login",
            "node_count": 2,
            "created_at": "2026-01-01T00:00:00+00:00",
            "nodes": [
                {
                    "id": "node-1",
                    "task": "Analyse scope",
                    "depends_on": [],
                    "agent_hint": None,
                    "budget_tokens": None,
                    "status": "pending",
                },
                {
                    "id": "node-2",
                    "task": "Implement login",
                    "depends_on": ["node-1"],
                    "agent_hint": "coder",
                    "budget_tokens": 500,
                    "status": "pending",
                },
            ],
        }

        with patch(
            "thegent.cli.apps.orchestrate.orchestrate_plan_impl",
            return_value=mock_result,
        ):
            result = runner.invoke(app, ["plan", "build login"])

        assert result.exit_code == 0

    # @trace WL-088
    def test_plan_command_prints_goal(self, runner: CliRunner) -> None:
        """orchestrate plan output must contain the goal."""
        from thegent.cli.apps.orchestrate import app

        mock_result: dict[str, Any] = {
            "plan_id": "plan-xyz",
            "goal": "write unit tests",
            "node_count": 1,
            "created_at": "2026-01-01T00:00:00+00:00",
            "nodes": [
                {
                    "id": "n1",
                    "task": "Write tests",
                    "depends_on": [],
                    "agent_hint": None,
                    "budget_tokens": None,
                    "status": "pending",
                }
            ],
        }

        with patch(
            "thegent.cli.apps.orchestrate.orchestrate_plan_impl",
            return_value=mock_result,
        ):
            result = runner.invoke(app, ["plan", "write unit tests"])

        assert "write unit tests" in result.output

    # @trace WL-088
    def test_plan_json_output(self, runner: CliRunner) -> None:
        """orchestrate plan --json must output valid JSON."""
        import json as _json

        from thegent.cli.apps.orchestrate import app

        mock_result: dict[str, Any] = {
            "plan_id": "plan-json",
            "goal": "json test",
            "node_count": 1,
            "created_at": "2026-01-01T00:00:00+00:00",
            "nodes": [],
        }

        with patch(
            "thegent.cli.apps.orchestrate.orchestrate_plan_impl",
            return_value=mock_result,
        ):
            result = runner.invoke(app, ["plan", "json test", "--json"])

        assert result.exit_code == 0
        parsed = _json.loads(result.output)
        assert parsed["plan_id"] == "plan-json"

    # @trace WL-088
    def test_plan_custom_max_depth_forwarded(self, runner: CliRunner) -> None:
        """--max-depth option must be forwarded to orchestrate_plan_impl."""
        from thegent.cli.apps.orchestrate import app

        mock_result: dict[str, Any] = {
            "plan_id": "p",
            "goal": "g",
            "node_count": 0,
            "created_at": "2026-01-01T00:00:00+00:00",
            "nodes": [],
        }

        with patch(
            "thegent.cli.apps.orchestrate.orchestrate_plan_impl",
            return_value=mock_result,
        ) as mock_impl:
            runner.invoke(app, ["plan", "g", "--max-depth", "5"])

        mock_impl.assert_called_once_with("g", max_depth=5, model="claude-haiku-4.5", timeout_s=30.0)

    # @trace WL-088
    def test_plan_custom_model_forwarded(self, runner: CliRunner) -> None:
        """--model option must be forwarded to orchestrate_plan_impl."""
        from thegent.cli.apps.orchestrate import app

        mock_result: dict[str, Any] = {
            "plan_id": "p",
            "goal": "g",
            "node_count": 0,
            "created_at": "2026-01-01T00:00:00+00:00",
            "nodes": [],
        }

        with patch(
            "thegent.cli.apps.orchestrate.orchestrate_plan_impl",
            return_value=mock_result,
        ) as mock_impl:
            runner.invoke(app, ["plan", "g", "--model", "gemini-flash"])

        mock_impl.assert_called_once_with("g", max_depth=3, model="gemini-flash", timeout_s=30.0)


@pytest.mark.requirement("FR-ORC-088")
class TestOrchestrateCLIRun:
    """CLI integration tests for `thegent orchestrate run`."""

    # @trace WL-088
    def test_run_command_exits_zero_on_all_passed(self, runner: CliRunner) -> None:
        """orchestrate run must exit 0 when all_passed is True."""
        from thegent.cli.apps.orchestrate import app

        mock_result: dict[str, Any] = {
            "plan_id": "plan-run",
            "goal": "execute pipeline",
            "success_count": 2,
            "failure_count": 0,
            "all_passed": True,
            "errors": [],
            "events": [],
            "nodes": [
                {
                    "id": "n1",
                    "task": "Task 1",
                    "status": "done",
                    "result": "ok",
                    "error": None,
                },
                {
                    "id": "n2",
                    "task": "Task 2",
                    "status": "done",
                    "result": "ok",
                    "error": None,
                },
            ],
        }

        with patch(
            "thegent.cli.apps.orchestrate.orchestrate_run_impl",
            return_value=mock_result,
        ):
            result = runner.invoke(app, ["run", "execute pipeline"])

        assert result.exit_code == 0

    # @trace WL-088
    def test_run_command_exits_one_on_failure(self, runner: CliRunner) -> None:
        """orchestrate run must exit 1 when all_passed is False."""
        from thegent.cli.apps.orchestrate import app

        mock_result: dict[str, Any] = {
            "plan_id": "plan-fail",
            "goal": "failing pipeline",
            "success_count": 1,
            "failure_count": 1,
            "all_passed": False,
            "errors": ["node failed"],
            "events": [],
            "nodes": [
                {
                    "id": "n1",
                    "task": "Task 1",
                    "status": "done",
                    "result": "ok",
                    "error": None,
                },
                {
                    "id": "n2",
                    "task": "Task 2",
                    "status": "failed",
                    "result": None,
                    "error": "node failed",
                },
            ],
        }

        with patch(
            "thegent.cli.apps.orchestrate.orchestrate_run_impl",
            return_value=mock_result,
        ):
            result = runner.invoke(app, ["run", "failing pipeline"])

        assert result.exit_code == 1

    # @trace WL-088
    def test_run_json_output_exits_zero_on_all_passed(self, runner: CliRunner) -> None:
        """orchestrate run --json must exit 0 and output valid JSON when all_passed."""
        import json as _json

        from thegent.cli.apps.orchestrate import app

        mock_result: dict[str, Any] = {
            "plan_id": "plan-json-run",
            "goal": "json run",
            "success_count": 1,
            "failure_count": 0,
            "all_passed": True,
            "errors": [],
            "events": [],
            "nodes": [
                {
                    "id": "n1",
                    "task": "T",
                    "status": "done",
                    "result": "ok",
                    "error": None,
                }
            ],
        }

        with patch(
            "thegent.cli.apps.orchestrate.orchestrate_run_impl",
            return_value=mock_result,
        ):
            result = runner.invoke(app, ["run", "json run", "--json"])

        assert result.exit_code == 0
        parsed = _json.loads(result.output)
        assert parsed["plan_id"] == "plan-json-run"

    # @trace WL-088
    def test_run_json_output_exits_one_on_failure(self, runner: CliRunner) -> None:
        """orchestrate run --json must exit 1 when all_passed is False."""
        from thegent.cli.apps.orchestrate import app

        mock_result: dict[str, Any] = {
            "plan_id": "p",
            "goal": "g",
            "success_count": 0,
            "failure_count": 1,
            "all_passed": False,
            "errors": ["boom"],
            "events": [],
            "nodes": [],
        }

        with patch(
            "thegent.cli.apps.orchestrate.orchestrate_run_impl",
            return_value=mock_result,
        ):
            result = runner.invoke(app, ["run", "g", "--json"])

        assert result.exit_code == 1

    # @trace WL-088
    def test_run_displays_events(self, runner: CliRunner) -> None:
        """orchestrate run must print event lines when events are present."""
        from thegent.cli.apps.orchestrate import app

        mock_result: dict[str, Any] = {
            "plan_id": "p",
            "goal": "event test",
            "success_count": 1,
            "failure_count": 0,
            "all_passed": True,
            "errors": [],
            "events": [
                {
                    "event_id": "e1",
                    "request_id": "r1",
                    "event_type": "started",
                    "message": "Agent started",
                    "timestamp": "2026-01-01T00:00:00",
                }
            ],
            "nodes": [
                {
                    "id": "n1",
                    "task": "T",
                    "status": "done",
                    "result": "ok",
                    "error": None,
                }
            ],
        }

        with patch(
            "thegent.cli.apps.orchestrate.orchestrate_run_impl",
            return_value=mock_result,
        ):
            result = runner.invoke(app, ["run", "event test"])

        assert "started" in result.output

    # @trace WL-088
    def test_run_fail_fast_forwarded(self, runner: CliRunner) -> None:
        """--fail-fast must be forwarded to orchestrate_run_impl."""
        from thegent.cli.apps.orchestrate import app

        mock_result: dict[str, Any] = {
            "plan_id": "p",
            "goal": "g",
            "success_count": 1,
            "failure_count": 0,
            "all_passed": True,
            "errors": [],
            "events": [],
            "nodes": [],
        }

        with patch(
            "thegent.cli.apps.orchestrate.orchestrate_run_impl",
            return_value=mock_result,
        ) as mock_impl:
            runner.invoke(app, ["run", "g", "--fail-fast"])

        call_kwargs = mock_impl.call_args
        assert call_kwargs.kwargs.get("fail_fast") is True

    # @trace WL-088
    def test_run_model_forwarded(self, runner: CliRunner) -> None:
        """--model option must be forwarded to orchestrate_run_impl."""
        from thegent.cli.apps.orchestrate import app

        mock_result: dict[str, Any] = {
            "plan_id": "p",
            "goal": "g",
            "success_count": 1,
            "failure_count": 0,
            "all_passed": True,
            "errors": [],
            "events": [],
            "nodes": [],
        }

        with patch(
            "thegent.cli.apps.orchestrate.orchestrate_run_impl",
            return_value=mock_result,
        ) as mock_impl:
            runner.invoke(app, ["run", "g", "--model", "gemini-ultra"])

        call_kwargs = mock_impl.call_args
        assert call_kwargs.kwargs.get("model") == "gemini-ultra"

    # @trace WL-088
    def test_run_prints_passed_summary(self, runner: CliRunner) -> None:
        """orchestrate run output must contain PASSED when all nodes succeed."""
        from thegent.cli.apps.orchestrate import app

        mock_result: dict[str, Any] = {
            "plan_id": "p",
            "goal": "my pipeline",
            "success_count": 3,
            "failure_count": 0,
            "all_passed": True,
            "errors": [],
            "events": [],
            "nodes": [],
        }

        with patch(
            "thegent.cli.apps.orchestrate.orchestrate_run_impl",
            return_value=mock_result,
        ):
            result = runner.invoke(app, ["run", "my pipeline"])

        assert "PASSED" in result.output

    # @trace WL-088
    def test_run_prints_failed_summary(self, runner: CliRunner) -> None:
        """orchestrate run output must contain FAILED when nodes fail."""
        from thegent.cli.apps.orchestrate import app

        mock_result: dict[str, Any] = {
            "plan_id": "p",
            "goal": "my pipeline",
            "success_count": 0,
            "failure_count": 1,
            "all_passed": False,
            "errors": ["something broke"],
            "events": [],
            "nodes": [],
        }

        with patch(
            "thegent.cli.apps.orchestrate.orchestrate_run_impl",
            return_value=mock_result,
        ):
            result = runner.invoke(app, ["run", "my pipeline"])

        assert "FAILED" in result.output


# ---------------------------------------------------------------------------
# App registration test
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-ORC-088")
class TestOrchestrateAppRegistration:
    """Verify the orchestrate app is registered in the main CLI."""

    # @trace WL-088
    def test_orchestrate_app_importable(self) -> None:
        """orchestrate app module must be importable."""
        from thegent.cli.apps import orchestrate  # noqa: F401

    # @trace WL-088
    def test_orchestrate_app_has_plan_command(self) -> None:
        """orchestrate typer app must expose a 'plan' command."""
        from thegent.cli.apps.orchestrate import app

        command_names = [cmd.name for cmd in app.registered_commands]
        assert "plan" in command_names

    # @trace WL-088
    def test_orchestrate_app_has_run_command(self) -> None:
        """orchestrate typer app must expose a 'run' command."""
        from thegent.cli.apps.orchestrate import app

        command_names = [cmd.name for cmd in app.registered_commands]
        assert "run" in command_names

    # @trace WL-088
    def test_main_app_includes_orchestrate(self) -> None:
        """The main CLI app must include 'orchestrate' as a registered group."""
        from thegent.cli.apps.main import app

        group_names = [g.name for g in app.registered_groups]
        assert "orchestrate" in group_names
