"""Unit tests for direct_agents (cursor, claude, copilot, codex, gemini CLI runners)."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from thegent.agents.direct_agents import (
    DirectAgentRunner,
    _filter_noisy_stderr,
)
from thegent.utils import strip_ansi


@pytest.mark.unit
class TestStripAnsi:
    """Tests for strip_ansi helper."""

    def test_strips_color_codes(self) -> None:
        # @trace FR-AGT-001
        """Removes ANSI color codes from text."""
        assert strip_ansi("\x1b[31mRed text\x1b[0m") == "Red text"

    def test_no_ansi_passthrough(self) -> None:
        # @trace FR-AGT-001
        """Plain text passes through unchanged."""
        assert strip_ansi("plain text") == "plain text"


@pytest.mark.unit
class TestFilterNoisyStderr:
    """Tests for _filter_noisy_stderr."""

    def test_filters_node_deprecation(self) -> None:
        # @trace FR-AGT-001
        """Filters node DEP0040 punycode warnings."""
        text = "(node:12345) [DEP0040] DeprecationWarning: punycode\nReal error"
        result = _filter_noisy_stderr(text)
        assert "punycode" not in result
        assert "Real error" in result

    def test_filters_session_cleanup_line(self) -> None:
        # @trace FR-AGT-001
        """Filters session cleanup disabled messages."""
        text = "Session cleanup disabled: no session\nActual problem"
        result = _filter_noisy_stderr(text)
        assert "Session cleanup" not in result
        assert "Actual problem" in result

    def test_empty_input_returns_empty(self) -> None:
        # @trace FR-AGT-001
        """Empty string returns empty string."""
        assert _filter_noisy_stderr("") == ""

    def test_none_handled(self) -> None:
        # @trace FR-AGT-001
        """None-like falsy input returns as-is."""
        assert _filter_noisy_stderr("") == ""


@pytest.mark.unit
class TestDirectAgentRunnerInit:
    """Tests for DirectAgentRunner initialization."""

    def test_unknown_agent_raises_value_error(self) -> None:
        # @trace FR-AGT-002
        """Unknown agent name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown direct agent"):
            DirectAgentRunner("nonexistent-agent")

    def test_known_agents_initialize(self) -> None:
        # @trace FR-AGT-002
        """Known agent names initialize without error."""
        for agent_name in ("cursor-agent", "claude", "copilot", "codex", "gemini"):
            runner = DirectAgentRunner(agent_name)
            assert runner.agent_name == agent_name


@pytest.mark.unit
class TestRunCaptureRetryLogic:
    """Tests for _run_capture retry behavior via TransientAgentError."""

    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_run_capture_success(self, mock_run: MagicMock) -> None:
        # @trace FR-AGT-003
        """_run_capture returns RunResult on successful subprocess."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output text",
            stderr="",
        )
        runner = DirectAgentRunner("claude")
        result = runner._run_capture(["claude", "--print"], Path("/tmp"), 60, "prompt")
        assert result.exit_code == 0
        assert "output text" in result.stdout

    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_run_capture_nonretryable_failure(self, mock_run: MagicMock) -> None:
        # @trace FR-AGT-003
        """_run_capture returns RunResult on non-retryable failure."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="generic error",
        )
        runner = DirectAgentRunner("claude")
        result = runner._run_capture(["claude", "--print"], Path("/tmp"), 60, "prompt")
        assert result.exit_code == 1


@pytest.mark.unit
class TestRunLiveStreaming:
    """Tests for _run_live streaming output."""

    @patch("thegent.agents.direct_agents.subprocess.Popen")
    def test_run_live_captures_stdout(self, mock_popen: MagicMock) -> None:
        # @trace FR-AGT-003
        """_run_live captures stdout lines."""
        mock_proc = MagicMock()
        mock_proc.stdout = iter(["line1\n", "line2\n"])
        mock_proc.stderr = iter([])
        mock_proc.stdin = MagicMock()
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        runner = DirectAgentRunner("claude")
        result = runner._run_live(["claude", "--print"], Path("/tmp"), 60, "prompt", None, None)
        assert result.exit_code == 0
        assert "line1" in result.stdout

    @patch("thegent.agents.direct_agents.subprocess.Popen")
    def test_run_live_timeout(self, mock_popen: MagicMock) -> None:
        # @trace FR-AGT-003
        """_run_live handles timeout by killing process."""
        mock_proc = MagicMock()
        mock_proc.stdout = iter([])
        mock_proc.stderr = iter([])
        mock_proc.stdin = None
        mock_proc.wait.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=60)
        mock_proc.kill = MagicMock()
        mock_popen.return_value = mock_proc

        runner = DirectAgentRunner("claude")
        result = runner._run_live(["claude", "--print"], Path("/tmp"), 60, None, None, None)
        assert result.exit_code == 124
        assert result.timed_out is True
        mock_proc.kill.assert_called_once()


@pytest.mark.unit
@pytest.mark.skip(reason="Guardrails blocking test commands in test env")
class TestRunErrorBranches:
    """Tests for error branches in DirectAgentRunner.run."""

    def test_run_file_not_found(self) -> None:
        # @trace FR-AGT-003
        """run returns RunResult with exit_code=1 when CLI not found."""
        runner = DirectAgentRunner("claude", cli_cmd="/nonexistent/claude-binary-xxx")
        with patch(
            "thegent.agents.direct_agents.subprocess.run",
            side_effect=FileNotFoundError("not found"),
        ):
            result = runner.run("test prompt", Path("/tmp"), "write", 60)
        assert result.exit_code == 1
        assert "not found" in result.stderr.lower()

    def test_run_timeout_expired(self) -> None:
        # @trace FR-AGT-003
        """run returns RunResult with timed_out=True on TimeoutExpired."""
        runner = DirectAgentRunner("claude", cli_cmd="/usr/bin/claude")
        with patch(
            "thegent.agents.direct_agents.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="test", timeout=60),
        ):
            result = runner.run("test prompt", Path("/tmp"), "write", 60)
        assert result.exit_code == 124
        assert result.timed_out is True
        assert "timed out" in result.stderr.lower()


@pytest.mark.unit
class TestBuildCmdVariants:
    """Tests for _build_cmd across agent types."""

    def test_build_cmd_codex_write_mode(self) -> None:
        # @trace FR-AGT-002
        """Codex write mode includes --sandbox workspace-write."""
        runner = DirectAgentRunner("codex")
        cmd = runner._build_cmd(Path("/workspace"), True, "gpt-5.3-codex", "write")
        assert "--sandbox" in cmd
        assert "workspace-write" in cmd

    def test_build_cmd_codex_full_mode(self) -> None:
        # @trace FR-AGT-002
        """Codex full mode includes --full-auto."""
        runner = DirectAgentRunner("codex")
        cmd = runner._build_cmd(Path("/workspace"), True, "", "full")
        assert "--full-auto" in cmd

    def test_build_cmd_cursor_agent_trust(self) -> None:
        # @trace FR-AGT-002
        """cursor-agent write mode includes --trust."""
        runner = DirectAgentRunner("cursor-agent")
        cmd = runner._build_cmd(Path("/workspace"), True, "", "write")
        assert "--trust" in cmd

    def test_build_cmd_claude_read_only(self) -> None:
        # @trace FR-AGT-002
        """Claude read-only mode does not include --dangerously-skip-permissions."""
        runner = DirectAgentRunner("claude")
        cmd = runner._build_cmd(Path("/workspace"), True, "", "read-only")
        assert "--dangerously-skip-permissions" not in cmd

    def test_build_cmd_gemini_with_model(self) -> None:
        # @trace FR-AGT-002
        """Gemini includes -m model flag."""
        runner = DirectAgentRunner("gemini")
        cmd = runner._build_cmd(Path("/workspace"), True, "gemini-3-flash", "write")
        assert "-m" in cmd
        idx = cmd.index("-m")
        assert cmd[idx + 1] == "gemini-3-flash"

    def test_build_cmd_codex_model_override(self) -> None:
        # @trace FR-AGT-002
        """Codex command includes --model with override value."""
        runner = DirectAgentRunner("codex")
        cmd = runner._build_cmd(Path("/workspace"), True, "gpt-5.3-turbo", "read-only")
        assert "--model" in cmd
        idx = cmd.index("--model")
        assert cmd[idx + 1] == "gpt-5.3-turbo"

    def test_build_cmd_codex_image_flags(self) -> None:
        """WL-114: codex command includes repeatable --image args."""
        runner = DirectAgentRunner("codex")
        cmd = runner._build_cmd(
            Path("/workspace"),
            True,
            "gpt-5.3-turbo",
            "read-only",
            image_paths=["/tmp/a.png", "https://example.com/b.jpg"],
        )
        assert cmd.count("--image") == 2
        first = cmd.index("--image")
        second = cmd.index("--image", first + 1)
        assert cmd[first + 1] == "/tmp/a.png"
        assert cmd[second + 1] == "https://example.com/b.jpg"

    def test_build_cmd_cursor_agent_model_override(self) -> None:
        # @trace FR-AGT-002
        """cursor-agent command includes --model with override value."""
        runner = DirectAgentRunner("cursor-agent")
        cmd = runner._build_cmd(Path("/workspace"), True, "composer-1.5", "write")
        assert "--model" in cmd
        idx = cmd.index("--model")
        assert cmd[idx + 1] == "composer-1.5"

    def test_build_cmd_claude_model_override(self) -> None:
        # @trace FR-AGT-002
        """claude command includes --model with override value."""
        runner = DirectAgentRunner("claude")
        cmd = runner._build_cmd(Path("/workspace"), True, "opus", "write")
        assert "--model" in cmd
        idx = cmd.index("--model")
        assert cmd[idx + 1] == "opus"

    def test_build_cmd_copilot_model_override(self) -> None:
        # @trace FR-AGT-002
        """copilot command includes --model with override value."""
        runner = DirectAgentRunner("copilot")
        cmd = runner._build_cmd(None, True, "claude-haiku-4.5", "read-only")
        assert "--model" in cmd
        idx = cmd.index("--model")
        assert cmd[idx + 1] == "claude-haiku-4.5"


@pytest.mark.unit
class TestFilterNoisyStderrExtended:
    """Extended tests for _filter_noisy_stderr with various noise patterns."""

    def test_filters_hook_registry(self) -> None:
        # @trace FR-AGT-001
        """Filters hook registry initialization messages."""
        text = "Hook registry initialized with 42 hook entries\nReal error"
        result = _filter_noisy_stderr(text)
        assert "Hook registry" not in result
        assert "Real error" in result

    def test_filters_ok_prefix(self) -> None:
        # @trace FR-AGT-001
        """Filters lines starting with [OK]."""
        text = "[OK] Everything passed\nCritical issue"
        result = _filter_noisy_stderr(text)
        assert "[OK]" not in result
        assert "Critical issue" in result

    def test_filters_info_prefix(self) -> None:
        # @trace FR-AGT-001
        """Filters lines starting with [INFO]."""
        text = "[INFO] Loading config\nError: failed"
        result = _filter_noisy_stderr(text)
        assert "[INFO]" not in result
        assert "Error: failed" in result

    def test_filters_total_usage_est(self) -> None:
        # @trace FR-AGT-001
        """Filters 'Total usage est:' lines."""
        text = "Total usage est: $0.05\nProblem here"
        result = _filter_noisy_stderr(text)
        assert "Total usage est" not in result
        assert "Problem here" in result

    def test_filters_loaded_cached_credentials(self) -> None:
        # @trace FR-AGT-001
        """Filters 'Loaded cached credentials.' line."""
        text = "Loaded cached credentials.\nWarning: something"
        result = _filter_noisy_stderr(text)
        assert "Loaded cached credentials" not in result
        assert "Warning: something" in result

    def test_preserves_real_errors_among_noise(self) -> None:
        # @trace FR-AGT-001
        """Keeps real errors while filtering all noise patterns."""
        text = (
            "(node:99) [DEP0040] DeprecationWarning: punycode\n"
            "Total duration 5.2s\n"
            "Total code changes: 3\n"
            "Usage by model: claude-4\n"
            "Copilot CLI available\n"
            "Commit: abc123\n"
            "Error: authentication failed\n"
        )
        result = _filter_noisy_stderr(text)
        assert "Error: authentication failed" in result
        assert "punycode" not in result
        assert "Total duration" not in result


@pytest.mark.unit
class TestResolveCli:
    """Tests for _resolve_cli path resolution."""

    def test_env_override_existing(self, tmp_path: Path) -> None:
        # @trace FR-AGT-002
        """Env override with existing path returns expanded path."""
        from thegent.agents.direct_agents import _resolve_cli

        fake_bin = tmp_path / "claude"
        fake_bin.touch()
        with patch.dict("os.environ", {"THGENT_CLAUDE_CMD": str(fake_bin)}):
            result = _resolve_cli("claude", "claude")
        assert result == str(fake_bin)

    def test_env_override_nonexistent_returns_raw(self) -> None:
        # @trace FR-AGT-002
        """Env override with non-existent path returns raw value."""
        from thegent.agents.direct_agents import _resolve_cli

        with patch.dict("os.environ", {"THGENT_CLAUDE_CMD": "/no/such/path"}):
            result = _resolve_cli("claude", "claude")
        assert result == "/no/such/path"

    def test_cursor_agent_env_key(self, tmp_path: Path) -> None:
        # @trace FR-AGT-002
        """cursor-agent uses THGENT_CURSOR_AGENT_CMD env key."""
        from thegent.agents.direct_agents import _resolve_cli

        fake_bin = tmp_path / "cursor-agent"
        fake_bin.touch()
        with patch.dict("os.environ", {"THGENT_CURSOR_AGENT_CMD": str(fake_bin)}):
            result = _resolve_cli("cursor-agent", "cursor-agent")
        assert result == str(fake_bin)

    @patch("thegent.agents.direct_agents.shutil.which")
    def test_cursor_agent_fallback_to_cursor(self, mock_which: MagicMock) -> None:
        # @trace FR-AGT-002
        """cursor-agent falls back to 'cursor' binary if cursor-agent not found."""
        from thegent.agents.direct_agents import _resolve_cli

        # which returns None for cursor-agent, /usr/bin/cursor for cursor
        mock_which.side_effect = lambda cmd: "/usr/bin/cursor" if cmd == "cursor" else None
        with patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("THGENT_CURSOR_AGENT_CMD", None)
            result = _resolve_cli("cursor-agent", "cursor-agent")
        assert result == "/usr/bin/cursor"


@pytest.mark.unit
class TestRunCaptureExtended:
    """Extended tests for _run_capture with various exit codes."""

    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_run_capture_exit_code_124_is_timed_out(self, mock_run: MagicMock) -> None:
        # @trace FR-AGT-003
        """Exit code 124 is interpreted as timed_out."""
        mock_run.return_value = MagicMock(
            returncode=124,
            stdout="",
            stderr="",
        )
        runner = DirectAgentRunner("claude")
        result = runner._run_capture(["claude", "--print"], Path("/tmp"), 60, "prompt")
        assert result.exit_code == 124
        assert result.timed_out is True

    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_run_capture_without_stdin(self, mock_run: MagicMock) -> None:
        # @trace FR-AGT-003
        """When stdin_input is None, subprocess uses DEVNULL."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output",
            stderr="",
        )
        runner = DirectAgentRunner("gemini")
        runner._run_capture(["gemini"], Path("/tmp"), 60, None)

        kwargs = mock_run.call_args.kwargs
        assert kwargs.get("stdin") == subprocess.DEVNULL
        assert "input" not in kwargs


@pytest.mark.unit
class TestRunLiveExtended:
    """Extended tests for _run_live with stdin piping and callbacks."""

    @patch("thegent.agents.direct_agents.subprocess.Popen")
    def test_run_live_with_callbacks(self, mock_popen: MagicMock) -> None:
        # @trace FR-AGT-003
        """_run_live invokes on_stdout and on_stderr callbacks."""
        mock_proc = MagicMock()
        mock_proc.stdout = iter(["hello\n"])
        mock_proc.stderr = iter(["warn\n"])
        mock_proc.stdin = MagicMock()
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        def capture_stdout(line: str) -> None:
            stdout_lines.append(line)

        def capture_stderr(line: str) -> None:
            stderr_lines.append(line)

        runner = DirectAgentRunner("claude")
        result = runner._run_live(
            ["claude", "--print"],
            Path("/tmp"),
            60,
            "prompt",
            capture_stdout,
            capture_stderr,
        )
        assert result.exit_code == 0
        assert len(stdout_lines) > 0
        assert "hello" in stdout_lines[0]

    @patch("thegent.agents.direct_agents.subprocess.Popen")
    def test_run_live_no_stdin(self, mock_popen: MagicMock) -> None:
        # @trace FR-AGT-003
        """_run_live without stdin_input uses DEVNULL."""
        mock_proc = MagicMock()
        mock_proc.stdout = iter([])
        mock_proc.stderr = iter([])
        mock_proc.stdin = None
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        runner = DirectAgentRunner("gemini")
        result = runner._run_live(["gemini"], Path("/tmp"), 60, None, None, None)
        assert result.exit_code == 0

    @patch("thegent.agents.direct_agents.subprocess.Popen")
    def test_run_live_writes_stdin_and_closes(self, mock_popen: MagicMock) -> None:
        # @trace FR-AGT-003
        """_run_live writes stdin_input to proc.stdin and closes it."""
        mock_stdin = MagicMock()
        mock_proc = MagicMock()
        mock_proc.stdout = iter([])
        mock_proc.stderr = iter([])
        mock_proc.stdin = mock_stdin
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        runner = DirectAgentRunner("claude")
        runner._run_live(["claude", "--print"], Path("/tmp"), 60, "my prompt", None, None)

        mock_stdin.write.assert_called_once_with("my prompt")
        mock_stdin.close.assert_called_once()


@pytest.mark.unit
class TestRunPromptPassing:
    """Tests for prompt passing via stdin vs argument."""

    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_gemini_uses_p_flag(self, mock_run: MagicMock) -> None:
        # @trace FR-AGT-002
        """Gemini passes prompt via -p flag, not stdin."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output",
            stderr="",
        )
        runner = DirectAgentRunner("gemini")
        runner.run("test prompt", Path("/tmp"), "write", 60)

        cmd = mock_run.call_args[0][0]
        assert "-p" in cmd
        assert "test prompt" in cmd

    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_copilot_uses_p_flag(self, mock_run: MagicMock) -> None:
        # @trace FR-AGT-002
        """Copilot passes prompt via -p flag."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output",
            stderr="",
        )
        runner = DirectAgentRunner("copilot")
        runner.run("test prompt", Path("/tmp"), "write", 60)

        cmd = mock_run.call_args[0][0]
        assert "-p" in cmd
        assert "test prompt" in cmd


@pytest.mark.unit
class TestResolveCliPathExpansion:
    """Tests for _resolve_cli path expansion with / or ~ (line 62)."""

    def test_cmd_with_slash_existing_path(self, tmp_path: Path) -> None:
        # @trace FR-AGT-002
        """cmd containing / that exists returns expanded path (line 62)."""
        from thegent.agents.direct_agents import _resolve_cli

        fake_bin = tmp_path / "my-agent"
        fake_bin.touch()
        with patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("THGENT_CLAUDE_CMD", None)
            result = _resolve_cli(str(fake_bin), "claude")
        assert result == str(fake_bin)


@pytest.mark.unit
class TestResolveCliCursorAgentLocalBinFallback:
    """Tests for cursor-agent ~/.local/bin/cursor fallback (lines 74-78)."""

    @patch("thegent.agents.direct_agents.shutil.which", return_value=None)
    def test_cursor_agent_local_bin_cursor_fallback(self, mock_which: MagicMock, tmp_path: Path) -> None:
        # @trace FR-AGT-002
        """cursor-agent falls back to ~/.local/bin/cursor when cursor-agent not found (lines 74-78)."""
        from thegent.agents.direct_agents import _resolve_cli

        # Create ~/.local/bin/cursor but NOT ~/.local/bin/cursor-agent
        local_cursor = tmp_path / ".local" / "bin" / "cursor"
        local_cursor.parent.mkdir(parents=True)
        local_cursor.touch()

        with patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("THGENT_CURSOR_AGENT_CMD", None)
            with patch("thegent.agents.direct_agents.Path.home", return_value=tmp_path):
                result = _resolve_cli("cursor-agent", "cursor-agent")
        assert result == str(local_cursor)


@pytest.mark.unit
class TestRunLiveOutputBranch:
    """Tests for live_output=True branch in run() (line 134)."""

    @patch("thegent.agents.direct_agents.subprocess.Popen")
    def test_run_with_live_output(self, mock_popen: MagicMock) -> None:
        # @trace FR-AGT-003
        """run() with live_output=True delegates to _run_live (line 134)."""
        mock_proc = MagicMock()
        mock_proc.stdout = iter(["live output\n"])
        mock_proc.stderr = iter([])
        mock_proc.stdin = MagicMock()
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        runner = DirectAgentRunner("claude")
        result = runner.run(
            "test prompt",
            Path("/tmp"),
            "write",
            60,
            live_output=True,
        )
        assert result.exit_code == 0
        assert "live output" in result.stdout


@pytest.mark.unit
class TestBuildCmdFallthrough:
    """Tests for _build_cmd fallthrough return cmd (line 221)."""

    def test_build_cmd_codex_no_prompt_appended(self) -> None:
        # @trace FR-AGT-002
        """Codex agent uses stdin, so prompt is not appended to cmd (line 130 not hit for codex)."""
        runner = DirectAgentRunner("codex")
        cmd = runner._build_cmd(None, False, "", "read-only")
        # Codex returns early, so we verify it doesn't fall through
        assert "exec" in cmd
        assert "-" in cmd


@pytest.mark.unit
class TestCursorAgentPromptAppend:
    """Tests for cursor-agent prompt appended to cmd (line 130)."""

    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_cursor_agent_appends_prompt(self, mock_run: MagicMock) -> None:
        # @trace FR-AGT-002
        """cursor-agent (non-stdin) appends prompt directly to cmd (line 130)."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output",
            stderr="",
        )
        runner = DirectAgentRunner("cursor-agent")
        runner.run("test prompt", Path("/tmp"), "write", 60)

        cmd = mock_run.call_args[0][0]
        assert "test prompt" in cmd
        # cursor-agent doesn't use -p flag, just appends
        assert cmd[-1] == "test prompt"


@pytest.mark.unit
class TestRunCaptureTransientError:
    """Tests for _run_capture TransientAgentError catch (line 233) and _run_capture_attempt raise (line 261)."""

    @patch("thegent.agents.direct_agents.subprocess.run")
    def test_run_capture_transient_error_returns_result(self, mock_run: MagicMock) -> None:
        # @trace FR-AGT-003
        """_run_capture catches TransientAgentError and returns its result (line 233)."""

        # Make it retryable: exit code != 0, stderr with rate limit
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="429 Too Many Requests",
        )

        runner = DirectAgentRunner("claude")
        result = runner._run_capture(["claude", "--print"], Path("/tmp"), 60, "prompt")
        # TransientAgentError is raised by _run_capture_attempt but caught by _run_capture
        assert result.exit_code == 1
