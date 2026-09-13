"""Chaos tests for Lifecycle Loop resilience.

# @trace WL-134 B90-W2-C3
"""

from unittest.mock import MagicMock, patch

import pytest

from tests.chaos.engine import ChaosEngine
from thegent.agents.loop_controller import LifecycleLoopController
from thegent.config import ThegentSettings

pytestmark = pytest.mark.chaos


@pytest.fixture
def mock_settings(tmp_path):
    settings = MagicMock(spec=ThegentSettings)
    settings.cwd = tmp_path / "cwd"
    settings.cwd.mkdir()
    settings.session_dir = tmp_path / "sessions"
    settings.session_dir.mkdir()
    settings.default_timeout = 60
    return settings


@pytest.fixture
def controller(mock_settings):
    return LifecycleLoopController(
        settings=mock_settings,
        worker_agent_name="cursor",
        checker_agent_name="antigravity",
    )


@pytest.fixture
def chaos_engine():
    return ChaosEngine(failure_rate=0.5, latency_range=(0.01, 0.05))


@pytest.mark.deep
@patch("thegent.agents.loop_controller.run_impl")
def test_lifecycle_loop_resilience_to_transient_failures(
    mock_run, controller, chaos_engine
):
    """Lifecycle Loop should retry on transient failures injected by Chaos Engine."""

    # Define a side effect that fails with a retryable error first, then succeeds
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {"exit_code": 1, "stdout": "Rate limit exceeded", "stderr": ""}
        return {"exit_code": 0, "stdout": "Success! STOP", "stderr": ""}

    mock_run.side_effect = side_effect

    # Use short sleep for testing
    with patch("time.sleep"):
        state = controller.run_loop("Start", "Todo")

    assert state.stopped is True
    assert "Human stop signal" in state.stop_reason
    assert call_count == 2  # One failure, one success after retry
    assert (
        state.iteration == 1
    )  # Success happened in iteration 1 (after internal retries)


@pytest.mark.deep
@patch("thegent.agents.loop_controller.run_impl")
def test_lifecycle_loop_stops_on_permanent_failure(mock_run, controller):
    """Lifecycle Loop should NOT retry on permanent failures."""

    mock_run.return_value = {
        "exit_code": 1,
        "stdout": "Permanent Error: Invalid Config",
        "stderr": "",
    }

    state = controller.run_loop("Start", "Todo")

    assert state.stopped is True
    assert "Worker failed" in state.stop_reason
    assert mock_run.call_count == 1
