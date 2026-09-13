"""Tests for GW-67: Agent-to-Agent (A2A) protocol support.

# @trace FR-PROTO-067
"""

from __future__ import annotations

import orjson as json
import pytest

from thegent.protocols.a2a import (
    A2AMessage,
    A2ARouter,
    a2a_message_from_dict,
    a2a_message_to_dict,
    create_response,
    validate_a2a_message,
)


@pytest.mark.requirement("FR-PROTO-067")
class TestA2AMessage:
    def test_create_a2a_message(self) -> None:
        """A2AMessage has auto-generated id and timestamp."""
        msg = A2AMessage(
            source_agent="agent-A",
            target_agent="agent-B",
            message_type="request",
            payload={"text": "hello"},
        )
        assert msg.id  # non-empty auto-generated UUID
        assert msg.timestamp > 0.0
        assert msg.correlation_id == ""
        assert msg.metadata == {}

    def test_validate_valid_message(self) -> None:
        """Valid message returns empty error list."""
        msg = A2AMessage(
            source_agent="agent-A",
            target_agent="agent-B",
            message_type="request",
            payload={"q": "test"},
        )
        errors = validate_a2a_message(msg)
        assert errors == []

    def test_validate_empty_source_agent(self) -> None:
        """Empty source_agent produces a validation error."""
        msg = A2AMessage(
            source_agent="",
            target_agent="agent-B",
            message_type="request",
            payload={},
        )
        errors = validate_a2a_message(msg)
        assert any("source_agent" in e for e in errors)

    def test_validate_invalid_message_type(self) -> None:
        """Unknown message_type produces a validation error."""
        msg = A2AMessage(
            source_agent="agent-A",
            target_agent="agent-B",
            message_type="unknown_type",
            payload={},
        )
        errors = validate_a2a_message(msg)
        assert any("message_type" in e for e in errors)

    def test_from_dict_roundtrip(self) -> None:
        """from_dict(to_dict(msg)) reproduces all original fields."""
        original = A2AMessage(
            source_agent="agent-A",
            target_agent="agent-B",
            message_type="event",
            payload={"key": "value"},
            metadata={"env": "prod"},
            correlation_id="corr-123",
        )
        data = a2a_message_to_dict(original)
        reconstructed = a2a_message_from_dict(data)

        assert reconstructed.id == original.id
        assert reconstructed.source_agent == original.source_agent
        assert reconstructed.target_agent == original.target_agent
        assert reconstructed.message_type == original.message_type
        assert reconstructed.payload == original.payload
        assert reconstructed.metadata == original.metadata
        assert reconstructed.correlation_id == original.correlation_id
        assert abs(reconstructed.timestamp - original.timestamp) < 1.0

    def test_from_dict_missing_required(self) -> None:
        """Missing source_agent in dict raises ValueError."""
        data = {
            "target_agent": "agent-B",
            "message_type": "request",
            "payload": {},
        }
        with pytest.raises(ValueError, match="source_agent"):
            a2a_message_from_dict(data)

    def test_create_response_correlation(self) -> None:
        """Response message has correlation_id equal to the request's id."""
        request = A2AMessage(
            source_agent="agent-A",
            target_agent="agent-B",
            message_type="request",
            payload={"question": "What is 2+2?"},
        )
        response = create_response(request, source_agent="agent-B", payload={"answer": 4})
        assert response.correlation_id == request.id
        assert response.target_agent == request.source_agent
        assert response.source_agent == "agent-B"

    def test_create_response_error_type(self) -> None:
        """error='' produces type 'response'; non-empty error produces type 'error'."""
        request = A2AMessage(
            source_agent="agent-A",
            target_agent="agent-B",
            message_type="request",
            payload={},
        )
        ok_response = create_response(request, source_agent="agent-B", payload={})
        assert ok_response.message_type == "response"

        err_response = create_response(request, source_agent="agent-B", payload={}, error="something went wrong")
        assert err_response.message_type == "error"
        assert "error" in err_response.payload

    def test_a2a_message_to_dict_serializable(self) -> None:
        """to_dict result contains only JSON-serializable types."""
        msg = A2AMessage(
            source_agent="agent-A",
            target_agent="agent-B",
            message_type="response",
            payload={"result": [1, 2, 3]},
            metadata={"trace": "abc"},
        )
        data = a2a_message_to_dict(msg)
        # Must not raise
        serialized = json.dumps(data)
        assert len(serialized) > 0


@pytest.mark.requirement("FR-PROTO-067")
class TestA2ARouter:
    def test_router_register_and_route(self) -> None:
        """Registered handler receives the routed message."""
        router = A2ARouter()
        received: list[A2AMessage] = []

        def handler(msg: A2AMessage) -> A2AMessage | None:
            received.append(msg)
            return None

        router.register("agent-B", handler)
        msg = A2AMessage(
            source_agent="agent-A",
            target_agent="agent-B",
            message_type="request",
            payload={"hello": "world"},
        )
        responses = router.route(msg)
        assert len(received) == 1
        assert received[0] is msg
        assert responses == []

    def test_router_unregistered_target(self) -> None:
        """No handler registered for target -> empty list returned."""
        router = A2ARouter()
        msg = A2AMessage(
            source_agent="agent-A",
            target_agent="agent-X",
            message_type="request",
            payload={},
        )
        responses = router.route(msg)
        assert responses == []

    def test_router_list_agents(self) -> None:
        """Registered agents appear in list_agents()."""
        router = A2ARouter()
        router.register("agent-B", lambda _: None)
        router.register("agent-C", lambda _: None)
        agents = router.list_agents()
        assert "agent-B" in agents
        assert "agent-C" in agents

    def test_router_unregister(self) -> None:
        """Unregistered handler is no longer called."""
        router = A2ARouter()
        call_count = [0]

        def handler(_msg: A2AMessage) -> A2AMessage | None:
            call_count[0] += 1
            return None

        router.register("agent-B", handler)
        router.unregister("agent-B")

        msg = A2AMessage(
            source_agent="agent-A",
            target_agent="agent-B",
            message_type="event",
            payload={},
        )
        router.route(msg)
        assert call_count[0] == 0
        assert "agent-B" not in router.list_agents()

    def test_router_handler_returns_response(self) -> None:
        """Handler returning an A2AMessage adds it to the responses list."""
        router = A2ARouter()

        def handler(msg: A2AMessage) -> A2AMessage:
            return create_response(msg, source_agent="agent-B", payload={"ack": True})

        router.register("agent-B", handler)
        msg = A2AMessage(
            source_agent="agent-A",
            target_agent="agent-B",
            message_type="request",
            payload={"ping": True},
        )
        responses = router.route(msg)
        assert len(responses) == 1
        assert responses[0].correlation_id == msg.id
