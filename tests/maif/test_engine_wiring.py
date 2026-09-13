"""Tests for ExecutionEngine and MAIFAgentRunner wiring."""

from unittest.mock import MagicMock, patch

import pytest

from thegent.agents.base import AgentRunner, RunResult
from thegent.agents.maif_runner import MAIFAgentRunner
from thegent.execution import RunMeta
from thegent.orchestration.execution.engine import ExecutionEngine


class MockRunner(AgentRunner):
    def run(self, prompt, cwd, mode, timeout, **kwargs):
        return RunResult(exit_code=0, stdout="Mock output", stderr="")


@pytest.fixture
def temp_session_dir(tmp_path):
    session_dir = tmp_path / ".thegent" / "sessions"
    session_dir.mkdir(parents=True)
    return session_dir


@pytest.fixture
def mock_settings(temp_session_dir):
    settings = MagicMock()
    settings.session_dir = temp_session_dir
    return settings


def test_execution_engine_generates_artifacts(mock_settings, temp_session_dir):
    engine = ExecutionEngine(settings=mock_settings)
    runner = MockRunner()
    run_meta = RunMeta(
        run_id="run_test_123",
        prompt="Test prompt",
        owner="test_user",
        agent="test_agent",
        cwd=str(temp_session_dir),
        started_at_utc="2026-02-20T00:00:00Z",
    )

    with (
        patch("thegent.execution.Auditor.sign_run") as mock_sign,
        patch("thegent.execution.Auditor.generate_maif_artifact", create=True) as mock_gen,
        patch("thegent.execution.Auditor.persist_maif_artifact", create=True) as mock_persist,
    ):
        mock_gen.return_value = {"id": "art_123", "session_id": "run_test_123"}

        result = engine.execute(runner, run_meta)

        assert result.stdout == "Mock output"
        mock_sign.assert_called_once_with(run_meta)
        mock_gen.assert_called_once()
        mock_persist.assert_called_once()


def test_maif_agent_runner_wiring(mock_settings):
    inner_runner = MockRunner()
    # We need to patch ExecutionEngine inside MAIFAgentRunner or pass a mocked one
    mock_engine = MagicMock(spec=ExecutionEngine)
    maif_runner = MAIFAgentRunner(runner=inner_runner, engine=mock_engine)

    maif_runner.run(prompt="Hello", agent_name="claude", owner="bob")

    mock_engine.execute.assert_called_once()
    call_args = mock_engine.execute.call_args[1]
    assert call_args["runner"] == inner_runner
    assert call_args["run_meta"].prompt == "Hello"
    assert call_args["run_meta"].agent == "claude"
    assert call_args["run_meta"].owner == "bob"
