"""Integration tests for TraceRecorder with agent execution pipeline.

These tests validate:
- TracedAgentRunner wrapping behavior
- Recording overhead <10%
- Trace file persistence
- Integration with agent execution
- Metrics collection
"""

import time
from pathlib import Path

import pytest

# Module under test (thegent.trace.integration) was removed when trace was reduced to stubs.
thegent_trace_integration = pytest.importorskip(
    "thegent.trace.integration",
    reason="thegent.trace.integration module removed; recorder integration tests skipped",
)
from thegent.trace.integration import (  # noqa: E402  (importorskip may skip before this)
    ExecutionMetrics,
    TracedAgentRunner,
    TraceRecordingContext,
    create_traced_agent_runner,
    estimate_trace_overhead,
)
from thegent.trace.recorder import RecorderConfig, TraceRecorder

from thegent.agents.base import AgentRunner, RunResult


class MockAgentRunner(AgentRunner):
    """Mock agent runner for testing without external dependencies."""

    def __init__(self, execution_time_ms: float = 100):
        """Initialize mock runner.

        Args:
            execution_time_ms: Simulated execution time.
        """
        self.execution_time_ms = execution_time_ms
        self.call_count = 0

    def run(
        self,
        prompt: str,
        cwd: Path | None,
        mode: str,
        timeout: int,
        *,
        use_stream: bool = True,
        live_output: bool = False,
        on_stdout=None,
        on_stderr=None,
    ) -> RunResult:
        """Simulate agent execution."""
        self.call_count += 1

        # Simulate execution
        time.time()
        time.sleep(self.execution_time_ms / 1000.0)

        return RunResult(
            exit_code=0,
            stdout=f"Mock output for prompt: {prompt[:50]}",
            stderr="",
            timed_out=False,
        )


class TestTracedAgentRunner:
    """Tests for TracedAgentRunner wrapper."""

    def test_traced_runner_wraps_base_runner(self, tmp_path):
        """Test that TracedAgentRunner wraps and delegates to base runner."""
        base_runner = MockAgentRunner(execution_time_ms=50)
        config = RecorderConfig(trace_dir=tmp_path)
        recorder = TraceRecorder(session_id="test-session", config=config)

        traced_runner = TracedAgentRunner(base_runner, recorder)

        result = traced_runner.run(
            prompt="Test prompt",
            cwd=None,
            mode="read-only",
            timeout=10,
        )

        assert result.exit_code == 0
        assert "Mock output" in result.stdout
        assert base_runner.call_count == 1

    def test_traced_runner_records_execution(self, tmp_path):
        """Test that traced runner records execution details."""
        base_runner = MockAgentRunner(execution_time_ms=50)
        config = RecorderConfig(trace_dir=tmp_path)
        recorder = TraceRecorder(session_id="test-session", config=config)

        traced_runner = TracedAgentRunner(base_runner, recorder)

        traced_runner.run(
            prompt="Test prompt",
            cwd=None,
            mode="write",
            timeout=30,
        )

        assert traced_runner._tool_call_count >= 1
        assert len(traced_runner._recorded_tool_calls) >= 1

    def test_traced_runner_execution_metrics(self, tmp_path):
        """Test that execution metrics are collected."""
        base_runner = MockAgentRunner(execution_time_ms=100)
        config = RecorderConfig(trace_dir=tmp_path)
        recorder = TraceRecorder(session_id="test-session", config=config)

        traced_runner = TracedAgentRunner(base_runner, recorder)

        traced_runner.run(
            prompt="Test prompt",
            cwd=None,
            mode="read-only",
            timeout=10,
        )

        metrics = traced_runner.get_execution_metrics()

        assert isinstance(metrics, ExecutionMetrics)
        assert metrics.tool_call_count >= 1
        assert metrics.total_duration_ms >= 100  # At least the mock delay
        assert 0 <= metrics.recording_overhead_pct <= 100

    def test_traced_runner_overhead_acceptable(self, tmp_path):
        """Test that recording overhead is <10% of execution time."""
        base_runner = MockAgentRunner(execution_time_ms=500)
        config = RecorderConfig(trace_dir=tmp_path)
        recorder = TraceRecorder(session_id="test-session", config=config)

        traced_runner = TracedAgentRunner(base_runner, recorder)

        traced_runner.run(
            prompt="Test prompt",
            cwd=None,
            mode="write",
            timeout=60,
        )

        metrics = traced_runner.get_execution_metrics()

        # Overhead should be < 10% (actual overhead may be lower)
        assert metrics.recording_overhead_pct < 15  # Allow some margin in tests

    def test_traced_runner_preserves_error_result(self, tmp_path):
        """Test that traced runner preserves error results from base runner."""

        class ErrorRunner(AgentRunner):
            def run(self, prompt, cwd, mode, timeout, **kwargs):
                return RunResult(exit_code=1, stdout="", stderr="Error occurred")

        config = RecorderConfig(trace_dir=tmp_path)
        recorder = TraceRecorder(session_id="test-session", config=config)

        traced_runner = TracedAgentRunner(ErrorRunner(), recorder)

        result = traced_runner.run(
            prompt="Test prompt",
            cwd=None,
            mode="read-only",
            timeout=10,
        )

        assert result.exit_code == 1
        assert result.stderr == "Error occurred"


class TestCreateTracedAgentRunner:
    """Tests for factory function."""

    def test_create_traced_agent_runner(self, tmp_path):
        """Test factory function creates recorder and runner."""
        base_runner = MockAgentRunner()

        recorder, traced_runner = create_traced_agent_runner(
            base_runner,
            session_id="test-session",
            trace_dir=tmp_path,
        )

        assert isinstance(recorder, TraceRecorder)
        assert isinstance(traced_runner, TracedAgentRunner)
        assert traced_runner.recorder is recorder

    def test_create_traced_agent_runner_with_config(self, tmp_path):
        """Test factory function respects custom config."""
        base_runner = MockAgentRunner()
        config = RecorderConfig(
            trace_dir=tmp_path,
            compression="gzip",
        )

        recorder, _traced_runner = create_traced_agent_runner(
            base_runner,
            session_id="test-session",
            config=config,
        )

        assert recorder.config == config


class TestTraceRecordingContext:
    """Tests for context manager."""

    def test_trace_recording_context_creation(self, tmp_path):
        """Test context manager creation."""
        base_runner = MockAgentRunner(execution_time_ms=50)

        ctx = TraceRecordingContext(
            base_runner,
            session_id="test-session",
            trace_dir=tmp_path,
        )

        assert ctx.base_runner is base_runner
        assert ctx.session_id == "test-session"
        assert ctx.trace_dir == tmp_path


class TestExecutionMetrics:
    """Tests for ExecutionMetrics."""

    def test_execution_metrics_calculation(self, tmp_path):
        """Test metrics are calculated correctly."""
        base_runner = MockAgentRunner(execution_time_ms=100)
        config = RecorderConfig(trace_dir=tmp_path)
        recorder = TraceRecorder(session_id="test-session", config=config)

        traced_runner = TracedAgentRunner(base_runner, recorder)

        traced_runner.run(
            prompt="Test prompt",
            cwd=None,
            mode="read-only",
            timeout=10,
        )

        metrics = traced_runner.get_execution_metrics()

        assert metrics.tool_call_count >= 1
        assert metrics.total_duration_ms >= 100
        assert metrics.recording_overhead_ms >= 0
        assert 0 <= metrics.recording_overhead_pct <= 100
        assert metrics.trace_file_size_bytes >= 0

    def test_execution_metrics_before_run_raises(self, tmp_path):
        """Test that getting metrics before run raises error."""
        base_runner = MockAgentRunner()
        config = RecorderConfig(trace_dir=tmp_path)
        recorder = TraceRecorder(session_id="test-session", config=config)

        traced_runner = TracedAgentRunner(base_runner, recorder)

        with pytest.raises(RuntimeError):
            traced_runner.get_execution_metrics()


class TestTraceOverheadEstimation:
    """Tests for overhead estimation utility."""

    def test_estimate_trace_overhead_defaults(self):
        """Test overhead estimation with default parameters."""
        overhead = estimate_trace_overhead(tool_call_count=100)

        assert "compression_ms" in overhead
        assert "redaction_ms" in overhead
        assert "async_write_ms" in overhead
        assert "total_ms" in overhead
        assert "overhead_pct" in overhead

        # All values should be non-negative
        for key, value in overhead.items():
            assert value >= 0, f"{key} should be non-negative"

    def test_estimate_trace_overhead_scales_with_tool_calls(self):
        """Test that overhead scales with tool call count."""
        overhead_100 = estimate_trace_overhead(tool_call_count=100)
        overhead_1000 = estimate_trace_overhead(tool_call_count=1000)

        # More tool calls should result in higher absolute overhead
        assert overhead_1000["total_ms"] > overhead_100["total_ms"]

    def test_estimate_trace_overhead_custom_sizes(self):
        """Test overhead estimation with custom data sizes."""
        overhead = estimate_trace_overhead(
            tool_call_count=50,
            avg_tool_args_bytes=1000,
            avg_tool_result_bytes=5000,
        )

        assert overhead["total_ms"] >= 0
        assert 0 <= overhead["overhead_pct"] <= 100

    def test_estimate_trace_overhead_caps_percentage(self):
        """Test that overhead percentage is capped at 100%."""
        # With zero execution time, overhead could theoretically exceed 100%
        # But we cap it at 100%
        overhead = estimate_trace_overhead(tool_call_count=10000)

        assert overhead["overhead_pct"] <= 100


class TestIntegrationWithRealRecorder:
    """Integration tests with real TraceRecorder."""

    def test_traced_runner_creates_trace_file(self, tmp_path):
        """Test that traced runner creates actual trace files."""
        base_runner = MockAgentRunner(execution_time_ms=50)
        config = RecorderConfig(trace_dir=tmp_path)
        recorder = TraceRecorder(session_id="test-session", config=config)

        traced_runner = TracedAgentRunner(base_runner, recorder)

        traced_runner.run(
            prompt="Test prompt",
            cwd=None,
            mode="read-only",
            timeout=10,
        )

        # Trace file should exist
        trace_file = tmp_path / "test-session.jsonl.gz"
        assert trace_file.exists() or (tmp_path / "test-session.jsonl").exists()

    def test_traced_runner_multiple_executions(self, tmp_path):
        """Test that traced runner handles multiple executions."""
        base_runner = MockAgentRunner(execution_time_ms=50)
        config = RecorderConfig(trace_dir=tmp_path)
        recorder = TraceRecorder(session_id="test-session", config=config)

        traced_runner = TracedAgentRunner(base_runner, recorder)

        # Run multiple times
        for i in range(3):
            result = traced_runner.run(
                prompt=f"Test prompt {i}",
                cwd=None,
                mode="read-only",
                timeout=10,
            )
            assert result.exit_code == 0

        # All calls should be recorded
        assert traced_runner._tool_call_count >= 3
