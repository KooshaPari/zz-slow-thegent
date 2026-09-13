"""Unit tests for CursorApiRunner."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from tests.conftest_factories import make_run_result
from thegent.agents.cursor_api_runner import (
    _PROXY_MODEL,
    CursorApiRunner,
)
from thegent.utils import strip_ansi

# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCursorApiRunnerInit:
    def test_default_construction(self) -> None:
        # @trace FR-AGT-005
        runner = CursorApiRunner()
        assert runner._model == _PROXY_MODEL
        assert runner._settings is not None

    def test_custom_model_overrides_default(self) -> None:
        # @trace FR-AGT-005
        runner = CursorApiRunner(model="custom-cursor-model")
        assert runner._model == "custom-cursor-model"

    def test_settings_are_stored(self) -> None:
        # @trace FR-AGT-005
        from thegent.config import ThegentSettings

        settings = ThegentSettings()
        runner = CursorApiRunner(settings=settings)
        assert runner._settings is settings


# ---------------------------------------------------------------------------
# API request building (command building)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCommandBuilding:
    @patch("thegent.agents.cursor_api_runner._is_cursor_api_reachable", return_value=True)
    @patch("thegent.agents.cursor_api_runner._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.cursor_api_runner._run_with_retry")
    def test_basic_command_includes_required_flags(self, mock_retry, mock_resolve, mock_reachable) -> None:
        # @trace FR-AGT-005
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        runner = CursorApiRunner()
        runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        cmd = mock_retry.call_args.args[0]
        assert cmd[0] == "/usr/bin/codex"
        assert "exec" in cmd
        assert "-" in cmd
        assert "--skip-git-repo-check" in cmd
        assert "--json" in cmd
        assert "--model" in cmd

    @patch("thegent.agents.cursor_api_runner._is_cursor_api_reachable", return_value=True)
    @patch("thegent.agents.cursor_api_runner._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.cursor_api_runner._run_with_retry")
    def test_write_mode_adds_sandbox(self, mock_retry, mock_resolve, mock_reachable) -> None:
        # @trace FR-AGT-005
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        runner = CursorApiRunner()
        runner.run(prompt="test", cwd=None, mode="write", timeout=60)

        cmd = mock_retry.call_args.args[0]
        assert "--sandbox" in cmd
        assert "workspace-write" in cmd

    @patch("thegent.agents.cursor_api_runner._is_cursor_api_reachable", return_value=True)
    @patch("thegent.agents.cursor_api_runner._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.cursor_api_runner._run_with_retry")
    def test_full_mode_adds_full_auto(self, mock_retry, mock_resolve, mock_reachable) -> None:
        # @trace FR-AGT-005
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        runner = CursorApiRunner()
        runner.run(prompt="test", cwd=None, mode="full", timeout=60)

        cmd = mock_retry.call_args.args[0]
        assert "--full-auto" in cmd


# ---------------------------------------------------------------------------
# Response parsing / env setup
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestEnvSetup:
    @patch("thegent.agents.cursor_api_runner._is_cursor_api_reachable", return_value=True)
    @patch("thegent.agents.cursor_api_runner._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.cursor_api_runner._run_with_retry")
    def test_env_uses_cursor_api_url(self, mock_retry, mock_resolve, mock_reachable) -> None:
        # @trace FR-AGT-005
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        runner = CursorApiRunner()
        runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        env = mock_retry.call_args.args[4]
        assert "OPENAI_BASE_URL" in env
        assert "OPENAI_API_KEY" in env


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestErrorHandling:
    @patch("thegent.agents.cursor_api_runner._is_cursor_api_reachable", return_value=False)
    def test_unreachable_api_returns_error(self, mock_reachable) -> None:
        # @trace FR-AGT-005
        runner = CursorApiRunner()
        result = runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        assert result.exit_code == 1
        assert "cursor-api not reachable" in result.stderr
        assert not result.timed_out

    @patch("thegent.agents.cursor_api_runner._is_cursor_api_reachable", return_value=True)
    @patch("thegent.agents.cursor_api_runner._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.cursor_api_runner._run_with_retry")
    def test_timeout_expired_returns_timed_out(self, mock_retry, mock_resolve, mock_reachable) -> None:
        # @trace FR-AGT-005
        import subprocess

        mock_retry.side_effect = subprocess.TimeoutExpired(cmd="codex", timeout=60)

        runner = CursorApiRunner()
        result = runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        assert result.exit_code == 124
        assert result.timed_out is True
        assert "timed out" in result.stderr

    @patch("thegent.agents.cursor_api_runner._is_cursor_api_reachable", return_value=True)
    @patch("thegent.agents.cursor_api_runner._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.cursor_api_runner._run_with_retry")
    def test_codex_not_found_returns_install_message(self, mock_retry, mock_resolve, mock_reachable) -> None:
        # @trace FR-AGT-005
        mock_retry.side_effect = FileNotFoundError("codex")

        runner = CursorApiRunner()
        result = runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        assert result.exit_code == 1
        assert "codex CLI not found" in result.stderr

    @patch("thegent.agents.cursor_api_runner._is_cursor_api_reachable", return_value=True)
    @patch("thegent.agents.cursor_api_runner._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.cursor_api_runner._run_with_retry")
    def test_transient_error_returns_result(self, mock_retry, mock_resolve, mock_reachable) -> None:
        # @trace FR-AGT-005
        from thegent.agents.resilience import TransientAgentError

        err_result = make_run_result(exit_code=1, stderr="429 too many requests")
        mock_retry.side_effect = TransientAgentError(err_result)

        runner = CursorApiRunner()
        result = runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        assert result.exit_code == 1
        assert "429 too many requests" in result.stderr


# ---------------------------------------------------------------------------
# Initialization edge cases
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCursorApiRunnerInitEdgeCases:
    def test_none_settings_creates_default(self) -> None:
        # @trace FR-AGT-005
        """Passing None settings creates a default ThegentSettings."""
        runner = CursorApiRunner(settings=None)
        assert runner._settings is not None
        from thegent.config import ThegentSettings

        assert isinstance(runner._settings, ThegentSettings)

    def test_empty_string_model_uses_proxy_model(self) -> None:
        # @trace FR-AGT-005
        """Empty string model falls back to _PROXY_MODEL."""
        runner = CursorApiRunner(model="")
        assert runner._model == _PROXY_MODEL


# ---------------------------------------------------------------------------
# _resolve_codex
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestResolveCodex:
    @patch(
        "thegent.agents.cursor_api_runner.shutil.which",
        return_value="/usr/local/bin/codex",
    )
    def test_finds_codex_on_path(self, mock_which) -> None:
        # @trace FR-AGT-005
        """Returns path from shutil.which when codex is on PATH."""
        from thegent.agents.cursor_api_runner import _resolve_codex

        assert _resolve_codex() == "/usr/local/bin/codex"

    @patch("thegent.agents.cursor_api_runner.shutil.which", return_value=None)
    def test_fallback_to_local_bin(self, mock_which, tmp_path) -> None:
        # @trace FR-AGT-005
        """Falls back to ~/.local/bin/codex when which returns None."""
        from thegent.agents.cursor_api_runner import _resolve_codex

        local_codex = tmp_path / ".local" / "bin" / "codex"
        local_codex.parent.mkdir(parents=True)
        local_codex.touch()
        with patch("thegent.agents.cursor_api_runner.Path.home", return_value=tmp_path):
            result = _resolve_codex()
        assert result == str(local_codex)

    @patch("thegent.agents.cursor_api_runner.shutil.which", return_value=None)
    def test_returns_bare_codex_when_nothing_found(self, mock_which) -> None:
        # @trace FR-AGT-005
        """Returns 'codex' string when neither which nor local bin finds it."""
        from thegent.agents.cursor_api_runner import _resolve_codex

        result = _resolve_codex()
        assert result == "codex"


# ---------------------------------------------------------------------------
# strip_ansi
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStripAnsiCursorApi:
    def test_removes_ansi_sequences(self) -> None:
        # @trace FR-AGT-005
        """Strips ANSI color codes from text."""
        assert strip_ansi("\x1b[32mgreen\x1b[0m") == "green"

    def test_plain_text_unchanged(self) -> None:
        # @trace FR-AGT-005
        """Plain text without ANSI codes passes through."""
        assert strip_ansi("no colors here") == "no colors here"


# ---------------------------------------------------------------------------
# _is_cursor_api_reachable
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestIsCursorApiReachable:
    @patch(
        "thegent.agents.cursor_api_runner._check_cursor_api_reachable",
        return_value=(True, False, 200),
    )
    def test_reachable_returns_true(self, mock_check) -> None:
        # @trace FR-AGT-005
        """Returns True when reachability check succeeds."""
        from thegent.agents.cursor_api_runner import _is_cursor_api_reachable

        assert _is_cursor_api_reachable("http://127.0.0.1:3000", "token") is True

    @patch(
        "thegent.agents.cursor_api_runner._check_cursor_api_reachable",
        return_value=(False, False, 500),
    )
    def test_unreachable_returns_false(self, mock_check) -> None:
        # @trace FR-AGT-005
        """Returns False when HTTP check is unsuccessful."""
        from thegent.agents.cursor_api_runner import _is_cursor_api_reachable

        assert _is_cursor_api_reachable("http://127.0.0.1:3000", "token") is False

    @patch(
        "thegent.agents.cursor_api_runner._check_cursor_api_reachable",
        return_value=(False, True, None),
    )
    def test_empty_token_still_sends_request(self, mock_check) -> None:
        # @trace FR-AGT-005
        """Empty token still attempts the request without auth header."""
        from thegent.agents.cursor_api_runner import _is_cursor_api_reachable

        _is_cursor_api_reachable("http://127.0.0.1:3000", "")
        mock_check.assert_called_once_with("http://127.0.0.1:3000", "", 3.0)


# ---------------------------------------------------------------------------
# Command construction with cwd and agent_model override
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCommandBuildingExtended:
    @patch("thegent.agents.cursor_api_runner._is_cursor_api_reachable", return_value=True)
    @patch("thegent.agents.cursor_api_runner._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.cursor_api_runner._run_with_retry")
    def test_cwd_adds_cd_flag(self, mock_retry, mock_resolve, mock_reachable, tmp_path) -> None:
        # @trace FR-AGT-005
        """Passing cwd adds --cd flag."""
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        runner = CursorApiRunner()
        runner.run(prompt="test", cwd=tmp_path, mode="read-only", timeout=60)

        cmd = mock_retry.call_args.args[0]
        assert "--cd" in cmd
        assert str(tmp_path) in cmd

    @patch("thegent.agents.cursor_api_runner._is_cursor_api_reachable", return_value=True)
    @patch("thegent.agents.cursor_api_runner._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.cursor_api_runner._run_with_retry")
    def test_agent_model_override(self, mock_retry, mock_resolve, mock_reachable) -> None:
        # @trace FR-AGT-005
        """agent_model parameter overrides default model."""
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        runner = CursorApiRunner(model="default-model")
        runner.run(
            prompt="test",
            cwd=None,
            mode="read-only",
            timeout=60,
            agent_model="override-model",
        )

        cmd = mock_retry.call_args.args[0]
        idx = cmd.index("--model")
        assert cmd[idx + 1] == "override-model"

    @patch("thegent.agents.cursor_api_runner._is_cursor_api_reachable", return_value=True)
    @patch("thegent.agents.cursor_api_runner._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.cursor_api_runner._run_with_retry")
    def test_no_stream_omits_json_flag(self, mock_retry, mock_resolve, mock_reachable) -> None:
        # @trace FR-AGT-005
        """use_stream=False omits --json flag."""
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        runner = CursorApiRunner()
        runner.run(prompt="test", cwd=None, mode="read-only", timeout=60, use_stream=False)

        cmd = mock_retry.call_args.args[0]
        assert "--json" not in cmd

    @patch("thegent.agents.cursor_api_runner._is_cursor_api_reachable", return_value=True)
    @patch("thegent.agents.cursor_api_runner._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.cursor_api_runner._run_with_retry")
    def test_token_from_env_when_settings_empty(self, mock_retry, mock_resolve, mock_reachable) -> None:
        # @trace FR-AGT-005
        """Falls back to THGENT_CURSOR_API_TOKEN env var when settings token is empty."""
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        from thegent.config import ThegentSettings

        settings = ThegentSettings(cursor_api_token="")
        runner = CursorApiRunner(settings=settings)

        with patch.dict("os.environ", {"THGENT_CURSOR_API_TOKEN": "env-token-123"}):
            runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        env = mock_retry.call_args.args[4]
        assert env["OPENAI_API_KEY"] == "env-token-123"

    @patch("thegent.agents.cursor_api_runner._is_cursor_api_reachable", return_value=True)
    @patch("thegent.agents.cursor_api_runner._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.cursor_api_runner._run_with_retry")
    def test_no_token_uses_sk_dummy(self, mock_retry, mock_resolve, mock_reachable) -> None:
        # @trace FR-AGT-005
        """When no token is available, uses sk-dummy as API key."""
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        from thegent.config import ThegentSettings

        settings = ThegentSettings(cursor_api_token="")
        runner = CursorApiRunner(settings=settings)

        with patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("THGENT_CURSOR_API_TOKEN", None)
            runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        env = mock_retry.call_args.args[4]
        assert env["OPENAI_API_KEY"] == "sk-dummy"


# ---------------------------------------------------------------------------
# _run_with_retry coverage (lines 56-73)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRunWithRetryCursorApi:
    @patch("thegent.agents.cursor_api_runner.subprocess.run")
    def test_successful_run(self, mock_run) -> None:
        # @trace FR-AGT-005
        """_run_with_retry returns RunResult on success (lines 56-73)."""
        from thegent.agents.cursor_api_runner import _run_with_retry

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output text",
            stderr="",
        )
        result = _run_with_retry.__wrapped__(["codex", "exec"], "prompt", None, 60, {})
        assert result.exit_code == 0
        assert result.stdout == "output text"

    @patch("thegent.agents.cursor_api_runner.subprocess.run")
    def test_retryable_failure_raises_transient(self, mock_run) -> None:
        # @trace FR-AGT-005
        """_run_with_retry raises TransientAgentError on retryable failure (lines 69-72)."""
        from thegent.agents.cursor_api_runner import _run_with_retry
        from thegent.agents.resilience import TransientAgentError

        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="429 Too Many Requests",
        )
        with pytest.raises(TransientAgentError):
            _run_with_retry.__wrapped__(["codex", "exec"], "prompt", None, 60, {})

    @patch("thegent.agents.cursor_api_runner.subprocess.run")
    def test_nonretryable_failure_returns_result(self, mock_run) -> None:
        # @trace FR-AGT-005
        """_run_with_retry returns RunResult on non-retryable failure (line 73)."""
        from thegent.agents.cursor_api_runner import _run_with_retry

        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="fatal: unknown error",
        )
        result = _run_with_retry.__wrapped__(["codex", "exec"], "prompt", None, 60, {})
        assert result.exit_code == 1

    @patch("thegent.agents.cursor_api_runner.subprocess.run")
    def test_exit_code_124_is_timed_out(self, mock_run) -> None:
        # @trace FR-AGT-005
        """_run_with_retry marks exit code 124 as timed_out (line 69)."""
        from thegent.agents.cursor_api_runner import _run_with_retry

        mock_run.return_value = MagicMock(
            returncode=124,
            stdout="",
            stderr="",
        )
        result = _run_with_retry.__wrapped__(["codex", "exec"], "prompt", None, 60, {})
        assert result.timed_out is True

    @patch("thegent.agents.cursor_api_runner.subprocess.run")
    def test_cwd_passed_as_string(self, mock_run) -> None:
        # @trace FR-AGT-005
        """_run_with_retry passes cwd as string (line 62)."""
        from thegent.agents.cursor_api_runner import _run_with_retry

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="ok",
            stderr="",
        )
        _run_with_retry.__wrapped__(["codex", "exec"], "prompt", Path("/workspace"), 60, {})
        call_kwargs = mock_run.call_args
        assert call_kwargs.kwargs.get("cwd") == "/workspace" or call_kwargs[1].get("cwd") == "/workspace"
