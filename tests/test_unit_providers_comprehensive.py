"""Comprehensive unit tests for all agent providers/runners."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from thegent.agents.codex_proxy import CodexProxyRunner
from thegent.agents.cursor_api_runner import CursorApiRunner
from thegent.agents.direct_agents import DirectAgentRunner


class TestDirectAgentRunnerComprehensive:
    """Comprehensive tests for DirectAgentRunner."""

    @pytest.mark.parametrize("agent", ["cursor-agent", "gemini", "claude", "copilot", "codex"])
    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_run_basic(self, mock_run, agent, project_root) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        runner = DirectAgentRunner(agent)
        result = runner.run("test", project_root, "read-only", 30)
        assert result.exit_code == 0
        assert result.stdout == "ok"
        mock_run.assert_called_once()

    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_cursor_workspace_arg(self, mock_run, project_root) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        runner = DirectAgentRunner("cursor-agent")
        runner.run("test", project_root, "write", 30)
        cmd = mock_run.call_args[0][0]
        assert "--workspace" in cmd
        assert str(project_root) in cmd

    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_claude_stream_arg(self, mock_run, project_root) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        runner = DirectAgentRunner("claude")
        runner.run("test", project_root, "read-only", 30, use_stream=True)
        cmd = mock_run.call_args[0][0]
        assert "--output-format" in cmd
        assert "stream-json" in cmd

    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_mode_mapping(self, mock_run, project_root) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

        # Codex mode mapping
        runner = DirectAgentRunner("codex")
        runner.run("test", project_root, "write", 30)
        cmd = mock_run.call_args[0][0]
        assert "--sandbox" in cmd
        assert "workspace-write" in cmd

        runner.run("test", project_root, "full", 30)
        cmd = mock_run.call_args[0][0]
        assert "--full-auto" in cmd

        # Cursor mode mapping
        runner = DirectAgentRunner("cursor-agent")
        runner.run("test", project_root, "read-only", 30)
        cmd = mock_run.call_args[0][0]
        assert "--trust" not in cmd

        runner.run("test", project_root, "write", 30)
        cmd = mock_run.call_args[0][0]
        assert "--trust" in cmd

        # Claude mode mapping
        runner = DirectAgentRunner("claude")
        runner.run("test", project_root, "read-only", 30)
        cmd = mock_run.call_args[0][0]
        assert "--dangerously-skip-permissions" not in cmd

        runner.run("test", project_root, "write", 30)
        cmd = mock_run.call_args[0][0]
        assert "--dangerously-skip-permissions" in cmd

    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_timeout_handling(self, mock_run, project_root) -> None:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["test"], timeout=30)
        runner = DirectAgentRunner("gemini")
        result = runner.run("test", project_root, "read-only", 30)
        assert result.exit_code == 124
        assert result.timed_out is True
        assert "timed out" in result.stderr

    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_retry_on_transient_error(self, mock_run, project_root) -> None:
        # First call fails with retryable error, second succeeds
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="rate limit exceeded"),
            MagicMock(returncode=0, stdout="success", stderr=""),
        ]
        runner = DirectAgentRunner("gemini")
        # Use a small timeout to speed up test if it retries
        with patch("time.sleep"):  # Skip sleep in tests
            result = runner.run("test", project_root, "read-only", 30)

        assert result.exit_code == 0
        assert result.stdout == "success"
        assert mock_run.call_count == 2

    @patch("thegent.agents.direct_agents.subprocess.Popen")
    def test_run_live(self, mock_popen, project_root) -> None:
        mock_proc = MagicMock()
        mock_proc.stdout = ["line1\n", "line2\n"]
        mock_proc.stderr = []
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        on_stdout = MagicMock()
        runner = DirectAgentRunner("gemini")
        result = runner.run("test", project_root, "read-only", 30, live_output=True, on_stdout=on_stdout)

        assert result.exit_code == 0
        assert result.stdout == "line1\nline2\n"
        assert on_stdout.call_count == 2
        on_stdout.assert_any_call("line1")
        on_stdout.assert_any_call("line2")


class TestCodexProxyRunnerComprehensive:
    """Comprehensive tests for CodexProxyRunner."""

    @pytest.mark.parametrize("agent", ["antigravity", "minimax", "glm", "cliproxy", "roo", "kilo"])
    @patch("thegent.agents.codex_proxy.ensure_proxy_running")
    @patch("thegent.agents.codex_proxy.subprocess.run")
    def test_proxy_agents_basic(self, mock_run, mock_ensure, agent, project_root) -> None:
        mock_ensure.return_value = "http://localhost:8317"
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

        runner = CodexProxyRunner(agent)
        result = runner.run("test", project_root, "read-only", 30)

        assert result.exit_code == 0
        mock_ensure.assert_called_once()
        env = mock_run.call_args[1]["env"]
        assert env["OPENAI_BASE_URL"] == "http://localhost:8317"

    @patch("thegent.agents.codex_proxy.ensure_proxy_running")
    @patch("thegent.agents.codex_proxy.subprocess.run")
    def test_mode_mapping(self, mock_run, mock_ensure, project_root) -> None:
        mock_ensure.return_value = "http://localhost:8317"
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

        runner = CodexProxyRunner("antigravity")

        # Test write mode
        runner.run("test", project_root, "write", 30)
        cmd = mock_run.call_args[0][0]
        assert "--sandbox" in cmd
        assert "workspace-write" in cmd

        # Test full mode
        runner.run("test", project_root, "full", 30)
        cmd = mock_run.call_args[0][0]
        assert "--full-auto" in cmd


class TestCursorApiRunnerComprehensive:
    """Comprehensive tests for CursorApiRunner."""

    @patch("thegent.agents.cursor_api_runner._is_cursor_api_reachable")
    @patch("thegent.agents.cursor_api_runner.subprocess.run")
    def test_cursor_api_basic(self, mock_run, mock_reachable, project_root) -> None:
        mock_reachable.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

        runner = CursorApiRunner()
        result = runner.run("test", project_root, "read-only", 30)

        assert result.exit_code == 0
        mock_reachable.assert_called_once()
        env = mock_run.call_args[1]["env"]
        assert "OPENAI_BASE_URL" in env

    @patch("thegent.agents.cursor_api_runner._is_cursor_api_reachable")
    def test_cursor_api_unreachable(self, mock_reachable, project_root) -> None:
        mock_reachable.return_value = False

        runner = CursorApiRunner()
        result = runner.run("test", project_root, "read-only", 30)

        assert result.exit_code == 1
        assert "not reachable" in result.stderr

    @patch("thegent.agents.cursor_api_runner._is_cursor_api_reachable")
    @patch("thegent.agents.cursor_api_runner.subprocess.run")
    def test_mode_mapping(self, mock_run, mock_reachable, project_root) -> None:
        mock_reachable.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

        runner = CursorApiRunner()

        # Test full mode
        runner.run("test", project_root, "full", 30)
        cmd = mock_run.call_args[0][0]
        assert "--full-auto" in cmd
