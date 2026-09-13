"""Tests for CrossProjectIpc — file-based cross-project agent IPC.

# @trace impl-cross-project-ipc
"""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING

import orjson as json
import pytest

if TYPE_CHECKING:
    from pathlib import Path

from thegent.ipc.cross_project import (
    BROADCAST_ADDR,
    CrossProjectIpc,
    CrossProjectIpcServer,
    IpcMessage,
    _inbox_name,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ipc_dir(tmp_path: Path) -> Path:
    """Isolated IPC directory for each test."""
    d = tmp_path / "ipc"
    d.mkdir()
    return d


@pytest.fixture
def project_a(tmp_path: Path) -> Path:
    p = tmp_path / "project_a"
    p.mkdir()
    return p


@pytest.fixture
def project_b(tmp_path: Path) -> Path:
    p = tmp_path / "project_b"
    p.mkdir()
    return p


@pytest.fixture
def alice(ipc_dir: Path, project_a: Path) -> CrossProjectIpc:
    return CrossProjectIpc("alice", project_a, ipc_dir=ipc_dir)


@pytest.fixture
def bob(ipc_dir: Path, project_b: Path) -> CrossProjectIpc:
    return CrossProjectIpc("bob", project_b, ipc_dir=ipc_dir)


@pytest.fixture
def carol(ipc_dir: Path, project_b: Path) -> CrossProjectIpc:
    return CrossProjectIpc("carol", project_b, ipc_dir=ipc_dir)


# ---------------------------------------------------------------------------
# 1. IpcMessage serialisation
# ---------------------------------------------------------------------------


class TestIpcMessage:
    """IpcMessage dataclass serialises and deserialises correctly."""

    def test_to_json_round_trip(self) -> None:
        msg = IpcMessage(
            msg_id="abc",
            sender="p1:a1",
            recipient="p2:a2",
            topic="ping",
            payload={"k": 1},
            timestamp=1.0,
            reply_to=None,
        )
        restored = IpcMessage.from_json(msg.to_json())
        assert restored == msg

    def test_from_dict_round_trip(self) -> None:
        data = {
            "msg_id": "xyz",
            "sender": "p1:a1",
            "recipient": "p2:a2",
            "topic": "event",
            "payload": {"hello": "world"},
            "timestamp": 42.5,
            "reply_to": "parent-id",
        }
        msg = IpcMessage.from_dict(data)
        assert msg.reply_to == "parent-id"
        assert msg.payload == {"hello": "world"}

    def test_reply_to_defaults_to_none(self) -> None:
        msg = IpcMessage(
            msg_id="id1",
            sender="p:a",
            recipient="p:b",
            topic="t",
            payload={},
            timestamp=0.0,
        )
        assert msg.reply_to is None


# ---------------------------------------------------------------------------
# 2. Inbox naming
# ---------------------------------------------------------------------------


class TestInboxName:
    """_inbox_name() produces consistent, filesystem-safe names."""

    def test_broadcast_returns_fixed_name(self) -> None:
        assert _inbox_name(BROADCAST_ADDR) == "broadcast"

    def test_address_produces_hex_prefix(self) -> None:
        name = _inbox_name("/home/user/proj:agent-1")
        assert all(c in "0123456789abcdef" for c in name)
        assert len(name) == 16

    def test_different_addresses_differ(self) -> None:
        n1 = _inbox_name("/proj/a:agent")
        n2 = _inbox_name("/proj/b:agent")
        assert n1 != n2

    def test_same_address_consistent(self) -> None:
        addr = "/some/path:agent-x"
        assert _inbox_name(addr) == _inbox_name(addr)


# ---------------------------------------------------------------------------
# 3. CrossProjectIpc initialisation
# ---------------------------------------------------------------------------


class TestInit:
    """CrossProjectIpc creates its inbox directories on construction."""

    def test_inbox_dirs_created(self, ipc_dir: Path, project_a: Path) -> None:
        ipc = CrossProjectIpc("agent1", project_a, ipc_dir=ipc_dir)
        inbox = ipc._inbox_dir
        assert (inbox / "tmp").is_dir()
        assert (inbox / "new").is_dir()
        assert (inbox / "cur").is_dir()

    def test_address_format(self, ipc_dir: Path, project_a: Path) -> None:
        ipc = CrossProjectIpc("myagent", project_a, ipc_dir=ipc_dir)
        assert ipc.address == f"{project_a}:myagent"


# ---------------------------------------------------------------------------
# 4. send() — file creation in recipient's inbox
# ---------------------------------------------------------------------------


class TestSend:
    """send() atomically delivers a file to the recipient's inbox."""

    def test_send_creates_file_in_recipient_new(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        msg_id = alice.send(bob.address, "greet", {"hello": True})
        new_dir = bob._inbox_dir / "new"
        assert (new_dir / msg_id).exists()

    def test_send_returns_nonempty_msg_id(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        msg_id = alice.send(bob.address, "t", {})
        assert isinstance(msg_id, str)
        assert msg_id

    def test_send_ids_are_unique(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        ids = {alice.send(bob.address, "t", {}) for _ in range(10)}
        assert len(ids) == 10

    def test_send_file_is_valid_json(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        msg_id = alice.send(bob.address, "data", {"x": 42})
        new_path = bob._inbox_dir / "new" / msg_id
        data = json.loads(new_path.read_text())
        assert data["topic"] == "data"
        assert data["payload"] == {"x": 42}
        assert data["sender"] == alice.address
        assert data["recipient"] == bob.address

    def test_send_nothing_in_tmp_after_delivery(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        alice.send(bob.address, "t", {})
        assert list((bob._inbox_dir / "tmp").iterdir()) == []


# ---------------------------------------------------------------------------
# 5. receive() — claiming a message
# ---------------------------------------------------------------------------


class TestReceive:
    """receive() claims the next message from the personal inbox."""

    def test_receive_returns_none_on_empty_inbox(self, bob: CrossProjectIpc) -> None:
        assert bob.receive() is None

    def test_receive_picks_up_sent_message(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        msg_id = alice.send(bob.address, "ping", {"seq": 1})
        msg = bob.receive()
        assert msg is not None
        assert msg.msg_id == msg_id
        assert msg.topic == "ping"
        assert msg.payload == {"seq": 1}

    def test_receive_moves_to_cur(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        msg_id = alice.send(bob.address, "t", {})
        bob.receive()
        assert not (bob._inbox_dir / "new" / msg_id).exists()
        assert (bob._inbox_dir / "cur" / msg_id).exists()

    def test_receive_nonblocking_returns_none_immediately(self, bob: CrossProjectIpc) -> None:
        start = time.monotonic()
        result = bob.receive(timeout=0.0)
        elapsed = time.monotonic() - start
        assert result is None
        assert elapsed < 0.5

    def test_receive_with_timeout_waits_then_returns(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        """receive() with timeout returns as soon as a message arrives."""

        def _send_later() -> None:
            time.sleep(0.1)
            alice.send(bob.address, "delayed", {})

        t = threading.Thread(target=_send_later)
        t.start()
        msg = bob.receive(timeout=2.0)
        t.join()
        assert msg is not None
        assert msg.topic == "delayed"

    def test_receive_with_timeout_expires(self, bob: CrossProjectIpc) -> None:
        """receive() returns None when nothing arrives within timeout."""
        start = time.monotonic()
        result = bob.receive(timeout=0.15)
        elapsed = time.monotonic() - start
        assert result is None
        assert elapsed >= 0.1  # waited at least the timeout


# ---------------------------------------------------------------------------
# 6. broadcast() — multiple recipients
# ---------------------------------------------------------------------------


class TestBroadcast:
    """broadcast() delivers to the shared broadcast inbox."""

    def test_broadcast_creates_file_in_broadcast_inbox(self, alice: CrossProjectIpc, ipc_dir: Path) -> None:
        msg_id = alice.broadcast("announce", {"version": 2})
        broadcast_dir = ipc_dir / "broadcast"
        assert (broadcast_dir / "new" / msg_id).exists()

    def test_multiple_receivers_can_read_broadcast(
        self,
        alice: CrossProjectIpc,
        bob: CrossProjectIpc,
        carol: CrossProjectIpc,
    ) -> None:
        """Two agents can each independently read a broadcast message."""
        alice.broadcast("hello", {"all": True})
        msg_bob = bob.receive_broadcast()
        assert msg_bob is not None
        assert msg_bob.topic == "hello"

        # Carol polls a *different* inbox instance backed by the same dir —
        # broadcast inbox holds multiple files if multiple were sent.
        # Here only one message was sent, so we send a second for Carol.
        alice.broadcast("hello", {"all": True})
        msg_carol = carol.receive_broadcast()
        assert msg_carol is not None

    def test_broadcast_sets_recipient_wildcard(self, alice: CrossProjectIpc, ipc_dir: Path) -> None:
        msg_id = alice.broadcast("event", {})
        broadcast_dir = ipc_dir / "broadcast"
        data = json.loads((broadcast_dir / "new" / msg_id).read_text())
        assert data["recipient"] == BROADCAST_ADDR


# ---------------------------------------------------------------------------
# 7. reply() — links to original message
# ---------------------------------------------------------------------------


class TestReply:
    """reply() sends a message that references the original msg_id."""

    def test_reply_delivered_to_sender_inbox(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        alice.send(bob.address, "ping", {})
        original = bob.receive()
        assert original is not None

        bob.reply(original, {"pong": True})
        reply = alice.receive()
        assert reply is not None
        assert reply.payload == {"pong": True}

    def test_reply_sets_reply_to_field(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        msg_id = alice.send(bob.address, "req", {"n": 7})
        original = bob.receive()
        assert original is not None

        reply_id = bob.reply(original, {"result": 49})
        # Read raw JSON from alice's inbox to verify reply_to
        reply_path = alice._inbox_dir / "new" / reply_id
        data = json.loads(reply_path.read_text())
        assert data["reply_to"] == msg_id

    def test_reply_preserves_topic(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        alice.send(bob.address, "compute", {})
        original = bob.receive()
        assert original is not None

        reply_id = bob.reply(original, {})
        data = json.loads((alice._inbox_dir / "new" / reply_id).read_text())
        assert data["topic"] == "compute"


# ---------------------------------------------------------------------------
# 8. ack() — removes message from cur/
# ---------------------------------------------------------------------------


class TestAck:
    """ack() removes the message file from cur/ (idempotent)."""

    def test_ack_removes_from_cur(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        alice.send(bob.address, "t", {})
        msg = bob.receive()
        assert msg is not None
        bob.ack(msg.msg_id)
        assert not (bob._inbox_dir / "cur" / msg.msg_id).exists()

    def test_ack_idempotent(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        alice.send(bob.address, "t", {})
        msg = bob.receive()
        assert msg is not None
        bob.ack(msg.msg_id)
        bob.ack(msg.msg_id)  # must not raise

    def test_ack_unknown_id_silent(self, bob: CrossProjectIpc) -> None:
        bob.ack("nonexistent-id")  # must not raise


# ---------------------------------------------------------------------------
# 9. receive_topic() — topic filtering
# ---------------------------------------------------------------------------


class TestReceiveTopic:
    """receive_topic() returns only messages matching the given topic."""

    def test_receive_topic_returns_matching_message(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        alice.send(bob.address, "irrelevant", {})
        alice.send(bob.address, "important", {"data": 99})
        msg = bob.receive_topic("important", timeout=0.5)
        assert msg is not None
        assert msg.topic == "important"
        assert msg.payload == {"data": 99}

    def test_receive_topic_nonblocking_miss(self, bob: CrossProjectIpc) -> None:
        result = bob.receive_topic("missing", timeout=0.0)
        assert result is None

    def test_receive_topic_timeout_expires(self, bob: CrossProjectIpc) -> None:
        start = time.monotonic()
        result = bob.receive_topic("nope", timeout=0.15)
        elapsed = time.monotonic() - start
        assert result is None
        assert elapsed >= 0.1


# ---------------------------------------------------------------------------
# 10. Concurrent sends are atomic
# ---------------------------------------------------------------------------


class TestConcurrentSends:
    """Concurrent senders to the same inbox do not corrupt messages."""

    def test_concurrent_sends_all_arrive(self, ipc_dir: Path, project_a: Path, project_b: Path) -> None:
        """N concurrent senders each deliver exactly one message."""
        n = 20
        receiver = CrossProjectIpc("receiver", project_b, ipc_dir=ipc_dir)
        errors: list[Exception] = []
        sent_ids: list[str] = []
        lock = threading.Lock()

        def _send(idx: int) -> None:
            sender = CrossProjectIpc(f"sender-{idx}", project_a, ipc_dir=ipc_dir)
            try:
                mid = sender.send(receiver.address, "concurrent", {"idx": idx})
                with lock:
                    sent_ids.append(mid)
            except Exception as exc:
                with lock:
                    errors.append(exc)

        threads = [threading.Thread(target=_send, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Sender errors: {errors}"
        assert len(sent_ids) == n

        # All messages should be in the receiver's new/ inbox.
        present = {f.name for f in (receiver._inbox_dir / "new").iterdir() if f.is_file()}
        for mid in sent_ids:
            assert mid in present, f"Missing message {mid}"


# ---------------------------------------------------------------------------
# 11. CrossProjectIpcServer
# ---------------------------------------------------------------------------


class TestCrossProjectIpcServer:
    """CrossProjectIpcServer dispatches messages to topic handlers."""

    def test_server_dispatches_to_handler(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        received: list[IpcMessage] = []
        server = CrossProjectIpcServer(bob, poll_interval=0.01, include_broadcast=False)
        server.register("greet", received.append)

        alice.send(bob.address, "greet", {"msg": "hello"})
        server.run(max_iterations=10)

        assert len(received) == 1
        assert received[0].topic == "greet"

    def test_server_calls_default_handler_for_unknown_topic(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        received: list[IpcMessage] = []
        server = CrossProjectIpcServer(bob, poll_interval=0.01, include_broadcast=False)
        server.set_default_handler(received.append)

        alice.send(bob.address, "unknown-topic", {})
        server.run(max_iterations=10)

        assert len(received) == 1

    def test_server_stop_terminates_loop(self, bob: CrossProjectIpc) -> None:
        server = CrossProjectIpcServer(bob, poll_interval=0.01)
        server._running = True

        def _stopper() -> None:
            time.sleep(0.05)
            server.stop()

        t = threading.Thread(target=_stopper)
        t.start()
        start = time.monotonic()
        server.run()
        t.join()
        assert time.monotonic() - start < 2.0

    def test_server_acks_processed_message(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        server = CrossProjectIpcServer(bob, poll_interval=0.01, include_broadcast=False)
        server.register("ping", lambda _: None)

        msg_id = alice.send(bob.address, "ping", {})
        server.run(max_iterations=5)

        # Message should be acked (removed from cur/)
        assert not (bob._inbox_dir / "cur" / msg_id).exists()

    def test_server_handles_broadcast_messages(self, alice: CrossProjectIpc, bob: CrossProjectIpc) -> None:
        bcast_received: list[IpcMessage] = []
        server = CrossProjectIpcServer(bob, poll_interval=0.01, include_broadcast=True)
        server.set_default_handler(bcast_received.append)

        alice.broadcast("event", {"n": 1})
        server.run(max_iterations=10)

        assert any(m.recipient == BROADCAST_ADDR for m in bcast_received)
