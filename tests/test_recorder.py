"""Unit tests for TraceRecorder."""

import pytest

# Modules under test (thegent.trace.recorder, thegent.trace.schema) were removed when
# trace was reduced to stubs.
_recorder_module = pytest.importorskip(
    "thegent.trace.recorder",
    reason="thegent.trace.recorder module removed; trace recorder tests skipped",
)
_schema_module = pytest.importorskip(
    "thegent.trace.schema",
    reason="thegent.trace.schema module removed; trace schema tests skipped",
)
from datetime import UTC

from thegent.trace.recorder import (  # noqa: E402  (importorskip may skip before this)
    RecorderConfig,
    RedactionConfig,
    TraceCleanup,
    TraceRecorder,
)
from thegent.trace.schema import ToolCallRecord  # noqa: E402


class TestRedactionConfig:
    """Tests for RedactionConfig."""

    def test_default_redaction_config(self):
        """Test default redaction configuration."""
        config = RedactionConfig()
        assert config.enabled is True
        assert config.replace_with == "[REDACTED]"
        assert "api_key" in config.fields_to_always_redact
        assert "password" in config.fields_to_always_redact


class TestTraceRecorder:
    """Tests for TraceRecorder class."""

    @pytest.fixture
    def temp_trace_dir(self, tmp_path):
        """Create temporary trace directory."""
        trace_dir = tmp_path / "traces"
        trace_dir.mkdir()
        return str(trace_dir)

    @pytest.fixture
    def recorder(self, temp_trace_dir):
        """Create test recorder."""
        config = RecorderConfig(
            trace_dir=temp_trace_dir,
            async_write=False,  # Sync for testing
        )
        return TraceRecorder("sess-test-1", config)

    def test_recorder_initialization(self, recorder):
        """Test recorder initialization."""
        assert recorder.session_id == "sess-test-1"
        assert recorder.config is not None
        assert recorder.config.redaction.enabled is True

    @pytest.mark.asyncio
    async def test_record_tool_call(self, recorder):
        """Test recording a tool call."""
        await recorder.record_tool_call(
            tool="bash",
            tool_name="bash",
            args={"command": "echo hello"},
            result={"stdout": "hello", "returncode": 0},
            duration_ms=10.0,
        )

        # Verify file was written
        size = recorder.get_trace_file_size()
        assert size > 0

    @pytest.mark.asyncio
    async def test_record_decision(self, recorder):
        """Test recording a decision."""
        await recorder.record_decision(
            decision_type="model_choice",
            context="Select model for inference",
            selected_value="claude-opus",
        )

        size = recorder.get_trace_file_size()
        assert size > 0

    def test_redact_api_key(self, recorder):
        """Test redaction of API key."""
        data = {
            "model": "claude-opus",
            "api_key": "sk-1234567890",
        }

        redacted = recorder._redact_data(data)
        assert redacted["model"] == "claude-opus"
        assert redacted["api_key"] == "[REDACTED]"

    def test_redact_password(self, recorder):
        """Test redaction of password field."""
        data = {
            "username": "user@example.com",
            "password": "secret123",
        }

        redacted = recorder._redact_data(data)
        assert redacted["username"] == "user@example.com"
        assert redacted["password"] == "[REDACTED]"

    def test_redact_nested_data(self, recorder):
        """Test redaction of nested sensitive data."""
        data = {
            "config": {
                "api_key": "secret",
                "model": "claude-opus",
            }
        }

        redacted = recorder._redact_data(data)
        assert redacted["config"]["api_key"] == "[REDACTED]"
        assert redacted["config"]["model"] == "claude-opus"

    def test_is_sensitive_field(self, recorder):
        """Test sensitive field detection."""
        assert recorder._is_sensitive_field("api_key") is True
        assert recorder._is_sensitive_field("API_KEY") is True
        assert recorder._is_sensitive_field("token") is True
        assert recorder._is_sensitive_field("password") is True
        assert recorder._is_sensitive_field("model") is False
        assert recorder._is_sensitive_field("command") is False

    def test_find_redacted_fields(self, recorder):
        """Test finding which fields were redacted."""
        original = {
            "api_key": "secret",
            "model": "claude",
            "nested": {
                "password": "pass123",
            },
        }

        redacted_fields = recorder._find_redacted_fields(original)
        assert "api_key" in redacted_fields
        assert "nested.password" in redacted_fields
        assert "model" not in redacted_fields

    def test_truncate_result_large_output(self, recorder):
        """Test truncation of large result."""
        large_output = "x" * (50 * 1024 * 1024)  # 50MB
        result = {"stdout": large_output}

        truncated = recorder._truncate_result(result)
        assert "truncated" in truncated["stdout"]
        assert len(truncated["stdout"]) < len(large_output)
        assert "stdout_truncated_original_size" in truncated

    @pytest.mark.asyncio
    async def test_async_start_stop(self, temp_trace_dir):
        """Test async start and stop."""
        config = RecorderConfig(
            trace_dir=temp_trace_dir,
            async_write=True,
        )
        recorder = TraceRecorder("sess-async-1", config)

        await recorder.start()
        assert recorder.running is True

        # Record something
        await recorder.record_tool_call(
            tool="bash",
            tool_name="bash",
            args={"command": "ls"},
            result={"stdout": "file1", "returncode": 0},
            duration_ms=10.0,
        )

        await recorder.stop()
        assert recorder.running is False

    def test_get_trace_file_size(self, recorder):
        """Test getting trace file size."""
        size_before = recorder.get_trace_file_size()

        # Write a record synchronously
        record = ToolCallRecord(
            timestamp="2026-02-18T12:00:00Z",
            sequence_id=1,
            tool="bash",
            tool_name="bash",
            args={"command": "echo hello"},
            result={"stdout": "hello"},
            duration_ms=10.0,
        )
        recorder.trace_file.write_record(record)

        size_after = recorder.get_trace_file_size()
        assert size_after > size_before

    def test_delete_trace(self, recorder):
        """Test deleting trace file."""
        # Write a record
        record = ToolCallRecord(
            timestamp="2026-02-18T12:00:00Z",
            sequence_id=1,
            tool="bash",
            tool_name="bash",
            args={"command": "ls"},
            result={"stdout": ""},
            duration_ms=10.0,
        )
        recorder.trace_file.write_record(record)

        assert recorder.trace_file.path.exists()

        recorder.delete_trace()
        assert not recorder.trace_file.path.exists()


class TestTraceCleanup:
    """Tests for TraceCleanup class."""

    def test_cleanup_initialization(self, tmp_path):
        """Test cleanup initialization."""
        cleanup = TraceCleanup(str(tmp_path), ttl_days=7)
        assert cleanup.ttl_days == 7

    @pytest.mark.asyncio
    async def test_cleanup_nonexistent_dir(self, tmp_path):
        """Test cleanup with nonexistent directory."""
        cleanup = TraceCleanup(str(tmp_path / "nonexistent"), ttl_days=7)
        deleted = await cleanup.cleanup_expired_traces()
        assert deleted == 0

    @pytest.mark.asyncio
    async def test_cleanup_recent_traces(self, tmp_path):
        """Test that recent traces are not deleted."""
        cleanup = TraceCleanup(str(tmp_path), ttl_days=7)

        # Create a recent trace file
        trace_file = tmp_path / "recent.jsonl.gz"
        trace_file.write_text("test")

        deleted = await cleanup.cleanup_expired_traces()
        assert deleted == 0
        assert trace_file.exists()

    @pytest.mark.asyncio
    async def test_cleanup_expired_traces(self, tmp_path):
        """Test that expired traces are deleted."""
        from datetime import datetime, timedelta

        cleanup = TraceCleanup(str(tmp_path), ttl_days=7)

        # Create an old trace file (simulate old mtime)
        trace_file = tmp_path / "old.jsonl.gz"
        trace_file.write_text("test")

        # Set mtime to 10 days ago
        old_time = (datetime.now(UTC) - timedelta(days=10)).timestamp()
        import os

        os.utime(trace_file, (old_time, old_time))

        deleted = await cleanup.cleanup_expired_traces()
        assert deleted == 1
        assert not trace_file.exists()


class TestRecorderIntegration:
    """Integration tests for recorder."""

    @pytest.mark.asyncio
    async def test_full_recording_session(self, tmp_path):
        """Test a complete recording session."""
        config = RecorderConfig(
            trace_dir=str(tmp_path),
            async_write=False,  # Sync for determinism in testing
        )
        recorder = TraceRecorder("sess-integration-1", config)

        # Record multiple events
        await recorder.record_tool_call(
            tool="bash",
            tool_name="bash",
            args={"command": "git status"},
            result={"stdout": "On branch main", "returncode": 0},
            duration_ms=150.0,
        )

        await recorder.record_decision(
            decision_type="model_choice",
            context="Route to best model",
            selected_value="claude-opus",
            alternatives=["claude-haiku", "gpt-5"],
            confidence=0.95,
        )

        await recorder.record_tool_call(
            tool="llm",
            tool_name="claude",
            args={
                "model": "claude-opus",
                "api_key": "sk-secret123",  # Should be redacted
                "prompt": "Summarize git status",
            },
            result={"response": "Summary: on branch main"},
            duration_ms=2000.0,
        )

        # Verify file size
        size = recorder.get_trace_file_size()
        assert size > 0

        # Read traces back
        traces = recorder.trace_file.read_records()
        assert len(traces) == 3

        # Verify redaction occurred
        tool_records = [t for t in traces if isinstance(t, ToolCallRecord)]
        assert tool_records[1].args["api_key"] == "[REDACTED]"
        assert "api_key" in tool_records[1].redacted_fields
