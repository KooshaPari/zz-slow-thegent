
"""Unit tests for AgentDeployer with LifecycleController integration."""

from unittest.mock import MagicMock, patch

import pytest

from thegent.governance.agent_deployer import (
    AgentDeployer,
    DeploymentResult,
    TaskExecutionResult,
)


class MockCostController:
    """Mock cost controller for testing."""

    def __init__(self):
        self.calls = []
        self.spawn_allowed = True

    def record_call(
        self,
        dimension: str,
        agent_type: str,
        *,
        cost_usd: float | None = None,
    ) -> None:
        self.calls.append((dimension, agent_type, cost_usd))

    def can_spawn(self, estimated_calls: int = 1) -> bool:
        return self.spawn_allowed

    def get_tier(self) -> str:
        return "standard"


@pytest.fixture
def mock_cost_controller():
    """Create a mock cost controller."""
    return MockCostController()


@pytest.fixture
def agent_deployer_soft(mock_cost_controller):
    """Create AgentDeployer with soft mode."""
    return AgentDeployer(
        cost_controller=mock_cost_controller,
        max_concurrent=2,
        lifecycle_mode="soft",
    )


@pytest.fixture
def agent_deployer_hard(mock_cost_controller):
    """Create AgentDeployer with hard mode."""
    return AgentDeployer(
        cost_controller=mock_cost_controller,
        max_concurrent=2,
        lifecycle_mode="hard",
    )


def test_agent_deployer_initialization_soft(agent_deployer_soft):
    """Test AgentDeployer initializes with soft mode correctly."""
    assert agent_deployer_soft.lifecycle_mode == "soft"
    assert agent_deployer_soft._settings is not None
    assert agent_deployer_soft.max_concurrent == 2


def test_agent_deployer_initialization_hard(agent_deployer_hard):
    """Test AgentDeployer initializes with hard mode correctly."""
    assert agent_deployer_hard.lifecycle_mode == "hard"
    assert agent_deployer_hard._settings is not None


def test_agent_deployer_default_mode(mock_cost_controller):
    """Test AgentDeployer defaults to soft mode."""
    deployer = AgentDeployer(cost_controller=mock_cost_controller)
    assert deployer.lifecycle_mode == "soft"


def test_task_execution_result_model():
    """Test TaskExecutionResult model fields."""
    result = TaskExecutionResult(
        task_id="task-1",
        run_id="run-123",
        exit_code=0,
    )
    assert result.task_id == "task-1"
    assert result.run_id == "run-123"
    assert result.exit_code == 0
    assert result.started_at != ""
    assert result.completed_at == ""
    assert result.error == ""


def test_deployment_result_model():
    """Test DeploymentResult model fields."""
    result = DeploymentResult(
        plan_id="plan-1",
        cycle_id="cycle-1",
    )
    assert result.plan_id == "plan-1"
    assert result.cycle_id == "cycle-1"
    assert result.tasks_attempted == 0
    assert result.tasks_completed == 0
    assert result.tasks_failed == 0
    assert result.total_calls_used == 0
    assert result.executions == []
    assert result.started_at != ""
    assert result.completed_at == ""


@patch("thegent.governance.agent_deployer.LifecycleController")
def test_execute_task_uses_lifecycle_controller(mock_lifecycle_cls, mock_cost_controller):
    """Test that _execute_task uses LifecycleController."""
    # Setup mock
    mock_controller = MagicMock()
    mock_lifecycle_cls.return_value = mock_controller

    mock_state = MagicMock()
    mock_state.stopped = False
    mock_state.stop_reason = None
    mock_state.last_cost_usd = 0.001
    mock_state.last_model = "gemini-3-flash"
    mock_controller.run_loop.return_value = mock_state

    # Create AgentDeployer (creates fresh LifecycleController per task)
    deployer = AgentDeployer(
        cost_controller=mock_cost_controller,
        max_concurrent=2,
        lifecycle_mode="soft",
    )

    # Create a mock task
    mock_task = MagicMock()
    mock_task.task_id = "test-task-1"
    mock_task.prompt_template = "Fix the bug in module X"
    mock_task.agent_role = "writer_standard"
    mock_task.dimension = "quality"
    mock_task.estimated_cost_calls = 1
    mock_task.todo_spec = ""

    # Execute
    result = deployer._execute_task(mock_task, "cycle-1")

    # Verify LifecycleController was instantiated and used
    mock_lifecycle_cls.assert_called_once()
    mock_controller.run_loop.assert_called_once()
    call_kwargs = mock_controller.run_loop.call_args[1]
    assert call_kwargs["initial_prompt"] == "Fix the bug in module X"
    assert result.task_id == "test-task-1"
    assert result.exit_code == 0


def test_get_ready_batch():
    """Test get_ready_batch returns tasks with all dependencies satisfied."""
    deployer = AgentDeployer(cost_controller=MockCostController())

    # Create mock plan
    mock_plan = MagicMock()
    mock_plan.dag_edges = {
        "task-2": ["task-1"],
        "task-3": ["task-1", "task-2"],
    }

    task1 = MagicMock()
    task1.task_id = "task-1"
    task1.dependencies = []

    task2 = MagicMock()
    task2.task_id = "task-2"
    task2.dependencies = ["task-1"]

    task3 = MagicMock()
    task3.task_id = "task-3"
    task3.dependencies = ["task-1", "task-2"]

    mock_plan.tasks = [task1, task2, task3]

    # Test with no completed tasks
    ready = deployer.get_ready_batch(mock_plan, set())
    assert len(ready) == 1
    assert ready[0].task_id == "task-1"

    # Test with task-1 completed
    ready = deployer.get_ready_batch(mock_plan, {"task-1"})
    assert len(ready) == 1
    assert ready[0].task_id == "task-2"

    # Test with task-1 and task-2 completed
    ready = deployer.get_ready_batch(mock_plan, {"task-1", "task-2"})
    assert len(ready) == 1
    assert ready[0].task_id == "task-3"

    # Test with all completed
    ready = deployer.get_ready_batch(mock_plan, {"task-1", "task-2", "task-3"})
    assert len(ready) == 0
