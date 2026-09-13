"""Unit tests for CodexProxyRunner."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest_factories import make_run_result
from thegent.agents.codex_proxy import (
    _PROXY_MODEL,
    CodexProxyRunner,
)
from thegent.utils import strip_ansi

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# strip_ansi helper
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStripAnsi:
    def test_strips_color_codes(self) -> None:
        # @trace FR-AGT-004
        raw = "\x1b[31mERROR\x1b[0m: something went wrong"
        assert strip_ansi(raw) == "ERROR: something went wrong"

    def test_passthrough_plain_text(self) -> None:
        # @trace FR-AGT-004
        text = "no ansi here"
        assert strip_ansi(text) == "no ansi here"


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCodexProxyRunnerInit:
    def test_valid_agent_names(self) -> None:
        # @trace FR-AGT-004
        for name in _PROXY_MODEL:
            runner = CodexProxyRunner(agent_name=name)
            assert runner.agent_name == name
            assert runner._model == _PROXY_MODEL[name]

    def test_unknown_agent_raises(self) -> None:
        # @trace FR-AGT-004
        with pytest.raises(ValueError, match="Unknown proxy agent"):
            CodexProxyRunner(agent_name="nonexistent")

    def test_custom_model_overrides_default(self) -> None:
        # @trace FR-AGT-004
        runner = CodexProxyRunner(agent_name="claude", model="custom-model")
        assert runner._model == "custom-model"

    def test_default_model_from_registry(self) -> None:
        # @trace FR-AGT-004
        runner = CodexProxyRunner(agent_name="gemini")
        assert runner._model == "gemini-2.5-flash"


# ---------------------------------------------------------------------------
# Command building
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCommandBuilding:
    @patch(
        "thegent.agents.codex_proxy.ensure_proxy_running",
        return_value="http://localhost:8317/v1",
    )
    @patch("thegent.agents.codex_proxy._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.codex_proxy._run_with_retry")
    def test_basic_command_structure(
        self, mock_retry, mock_resolve, mock_proxy
    ) -> None:
        # @trace FR-AGT-004
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        runner = CodexProxyRunner(agent_name="claude")
        runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        cmd = mock_retry.call_args.args[0]
        assert cmd[0] == "/usr/bin/codex"
        assert "exec" in cmd
        assert "-" in cmd
        assert "--skip-git-repo-check" in cmd
        assert "--json" in cmd  # use_stream=True by default
        assert "--model" in cmd

    @patch(
        "thegent.agents.codex_proxy.ensure_proxy_running",
        return_value="http://localhost:8317/v1",
    )
    @patch("thegent.agents.codex_proxy._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.codex_proxy._run_with_retry")
    def test_write_mode_adds_sandbox(
        self, mock_retry, mock_resolve, mock_proxy
    ) -> None:
        # @trace FR-AGT-004
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        runner = CodexProxyRunner(agent_name="codex")
        runner.run(prompt="test", cwd=None, mode="write", timeout=60)

        cmd = mock_retry.call_args.args[0]
        assert "--sandbox" in cmd
        assert "workspace-write" in cmd

    @patch(
        "thegent.agents.codex_proxy.ensure_proxy_running",
        return_value="http://localhost:8317/v1",
    )
    @patch("thegent.agents.codex_proxy._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.codex_proxy._run_with_retry")
    def test_full_mode_adds_full_auto(
        self, mock_retry, mock_resolve, mock_proxy
    ) -> None:
        # @trace FR-AGT-004
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        runner = CodexProxyRunner(agent_name="codex")
        runner.run(prompt="test", cwd=None, mode="full", timeout=60)

        cmd = mock_retry.call_args.args[0]
        assert "--full-auto" in cmd

    @patch(
        "thegent.agents.codex_proxy.ensure_proxy_running",
        return_value="http://localhost:8317/v1",
    )
    @patch("thegent.agents.codex_proxy._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.codex_proxy._run_with_retry")
    def test_cwd_adds_cd_flag(
        self, mock_retry, mock_resolve, mock_proxy, tmp_path: Path
    ) -> None:
        # @trace FR-AGT-004
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        runner = CodexProxyRunner(agent_name="codex")
        runner.run(prompt="test", cwd=tmp_path, mode="read-only", timeout=60)

        cmd = mock_retry.call_args.args[0]
        assert "--cd" in cmd
        assert str(tmp_path) in cmd

    @patch(
        "thegent.agents.codex_proxy.ensure_proxy_running",
        return_value="http://localhost:8317/v1",
    )
    @patch("thegent.agents.codex_proxy._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.codex_proxy._run_with_retry")
    def test_image_paths_add_repeatable_image_flags(
        self, mock_retry, mock_resolve, mock_proxy
    ) -> None:
        """WL-114: codex proxy runner forwards repeatable --image flags."""
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        runner = CodexProxyRunner(agent_name="codex")
        runner.run(
            prompt="test",
            cwd=None,
            mode="read-only",
            timeout=60,
            image_paths=["/tmp/a.png", "https://example.com/b.jpg"],
        )

        cmd = mock_retry.call_args.args[0]
        assert cmd.count("--image") == 2
        first = cmd.index("--image")
        second = cmd.index("--image", first + 1)
        assert cmd[first + 1] == "/tmp/a.png"
        assert cmd[second + 1] == "https://example.com/b.jpg"


# ---------------------------------------------------------------------------
# Run method with mock subprocess
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRunMethod:
    @patch("thegent.agents.codex_proxy.ensure_proxy_running")
    def test_proxy_failure_returns_error_result(self, mock_proxy) -> None:
        # @trace FR-AGT-004
        mock_proxy.side_effect = FileNotFoundError("cli-proxy-api-plus not found")

        runner = CodexProxyRunner(agent_name="claude")
        result = runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        assert result.exit_code == 1
        assert "cli-proxy-api-plus not found" in result.stderr

    @patch(
        "thegent.agents.codex_proxy.ensure_proxy_running",
        return_value="http://localhost:8317/v1",
    )
    @patch("thegent.agents.codex_proxy._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.codex_proxy._run_with_retry")
    def test_env_sets_openai_base_url(
        self, mock_retry, mock_resolve, mock_proxy
    ) -> None:
        # @trace FR-AGT-004
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        runner = CodexProxyRunner(agent_name="claude")
        runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        env = mock_retry.call_args.args[4]
        assert env["OPENAI_BASE_URL"] == "http://localhost:8317/v1"
        assert env["OPENAI_API_KEY"] == "sk-dummy"


# ---------------------------------------------------------------------------
# Timeout handling
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTimeoutHandling:
    @patch(
        "thegent.agents.codex_proxy.ensure_proxy_running",
        return_value="http://localhost:8317/v1",
    )
    @patch("thegent.agents.codex_proxy._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.codex_proxy._run_with_retry")
    def test_timeout_expired_returns_timed_out_result(
        self, mock_retry, mock_resolve, mock_proxy
    ) -> None:
        # @trace FR-AGT-004
        import subprocess

        mock_retry.side_effect = subprocess.TimeoutExpired(cmd="codex", timeout=60)

        runner = CodexProxyRunner(agent_name="claude")
        result = runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        assert result.exit_code == 124
        assert result.timed_out is True
        assert "timed out" in result.stderr

    @patch(
        "thegent.agents.codex_proxy.ensure_proxy_running",
        return_value="http://localhost:8317/v1",
    )
    @patch("thegent.agents.codex_proxy._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.codex_proxy._run_with_retry")
    def test_codex_not_found_returns_install_message(
        self, mock_retry, mock_resolve, mock_proxy
    ) -> None:
        # @trace FR-AGT-004
        mock_retry.side_effect = FileNotFoundError("codex")

        runner = CodexProxyRunner(agent_name="claude")
        result = runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        assert result.exit_code == 1
        assert "codex CLI not found" in result.stderr

    @patch(
        "thegent.agents.codex_proxy.ensure_proxy_running",
        return_value="http://localhost:8317/v1",
    )
    @patch("thegent.agents.codex_proxy._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.codex_proxy._run_with_retry")
    def test_transient_error_returns_result(
        self, mock_retry, mock_resolve, mock_proxy
    ) -> None:
        # @trace FR-AGT-004
        from thegent.agents.resilience import TransientAgentError

        err_result = make_run_result(exit_code=1, stderr="429 rate limit")
        mock_retry.side_effect = TransientAgentError(err_result)

        runner = CodexProxyRunner(agent_name="claude")
        result = runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        assert result.exit_code == 1
        assert "429 rate limit" in result.stderr


# ---------------------------------------------------------------------------
# _resolve_codex local bin fallback (lines 39-42)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestResolveCodexWhichFound:
    @patch(
        "thegent.agents.codex_proxy.shutil.which", return_value="/usr/local/bin/codex"
    )
    def test_which_found_returns_path(self, mock_which) -> None:
        # @trace FR-AGT-004
        """_resolve_codex returns path from shutil.which when codex is on PATH (line 38)."""
        from thegent.agents.codex_proxy import _resolve_codex

        assert _resolve_codex() == "/usr/local/bin/codex"


@pytest.mark.unit
class TestResolveCodexLocalBin:
    @patch("thegent.agents.codex_proxy.shutil.which", return_value=None)
    def test_fallback_to_local_bin(self, mock_which, tmp_path: Path) -> None:
        # @trace FR-AGT-004
        """_resolve_codex falls back to ~/.local/bin/codex (lines 39-41)."""
        from thegent.agents.codex_proxy import _resolve_codex

        local_codex = tmp_path / ".local" / "bin" / "codex"
        local_codex.parent.mkdir(parents=True)
        local_codex.touch()
        with patch("thegent.agents.codex_proxy.Path.home", return_value=tmp_path):
            result = _resolve_codex()
        assert result == str(local_codex)

    @patch("thegent.agents.codex_proxy.shutil.which", return_value=None)
    def test_returns_bare_codex_when_nothing_found(self, mock_which) -> None:
        # @trace FR-AGT-004
        """_resolve_codex returns 'codex' when neither which nor local bin finds it (line 42)."""
        from thegent.agents.codex_proxy import _resolve_codex

        result = _resolve_codex()
        assert result == "codex"


# ---------------------------------------------------------------------------
# _run_with_retry TransientAgentError raise (line 70)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRunWithRetryTransient:
    @patch("thegent.agents.codex_proxy.subprocess.run")
    def test_retryable_failure_raises_transient(self, mock_run) -> None:
        # @trace FR-AGT-004
        """_run_with_retry raises TransientAgentError on retryable failure (line 70)."""
        from thegent.agents.codex_proxy import _run_with_retry
        from thegent.agents.resilience import TransientAgentError

        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="429 Too Many Requests",
        )

        with pytest.raises(TransientAgentError):
            _run_with_retry.__wrapped__(["codex", "exec"], "prompt", None, 60, {})

    @patch("thegent.agents.codex_proxy.subprocess.run")
    def test_successful_run_returns_result(self, mock_run) -> None:
        # @trace FR-AGT-004
        """_run_with_retry returns RunResult on success (line 71)."""
        from thegent.agents.codex_proxy import _run_with_retry

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output text",
            stderr="",
        )
        result = _run_with_retry.__wrapped__(["codex", "exec"], "prompt", None, 60, {})
        assert result.exit_code == 0
        assert result.stdout == "output text"

    @patch("thegent.agents.codex_proxy.subprocess.run")
    def test_nonretryable_failure_returns_result(self, mock_run) -> None:
        # @trace FR-AGT-004
        """_run_with_retry returns RunResult on non-retryable failure (line 71)."""
        from thegent.agents.codex_proxy import _run_with_retry

        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="fatal: unknown error",
        )
        result = _run_with_retry.__wrapped__(["codex", "exec"], "prompt", None, 60, {})
        assert result.exit_code == 1
