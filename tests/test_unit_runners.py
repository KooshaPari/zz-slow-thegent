"""Unit tests for agent runners (mocked subprocess)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from thegent.agents.codex_proxy import CodexProxyRunner
from thegent.agents.direct_agents import DirectAgentRunner


@pytest.mark.unit
class TestDirectAgentRunner:
    """Tests for DirectAgentRunner."""

    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_run_invokes_gemini_cli(self, mock_run: MagicMock, project_root: Path) -> None:
        # @trace FR-AGT-002
        """Run invokes gemini CLI with correct args."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output",
            stderr="",
        )

        runner = DirectAgentRunner("gemini", default_model="")
        result = runner.run(
            prompt="list dirs",
            cwd=project_root,
            mode="read-only",
            timeout=60,
        )

        assert result.exit_code == 0
        assert result.stdout == "output"
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "gemini" in cmd[0] or cmd[0].endswith("gemini")
        assert "list dirs" in cmd
        assert "--output-format" in cmd or "stream-json" in cmd

    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_run_invokes_cursor_with_workspace(self, mock_run: MagicMock, project_root: Path) -> None:
        # @trace FR-AGT-002
        """Run invokes cursor with --workspace when cwd provided."""
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

        runner = DirectAgentRunner("cursor-agent", default_model="")
        runner.run(
            prompt="test",
            cwd=project_root,
            mode="write",
            timeout=30,
        )

        cmd = mock_run.call_args[0][0]
        assert "--workspace" in cmd
        assert str(project_root) in cmd
        assert "--print" in cmd
        assert "test" in cmd

    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_strips_ansi(self, mock_run: MagicMock) -> None:
        # @trace FR-AGT-003
        """ANSI escape sequences are stripped from output."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="\x1b[32mgreen\x1b[0m text",
            stderr="",
        )

        runner = DirectAgentRunner("gemini", default_model="")
        result = runner.run(prompt="x", cwd=None, mode="write", timeout=10)
        assert "green" in result.stdout
        assert "\x1b" not in result.stdout

    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_file_not_found_returns_helpful_error(self, mock_run: MagicMock) -> None:
        # @trace FR-AGT-010
        """When CLI not found, returns helpful stderr."""
        mock_run.side_effect = FileNotFoundError

        runner = DirectAgentRunner("gemini", default_model="")
        result = runner.run(prompt="x", cwd=None, mode="write", timeout=10)
        assert result.exit_code == 1
        assert "not found" in result.stderr


@pytest.mark.unit
class TestCodexProxyRunner:
    """Tests for CodexProxyRunner (codex via CLIProxyAPIPlus)."""

    @patch("thegent.agents.codex_proxy.ensure_proxy_running")
    @patch("thegent.agents.codex_proxy.subprocess.run")
    def test_run_invokes_codex_with_proxy_env(
        self,
        mock_run: MagicMock,
        mock_ensure: MagicMock,
        project_root: Path,
    ) -> None:
        # @trace FR-AGT-001
        """Run invokes codex exec with OPENAI_BASE_URL and OPENAI_API_KEY set."""
        mock_ensure.return_value = "http://127.0.0.1:8317/v1"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output",
            stderr="",
        )

        runner = CodexProxyRunner("antigravity")
        result = runner.run(
            prompt="test",
            cwd=project_root,
            mode="write",
            timeout=60,
        )

        assert result.exit_code == 0
        mock_ensure.assert_called_once()
        mock_run.assert_called_once()
        call_kw = mock_run.call_args[1]
        assert call_kw["env"]["OPENAI_BASE_URL"] == "http://127.0.0.1:8317/v1"
        assert call_kw["env"]["OPENAI_API_KEY"] == "sk-dummy"
        cmd = mock_run.call_args[0][0]
        assert "codex" in cmd[0] or cmd[0].endswith("codex")
        assert "exec" in cmd
        assert call_kw["input"] == "test"

    @patch("thegent.agents.codex_proxy.ensure_proxy_running")
    def test_run_proxy_unavailable_returns_error(self, mock_ensure: MagicMock) -> None:
        # @trace FR-AGT-010
        """When proxy cannot start, returns exit_code 1 with error message."""
        mock_ensure.side_effect = FileNotFoundError("cli-proxy-api-plus not found")

        runner = CodexProxyRunner("antigravity")
        result = runner.run(prompt="x", cwd=None, mode="write", timeout=10)

        assert result.exit_code == 1
        assert "not found" in result.stderr

    @patch("thegent.agents.codex_proxy.ensure_proxy_running")
    @patch("thegent.agents.codex_proxy.subprocess.run")
    def test_run_minimax_glm_use_proxy(
        self,
        mock_run: MagicMock,
        mock_ensure: MagicMock,
        project_root: Path,
    ) -> None:
        # @trace FR-AGT-001
        """minimax and glm use CodexProxyRunner (same backend as antigravity)."""
        mock_ensure.return_value = "http://127.0.0.1:8317/v1"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output",
            stderr="",
        )
        for agent in ("minimax", "glm"):
            runner = CodexProxyRunner(agent)
            result = runner.run(
                prompt="test",
                cwd=project_root,
                mode="write",
                timeout=60,
            )
            assert result.exit_code == 0
            cmd = mock_run.call_args[0][0]
            assert "codex" in cmd[0] or cmd[0].endswith("codex")
            assert "exec" in cmd
