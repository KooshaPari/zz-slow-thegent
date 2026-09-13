"""Unit tests for Lifecycle loops and Checker Agent."""

from unittest.mock import MagicMock, patch

import pytest

from thegent.agents.checker import CheckerDecision, CheckerResult
from thegent.agents.loop_controller import LifecycleLoopController, LoopMode
from thegent.config import ThegentSettings


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
        worker_agent_name="test-worker",
        checker_agent_name="test-checker",
        mode=LoopMode.SOFT,
        max_iterations=3,
    )


@patch("thegent.agents.loop_controller.run_impl")
def test_loop_controller_stops_on_kill(mock_run, controller):
    """Loop stops when checker returns KILL."""
    mock_run.return_value = {"exit_code": 0, "stdout": "Worker output", "stderr": ""}

    with patch.object(controller.checker, "decide") as mock_decide:
        mock_decide.return_value = CheckerResult(
            decision=CheckerDecision.KILL,
            reason="Task complete",
        )

        state = controller.run_loop("Start", "Todo")

        assert state.iteration == 1
        assert state.stopped is True
        assert "Checker terminated" in state.stop_reason
        assert mock_run.call_count == 1


@patch("thegent.agents.loop_controller.run_impl")
def test_loop_controller_continues_on_continue(mock_run, controller):
    """Loop continues when checker returns CONTINUE."""
    mock_run.return_value = {"exit_code": 0, "stdout": "Worker output", "stderr": ""}

    with patch.object(controller.checker, "decide") as mock_decide:
        # 1st: CONTINUE, 2nd: CONTINUE, 3rd: max iterations reached
        mock_decide.side_effect = [
            CheckerResult(decision=CheckerDecision.CONTINUE, reason="Keep going"),
            CheckerResult(decision=CheckerDecision.CONTINUE, reason="Almost there"),
            CheckerResult(decision=CheckerDecision.CONTINUE, reason="One more"),
        ]

        state = controller.run_loop("Start", "Todo")

        assert state.iteration == 3
        assert state.stopped is False
        assert state.stop_reason == "Max iterations reached"
        assert mock_run.call_count == 3


@patch("thegent.agents.loop_controller.run_impl")
def test_loop_controller_re_prompts(mock_run, controller):
    """Loop uses new prompt when checker returns RE_PROMPT."""
    mock_run.return_value = {"exit_code": 0, "stdout": "Worker output", "stderr": ""}

    with patch.object(controller.checker, "decide") as mock_decide:
        mock_decide.side_effect = [
            CheckerResult(
                decision=CheckerDecision.RE_PROMPT, prompt="Fix bug", reason="Bug found"
            ),
            CheckerResult(decision=CheckerDecision.KILL, reason="Done now"),
        ]

        controller.run_loop("Start", "Todo")

        assert mock_run.call_count == 2
        # Check second call prompt
        assert mock_run.call_args_list[1].kwargs["prompt"] == "Fix bug"


@patch("thegent.agents.loop_controller.run_impl")
def test_loop_controller_matches_presets(mock_run, controller):
    """Loop matches output to presets before calling checker."""
    # First call output contains "pytest", should match "write_tests" preset
    mock_run.side_effect = [
        {
            "exit_code": 0,
            "stdout": "I wrote some code, now I should run pytest",
            "stderr": "",
        },
        {"exit_code": 0, "stdout": "Tests passed", "stderr": "STOP"},
    ]

    with patch.object(controller.checker, "decide") as mock_decide:
        controller.run_loop("Start", "Todo")

        # Should NOT have called checker for the first iteration because preset matched
        # But wait, in my impl, if preset matches, it calls 'continue' which goes to next loop.
        # So it should call mock_run again with the preset prompt.
        assert mock_run.call_count == 2
        from thegent.agents.presets import get_preset

        expected_prompt = get_preset("write_tests").prompt
        assert mock_run.call_args_list[1].kwargs["prompt"] == expected_prompt

        # Checker should NOT have been called for the first iteration
        assert mock_decide.call_count == 0


@patch("thegent.agents.loop_controller.run_impl")
def test_soft_loop_stops_on_signal(mock_run, controller):
    """Soft loop stops when STOP signal seen in worker output."""
    mock_run.return_value = {"exit_code": 0, "stdout": "All done! STOP", "stderr": ""}

    with patch.object(controller.checker, "decide") as mock_decide:
        mock_decide.return_value = CheckerResult(
            decision=CheckerDecision.CONTINUE, reason="Ok"
        )

        state = controller.run_loop("Start", "Todo")

        assert state.iteration == 1
        assert state.stopped is True
        assert "Human stop signal" in state.stop_reason


@patch("thegent.agents.loop_controller.run_impl")
def test_loop_controller_respects_external_stop(mock_run, controller):
    """Loop stops when external STOP file is present."""
    mock_run.return_value = {"exit_code": 0, "stdout": "Worker output", "stderr": ""}

    # Create STOP file in session dir
    session_dir = controller.settings.session_dir / controller.state.session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "STOP").write_text("STOP")

    state = controller.run_loop("Start", "Todo")

    assert state.iteration == 1  # Incremented before check
    assert state.stopped is True
    assert "External stop signal" in state.stop_reason
    assert mock_run.call_count == 0


@patch("thegent.agents.loop_controller.run_impl")
def test_loop_controller_handles_takeover(mock_run, controller):
    """Loop uses takeover prompt if takeover.json is present."""
    mock_run.return_value = {"exit_code": 0, "stdout": "Worker output", "stderr": ""}

    # Create takeover.json in session dir
    session_dir = controller.settings.session_dir / controller.state.session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    import json

    (session_dir / "takeover.json").write_text(
        json.dumps({"prompt": "Takeover Prompt"}).decode()
    )

    with patch.object(controller.checker, "decide") as mock_decide:
        mock_decide.return_value = CheckerResult(
            decision=CheckerDecision.KILL, reason="Done"
        )

        controller.run_loop("Start", "Todo")

        assert mock_run.call_count == 1
        assert mock_run.call_args.kwargs["prompt"] == "Takeover Prompt"


@patch("thegent.agents.loop_controller.run_impl")
def test_loop_controller_escalates_on_denial(mock_run, controller):
    """Loop escalates to queue when policy denies the task."""
    # "delete" keyword should trigger PolicyEffect.DENY
    with patch(
        "thegent.governance.escalation.EscalationQueue.escalate"
    ) as mock_escalate:
        state = controller.run_loop("delete all files", "Todo")

        assert state.stopped is True
        assert "Policy denied" in state.stop_reason
        assert mock_escalate.call_count == 1
        args = mock_escalate.call_args.kwargs
        assert args["run_id"] == state.session_id
        assert "High-risk operation" in args["reason"]


@patch("thegent.agents.loop_controller.run_impl")
def test_loop_controller_respects_policy_override(mock_run, controller):
    """Loop allows task when policy has an active override."""
    mock_run.return_value = {"exit_code": 0, "stdout": "STOP", "stderr": ""}

    # Apply override for the high-risk rule
    from thegent.governance.overrides import OverrideManager

    om = OverrideManager(controller.settings)
    om.apply_override("HIGH_RISK_LANE", "Test Override", "tester")

    state = controller.run_loop("delete files", "Todo")

    # Should NOT be stopped by policy
    assert state.stopped is True  # Stopped by STOP signal in output
    assert "Human stop signal" in state.stop_reason
    assert mock_run.call_count == 1
    assert mock_run.call_args.kwargs["prompt"] == "delete files"


@patch("thegent.agents.loop_controller.run_impl")
def test_loop_controller_respects_policy_denial(mock_run, controller):
    """Loop stops when policy denies the task."""
    # "delete" keyword should trigger PolicyEffect.DENY
    state = controller.run_loop("delete all files", "Todo")

    assert state.stopped is True
    assert "Policy denied" in state.stop_reason
    assert mock_run.call_count == 0
