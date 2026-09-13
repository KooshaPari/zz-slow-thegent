"""Tests for InterAgentProtocol message schemas.

@trace FR-PROTO-001 -- SubAgentRequest model creation and validation.
@trace FR-PROTO-002 -- SubAgentResult model creation and validation.
@trace FR-PROTO-003 -- SubAgentEvent model creation and validation.
@trace FR-PROTO-004 -- JSONL serialization/deserialization roundtrip.
@trace FR-PROTO-005 -- SubAgentProtocolSerializer file operations.
@trace FR-PROTO-006 -- Event factory methods.
@trace FR-PROTO-007 -- Status property checks (is_success, is_terminal).
@trace FR-PROTO-008 -- Request context updates.
@trace FR-PROTO-009 -- Field validation and constraints.
@trace FR-PROTO-010 -- Event sequence ordering.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import orjson as json
import pytest

from thegent.orchestration.protocol import (
    SubAgentEvent,
    SubAgentEventType,
    SubAgentProtocolSerializer,
    SubAgentRequest,
    SubAgentResult,
    SubAgentStatus,
)

# =============================================================================
# SubAgentRequest Tests
# =============================================================================


class TestSubAgentRequest:
    """Unit tests for SubAgentRequest model. @trace FR-PROTO-001"""

    def test_default_creation(self) -> None:
        """Test creating a request with defaults."""
        req = SubAgentRequest(agent_type="codex", task="Implement feature X")
        assert req.agent_type == "codex"
        assert req.task == "Implement feature X"
        assert req.request_id.startswith("req_")
        assert req.timeout_seconds == 300
        assert req.priority == 10
        assert req.context == {}
        assert req.capabilities == []
        assert req.metadata == {}

    def test_custom_fields(self) -> None:
        """Test creating a request with custom fields."""
        req = SubAgentRequest(
            request_id="req_123",
            parent_id="parent_456",
            agent_type="claude",
            task="Fix bug Y",
            context={"file": "src/main.py"},
            timeout_seconds=600,
            priority=5,
            capabilities=["python", "refactor"],
            metadata={"source": "workflow"},
        )
        assert req.request_id == "req_123"
        assert req.parent_id == "parent_456"
        assert req.agent_type == "claude"
        assert req.task == "Fix bug Y"
        assert req.context == {"file": "src/main.py"}
        assert req.timeout_seconds == 600
        assert req.priority == 5
        assert req.capabilities == ["python", "refactor"]
        assert req.metadata == {"source": "workflow"}

    def test_timeout_validation_min(self) -> None:
        """Test timeout_seconds minimum validation."""
        with pytest.raises(ValueError):
            SubAgentRequest(agent_type="test", task="test", timeout_seconds=0)

    def test_timeout_validation_max(self) -> None:
        """Test timeout_seconds maximum validation."""
        with pytest.raises(ValueError):
            SubAgentRequest(agent_type="test", task="test", timeout_seconds=4000)

    def test_priority_validation_min(self) -> None:
        """Test priority minimum validation."""
        with pytest.raises(ValueError):
            SubAgentRequest(agent_type="test", task="test", priority=-1)

    def test_priority_validation_max(self) -> None:
        """Test priority maximum validation."""
        with pytest.raises(ValueError):
            SubAgentRequest(agent_type="test", task="test", priority=101)

    def test_with_updated_context(self) -> None:
        """Test creating copy with updated context."""
        req = SubAgentRequest(
            agent_type="test",
            task="test",
            context={"key1": "value1"},
        )
        updated = req.with_updated_context({"key2": "value2"})
        assert updated.context == {"key1": "value1", "key2": "value2"}
        # Original unchanged
        assert req.context == {"key1": "value1"}


class TestSubAgentRequestJsonl:
    """JSONL serialization tests for SubAgentRequest. @trace FR-PROTO-004"""

    def test_to_jsonl(self) -> None:
        """Test serialization to JSONL."""
        req = SubAgentRequest(
            request_id="req_test",
            agent_type="codex",
            task="Run tests",
        )
        jsonl = req.to_jsonl()
        # Should end with newline
        assert jsonl.endswith("\n")
        # Should be valid JSON
        data = json.loads(jsonl.strip())
        assert data["request_id"] == "req_test"
        assert data["agent_type"] == "codex"
        assert data["task"] == "Run tests"

    def test_from_jsonl(self) -> None:
        """Test deserialization from JSONL."""
        original = SubAgentRequest(
            request_id="req_test",
            agent_type="claude",
            task="Analyze code",
            priority=20,
        )
        jsonl = original.to_jsonl()
        restored = SubAgentRequest.from_jsonl(jsonl)
        assert restored.request_id == original.request_id
        assert restored.agent_type == original.agent_type
        assert restored.task == original.task
        assert restored.priority == original.priority

    def test_roundtrip(self) -> None:
        """Test complete roundtrip serialization."""
        original = SubAgentRequest(
            request_id="req_abc",
            parent_id="parent_xyz",
            agent_type="droid",
            task="Deploy service",
            context={"env": "prod"},
            timeout_seconds=120,
            priority=15,
            capabilities=["docker", "k8s"],
            metadata={"version": "1.0.0"},
        )
        jsonl = original.to_jsonl()
        restored = SubAgentRequest.from_jsonl(jsonl)
        assert restored.model_dump() == original.model_dump()


# =============================================================================
# SubAgentResult Tests
# =============================================================================


class TestSubAgentResult:
    """Unit tests for SubAgentResult model. @trace FR-PROTO-002"""

    def test_default_creation(self) -> None:
        """Test creating a result with defaults."""
        res = SubAgentResult(
            request_id="req_123",
            agent_type="codex",
            status=SubAgentStatus.COMPLETED,
        )
        assert res.request_id == "req_123"
        assert res.agent_type == "codex"
        assert res.status == SubAgentStatus.COMPLETED
        assert res.result_id.startswith("res_")
        assert res.output == {}
        assert res.error is None
        assert res.metrics == {}
        assert res.artifacts == []

    def test_custom_fields(self) -> None:
        """Test creating a result with custom fields."""
        res = SubAgentResult(
            request_id="req_456",
            result_id="res_789",
            parent_id="parent_abc",
            agent_type="claude",
            status=SubAgentStatus.FAILED,
            output={"files_changed": 5},
            error="Compilation failed",
            metrics={"duration_seconds": 45.2, "tokens": 12000},
            artifacts=[{"type": "file", "path": "output.log"}],
            metadata={"exit_code": 1},
        )
        assert res.result_id == "res_789"
        assert res.parent_id == "parent_abc"
        assert res.status == SubAgentStatus.FAILED
        assert res.error == "Compilation failed"
        assert res.metrics["duration_seconds"] == 45.2

    def test_is_success_completed(self) -> None:
        """Test is_success property for completed status."""
        res = SubAgentResult(
            request_id="req_test",
            agent_type="test",
            status=SubAgentStatus.COMPLETED,
        )
        assert res.is_success is True

    def test_is_success_failed(self) -> None:
        """Test is_success property for failed status."""
        res = SubAgentResult(
            request_id="req_test",
            agent_type="test",
            status=SubAgentStatus.FAILED,
        )
        assert res.is_success is False

    def test_is_terminal_completed(self) -> None:
        """Test is_terminal property for completed status."""
        res = SubAgentResult(
            request_id="req_test",
            agent_type="test",
            status=SubAgentStatus.COMPLETED,
        )
        assert res.is_terminal is True

    def test_is_terminal_running(self) -> None:
        """Test is_terminal property for running status."""
        res = SubAgentResult(
            request_id="req_test",
            agent_type="test",
            status=SubAgentStatus.RUNNING,
        )
        assert res.is_terminal is False

    def test_is_terminal_all_terminal_states(self) -> None:
        """Test is_terminal for all terminal states."""
        terminal_statuses = [
            SubAgentStatus.COMPLETED,
            SubAgentStatus.FAILED,
            SubAgentStatus.CANCELLED,
            SubAgentStatus.TIMEOUT,
        ]
        for status in terminal_statuses:
            res = SubAgentResult(
                request_id="req_test",
                agent_type="test",
                status=status,
            )
            assert res.is_terminal is True, f"Expected {status} to be terminal"

    def test_with_error(self) -> None:
        """Test creating copy with error."""
        res = SubAgentResult(
            request_id="req_test",
            agent_type="test",
            status=SubAgentStatus.RUNNING,
        )
        error_res = res.with_error("Something went wrong")
        assert error_res.status == SubAgentStatus.FAILED
        assert error_res.error == "Something went wrong"


class TestSubAgentResultJsonl:
    """JSONL serialization tests for SubAgentResult. @trace FR-PROTO-004"""

    def test_to_jsonl(self) -> None:
        """Test serialization to JSONL."""
        res = SubAgentResult(
            request_id="req_test",
            agent_type="codex",
            status=SubAgentStatus.COMPLETED,
            output={"result": "success"},
        )
        jsonl = res.to_jsonl()
        assert jsonl.endswith("\n")
        data = json.loads(jsonl.strip())
        assert data["request_id"] == "req_test"
        assert data["status"] == "completed"

    def test_from_jsonl(self) -> None:
        """Test deserialization from JSONL."""
        original = SubAgentResult(
            request_id="req_xyz",
            agent_type="claude",
            status=SubAgentStatus.FAILED,
            error="Test error",
        )
        jsonl = original.to_jsonl()
        restored = SubAgentResult.from_jsonl(jsonl)
        assert restored.request_id == original.request_id
        assert restored.status == original.status
        assert restored.error == original.error


# =============================================================================
# SubAgentEvent Tests
# =============================================================================


class TestSubAgentEvent:
    """Unit tests for SubAgentEvent model. @trace FR-PROTO-003"""

    def test_default_creation(self) -> None:
        """Test creating an event with defaults."""
        evt = SubAgentEvent(
            request_id="req_123",
            event_type=SubAgentEventType.STARTED,
        )
        assert evt.request_id == "req_123"
        assert evt.event_type == SubAgentEventType.STARTED
        assert evt.event_id.startswith("evt_")
        assert evt.payload == {}
        assert evt.message is None
        assert evt.severity == "info"
        assert evt.sequence == 0

    def test_custom_fields(self) -> None:
        """Test creating an event with custom fields."""
        evt = SubAgentEvent(
            event_id="evt_custom",
            request_id="req_456",
            parent_id="parent_abc",
            event_type=SubAgentEventType.TOOL_USE,
            payload={"tool": "grep", "pattern": "*.py"},
            message="Running grep",
            severity="debug",
            sequence=5,
        )
        assert evt.event_id == "evt_custom"
        assert evt.parent_id == "parent_abc"
        assert evt.event_type == SubAgentEventType.TOOL_USE
        assert evt.payload["tool"] == "grep"
        assert evt.severity == "debug"
        assert evt.sequence == 5


class TestSubAgentEventFactory:
    """Factory method tests for SubAgentEvent. @trace FR-PROTO-006"""

    def test_create_start(self) -> None:
        """Test STARTED event factory."""
        evt = SubAgentEvent.create_start(
            request_id="req_123",
            parent_id="parent_456",
            agent_type="codex",
        )
        assert evt.event_type == SubAgentEventType.STARTED
        assert evt.request_id == "req_123"
        assert evt.parent_id == "parent_456"
        assert evt.payload["agent_type"] == "codex"
        assert "started" in evt.message.lower()

    def test_create_progress(self) -> None:
        """Test PROGRESS event factory."""
        evt = SubAgentEvent.create_progress(
            request_id="req_123",
            progress=0.5,
        )
        assert evt.event_type == SubAgentEventType.PROGRESS
        assert evt.request_id == "req_123"
        assert evt.payload["progress"] == 0.5

    def test_create_progress_with_message(self) -> None:
        """Test PROGRESS event factory with custom message."""
        evt = SubAgentEvent.create_progress(
            request_id="req_123",
            progress=0.75,
            message="Analyzing files...",
        )
        assert evt.message == "Analyzing files..."

    def test_create_tool_use(self) -> None:
        """Test TOOL_USE event factory."""
        evt = SubAgentEvent.create_tool_use(
            request_id="req_123",
            tool_name="read_file",
            tool_input={"path": "main.py"},
        )
        assert evt.event_type == SubAgentEventType.TOOL_USE
        assert evt.payload["tool_name"] == "read_file"
        assert evt.payload["tool_input"] == {"path": "main.py"}

    def test_create_error(self) -> None:
        """Test ERROR event factory."""
        evt = SubAgentEvent.create_error(
            request_id="req_123",
            error="Connection timeout",
        )
        assert evt.event_type == SubAgentEventType.ERROR
        assert evt.payload["error"] == "Connection timeout"
        assert evt.severity == "error"

    def test_create_completed(self) -> None:
        """Test COMPLETED event factory."""
        evt = SubAgentEvent.create_completed(
            request_id="req_123",
            output={"files_created": 3},
        )
        assert evt.event_type == SubAgentEventType.COMPLETED
        assert evt.payload["output"] == {"files_created": 3}


class TestSubAgentEventJsonl:
    """JSONL serialization tests for SubAgentEvent. @trace FR-PROTO-004"""

    def test_to_jsonl(self) -> None:
        """Test serialization to JSONL."""
        evt = SubAgentEvent(
            request_id="req_test",
            event_type=SubAgentEventType.PROGRESS,
            payload={"progress": 0.25},
        )
        jsonl = evt.to_jsonl()
        assert jsonl.endswith("\n")
        data = json.loads(jsonl.strip())
        assert data["request_id"] == "req_test"
        assert data["event_type"] == "progress"

    def test_roundtrip(self) -> None:
        """Test complete roundtrip serialization."""
        original = SubAgentEvent(
            request_id="req_abc",
            parent_id="parent_xyz",
            event_type=SubAgentEventType.TOOL_USE,
            payload={"tool": "grep", "count": 42},
            message="Found 42 matches",
            severity="debug",
            sequence=10,
        )
        jsonl = original.to_jsonl()
        restored = SubAgentEvent.from_jsonl(jsonl)
        assert restored.model_dump() == original.model_dump()


# =============================================================================
# SubAgentProtocolSerializer Tests
# =============================================================================


class TestSubAgentProtocolSerializer:
    """Tests for SubAgentProtocolSerializer. @trace FR-PROTO-005"""

    def test_write_and_read_requests(self) -> None:
        """Test writing and reading requests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "requests.jsonl"
            req = SubAgentRequest(agent_type="test", task="test task")
            SubAgentProtocolSerializer.write_request(req, path)

            requests = SubAgentProtocolSerializer.read_requests(path)
            assert len(requests) == 1
            assert requests[0].agent_type == "test"

    def test_write_and_read_results(self) -> None:
        """Test writing and reading results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "results.jsonl"
            res = SubAgentResult(
                request_id="req_123",
                agent_type="test",
                status=SubAgentStatus.COMPLETED,
            )
            SubAgentProtocolSerializer.write_result(res, path)

            results = SubAgentProtocolSerializer.read_results(path)
            assert len(results) == 1
            assert results[0].status == SubAgentStatus.COMPLETED

    def test_write_and_read_events(self) -> None:
        """Test writing and reading events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "events.jsonl"
            evt = SubAgentEvent(
                request_id="req_123",
                event_type=SubAgentEventType.STARTED,
            )
            SubAgentProtocolSerializer.write_event(evt, path)

            events = SubAgentProtocolSerializer.read_events(path)
            assert len(events) == 1
            assert events[0].event_type == SubAgentEventType.STARTED

    def test_read_nonexistent_file(self) -> None:
        """Test reading from nonexistent file returns empty list."""
        path = Path("/nonexistent/file.jsonl")
        assert SubAgentProtocolSerializer.read_requests(path) == []
        assert SubAgentProtocolSerializer.read_results(path) == []
        assert SubAgentProtocolSerializer.read_events(path) == []

    def test_filter_events_by_request(self) -> None:
        """Test filtering events by request ID."""
        events = [
            SubAgentEvent(request_id="req_1", event_type=SubAgentEventType.STARTED, sequence=1),
            SubAgentEvent(request_id="req_2", event_type=SubAgentEventType.STARTED, sequence=1),
            SubAgentEvent(request_id="req_1", event_type=SubAgentEventType.PROGRESS, sequence=2),
            SubAgentEvent(request_id="req_1", event_type=SubAgentEventType.COMPLETED, sequence=3),
        ]
        filtered = SubAgentProtocolSerializer.filter_events_by_request(events, "req_1")
        assert len(filtered) == 3
        # Check sequence ordering
        assert filtered[0].sequence == 1
        assert filtered[1].sequence == 2
        assert filtered[2].sequence == 3

    def test_filter_events_preserves_order(self) -> None:
        """Test that filter maintains sequence order."""
        events = [
            SubAgentEvent(request_id="req_x", event_type=SubAgentEventType.STARTED, sequence=10),
            SubAgentEvent(request_id="req_x", event_type=SubAgentEventType.PROGRESS, sequence=5),
            SubAgentEvent(request_id="req_x", event_type=SubAgentEventType.COMPLETED, sequence=20),
        ]
        filtered = SubAgentProtocolSerializer.filter_events_by_request(events, "req_x")
        # Should be sorted by sequence
        assert filtered[0].sequence == 5
        assert filtered[1].sequence == 10
        assert filtered[2].sequence == 20


class TestStatusEnumValues:
    """Test enum values. @trace FR-PROTO-007"""

    def test_sub_agent_status_values(self) -> None:
        """Verify SubAgentStatus enum values."""
        assert SubAgentStatus.PENDING == "pending"
        assert SubAgentStatus.RUNNING == "running"
        assert SubAgentStatus.COMPLETED == "completed"
        assert SubAgentStatus.FAILED == "failed"
        assert SubAgentStatus.CANCELLED == "cancelled"
        assert SubAgentStatus.TIMEOUT == "timeout"

    def test_sub_agent_event_type_values(self) -> None:
        """Verify SubAgentEventType enum values."""
        assert SubAgentEventType.STARTED == "started"
        assert SubAgentEventType.PROGRESS == "progress"
        assert SubAgentEventType.TOOL_USE == "tool_use"
        assert SubAgentEventType.MESSAGE == "message"
        assert SubAgentEventType.ERROR == "error"
        assert SubAgentEventType.COMPLETED == "completed"
        assert SubAgentEventType.HEARTBEAT == "heartbeat"
        assert SubAgentEventType.CANCELLED == "cancelled"
