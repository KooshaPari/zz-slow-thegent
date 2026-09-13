"""Tests for MaildirQueue (heliosShield Phase 11 — Maildir-style task queue).

# @trace heliosShield-task-queue
"""

import time
from pathlib import Path

import orjson as json
import pytest

from thegent.mesh.task_queue import MaildirQueue

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def queue(tmp_path: Path) -> MaildirQueue:
    """A fresh MaildirQueue backed by a temporary directory."""
    return MaildirQueue(tmp_path / "q")


# ---------------------------------------------------------------------------
# 1. Initialisation
# ---------------------------------------------------------------------------


class TestInit:
    """MaildirQueue creates required directories on instantiation."""

    def test_directories_created(self, tmp_path: Path) -> None:
        """All three Maildir sub-directories are created."""
        MaildirQueue(tmp_path / "q")
        assert (tmp_path / "q" / "tmp").is_dir()
        assert (tmp_path / "q" / "new").is_dir()
        assert (tmp_path / "q" / "cur").is_dir()

    def test_idempotent_init(self, tmp_path: Path) -> None:
        """Constructing a second queue on the same path does not raise."""
        MaildirQueue(tmp_path / "q")
        MaildirQueue(tmp_path / "q")  # must not raise


# ---------------------------------------------------------------------------
# 2. Enqueue
# ---------------------------------------------------------------------------


class TestEnqueue:
    """enqueue() writes tasks atomically to new/."""

    def test_returns_unique_task_id(self, queue: MaildirQueue) -> None:
        """Each call returns a distinct non-empty task ID."""
        id1 = queue.enqueue({"work": "a"})
        id2 = queue.enqueue({"work": "b"})
        assert id1
        assert id2
        assert id1 != id2

    def test_task_file_appears_in_new(self, queue: MaildirQueue) -> None:
        """After enqueue(), a file with the task ID exists in new/."""
        task_id = queue.enqueue({"x": 1})
        assert (queue._new / task_id).exists()

    def test_task_file_absent_from_tmp(self, queue: MaildirQueue) -> None:
        """After enqueue(), no file lingers in tmp/."""
        task_id = queue.enqueue({"x": 1})
        assert not (queue._tmp / task_id).exists()

    def test_envelope_fields(self, queue: MaildirQueue) -> None:
        """The envelope contains all required fields with correct types."""
        before = time.time()
        task_id = queue.enqueue({"value": 42}, priority=3)
        envelope = json.loads((queue._new / task_id).read_text())

        assert envelope["id"] == task_id
        assert envelope["payload"] == {"value": 42}
        assert envelope["priority"] == 3
        assert envelope["attempts"] == 0
        assert envelope["created_at"] >= before

    def test_default_priority_is_5(self, queue: MaildirQueue) -> None:
        """Default priority is 5."""
        task_id = queue.enqueue({"x": 1})
        envelope = json.loads((queue._new / task_id).read_text())
        assert envelope["priority"] == 5

    def test_payload_is_arbitrary_json(self, queue: MaildirQueue) -> None:
        """Payload can be any JSON-serialisable value."""
        for payload in [None, 42, "string", [1, 2], {"nested": {"a": 1}}]:
            task_id = queue.enqueue(payload)
            envelope = json.loads((queue._new / task_id).read_text())
            assert envelope["payload"] == payload


# ---------------------------------------------------------------------------
# 3. Dequeue
# ---------------------------------------------------------------------------


class TestDequeue:
    """dequeue() claims tasks from new/ atomically."""

    def test_returns_none_on_empty_queue(self, queue: MaildirQueue) -> None:
        """An empty queue returns None."""
        assert queue.dequeue() is None

    def test_returns_task_dict(self, queue: MaildirQueue) -> None:
        """dequeue() returns the task envelope dict."""
        queue.enqueue({"work": "do_thing"})
        result = queue.dequeue()
        assert result is not None
        assert result["payload"] == {"work": "do_thing"}

    def test_task_moves_from_new_to_cur(self, queue: MaildirQueue) -> None:
        """After dequeue(), the file is in cur/ and absent from new/."""
        task_id = queue.enqueue({"a": 1})
        queue.dequeue()
        assert (queue._cur / task_id).exists()
        assert not (queue._new / task_id).exists()

    def test_attempts_incremented(self, queue: MaildirQueue) -> None:
        """dequeue() increments the attempts counter to 1 on first claim."""
        queue.enqueue({"a": 1})
        result = queue.dequeue()
        assert result is not None
        assert result["attempts"] == 1

    def test_owner_recorded_when_provided(self, queue: MaildirQueue) -> None:
        """dequeue() records the optional owner on the returned envelope."""
        queue.enqueue({"a": 1})
        result = queue.dequeue(owner="agent-007")
        assert result is not None
        assert result["owner"] == "agent-007"
        cur_task = json.loads((queue._cur / result["id"]).read_text(encoding="utf-8"))
        assert cur_task["owner"] == "agent-007"

    def test_empty_after_single_dequeue(self, queue: MaildirQueue) -> None:
        """A queue with one task is empty after one dequeue()."""
        queue.enqueue({"a": 1})
        queue.dequeue()
        assert queue.dequeue() is None

    def test_priority_ordering_lower_first(self, queue: MaildirQueue) -> None:
        """Tasks with lower priority values are dequeued first."""
        id_high = queue.enqueue({"label": "high"}, priority=9)
        id_low = queue.enqueue({"label": "low"}, priority=1)
        id_mid = queue.enqueue({"label": "mid"}, priority=5)

        first = queue.dequeue()
        second = queue.dequeue()
        third = queue.dequeue()

        assert first is not None
        assert first["id"] == id_low
        assert second is not None
        assert second["id"] == id_mid
        assert third is not None
        assert third["id"] == id_high

    def test_fifo_within_same_priority(self, queue: MaildirQueue) -> None:
        """Within the same priority, oldest task is dequeued first."""
        id_first = queue.enqueue({"seq": 1}, priority=5)
        time.sleep(0.01)  # ensure distinct created_at timestamps
        id_second = queue.enqueue({"seq": 2}, priority=5)

        result1 = queue.dequeue()
        result2 = queue.dequeue()

        assert result1 is not None
        assert result1["id"] == id_first
        assert result2 is not None
        assert result2["id"] == id_second

    def test_dequeue_multiple_tasks(self, queue: MaildirQueue) -> None:
        """All enqueued tasks can be dequeued exactly once."""
        ids = {queue.enqueue({"n": i}) for i in range(5)}
        dequeued_ids = set()
        for _ in range(5):
            result = queue.dequeue()
            assert result is not None
            dequeued_ids.add(result["id"])
        assert queue.dequeue() is None
        assert dequeued_ids == ids


# ---------------------------------------------------------------------------
# 4. Ack
# ---------------------------------------------------------------------------


class TestAck:
    """ack() removes a task from cur/ permanently."""

    def test_removes_task_from_cur(self, queue: MaildirQueue) -> None:
        """ack() deletes the task file from cur/."""
        queue.enqueue({"a": 1})
        result = queue.dequeue()
        assert result is not None
        task_id = result["id"]

        queue.ack(task_id)
        assert not (queue._cur / task_id).exists()

    def test_ack_is_idempotent(self, queue: MaildirQueue) -> None:
        """Calling ack() twice on the same task ID does not raise."""
        queue.enqueue({"a": 1})
        result = queue.dequeue()
        assert result is not None
        task_id = result["id"]

        queue.ack(task_id)
        queue.ack(task_id)  # must not raise

    def test_ack_unknown_id_silent(self, queue: MaildirQueue) -> None:
        """ack() on an unknown task ID does not raise."""
        queue.ack("non-existent-id")  # must not raise


# ---------------------------------------------------------------------------
# 5. Nack
# ---------------------------------------------------------------------------


class TestNack:
    """nack() returns a task from cur/ to new/ for retry."""

    def test_moves_task_back_to_new(self, queue: MaildirQueue) -> None:
        """nack() moves the file from cur/ back to new/."""
        queue.enqueue({"a": 1})
        result = queue.dequeue()
        assert result is not None
        task_id = result["id"]

        queue.nack(task_id)
        assert (queue._new / task_id).exists()
        assert not (queue._cur / task_id).exists()

    def test_nacked_task_can_be_dequeued_again(self, queue: MaildirQueue) -> None:
        """A nacked task can be claimed again by dequeue()."""
        queue.enqueue({"retry_me": True})
        result1 = queue.dequeue()
        assert result1 is not None
        queue.nack(result1["id"])

        result2 = queue.dequeue()
        assert result2 is not None
        assert result2["id"] == result1["id"]

    def test_nack_is_idempotent(self, queue: MaildirQueue) -> None:
        """nack() on an already-returned task does not raise."""
        queue.enqueue({"a": 1})
        result = queue.dequeue()
        assert result is not None
        task_id = result["id"]

        queue.nack(task_id)
        queue.nack(task_id)  # second call: file is now in new/, not cur/ — no raise

    def test_nack_unknown_id_silent(self, queue: MaildirQueue) -> None:
        """nack() on an unknown task ID does not raise."""
        queue.nack("non-existent-id")  # must not raise


# ---------------------------------------------------------------------------
# 6. List pending
# ---------------------------------------------------------------------------


class TestListPending:
    """list_pending() returns tasks from both new/ and cur/."""

    def test_empty_queue_returns_empty_list(self, queue: MaildirQueue) -> None:
        """Empty queue yields an empty list."""
        assert queue.list_pending() == []

    def test_new_tasks_appear_in_pending(self, queue: MaildirQueue) -> None:
        """Enqueued-but-not-dequeued tasks appear in list_pending()."""
        id1 = queue.enqueue({"a": 1})
        id2 = queue.enqueue({"b": 2})
        pending_ids = {e["id"] for e in queue.list_pending()}
        assert id1 in pending_ids
        assert id2 in pending_ids

    def test_in_flight_tasks_appear_in_pending(self, queue: MaildirQueue) -> None:
        """Dequeued-but-not-acked tasks still appear in list_pending()."""
        queue.enqueue({"a": 1})
        result = queue.dequeue()
        assert result is not None
        pending_ids = {e["id"] for e in queue.list_pending()}
        assert result["id"] in pending_ids

    def test_acked_tasks_absent_from_pending(self, queue: MaildirQueue) -> None:
        """Acked tasks no longer appear in list_pending()."""
        queue.enqueue({"a": 1})
        result = queue.dequeue()
        assert result is not None
        queue.ack(result["id"])
        assert queue.list_pending() == []

    def test_combined_new_and_cur(self, queue: MaildirQueue) -> None:
        """list_pending() aggregates tasks from both new/ and cur/."""
        id_new = queue.enqueue({"new": True})
        id_inflight = queue.enqueue({"inflight": True})
        queue.dequeue()  # claims one into cur/; the other stays in new/

        pending_ids = {e["id"] for e in queue.list_pending()}
        assert id_new in pending_ids
        assert id_inflight in pending_ids


class TestReclaimOwner:
    """reclaim_owner() returns tasks claimed by a specific agent."""

    def test_reclaim_owner_moves_cur_tasks_to_new(self, queue: MaildirQueue) -> None:
        """reclaim_owner() moves only matching-owner tasks from cur/ back to new/."""
        first = queue.enqueue({"a": 1})
        queue.dequeue(owner="agent-stale")
        queue.enqueue({"a": 2})
        result_other = queue.dequeue(owner="agent-active")
        assert result_other is not None

        reclaimed = queue.reclaim_owner("agent-stale")
        assert reclaimed == 1

        assert (queue._new / first).exists()
        assert not (queue._cur / first).exists()
        assert any(path.name == result_other["id"] for path in queue._cur.iterdir())


# ---------------------------------------------------------------------------
# 7. Crash-recovery semantics
# ---------------------------------------------------------------------------


class TestCrashRecovery:
    """Tasks in cur/ after a crash are visible and re-queueable."""

    def test_stranded_cur_tasks_visible_after_restart(self, tmp_path: Path) -> None:
        """A queue created on the same path sees tasks left in cur/ by a previous run."""
        q1 = MaildirQueue(tmp_path / "q")
        q1.enqueue({"important": True})
        result = q1.dequeue()
        assert result is not None
        task_id = result["id"]
        # Simulate a process crash — do not ack

        # New process attaches to the same queue
        q2 = MaildirQueue(tmp_path / "q")
        pending_ids = {e["id"] for e in q2.list_pending()}
        assert task_id in pending_ids

    def test_stranded_task_can_be_nacked_and_retried(self, tmp_path: Path) -> None:
        """A stranded cur/ task can be nacked and dequeued again."""
        q1 = MaildirQueue(tmp_path / "q")
        q1.enqueue({"important": True})
        result = q1.dequeue()
        assert result is not None
        task_id = result["id"]
        # Crash — no ack

        q2 = MaildirQueue(tmp_path / "q")
        q2.nack(task_id)  # recovery agent returns it to new/
        retry = q2.dequeue()
        assert retry is not None
        assert retry["id"] == task_id


# ---------------------------------------------------------------------------
# 8. Atomicity — basic sanity via filesystem checks
# ---------------------------------------------------------------------------


class TestAtomicity:
    """Verify that no partial state leaks into new/ or cur/."""

    def test_tmp_is_empty_after_enqueue(self, queue: MaildirQueue) -> None:
        """tmp/ is always empty after enqueue() completes."""
        for i in range(10):
            queue.enqueue({"i": i})
        assert list(queue._tmp.iterdir()) == []

    def test_new_file_is_valid_json_after_enqueue(self, queue: MaildirQueue) -> None:
        """Every file in new/ is valid JSON."""
        for i in range(5):
            queue.enqueue({"i": i})
        for f in queue._new.iterdir():
            data = json.loads(f.read_text())
            assert "id" in data
            assert "payload" in data
