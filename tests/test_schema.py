"""Unit tests for trace schema module."""

import pytest

# Module under test (thegent.trace.schema) was removed when trace was reduced to stubs.
_schema_module = pytest.importorskip(
    "thegent.trace.schema",
    reason="thegent.trace.schema module removed; trace schema tests skipped",
)
from thegent.trace.schema import (  # noqa: E402  (importorskip may skip before this)
    DecisionRecord,
    SessionRecord,
    ToolCallRecord,
    TraceFile,
    TraceRecord,
    validate_record,
)


class TestToolCallRecord:
    """Tests for ToolCallRecord dataclass."""

    def test_create_tool_call_record(self):
        """Test creating a tool call record."""
        record = ToolCallRecord(
            timestamp="2026-02-18T12:00:00Z",
            sequence_id=1,
            tool="bash",
            tool_name="bash",
            args={"command": "ls -la"},
            result={"stdout": "file1\nfile2", "returncode": 0},
            duration_ms=100.5,
        )

        assert record.timestamp == "2026-02-18T12:00:00Z"
        assert record.sequence_id == 1
        assert record.tool == "bash"
        assert record.tool_name == "bash"
        assert record.args["command"] == "ls -la"
        assert record.result["returncode"] == 0
        assert record.duration_ms == 100.5

    def test_tool_call_to_dict(self):
        """Test converting tool call to dictionary."""
        record = ToolCallRecord(
            timestamp="2026-02-18T12:00:00Z",
            sequence_id=1,
            tool="bash",
            tool_name="bash",
            args={"command": "ls"},
            result={"stdout": "", "returncode": 0},
            duration_ms=10.0,
        )

        data = record.to_dict()
        assert data["timestamp"] == "2026-02-18T12:00:00Z"
        assert data["sequence_id"] == 1
        assert data["tool"] == "bash"

    def test_tool_call_from_dict(self):
        """Test constructing tool call from dictionary."""
        data = {
            "timestamp": "2026-02-18T12:00:00Z",
            "sequence_id": 1,
            "tool": "llm",
            "tool_name": "claude",
            "args": {"model": "claude-opus"},
            "result": {"response": "Hello"},
            "duration_ms": 500.0,
        }

        record = ToolCallRecord.from_dict(data)
        assert record.tool == "llm"
        assert record.tool_name == "claude"
        assert record.args["model"] == "claude-opus"

    def test_tool_call_with_error(self):
        """Test tool call with error field."""
        record = ToolCallRecord(
            timestamp="2026-02-18T12:00:00Z",
            sequence_id=1,
            tool="bash",
            tool_name="bash",
            args={"command": "bad command"},
            result={},
            duration_ms=50.0,
            error="Command not found",
        )

        assert record.error == "Command not found"


class TestDecisionRecord:
    """Tests for DecisionRecord dataclass."""

    def test_create_decision_record(self):
        """Test creating a decision record."""
        record = DecisionRecord(
            timestamp="2026-02-18T12:00:00Z",
            sequence_id=1,
            decision_type="model_choice",
            context="Select model for inference",
            selected_value="claude-opus",
        )

        assert record.decision_type == "model_choice"
        assert record.selected_value == "claude-opus"
        assert record.timestamp == "2026-02-18T12:00:00Z"

    def test_decision_with_alternatives(self):
        """Test decision record with alternatives."""
        record = DecisionRecord(
            timestamp="2026-02-18T12:00:00Z",
            sequence_id=1,
            decision_type="routing",
            context="Route to cheapest provider",
            selected_value="gemini-3-flash",
            alternatives=["claude-haiku", "gpt-5-mini"],
            confidence=0.95,
        )

        assert record.alternatives == ["claude-haiku", "gpt-5-mini"]
        assert record.confidence == 0.95


class TestSessionRecord:
    """Tests for SessionRecord dataclass."""

    def test_create_session_record(self):
        """Test creating a session record."""
        record = SessionRecord(
            session_id="sess-123",
            agent_id="agent-1",
            started_at="2026-02-18T12:00:00Z",
        )

        assert record.session_id == "sess-123"
        assert record.agent_id == "agent-1"

    def test_session_with_config(self):
        """Test session record with configuration."""
        record = SessionRecord(
            session_id="sess-123",
            agent_id="agent-1",
            started_at="2026-02-18T12:00:00Z",
            model_versions={"claude": "claude-opus", "gemini": "gemini-3-flash"},
            config={"recording_enabled": True, "compression": "gzip"},
        )

        assert record.model_versions["claude"] == "claude-opus"
        assert record.config["recording_enabled"] is True


class TestTraceRecordUnion:
    """Tests for TraceRecord union type."""

    def test_infer_tool_call_from_dict(self):
        """Test inferring ToolCallRecord from dictionary."""
        data = {
            "timestamp": "2026-02-18T12:00:00Z",
            "sequence_id": 1,
            "tool": "bash",
            "tool_name": "bash",
            "args": {"command": "ls"},
            "result": {"stdout": ""},
            "duration_ms": 10.0,
        }

        record = TraceRecord.from_dict(data)
        assert isinstance(record, ToolCallRecord)
        assert record.tool == "bash"

    def test_infer_decision_from_dict(self):
        """Test inferring DecisionRecord from dictionary."""
        data = {
            "timestamp": "2026-02-18T12:00:00Z",
            "sequence_id": 1,
            "decision_type": "model_choice",
            "context": "Select model",
            "selected_value": "claude-opus",
        }

        record = TraceRecord.from_dict(data)
        assert isinstance(record, DecisionRecord)
        assert record.decision_type == "model_choice"

    def test_infer_session_from_dict(self):
        """Test inferring SessionRecord from dictionary."""
        data = {
            "session_id": "sess-123",
            "agent_id": "agent-1",
            "started_at": "2026-02-18T12:00:00Z",
        }

        record = TraceRecord.from_dict(data)
        assert isinstance(record, SessionRecord)
        assert record.session_id == "sess-123"


class TestTraceFile:
    """Tests for TraceFile reader/writer."""

    def test_write_and_read_records(self, tmp_path):
        """Test writing and reading records from trace file."""
        trace_file = TraceFile(str(tmp_path / "test.jsonl.gz"), compression="gzip")

        # Write records
        session = SessionRecord(
            session_id="sess-1",
            agent_id="agent-1",
            started_at="2026-02-18T12:00:00Z",
        )
        trace_file.write_record(session)

        tool_call = ToolCallRecord(
            timestamp="2026-02-18T12:00:00Z",
            sequence_id=1,
            tool="bash",
            tool_name="bash",
            args={"command": "ls"},
            result={"stdout": "file1", "returncode": 0},
            duration_ms=10.0,
        )
        trace_file.write_record(tool_call)

        # Read records back
        records = trace_file.read_records()
        assert len(records) == 2
        assert isinstance(records[0], SessionRecord)
        assert isinstance(records[1], ToolCallRecord)
        assert records[1].tool == "bash"

    def test_uncompressed_trace_file(self, tmp_path):
        """Test uncompressed trace file."""
        trace_file = TraceFile(str(tmp_path / "test.jsonl"), compression=None)

        record = ToolCallRecord(
            timestamp="2026-02-18T12:00:00Z",
            sequence_id=1,
            tool="bash",
            tool_name="bash",
            args={"command": "echo hello"},
            result={"stdout": "hello", "returncode": 0},
            duration_ms=5.0,
        )
        trace_file.write_record(record)

        records = trace_file.read_records()
        assert len(records) == 1
        assert records[0].result["stdout"] == "hello"

    def test_get_file_size(self, tmp_path):
        """Test getting trace file size."""
        trace_file = TraceFile(str(tmp_path / "test.jsonl.gz"), compression="gzip")

        record = ToolCallRecord(
            timestamp="2026-02-18T12:00:00Z",
            sequence_id=1,
            tool="bash",
            tool_name="bash",
            args={"command": "ls"},
            result={"stdout": ""},
            duration_ms=10.0,
        )
        trace_file.write_record(record)

        size = trace_file.get_file_size()
        assert size > 0

    def test_delete_trace_file(self, tmp_path):
        """Test deleting trace file."""
        path = tmp_path / "test.jsonl"
        trace_file = TraceFile(str(path), compression=None)

        record = ToolCallRecord(
            timestamp="2026-02-18T12:00:00Z",
            sequence_id=1,
            tool="bash",
            tool_name="bash",
            args={"command": "ls"},
            result={"stdout": ""},
            duration_ms=10.0,
        )
        trace_file.write_record(record)
        assert path.exists()

        trace_file.delete()
        assert not path.exists()


class TestValidation:
    """Tests for record validation."""

    def test_validate_valid_tool_call(self):
        """Test validation of valid tool call record."""
        record = ToolCallRecord(
            timestamp="2026-02-18T12:00:00Z",
            sequence_id=1,
            tool="bash",
            tool_name="bash",
            args={"command": "ls"},
            result={"stdout": ""},
            duration_ms=10.0,
        )
        assert validate_record(record) is True

    def test_validate_valid_decision(self):
        """Test validation of valid decision record."""
        record = DecisionRecord(
            timestamp="2026-02-18T12:00:00Z",
            sequence_id=1,
            decision_type="model_choice",
            context="Select model",
            selected_value="claude-opus",
        )
        assert validate_record(record) is True

    def test_validate_valid_session(self):
        """Test validation of valid session record."""
        record = SessionRecord(
            session_id="sess-1",
            agent_id="agent-1",
            started_at="2026-02-18T12:00:00Z",
        )
        assert validate_record(record) is True

    def test_validate_invalid_record(self):
        """Test validation of invalid record."""
        invalid_record = {"invalid": "data"}
        assert validate_record(invalid_record) is False


class TestComplexScenarios:
    """Integration tests with complex scenarios."""

    def test_full_trace_session(self, tmp_path):
        """Test a complete trace session with multiple record types."""
        trace_file = TraceFile(str(tmp_path / "full_session.jsonl.gz"), compression="gzip")

        # Session start
        session = SessionRecord(
            session_id="sess-full-1",
            agent_id="agent-full",
            started_at="2026-02-18T12:00:00Z",
            model_versions={"claude": "claude-opus"},
            config={"recording": True},
        )
        trace_file.write_record(session)

        # Decision: model choice
        decision = DecisionRecord(
            timestamp="2026-02-18T12:00:01Z",
            sequence_id=1,
            decision_type="model_choice",
            context="Route to best model",
            selected_value="claude-opus",
            alternatives=["claude-haiku", "gpt-5"],
            confidence=0.98,
        )
        trace_file.write_record(decision)

        # Tool call: bash
        bash_call = ToolCallRecord(
            timestamp="2026-02-18T12:00:02Z",
            sequence_id=2,
            tool="bash",
            tool_name="bash",
            args={"command": "git status"},
            result={"stdout": "On branch main", "returncode": 0},
            duration_ms=150.0,
        )
        trace_file.write_record(bash_call)

        # Tool call: LLM
        llm_call = ToolCallRecord(
            timestamp="2026-02-18T12:00:03Z",
            sequence_id=3,
            tool="llm",
            tool_name="claude",
            args={"model": "claude-opus", "prompt": "Summarize: ..."},
            result={"response": "Summary: ..."},
            duration_ms=2000.0,
        )
        trace_file.write_record(llm_call)

        # Read and verify
        records = trace_file.read_records()
        assert len(records) == 4
        assert isinstance(records[0], SessionRecord)
        assert isinstance(records[1], DecisionRecord)
        assert isinstance(records[2], ToolCallRecord)
        assert isinstance(records[3], ToolCallRecord)

        # Verify sequence
        tool_records = [r for r in records if isinstance(r, ToolCallRecord)]
        assert tool_records[0].tool == "bash"
        assert tool_records[1].tool == "llm"
