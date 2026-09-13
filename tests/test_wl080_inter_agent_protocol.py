"""Tests for WL-080: InterAgentProtocol — Typed Message Schema.

# @trace WL-080
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

import pytest

from thegent.orchestration.inter_agent_protocol import InterAgentMessage, MessageBus

# ---------------------------------------------------------------------------
# InterAgentMessage: field defaults
# ---------------------------------------------------------------------------


class TestInterAgentMessageDefaults:
    """Tests for InterAgentMessage field defaults and validation."""

    def test_id_is_auto_generated(self):
        # @trace WL-080
        msg = InterAgentMessage(
            sender_id="agent-a",
            recipient_id="agent-b",
            message_type="task_request",
            payload={},
        )
        assert msg.id is not None
        assert isinstance(msg.id, str)
        assert len(msg.id) > 0

    def test_id_is_uuid4_format(self):
        # @trace WL-080
        msg = InterAgentMessage(
            sender_id="agent-a",
            recipient_id="agent-b",
            message_type="task_request",
            payload={},
        )
        parsed = uuid.UUID(msg.id, version=4)
        assert str(parsed) == msg.id

    def test_created_at_is_utc_datetime(self):
        # @trace WL-080
        msg = InterAgentMessage(
            sender_id="agent-a",
            recipient_id="agent-b",
            message_type="task_request",
            payload={},
        )
        assert isinstance(msg.created_at, datetime)
        assert msg.created_at.tzinfo is not None
        assert msg.created_at.tzinfo == UTC

    def test_created_at_is_recent(self):
        # @trace WL-080
        before = datetime.now(UTC)
        msg = InterAgentMessage(
            sender_id="agent-a",
            recipient_id="agent-b",
            message_type="heartbeat",
            payload={},
        )
        after = datetime.now(UTC)
        assert before <= msg.created_at <= after

    def test_correlation_id_defaults_to_none(self):
        # @trace WL-080
        msg = InterAgentMessage(
            sender_id="agent-a",
            recipient_id="agent-b",
            message_type="result",
            payload={"data": 42},
        )
        assert msg.correlation_id is None

    def test_ttl_s_defaults_to_300(self):
        # @trace WL-080
        msg = InterAgentMessage(
            sender_id="agent-a",
            recipient_id="agent-b",
            message_type="status_update",
            payload={},
        )
        assert msg.ttl_s == 300

    def test_each_message_gets_unique_id(self):
        # @trace WL-080
        msgs = [
            InterAgentMessage(
                sender_id="agent-a",
                recipient_id="agent-b",
                message_type="heartbeat",
                payload={},
            )
            for _ in range(10)
        ]
        ids = [m.id for m in msgs]
        assert len(set(ids)) == 10


# ---------------------------------------------------------------------------
# InterAgentMessage: message_type literals
# ---------------------------------------------------------------------------


class TestInterAgentMessageTypes:
    """Tests for accepted message_type literal values."""

    @pytest.mark.parametrize(
        "mtype",
        ["task_request", "status_update", "result", "error", "heartbeat"],
    )
    def test_all_message_types_accepted(self, mtype: str):
        # @trace WL-080
        msg = InterAgentMessage(
            sender_id="s",
            recipient_id="r",
            message_type=mtype,  # type: ignore[arg-type]
            payload={},
        )
        assert msg.message_type == mtype

    def test_invalid_message_type_raises(self):
        # @trace WL-080
        with pytest.raises(Exception):
            InterAgentMessage(
                sender_id="s",
                recipient_id="r",
                message_type="unknown_type",  # type: ignore[arg-type]
                payload={},
            )


# ---------------------------------------------------------------------------
# InterAgentMessage: explicit field assignment
# ---------------------------------------------------------------------------


class TestInterAgentMessageFields:
    """Tests for explicit field assignment."""

    def test_correlation_id_can_be_set(self):
        # @trace WL-080
        corr = str(uuid.uuid4())
        msg = InterAgentMessage(
            sender_id="a",
            recipient_id="b",
            message_type="result",
            payload={},
            correlation_id=corr,
        )
        assert msg.correlation_id == corr

    def test_ttl_s_can_be_overridden(self):
        # @trace WL-080
        msg = InterAgentMessage(
            sender_id="a",
            recipient_id="b",
            message_type="task_request",
            payload={},
            ttl_s=60,
        )
        assert msg.ttl_s == 60

    def test_payload_accepts_arbitrary_dict(self):
        # @trace WL-080
        payload = {"nested": {"list": [1, 2, 3]}, "flag": True}
        msg = InterAgentMessage(
            sender_id="a",
            recipient_id="b",
            message_type="result",
            payload=payload,
        )
        assert msg.payload == payload

    def test_custom_id_is_accepted(self):
        # @trace WL-080
        custom_id = str(uuid.uuid4())
        msg = InterAgentMessage(
            id=custom_id,
            sender_id="a",
            recipient_id="b",
            message_type="heartbeat",
            payload={},
        )
        assert msg.id == custom_id


# ---------------------------------------------------------------------------
# MessageBus: subscribe / unsubscribe
# ---------------------------------------------------------------------------


class TestMessageBusSubscription:
    """Tests for MessageBus subscribe and unsubscribe behaviour."""

    def test_subscribe_returns_asyncio_queue(self):
        # @trace WL-080
        bus = MessageBus()
        q = bus.subscribe("agent-x")
        assert isinstance(q, asyncio.Queue)

    def test_subscribe_same_agent_returns_same_queue(self):
        # @trace WL-080
        bus = MessageBus()
        q1 = bus.subscribe("agent-x")
        q2 = bus.subscribe("agent-x")
        assert q1 is q2

    def test_unsubscribe_removes_queue(self):
        # @trace WL-080
        bus = MessageBus()
        bus.subscribe("agent-x")
        bus.unsubscribe("agent-x")
        # Re-subscribing after unsubscribe returns a fresh queue
        q_new = bus.subscribe("agent-x")
        assert isinstance(q_new, asyncio.Queue)

    def test_unsubscribe_nonexistent_agent_raises(self):
        # @trace WL-080
        bus = MessageBus()
        with pytest.raises(KeyError):
            bus.unsubscribe("ghost-agent")


# ---------------------------------------------------------------------------
# MessageBus: publish
# ---------------------------------------------------------------------------


class TestMessageBusPublish:
    """Tests for MessageBus.publish() delivery semantics."""

    def test_publish_delivers_to_recipient_queue(self):
        # @trace WL-080
        bus = MessageBus()
        bus.subscribe("agent-b")
        msg = InterAgentMessage(
            sender_id="agent-a",
            recipient_id="agent-b",
            message_type="task_request",
            payload={"task": "do_work"},
        )
        bus.publish(msg)
        assert bus._queues["agent-b"].qsize() == 1

    def test_publish_does_not_deliver_to_other_agents(self):
        # @trace WL-080
        bus = MessageBus()
        bus.subscribe("agent-b")
        bus.subscribe("agent-c")
        msg = InterAgentMessage(
            sender_id="agent-a",
            recipient_id="agent-b",
            message_type="task_request",
            payload={},
        )
        bus.publish(msg)
        assert bus._queues["agent-b"].qsize() == 1
        assert bus._queues["agent-c"].qsize() == 0

    def test_publish_to_unsubscribed_recipient_raises(self):
        # @trace WL-080
        bus = MessageBus()
        msg = InterAgentMessage(
            sender_id="a",
            recipient_id="no-such-agent",
            message_type="heartbeat",
            payload={},
        )
        with pytest.raises(KeyError):
            bus.publish(msg)

    def test_publish_multiple_messages_to_same_recipient(self):
        # @trace WL-080
        bus = MessageBus()
        bus.subscribe("agent-b")
        for i in range(5):
            bus.publish(
                InterAgentMessage(
                    sender_id="agent-a",
                    recipient_id="agent-b",
                    message_type="status_update",
                    payload={"seq": i},
                )
            )
        assert bus._queues["agent-b"].qsize() == 5

    def test_publish_preserves_message_identity(self):
        # @trace WL-080
        bus = MessageBus()
        bus.subscribe("agent-b")
        msg = InterAgentMessage(
            sender_id="agent-a",
            recipient_id="agent-b",
            message_type="result",
            payload={"value": 99},
        )
        bus.publish(msg)
        delivered = bus._queues["agent-b"].get_nowait()
        assert delivered is msg


# ---------------------------------------------------------------------------
# MessageBus: drain
# ---------------------------------------------------------------------------


class TestMessageBusDrain:
    """Tests for MessageBus.drain() behaviour."""

    def test_drain_returns_all_pending_messages(self):
        # @trace WL-080
        bus = MessageBus()
        bus.subscribe("agent-b")
        msgs = [
            InterAgentMessage(
                sender_id="a",
                recipient_id="agent-b",
                message_type="status_update",
                payload={"i": i},
            )
            for i in range(3)
        ]
        for m in msgs:
            bus.publish(m)
        result = bus.drain("agent-b")
        assert len(result) == 3
        assert result == msgs

    def test_drain_returns_empty_list_when_no_messages(self):
        # @trace WL-080
        bus = MessageBus()
        bus.subscribe("agent-b")
        result = bus.drain("agent-b")
        assert result == []

    def test_drain_clears_the_queue(self):
        # @trace WL-080
        bus = MessageBus()
        bus.subscribe("agent-b")
        bus.publish(
            InterAgentMessage(
                sender_id="a",
                recipient_id="agent-b",
                message_type="heartbeat",
                payload={},
            )
        )
        bus.drain("agent-b")
        assert bus._queues["agent-b"].qsize() == 0

    def test_drain_unsubscribed_agent_raises(self):
        # @trace WL-080
        bus = MessageBus()
        with pytest.raises(KeyError):
            bus.drain("ghost-agent")

    def test_drain_returns_messages_in_fifo_order(self):
        # @trace WL-080
        bus = MessageBus()
        bus.subscribe("agent-b")
        payloads = [{"seq": i} for i in range(5)]
        for p in payloads:
            bus.publish(
                InterAgentMessage(
                    sender_id="a",
                    recipient_id="agent-b",
                    message_type="result",
                    payload=p,
                )
            )
        result = bus.drain("agent-b")
        assert [m.payload for m in result] == payloads

    def test_drain_accepts_timeout_s_parameter(self):
        # @trace WL-080
        bus = MessageBus()
        bus.subscribe("agent-b")
        # Verify the parameter is accepted without error even when queue empty
        result = bus.drain("agent-b", timeout_s=0.0)
        assert result == []
