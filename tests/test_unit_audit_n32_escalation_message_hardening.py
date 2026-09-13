"""AUDIT-N+32 hardening tests for the dormant-core ``EscalationQueue`` + ``MessageEntry`` surfaces.

Targets the live class definitions in
``src/thegent/execution/__init__.py``:

- ``EscalationQueue`` (line ~414) — file-based JSONL queue used by the
  governance CLI / observability surfaces.
- ``MessageEntry`` (line ~606) — small value-object holder for
  execution messages.

This module verifies the AUDIT-N+32 hardening pass closed the
following SOTA-style gaps across both surfaces:

- NEW-1: per-instance ``_append_lock`` (RLock) on every public mutator
- NEW-2: defensive input validation on ``add`` (run_id, reason,
         priority, sla_minutes, blocked_at_utc, owner)
- NEW-3: defensive input validation on ``enqueue`` (item is dict with
         non-empty run_id)
- NEW-4: ``OSError``-safe ``_save`` + ``add`` rollback on IO failure
- NEW-5: ``corrupt_lines`` exposed as read-only property
- NEW-6: explicit ``clear()`` method returning cleared count
- NEW-7: ``list_pending`` returns defensive copies
- NEW-8: ``MessageEntry`` constructor validates role/content/timestamp
- NEW-9: ``MessageEntry`` __eq__ / __hash__ / __repr__
- NEW-10: ``MessageEntry.from_dict`` accepts dict-shaped input with
          missing fields and validates the result
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import pytest

from thegent.execution import (
    EscalationQueue,
    MessageEntry,
)

# ---------------------------------------------------------------------------
# EscalationQueue — NEW-1: per-instance RLock
# ---------------------------------------------------------------------------


class TestEscalationQueueAppendLock:
    """AUDIT-N+32 NEW-1: per-instance ``_append_lock`` (RLock)."""

    def test_lock_attribute_is_rlock(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        assert hasattr(queue, "_append_lock"), "EscalationQueue must expose _append_lock"
        lock = queue._append_lock
        # RLock supports re-entry from the same thread.
        with lock, lock:  # re-entry: would deadlock if Lock, not RLock
            pass

    def test_concurrent_add_serialised(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))

        def _worker(idx: int) -> None:
            queue.add(run_id=f"run-{idx}", reason=f"reason-{idx}", priority=3)

        threads = [threading.Thread(target=_worker, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All 50 items persisted.
        assert len(queue.queue) == 50
        # Each run_id appears exactly once.
        ids = [item["run_id"] for item in queue.queue]
        assert len(set(ids)) == 50

    def test_concurrent_enqueue_dequeue_serialised(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))

        def _enqueuer(idx: int) -> None:
            queue.enqueue({"run_id": f"run-{idx}", "value": idx})

        def _dequeuer() -> None:
            for _ in range(25):
                queue.dequeue()

        enq_threads = [threading.Thread(target=_enqueuer, args=(i,)) for i in range(25)]
        deq_threads = [threading.Thread(target=_dequeuer) for _ in range(5)]
        for t in enq_threads + deq_threads:
            t.start()
        for t in enq_threads + deq_threads:
            t.join()

        # Final queue must be consistent (no negative lengths, no dupes).
        ids = [item["run_id"] for item in queue.queue]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# EscalationQueue — NEW-2: defensive validation on add()
# ---------------------------------------------------------------------------


class TestEscalationQueueAddValidation:
    """AUDIT-N+32 NEW-2: defensive input validation on ``add``."""

    def test_add_rejects_empty_run_id(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        with pytest.raises(ValueError, match="run_id"):
            queue.add(run_id="", reason="blocked")

    def test_add_rejects_non_str_run_id(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        with pytest.raises(TypeError, match="run_id"):
            queue.add(run_id=None, reason="blocked")  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="run_id"):
            queue.add(run_id=123, reason="blocked")  # type: ignore[arg-type]

    def test_add_rejects_empty_reason(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        with pytest.raises(ValueError, match="reason"):
            queue.add(run_id="run-1", reason="")

    def test_add_rejects_non_str_reason(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        with pytest.raises(TypeError, match="reason"):
            queue.add(run_id="run-1", reason=42)  # type: ignore[arg-type]

    def test_add_rejects_priority_out_of_range(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        for bad in (0, 6, 99, -1):
            with pytest.raises(ValueError, match="priority"):
                queue.add(run_id="run-1", reason="blocked", priority=bad)

    def test_add_rejects_non_int_priority(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        with pytest.raises(TypeError, match="priority"):
            queue.add(run_id="run-1", reason="blocked", priority="3")  # type: ignore[arg-type]

    def test_add_rejects_bool_priority(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        # bool is a subclass of int — must be rejected explicitly.
        with pytest.raises(TypeError, match="priority"):
            queue.add(run_id="run-1", reason="blocked", priority=True)  # type: ignore[arg-type]

    def test_add_rejects_negative_sla_minutes(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        with pytest.raises(ValueError, match="sla_minutes"):
            queue.add(run_id="run-1", reason="blocked", sla_minutes=-5)

    def test_add_rejects_non_int_sla_minutes(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        with pytest.raises(TypeError, match="sla_minutes"):
            queue.add(run_id="run-1", reason="blocked", sla_minutes="60")  # type: ignore[arg-type]

    def test_add_rejects_non_str_blocked_at_utc(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        with pytest.raises(TypeError, match="blocked_at_utc"):
            queue.add(run_id="run-1", reason="blocked", blocked_at_utc=123)  # type: ignore[arg-type]

    def test_add_rejects_non_str_owner(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        with pytest.raises(TypeError, match="owner"):
            queue.add(run_id="run-1", reason="blocked", owner=42)  # type: ignore[arg-type]

    def test_add_accepts_all_valid_priorities(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        for p in (1, 2, 3, 4, 5):
            queue.add(run_id=f"run-{p}", reason="ok", priority=p)
        assert len(queue.queue) == 5

    def test_add_persists_to_disk(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        queue.add(run_id="run-1", reason="blocked", priority=2)
        # Reload from disk; item must survive.
        reloaded = EscalationQueue(str(tmp_path))
        assert len(reloaded.queue) == 1
        assert reloaded.queue[0]["run_id"] == "run-1"


# ---------------------------------------------------------------------------
# EscalationQueue — NEW-3: defensive validation on enqueue()
# ---------------------------------------------------------------------------


class TestEscalationQueueEnqueueValidation:
    """AUDIT-N+32 NEW-3: defensive input validation on ``enqueue``."""

    def test_enqueue_rejects_none(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        with pytest.raises(TypeError, match="dict"):
            queue.enqueue(None)  # type: ignore[arg-type]

    def test_enqueue_rejects_non_dict(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        with pytest.raises(TypeError, match="dict"):
            queue.enqueue("not-a-dict")  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="dict"):
            queue.enqueue(42)  # type: ignore[arg-type]

    def test_enqueue_rejects_dict_without_run_id(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        with pytest.raises(ValueError, match="run_id"):
            queue.enqueue({"foo": "bar"})

    def test_enqueue_rejects_dict_with_empty_run_id(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        with pytest.raises(ValueError, match="run_id"):
            queue.enqueue({"run_id": ""})

    def test_enqueue_rejects_dict_with_non_str_run_id(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        with pytest.raises(ValueError, match="run_id"):
            queue.enqueue({"run_id": 123})

    def test_enqueue_accepts_well_formed_dict(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        queue.enqueue({"run_id": "run-1", "extra": "value"})
        assert len(queue.queue) == 1
        assert queue.queue[0]["run_id"] == "run-1"


# ---------------------------------------------------------------------------
# EscalationQueue — NEW-4: OSError-safe _save + add rollback
# ---------------------------------------------------------------------------


class TestEscalationQueueIOSafety:
    """AUDIT-N+32 NEW-4: ``OSError``-safe ``_save`` + ``add`` rollback."""

    def test_save_raises_on_oserror(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        queue = EscalationQueue(str(tmp_path))
        queue.add(run_id="run-1", reason="blocked")

        import builtins

        real_open = builtins.open

        def _raising_open(file, mode="r", *args: Any, **kwargs: Any):  # type: ignore[no-untyped-def]
            if "w" in mode and str(queue.queue_path) in str(file):
                raise OSError("simulated disk failure")
            return real_open(file, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", _raising_open)

        with pytest.raises(OSError):
            queue._save()

    def test_add_rollback_on_oserror(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        queue = EscalationQueue(str(tmp_path))

        import builtins

        real_open = builtins.open

        def _raising_open(file, mode="r", *args: Any, **kwargs: Any):  # type: ignore[no-untyped-def]
            if "a" in mode and str(queue.queue_path) in str(file):
                raise OSError("simulated append failure")
            return real_open(file, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", _raising_open)

        with pytest.raises(OSError):
            queue.add(run_id="run-fail", reason="blocked")

        # In-memory state must be rolled back — no orphan entry.
        assert queue.queue == []


# ---------------------------------------------------------------------------
# EscalationQueue — NEW-5: corrupt_lines property
# ---------------------------------------------------------------------------


class TestEscalationQueueCorruptLines:
    """AUDIT-N+32 NEW-5: ``corrupt_lines`` exposed as read-only property."""

    def test_corrupt_lines_empty_on_clean_load(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        assert queue.corrupt_lines == ()

    def test_corrupt_lines_tracks_invalid_jsonl(self, tmp_path: Path) -> None:
        # Write a mix of valid and corrupt lines.
        queue_path = tmp_path / "escalation_queue.jsonl"
        queue_path.write_text(
            json.dumps({"run_id": "good", "reason": "ok"}) + "\n" + "this is not json\n" + "{broken: json\n",
            encoding="utf-8",
        )
        queue = EscalationQueue(str(tmp_path))
        # Good entry loaded, two corrupt lines tracked.
        assert len(queue.queue) == 1
        assert len(queue.corrupt_lines) == 2
        assert all(isinstance(line, str) for line in queue.corrupt_lines)

    def test_corrupt_lines_is_read_only_tuple(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        lines = queue.corrupt_lines
        # Tuple is immutable; assigning to an index raises TypeError.
        with pytest.raises(TypeError):
            lines[0] = "tampered"  # type: ignore[index]

    def test_corrupt_lines_not_mutated_by_list_pending(self, tmp_path: Path) -> None:
        queue_path = tmp_path / "escalation_queue.jsonl"
        queue_path.write_text(
            json.dumps({"run_id": "good", "reason": "ok", "status": "pending"}) + "\n" + "broken line\n",
            encoding="utf-8",
        )
        queue = EscalationQueue(str(tmp_path))
        # list_pending must NOT mutate _corrupt_lines (NEW-5 parity).
        before = queue.corrupt_lines
        queue.list_pending()
        queue.list_pending()
        queue.list_pending()
        after = queue.corrupt_lines
        assert before == after


# ---------------------------------------------------------------------------
# EscalationQueue — NEW-6: explicit clear() method
# ---------------------------------------------------------------------------


class TestEscalationQueueClear:
    """AUDIT-N+32 NEW-6: explicit ``clear()`` method."""

    def test_clear_empty_returns_zero(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        assert queue.clear() == 0
        assert queue.queue == []

    def test_clear_empties_queue(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        queue.add(run_id="run-1", reason="blocked")
        queue.add(run_id="run-2", reason="blocked")
        cleared = queue.clear()
        assert cleared == 2
        assert queue.queue == []

    def test_clear_returns_queue_plus_corrupt_count(self, tmp_path: Path) -> None:
        queue_path = tmp_path / "escalation_queue.jsonl"
        queue_path.write_text(
            json.dumps({"run_id": "good", "reason": "ok"}) + "\n" + "broken1\n" + "broken2\n",
            encoding="utf-8",
        )
        queue = EscalationQueue(str(tmp_path))
        cleared = queue.clear()
        assert cleared == 3  # 1 valid + 2 corrupt

    def test_clear_removes_on_disk_file(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        queue.add(run_id="run-1", reason="blocked")
        assert queue.queue_path.exists()
        queue.clear()
        assert not queue.queue_path.exists()

    def test_clear_when_file_missing(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        # No file written, no items, no corrupt lines.
        cleared = queue.clear()
        assert cleared == 0
        assert queue.queue == []


# ---------------------------------------------------------------------------
# EscalationQueue — NEW-7: defensive copies from list_pending
# ---------------------------------------------------------------------------


class TestEscalationQueueListPendingDefensiveCopies:
    """AUDIT-N+32 NEW-7: ``list_pending`` returns defensive copies."""

    def test_list_pending_mutating_returned_dict_does_not_persist(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        queue.add(run_id="run-1", reason="blocked", priority=2, sla_minutes=60)
        first = queue.list_pending()
        assert len(first) == 1
        first[0]["priority"] = 99
        first[0]["run_id"] = "tampered"
        # Reload; the underlying record must be unchanged.
        reloaded = EscalationQueue(str(tmp_path))
        again = reloaded.list_pending()
        assert again[0]["priority"] == 2
        assert again[0]["run_id"] == "run-1"

    def test_list_pending_mutating_returned_list_does_not_persist(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        queue.add(run_id="run-1", reason="blocked", priority=2, sla_minutes=60)
        first = queue.list_pending()
        first.clear()
        # Reload; underlying queue must still hold the item.
        reloaded = EscalationQueue(str(tmp_path))
        again = reloaded.list_pending()
        assert len(again) == 1

    def test_list_pending_past_sla_returns_defensive_copy(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        # sla_minutes=0 with a past blocked_at_utc means already past SLA.
        queue.add(
            run_id="run-1",
            reason="blocked",
            priority=2,
            sla_minutes=0,
            blocked_at_utc="2020-01-01T00:00:00Z",
        )
        past = queue.list_pending(past_sla_only=True)
        assert len(past) == 1
        past[0]["past_sla"] = False  # mutate
        # Reload; past_sla marker must still be True.
        reloaded = EscalationQueue(str(tmp_path))
        past2 = reloaded.list_pending(past_sla_only=True)
        assert past2[0]["past_sla"] is True


# ---------------------------------------------------------------------------
# EscalationQueue — defensive validation on resolve()
# ---------------------------------------------------------------------------


class TestEscalationQueueResolveValidation:
    """Validation on ``resolve`` (gap closed as part of the hardening pass)."""

    def test_resolve_rejects_non_str_run_id(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        with pytest.raises(TypeError, match="run_id"):
            queue.resolve(123)  # type: ignore[arg-type]

    def test_resolve_rejects_empty_run_id(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        with pytest.raises(ValueError, match="run_id"):
            queue.resolve("")

    def test_resolve_missing_returns_false(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        queue.add(run_id="run-1", reason="blocked")
        assert queue.resolve("run-missing") is False
        assert len(queue.queue) == 1

    def test_resolve_existing_returns_true(self, tmp_path: Path) -> None:
        queue = EscalationQueue(str(tmp_path))
        queue.add(run_id="run-1", reason="blocked")
        assert queue.resolve("run-1") is True
        assert queue.queue == []


# ---------------------------------------------------------------------------
# MessageEntry — NEW-8: defensive validation
# ---------------------------------------------------------------------------


class TestMessageEntryValidation:
    """AUDIT-N+32 NEW-8: defensive input validation on ``__init__``."""

    def test_init_rejects_non_str_role(self) -> None:
        with pytest.raises(TypeError, match="role"):
            MessageEntry(role=None, content="hi")  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="role"):
            MessageEntry(role=42, content="hi")  # type: ignore[arg-type]

    def test_init_rejects_unknown_role(self) -> None:
        with pytest.raises(ValueError, match="role"):
            MessageEntry(role="alien", content="hi")  # type: ignore[arg-type]

    def test_init_rejects_non_str_content(self) -> None:
        with pytest.raises(TypeError, match="content"):
            MessageEntry(role="user", content=None)  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="content"):
            MessageEntry(role="user", content=42)  # type: ignore[arg-type]

    def test_init_rejects_non_str_timestamp(self) -> None:
        with pytest.raises(TypeError, match="timestamp"):
            MessageEntry(role="user", content="hi", timestamp=123)  # type: ignore[arg-type]

    def test_init_accepts_known_roles(self) -> None:
        for role in (
            "system",
            "user",
            "assistant",
            "tool",
            "developer",
            "function",
            "",
        ):
            entry = MessageEntry(role=role, content="hi")
            assert entry.role == role

    def test_init_default_timestamp_empty_string(self) -> None:
        entry = MessageEntry(role="user", content="hi")
        assert entry.timestamp == ""

    def test_init_uses_slots(self) -> None:
        entry = MessageEntry(role="user", content="hi")
        # __slots__ prevents arbitrary attribute assignment.
        with pytest.raises(AttributeError):
            entry.injected = "tampered"  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# MessageEntry — NEW-9: equality, hashing, repr
# ---------------------------------------------------------------------------


class TestMessageEntryEquality:
    """AUDIT-N+32 NEW-9: explicit ``__eq__`` / ``__hash__`` / ``__repr__``."""

    def test_equal_when_all_fields_match(self) -> None:
        a = MessageEntry(role="user", content="hi", timestamp="t1")
        b = MessageEntry(role="user", content="hi", timestamp="t1")
        assert a == b

    def test_not_equal_when_role_differs(self) -> None:
        a = MessageEntry(role="user", content="hi", timestamp="t1")
        b = MessageEntry(role="assistant", content="hi", timestamp="t1")
        assert a != b

    def test_not_equal_when_content_differs(self) -> None:
        a = MessageEntry(role="user", content="hi", timestamp="t1")
        b = MessageEntry(role="user", content="bye", timestamp="t1")
        assert a != b

    def test_not_equal_when_timestamp_differs(self) -> None:
        a = MessageEntry(role="user", content="hi", timestamp="t1")
        b = MessageEntry(role="user", content="hi", timestamp="t2")
        assert a != b

    def test_not_equal_to_non_message_entry(self) -> None:
        entry = MessageEntry(role="user", content="hi")
        assert entry != "user"
        assert entry != 42
        assert entry != {"role": "user", "content": "hi", "timestamp": ""}

    def test_hash_consistent_with_equality(self) -> None:
        a = MessageEntry(role="user", content="hi", timestamp="t1")
        b = MessageEntry(role="user", content="hi", timestamp="t1")
        assert hash(a) == hash(b)

    def test_hashable_in_set(self) -> None:
        a = MessageEntry(role="user", content="hi", timestamp="t1")
        b = MessageEntry(role="user", content="hi", timestamp="t1")
        c = MessageEntry(role="user", content="bye", timestamp="t1")
        assert len({a, b, c}) == 2

    def test_repr_contains_all_fields(self) -> None:
        entry = MessageEntry(role="user", content="hi", timestamp="t1")
        rep = repr(entry)
        assert "MessageEntry" in rep
        assert "user" in rep
        assert "hi" in rep
        assert "t1" in rep


# ---------------------------------------------------------------------------
# MessageEntry — NEW-10: from_dict classmethod
# ---------------------------------------------------------------------------


class TestMessageEntryFromDict:
    """AUDIT-N+32 NEW-10: ``from_dict`` classmethod."""

    def test_from_dict_rejects_non_dict(self) -> None:
        with pytest.raises(TypeError, match="dict"):
            MessageEntry.from_dict(None)  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="dict"):
            MessageEntry.from_dict("not-a-dict")  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="dict"):
            MessageEntry.from_dict([1, 2, 3])  # type: ignore[arg-type]

    def test_from_dict_well_formed(self) -> None:
        entry = MessageEntry.from_dict({"role": "user", "content": "hi", "timestamp": "t1"})
        assert entry.role == "user"
        assert entry.content == "hi"
        assert entry.timestamp == "t1"

    def test_from_dict_missing_fields_use_defaults(self) -> None:
        entry = MessageEntry.from_dict({})
        assert entry.role == ""
        assert entry.content == ""
        assert entry.timestamp == ""

    def test_from_dict_partial_fields(self) -> None:
        entry = MessageEntry.from_dict({"role": "user"})
        assert entry.role == "user"
        assert entry.content == ""
        assert entry.timestamp == ""

    def test_from_dict_coerces_non_str_values(self) -> None:
        entry = MessageEntry.from_dict({"role": None, "content": 42, "timestamp": None})
        assert entry.role == ""
        assert entry.content == "42"
        assert entry.timestamp == ""

    def test_from_dict_round_trip_via_to_dict(self) -> None:
        original = MessageEntry(role="user", content="hi", timestamp="t1")
        round_tripped = MessageEntry.from_dict(original.to_dict())
        assert round_tripped == original
        assert round_tripped.to_dict() == original.to_dict()
