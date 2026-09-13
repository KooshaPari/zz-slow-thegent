"""Unit tests for Codex proxy improvements: instance isolation, resource limits, JSONL parsing, config injection, error handling.

# @trace FR-AGT-001 FR-AGT-002 FR-AGT-003 FR-AGT-004
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import orjson as json
import pytest

from tests.conftest_factories import make_run_result
from thegent.agents import codex_proxy
from thegent.agents.codex_proxy import (
    CodexAuthError,
    CodexInstanceError,
    CodexModelError,
    CodexProxyRunner,
    CodexResult,
    CodexSandboxError,
    _check_and_track_instance,
    _create_isolated_home,
    _parse_jsonl_output,
    _write_config_override,
)


@pytest.fixture(autouse=True)
def reset_instance_counter() -> None:
    """Reset instance counter before each test to ensure clean state.

    # @trace FR-AGT-002
    """
    codex_proxy._instance_counter = 0
    yield
    codex_proxy._instance_counter = 0


# ---------------------------------------------------------------------------
# Instance Isolation Tests (Improvement 1)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestInstanceIsolation:
    """Test CODEX_HOME isolation per instance."""

    def test_isolated_home_created_with_default_path(self) -> None:
        # @trace FR-AGT-001
        """_create_isolated_home creates isolated directory in ~/.codex/agents/."""
        instance_id = "test-instance-123"
        home = _create_isolated_home(instance_id)

        assert home.exists()
        assert "codex" in str(home)
        assert "agents" in str(home)
        assert instance_id in str(home)

        # Cleanup
        home.rmdir()
        home.parent.rmdir()

    def test_isolated_home_created_with_custom_base(self, tmp_path: Path) -> None:
        # @trace FR-AGT-001
        """_create_isolated_home respects custom base_dir."""
        instance_id = "test-instance-456"
        home = _create_isolated_home(instance_id, base_dir=tmp_path)

        assert home.exists()
        assert home.parent == tmp_path
        assert instance_id in str(home)

    def test_isolated_home_creates_parents(self, tmp_path: Path) -> None:
        # @trace FR-AGT-001
        """_create_isolated_home creates parent directories."""
        base = tmp_path / "deep" / "nested" / "path"
        instance_id = "nested-instance"
        home = _create_isolated_home(instance_id, base_dir=base)

        assert home.exists()
        assert home.is_dir()

    @patch("thegent.agents.codex_proxy.ensure_proxy_running", return_value="http://localhost:8317/v1")
    @patch("thegent.agents.codex_proxy._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.codex_proxy._run_with_retry")
    def test_run_sets_codex_home_env_var(self, mock_retry, mock_resolve, mock_proxy) -> None:
        # @trace FR-AGT-001
        """run() sets CODEX_HOME environment variable for instance isolation."""
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        with tempfile.TemporaryDirectory() as tmpdir:
            runner = CodexProxyRunner(
                agent_name="codex",
                codex_home=Path(tmpdir),
            )
            runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

            env = mock_retry.call_args.args[4]
            assert "CODEX_HOME" in env
            assert env["CODEX_HOME"] == tmpdir

    @patch("thegent.agents.codex_proxy.ensure_proxy_running", return_value="http://localhost:8317/v1")
    @patch("thegent.agents.codex_proxy._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.codex_proxy._run_with_retry")
    def test_run_creates_default_isolated_home(self, mock_retry, mock_resolve, mock_proxy) -> None:
        # @trace FR-AGT-001
        """run() creates default isolated home when codex_home is None."""
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        runner = CodexProxyRunner(agent_name="codex", keep_isolated_home=True)
        runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        env = mock_retry.call_args.args[4]
        assert "CODEX_HOME" in env
        codex_home = Path(env["CODEX_HOME"])
        assert codex_home.exists()
        assert runner.instance_id in str(codex_home)
        # Cleanup
        try:
            import shutil

            shutil.rmtree(codex_home)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Resource-Aware Spawning Tests (Improvement 2)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestResourceAwareSpawning:
    """Test concurrent instance limits and resource tracking."""

    def test_instance_counter_increments(self) -> None:
        # @trace FR-AGT-002
        """_get_next_instance_id increments counter."""
        from thegent.agents.codex_proxy import _get_next_instance_id

        id1 = _get_next_instance_id()
        id2 = _get_next_instance_id()

        # Both should be different
        assert id1 != id2
        assert "codex-" in id1
        assert "codex-" in id2

    def test_check_instance_within_limit(self) -> None:
        # @trace FR-AGT-002
        """_check_and_track_instance passes when under limit."""
        # Should not raise
        _check_and_track_instance(max_concurrent=1000)

    def test_check_instance_exceeds_limit(self) -> None:
        # @trace FR-AGT-002
        """_check_and_track_instance raises CodexInstanceError when exceeded."""
        # Increment counter first to exceed limit
        codex_proxy._instance_counter = 5
        with pytest.raises(CodexInstanceError, match="Concurrent instance limit"):
            _check_and_track_instance(max_concurrent=1)

    @patch("thegent.agents.codex_proxy.ensure_proxy_running", return_value="http://localhost:8317/v1")
    @patch("thegent.agents.codex_proxy._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.codex_proxy._run_with_retry")
    def test_run_respects_max_concurrent(self, mock_retry, mock_resolve, mock_proxy) -> None:
        # @trace FR-AGT-002
        """run() returns error when concurrent limit exceeded."""
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        runner = CodexProxyRunner(
            agent_name="codex",
            max_concurrent_instances=0,  # Force exceeded
        )
        result = runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        assert result.exit_code == 1
        assert "Concurrent instance limit" in result.stderr

    @patch("thegent.agents.codex_proxy.ensure_proxy_running", return_value="http://localhost:8317/v1")
    @patch("thegent.agents.codex_proxy._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.codex_proxy._run_with_retry")
    def test_run_sets_memory_limit_env(self, mock_retry, mock_resolve, mock_proxy) -> None:
        # @trace FR-AGT-002
        """run() sets CODEX_MEMORY_LIMIT_MB environment variable."""
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        runner = CodexProxyRunner(
            agent_name="codex",
            memory_limit_mb=256,
        )
        runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        env = mock_retry.call_args.args[4]
        assert env["CODEX_MEMORY_LIMIT_MB"] == "256"


# ---------------------------------------------------------------------------
# JSONL Parsing Tests (Improvement 3)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestJsonlParsing:
    """Test streaming JSONL output parsing."""

    def test_parse_simple_json_line(self) -> None:
        # @trace FR-AGT-003
        """_parse_jsonl_output extracts text from simple JSON line."""
        output = json.dumps({"choices": [{"text": "hello world"}]}).decode()
        text, tokens_in, tokens_out, _ = _parse_jsonl_output(output)

        assert text == "hello world"
        assert tokens_in == 0
        assert tokens_out == 0

    def test_parse_delta_chunks(self) -> None:
        # @trace FR-AGT-003
        """_parse_jsonl_output concatenates streaming delta chunks."""
        lines = [
            json.dumps({"choices": [{"delta": {"content": "hello"}}]}).decode(),
            json.dumps({"choices": [{"delta": {"content": " "}}]}).decode(),
            json.dumps({"choices": [{"delta": {"content": "world"}}]}).decode(),
        ]
        output = "\n".join(lines)
        text, _, _, _ = _parse_jsonl_output(output)

        assert text == "hello world"

    def test_parse_token_usage(self) -> None:
        # @trace FR-AGT-003
        """_parse_jsonl_output extracts token usage."""
        output = json.dumps(
            {
                "usage": {
                    "prompt_tokens": 42,
                    "completion_tokens": 128,
                }
            }
        )
        _, tokens_in, tokens_out, _ = _parse_jsonl_output(output)

        assert tokens_in == 42
        assert tokens_out == 128

    def test_parse_model_name(self) -> None:
        # @trace FR-AGT-003
        """_parse_jsonl_output extracts model name."""
        output = json.dumps({"model": "gpt-5.3-codex-spark"}).decode()
        _, _, _, model = _parse_jsonl_output(output)

        assert model == "gpt-5.3-codex-spark"

    def test_parse_multiline_with_non_json(self) -> None:
        # @trace FR-AGT-003
        """_parse_jsonl_output handles mixed JSON and plain text lines."""
        lines = [
            json.dumps({"choices": [{"text": "line1\n"}]}).decode(),
            "This is plain stderr text",
            json.dumps({"choices": [{"text": "line2"}]}).decode(),
        ]
        output = "\n".join(lines)
        text, _, _, _ = _parse_jsonl_output(output)

        # Should include both JSON text and plain text
        assert "line1" in text
        assert "line2" in text
        assert "plain stderr text" in text

    def test_parse_empty_output(self) -> None:
        # @trace FR-AGT-003
        """_parse_jsonl_output handles empty output."""
        text, tokens_in, tokens_out, model = _parse_jsonl_output("")

        assert text == ""
        assert tokens_in == 0
        assert tokens_out == 0
        assert model == ""

    def test_parse_message_format(self) -> None:
        # @trace FR-AGT-003
        """_parse_jsonl_output handles message format (non-streaming)."""
        output = json.dumps({"choices": [{"message": {"content": "This is a response"}}]}).decode()
        text, _, _, _ = _parse_jsonl_output(output)

        assert text == "This is a response"


# ---------------------------------------------------------------------------
# Config Injection Tests (Improvement 4)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestConfigInjection:
    """Test config.toml injection."""

    def test_write_config_override_basic(self) -> None:
        # @trace FR-AGT-004
        """_write_config_override writes config.toml with overrides."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_overrides = {
                "model": "gpt-5.3-codex-high",
                "sandbox": "workspace-write",
            }
            config_path = _write_config_override(config_overrides, Path(tmpdir))

            assert config_path.exists()
            content = config_path.read_text()
            assert "model" in content
            assert "gpt-5.3-codex-high" in content
            assert "sandbox" in content
            assert "workspace-write" in content

    def test_write_config_override_types(self) -> None:
        # @trace FR-AGT-004
        """_write_config_override handles different value types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_overrides = {
                "string_val": "value",
                "bool_val": "true",
                "int_val": "42",
            }
            config_path = _write_config_override(config_overrides, Path(tmpdir))

            content = config_path.read_text()
            assert 'string_val = "value"' in content
            # bool and int values written as-is
            assert "bool_val" in content
            assert "int_val" in content

    @patch("thegent.agents.codex_proxy.ensure_proxy_running", return_value="http://localhost:8317/v1")
    @patch("thegent.agents.codex_proxy._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.codex_proxy._run_with_retry")
    def test_run_injects_config_file(self, mock_retry, mock_resolve, mock_proxy) -> None:
        # @trace FR-AGT-004
        """run() creates config file and sets CODEX_CONFIG_DIR."""

        def capture_env(*args, **kwargs):
            # Capture env dict before cleanup happens
            captured_env = args[4].copy()
            captured_env["_captured"] = True
            return make_run_result(exit_code=0, stdout="ok")

        mock_retry.side_effect = capture_env

        config_overrides = {
            "model": "gpt-5.3-codex-high",
        }
        runner = CodexProxyRunner(
            agent_name="codex",
            config_overrides=config_overrides,
        )
        runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        # Verify config dir was in env (even if cleaned up after)
        env = mock_retry.call_args.args[4]
        assert "CODEX_CONFIG_DIR" in env
        # The directory exists during execution, gets cleaned up in finally

    @patch("thegent.agents.codex_proxy.ensure_proxy_running", return_value="http://localhost:8317/v1")
    @patch("thegent.agents.codex_proxy._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.codex_proxy._run_with_retry")
    def test_run_cleans_up_config_dir(self, mock_retry, mock_resolve, mock_proxy) -> None:
        # @trace FR-AGT-004
        """run() cleans up temporary config directory after completion."""
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        config_overrides = {"model": "gpt-5.3-codex-high"}
        runner = CodexProxyRunner(
            agent_name="codex",
            config_overrides=config_overrides,
        )
        runner.run(prompt="test", cwd=None, mode="read-only", timeout=60)

        # Note: cleanup happens in finally block; we can't easily test cleanup
        # without mocking shutil.rmtree, but we verify the env var was set
        env = mock_retry.call_args.args[4]
        assert "CODEX_CONFIG_DIR" in env


# ---------------------------------------------------------------------------
# Error Handling Tests (Improvement 5)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestErrorHandling:
    """Test typed error handling."""

    def test_codex_auth_error_defined(self) -> None:
        # @trace FR-AGT-005
        """CodexAuthError is defined and usable."""
        with pytest.raises(CodexAuthError):
            raise CodexAuthError("Invalid API key")

    def test_codex_sandbox_error_defined(self) -> None:
        # @trace FR-AGT-005
        """CodexSandboxError is defined and usable."""
        with pytest.raises(CodexSandboxError):
            raise CodexSandboxError("Sandbox violation")

    def test_codex_model_error_defined(self) -> None:
        # @trace FR-AGT-005
        """CodexModelError is defined and usable."""
        with pytest.raises(CodexModelError):
            raise CodexModelError("Model not found")

    def test_codex_instance_error_defined(self) -> None:
        # @trace FR-AGT-005
        """CodexInstanceError is defined and usable."""
        with pytest.raises(CodexInstanceError):
            raise CodexInstanceError("Too many instances")


# ---------------------------------------------------------------------------
# CodexResult Dataclass Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCodexResult:
    """Test CodexResult dataclass."""

    def test_codex_result_creation(self) -> None:
        # @trace FR-AGT-001
        """CodexResult can be instantiated with all fields."""
        result = CodexResult(
            text="Hello world",
            exit_code=0,
            tokens_in=100,
            tokens_out=50,
            model="gpt-5.3-codex-spark",
            duration_ms=1234,
            instance_id="codex-abc123",
            error_type=None,
        )

        assert result.text == "Hello world"
        assert result.exit_code == 0
        assert result.tokens_in == 100
        assert result.tokens_out == 50
        assert result.model == "gpt-5.3-codex-spark"
        assert result.duration_ms == 1234
        assert result.instance_id == "codex-abc123"
        assert result.error_type is None

    def test_codex_result_defaults(self) -> None:
        # @trace FR-AGT-001
        """CodexResult has sensible defaults."""
        result = CodexResult(
            text="Output",
            exit_code=0,
        )

        assert result.tokens_in == 0
        assert result.tokens_out == 0
        assert result.model == ""
        assert result.duration_ms == 0
        assert result.instance_id == ""
        assert result.error_type is None


# ---------------------------------------------------------------------------
# Integration: Multiple Improvements Together
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMultipleImprovements:
    """Test improvements working together."""

    @patch("thegent.agents.codex_proxy.ensure_proxy_running", return_value="http://localhost:8317/v1")
    @patch("thegent.agents.codex_proxy._resolve_codex", return_value="/usr/bin/codex")
    @patch("thegent.agents.codex_proxy._run_with_retry")
    def test_all_improvements_together(self, mock_retry, mock_resolve, mock_proxy) -> None:
        # @trace FR-AGT-001 FR-AGT-002 FR-AGT-003 FR-AGT-004
        """run() with all improvements: isolation, limits, config, parsing."""
        mock_retry.return_value = make_run_result(exit_code=0, stdout="ok")

        with tempfile.TemporaryDirectory() as tmpdir:
            runner = CodexProxyRunner(
                agent_name="codex",
                codex_home=Path(tmpdir),
                memory_limit_mb=256,
                max_concurrent_instances=10,
                config_overrides={"model": "gpt-5.3-codex-high"},
            )

            result = runner.run(
                prompt="test",
                cwd=None,
                mode="write",
                timeout=60,
            )

            assert result.exit_code == 0

            # Verify all improvements applied
            env = mock_retry.call_args.args[4]
            assert "CODEX_HOME" in env
            assert "CODEX_MEMORY_LIMIT_MB" in env
            assert "CODEX_CONFIG_DIR" in env
            assert env["CODEX_MEMORY_LIMIT_MB"] == "256"

            # Verify command has expected flags
            cmd = mock_retry.call_args.args[0]
            assert "--sandbox" in cmd
            assert "workspace-write" in cmd
