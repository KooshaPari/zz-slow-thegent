"""Tests for crew harness integration."""

from unittest.mock import MagicMock, patch

from thegent.agents.base import RunResult
from thegent.agents.crew.executor import ExecutionResult
from thegent.agents.crew.harness import create_agent_executor


class TestCrewHarness:
    """Test Crew harness integration."""

    @patch("thegent.agents.crew.harness.DirectAgentRunner")
    def test_agent_executor_success(self, mock_runner_class):
        """Test successful agent execution via harness."""
        # Setup mock runner
        mock_runner = MagicMock()
        mock_runner.run.return_value = RunResult(
            exit_code=0, stdout="Task completed successfully", stderr="", timed_out=False
        )
        mock_runner_class.return_value = mock_runner

        # Create executor
        executor = create_agent_executor(mode="write", timeout=100)

        # Run executor
        result = executor(agent_id="codex", prompt="Test prompt", context={"task_id": "task1"})

        # Verify results
        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert result.result == "Task completed successfully"
        assert result.task_id == "task1"

        # Verify runner was called correctly
        mock_runner_class.assert_called_with("codex")
        mock_runner.run.assert_called_with(
            prompt="Test prompt",
            cwd=None,
            mode="write",
            timeout=100,
            use_stream=True,
            live_output=False,
            agent_model=None,
        )

    @patch("thegent.agents.crew.harness.DirectAgentRunner")
    def test_agent_executor_failure(self, mock_runner_class):
        """Test failed agent execution via harness."""
        # Setup mock runner
        mock_runner = MagicMock()
        mock_runner.run.return_value = RunResult(exit_code=1, stdout="", stderr="Error occurred", timed_out=False)
        mock_runner_class.return_value = mock_runner

        # Create executor
        executor = create_agent_executor()

        # Run executor
        result = executor(agent_id="claude", prompt="Test prompt", context={"task_id": "task2"})

        # Verify results
        assert result.success is False
        assert result.error == "Error occurred"
        assert result.task_id == "task2"

    @patch("thegent.agents.crew.harness.DirectAgentRunner")
    def test_agent_executor_timeout(self, mock_runner_class):
        """Test timed out agent execution via harness."""
        # Setup mock runner
        mock_runner = MagicMock()
        mock_runner.run.return_value = RunResult(exit_code=124, stdout="", stderr="Timed out", timed_out=True)
        mock_runner_class.return_value = mock_runner

        # Create executor
        executor = create_agent_executor()

        # Run executor
        result = executor(agent_id="cursor", prompt="Test prompt", context={"task_id": "task3"})

        # Verify results
        assert result.success is False
        assert result.duration_seconds > 0
        assert result.task_id == "task3"
