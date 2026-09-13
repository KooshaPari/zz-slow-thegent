"""Chaos and fault-injection tests for MCP tools and execution (G-FM-05).

Scenarios: timeout mid-run, circuit breaker, corrupt session file, input guardrails.
"""

import os
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import orjson as json
import pytest

from thegent.agents.base import RunResult
from thegent.cli.commands.impl import logs_impl, ps_impl, run_impl, status_impl
from thegent.execution import CircuitBreakerRegistry


@pytest.mark.integration
@pytest.mark.skip(reason="Missing get_runner function")
class TestRunTimeout:
    """Timeout mid-run: mock runner sleeps; assert timed_out and exit_code."""

    def test_run_returns_timed_out_when_runner_times_out(self, tmp_path: Path) -> None:
        # @trace FR-MCP-001
        """run_impl returns timed_out=True when runner reports timeout."""
        with patch("thegent.cli.commands.impl.get_runner") as mock_get_runner:
            mock_runner = mock_get_runner.return_value
            mock_runner.run.return_value = RunResult(
                exit_code=124,
                stdout="",
                stderr="timeout",
                timed_out=True,
            )
            with patch("thegent.cli.commands.impl._resolve_cwd", return_value=tmp_path):
                result = run_impl(
                    agent="gemini",
                    prompt="test",
                    cd=tmp_path,
                    timeout=5,
                )
        assert result.get("timed_out") is True or result.get("status") == "timed_out"
        assert result.get("exit_code") != 0

    def test_run_with_slow_mock_returns_within_timeout(self, tmp_path: Path) -> None:
        # @trace FR-MCP-001
        """run_impl with fast mock returns quickly (sanity)."""
        with patch("thegent.cli.commands.impl.get_runner") as mock_get_runner:
            mock_runner = mock_get_runner.return_value
            mock_runner.run.return_value = RunResult(
                exit_code=0,
                stdout="<STATUS>completed</STATUS>",
                stderr="",
                timed_out=False,
            )
            with patch("thegent.cli.commands.impl._resolve_cwd", return_value=tmp_path):
                start = time.perf_counter()
                result = run_impl(
                    agent="gemini",
                    prompt="test",
                    cd=tmp_path,
                    timeout=90,
                )
                elapsed = time.perf_counter() - start
        assert elapsed < 5.0
        assert result.get("exit_code") == 0


@pytest.mark.integration
class TestCircuitBreaker:
    """Circuit breaker: 6 failures -> is_open; half-open after recovery."""

    def test_circuit_opens_after_threshold_failures(self, tmp_path: Path) -> None:
        # @trace FR-MCP-001
        """CircuitBreakerRegistry.is_open returns True after threshold failures."""
        cb = CircuitBreakerRegistry(tmp_path, threshold=2, window_s=300, recovery_s=60)
        cb.record_failure("gemini")
        cb.record_failure("gemini")
        assert cb.is_open("gemini") is True

    def test_circuit_closed_below_threshold(self, tmp_path: Path) -> None:
        # @trace FR-MCP-001
        """CircuitBreakerRegistry.is_open returns False below threshold."""
        cb = CircuitBreakerRegistry(tmp_path, threshold=3, window_s=300, recovery_s=60)
        cb.record_failure("gemini")
        assert cb.is_open("gemini") is False

    def test_circuit_half_open_after_recovery(self, tmp_path: Path) -> None:
        # @trace FR-MCP-001
        """After recovery_s, circuit allows trial (half-open)."""
        cb = CircuitBreakerRegistry(tmp_path, threshold=2, window_s=300, recovery_s=0)
        cb.record_failure("gemini")
        cb.record_failure("gemini")
        # With recovery_s=0, last failure is immediately "recovered"
        # Implementation: if last_failure and (now - last_failure) > recovery_s -> return False
        # So we need failures older than recovery_s. Write manual events.
        registry = tmp_path / "circuit_breakers.jsonl"
        tmp_path.mkdir(parents=True, exist_ok=True)
        old_ts = datetime.now(UTC)
        from datetime import timedelta

        old_ts = old_ts - timedelta(seconds=70)
        for _ in range(2):
            event = {
                "target": "gemini",
                "category": "agent",
                "event": "failure",
                "timestamp": old_ts.isoformat(),
            }
            with registry.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event).decode() + "\n")
        assert cb.is_open("gemini") is False


@pytest.mark.integration
class TestCorruptSession:
    """Corrupt session file: status/logs degrade gracefully."""

    def test_status_handles_nonexistent_session(self) -> None:
        # @trace FR-MCP-001
        """status_impl returns error for nonexistent session."""
        result = status_impl("nonexistent-session-xyz-123")
        assert isinstance(result, dict)
        assert "error" in result or "session_id" in result

    def test_logs_handles_nonexistent_session(self) -> None:
        # @trace FR-MCP-001
        """logs_impl returns error string for nonexistent session."""
        result = logs_impl("nonexistent-session-xyz-123")
        assert isinstance(result, str)
        assert "error" in result.lower() or "not found" in result.lower()

    def test_ps_skips_corrupt_session_meta(self, tmp_path: Path) -> None:
        # @trace FR-MCP-001
        """ps_impl skips corrupt JSON meta files; returns list without crashing."""
        from thegent.cli.commands.impl import _scope_key

        scope_dir = tmp_path / _scope_key("user:test")
        scope_dir.mkdir(parents=True)
        (scope_dir / "corrupt-session.json").write_text("not valid json {{{")
        with patch("thegent.cli.commands.impl.ThegentSettings") as mock_settings:
            inst = mock_settings.return_value
            inst.session_dir = tmp_path
            inst.retention_days_sessions = 7
            result = ps_impl(owner="user:test")
        assert isinstance(result, list)
        assert len(result) == 0


@pytest.mark.integration
@pytest.mark.skip(reason="Missing implementation")
class TestInputGuardrailsIntegration:
    """Input guardrails (G-GP-02) integration with run_impl."""

    def test_run_impl_guardrail_blocks_when_enabled(self, tmp_path: Path) -> None:
        # @trace FR-MCP-001
        """When THGENT_INPUT_GUARDRAILS_ENABLED=1 and agent not in allowlist, run_impl returns error."""
        with patch.dict(
            os.environ, {"THGENT_INPUT_GUARDRAILS_ENABLED": "1", "THGENT_AGENT_ALLOWLIST": "gemini,claude"}, clear=False
        ):
            result = run_impl(
                agent="unknown-agent",
                prompt="test",
                cd=tmp_path,
            )
        assert "error" in result
        assert "guardrail" in result["error"].lower() or "allowlist" in result["error"].lower()
        assert result.get("exit_code") == 1
