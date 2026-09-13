"""Tests for shell and context injection (Phase 13).

Covers:
- TGNT-P13.1: tmux session detection and naming
- TGNT-P13.2: Command injection via tmux send-keys
- TGNT-P13.3: Agent readiness detection
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from thegent.mesh.injection import ShellInjection

# ---------------------------------------------------------------------------
# TGNT-P13.1 – tmux session detection and naming
# ---------------------------------------------------------------------------


class TestSessionDetection:
    """Tmux session detection and naming convention."""

    # @trace TGNT-P13.1
    def test_session_name_format(self) -> None:
        """Session name follows mesh-{agent_id} convention."""
        inj = ShellInjection("abc-123")
        assert inj.session_name == "mesh-abc-123"

    # @trace TGNT-P13.1
    def test_find_session_returns_true_when_exists(self) -> None:
        """find_session returns True when tmux has-session succeeds."""
        inj = ShellInjection("agent-1")
        with patch("thegent.mesh.injection.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert inj.find_session() is True
            mock_run.assert_called_once_with(
                ["tmux", "has-session", "-t", "mesh-agent-1"],
                check=True,
                capture_output=True,
            )

    # @trace TGNT-P13.1
    def test_find_session_returns_false_when_missing(self) -> None:
        """find_session returns False when tmux has-session fails."""
        inj = ShellInjection("agent-2")
        with patch("thegent.mesh.injection.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "tmux")
            assert inj.find_session() is False


# ---------------------------------------------------------------------------
# TGNT-P13.2 – Command injection via tmux send-keys
# ---------------------------------------------------------------------------


class TestCommandInjection:
    """Command injection via tmux send-keys with delay."""

    # @trace TGNT-P13.2
    def test_send_command_calls_send_keys_literal(self) -> None:
        """send_command uses send-keys -l with literal text then Enter."""
        inj = ShellInjection("agent-3")
        with (
            patch.object(inj, "find_session", return_value=True),
            patch("thegent.mesh.injection.subprocess.run") as mock_run,
            patch("thegent.mesh.injection.time.sleep") as mock_sleep,
        ):
            result = inj.send_command("echo hello", wait=0.0)
            assert result is True
            assert mock_run.call_count == 2
            mock_run.assert_any_call(
                ["tmux", "send-keys", "-t", "mesh-agent-3", "-l", "echo hello"],
                check=True,
            )
            mock_run.assert_any_call(
                ["tmux", "send-keys", "-t", "mesh-agent-3", "Enter"],
                check=True,
            )
            mock_sleep.assert_called_once_with(0.0)

    # @trace TGNT-P13.2
    def test_send_command_default_wait(self) -> None:
        """send_command defaults to 1.5s wait between literal keys and Enter."""
        inj = ShellInjection("agent-4")
        with (
            patch.object(inj, "find_session", return_value=True),
            patch("thegent.mesh.injection.subprocess.run"),
            patch("thegent.mesh.injection.time.sleep") as mock_sleep,
        ):
            inj.send_command("ls")
            mock_sleep.assert_called_once_with(1.5)

    # @trace TGNT-P13.2
    def test_send_command_returns_false_when_session_missing(self) -> None:
        """send_command returns False if session does not exist."""
        inj = ShellInjection("agent-5")
        with patch.object(inj, "find_session", return_value=False):
            assert inj.send_command("echo x") is False

    # @trace TGNT-P13.2
    def test_send_command_returns_false_on_subprocess_error(self) -> None:
        """send_command returns False when subprocess.run raises."""
        inj = ShellInjection("agent-6")
        with (
            patch.object(inj, "find_session", return_value=True),
            patch("thegent.mesh.injection.subprocess.run") as mock_run,
            patch("thegent.mesh.injection.time.sleep"),
        ):
            mock_run.side_effect = subprocess.CalledProcessError(1, "tmux")
            assert inj.send_command("bad") is False


# ---------------------------------------------------------------------------
# TGNT-P13.3 – Agent readiness detection
# ---------------------------------------------------------------------------


class TestReadinessDetection:
    """Agent readiness detection via prompt pattern matching."""

    # @trace TGNT-P13.3
    def test_is_ready_matches_dollar_prompt(self) -> None:
        """is_ready detects '$ ' prompt on last line."""
        inj = ShellInjection("agent-7")
        with patch("thegent.mesh.injection.subprocess.check_output") as mock_out:
            mock_out.return_value = "some output\nuser@host:~$ "
            assert inj.is_ready() is True

    # @trace TGNT-P13.3
    def test_is_ready_matches_hash_prompt(self) -> None:
        """is_ready detects '# ' root prompt."""
        inj = ShellInjection("agent-8")
        with patch("thegent.mesh.injection.subprocess.check_output") as mock_out:
            mock_out.return_value = "root@host:/# "
            assert inj.is_ready() is True

    # @trace TGNT-P13.3
    def test_is_ready_matches_python_prompt(self) -> None:
        """is_ready detects '>>> ' Python REPL prompt."""
        inj = ShellInjection("agent-9")
        with patch("thegent.mesh.injection.subprocess.check_output") as mock_out:
            mock_out.return_value = "Python 3.12\n>>> "
            assert inj.is_ready() is True

    # @trace TGNT-P13.3
    def test_is_ready_returns_false_when_busy(self) -> None:
        """is_ready returns False when last line has no prompt pattern."""
        inj = ShellInjection("agent-10")
        with patch("thegent.mesh.injection.subprocess.check_output") as mock_out:
            mock_out.return_value = "compiling module...\nstill running"
            assert inj.is_ready() is False

    # @trace TGNT-P13.3
    def test_is_ready_returns_false_on_empty_output(self) -> None:
        """is_ready returns False when capture-pane returns empty output."""
        inj = ShellInjection("agent-11")
        with patch("thegent.mesh.injection.subprocess.check_output") as mock_out:
            mock_out.return_value = ""
            assert inj.is_ready() is False

    # @trace TGNT-P13.3
    def test_is_ready_returns_false_on_error(self) -> None:
        """is_ready returns False when tmux capture-pane fails."""
        inj = ShellInjection("agent-12")
        with patch("thegent.mesh.injection.subprocess.check_output") as mock_out:
            mock_out.side_effect = subprocess.CalledProcessError(1, "tmux")
            assert inj.is_ready() is False

    # @trace TGNT-P13.3
    def test_is_ready_custom_pattern(self) -> None:
        """is_ready supports custom prompt patterns."""
        inj = ShellInjection("agent-13")
        with patch("thegent.mesh.injection.subprocess.check_output") as mock_out:
            mock_out.return_value = "mysql> "
            assert inj.is_ready(prompt_pattern=r"mysql>\s") is True

    # @trace TGNT-P13.3
    def test_is_ready_calls_capture_pane_correctly(self) -> None:
        """is_ready calls tmux capture-pane with correct session target."""
        inj = ShellInjection("agent-14")
        with patch("thegent.mesh.injection.subprocess.check_output") as mock_out:
            mock_out.return_value = "$ "
            inj.is_ready()
            mock_out.assert_called_once_with(
                ["tmux", "capture-pane", "-p", "-t", "mesh-agent-14"],
                text=True,
            )
