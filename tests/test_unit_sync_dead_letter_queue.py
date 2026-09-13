"""Unit tests for sync dead-letter queue retry metadata and replay ordering."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import orjson as json

from thegent.sync.dead_letter_queue import (
    DEFAULT_BOARD_DEAD_LETTER_BACKOFF_MULTIPLIER,
    DEFAULT_BOARD_DEAD_LETTER_MAX_ATTEMPTS,
    DEFAULT_BOARD_DEAD_LETTER_RETRY_DELAY_SECONDS,
    RemoteWriteDeadLetterQueue,
    RemoteWriteDeadLetterRecord,
    compute_backoff_seconds,
)


def test_backoff_formula_is_deterministic() -> None:
    """Backoff increases geometrically with configured multiplier."""
    assert compute_backoff_seconds(0, base_delay_seconds=2.0, multiplier=2.0) == 2.0
    assert compute_backoff_seconds(1, base_delay_seconds=2.0, multiplier=2.0) == 4.0
    assert compute_backoff_seconds(2, base_delay_seconds=2.0, multiplier=2.0) == 8.0


def test_candidates_for_replay_are_deterministic(tmp_path) -> None:
    """Replay candidate selection is stable across invocations."""
    now = datetime.now(UTC)
    queue = RemoteWriteDeadLetterQueue(tmp_path / "dlq.jsonl")

    queue.write(
        [
            RemoteWriteDeadLetterRecord(
                entry_id="second",
                source="github",
                board_id="123",
                item={"id": "WL-1"},
                error="one",
                attempts=2,
                status="pending",
                first_failed_at=(now - timedelta(minutes=5)).isoformat(),
                next_attempt_at=(now + timedelta(minutes=1)).isoformat(),
                max_attempts=5,
            ),
            RemoteWriteDeadLetterRecord(
                entry_id="first",
                source="github",
                board_id="123",
                item={"id": "WL-2"},
                error="two",
                attempts=0,
                status="pending",
                first_failed_at=(now - timedelta(minutes=4)).isoformat(),
                next_attempt_at=(now + timedelta(minutes=1)).isoformat(),
                max_attempts=5,
            ),
            RemoteWriteDeadLetterRecord(
                entry_id="third",
                source="github",
                board_id="123",
                item={"id": "WL-3"},
                error="three",
                attempts=0,
                status="pending",
                first_failed_at=(now - timedelta(minutes=3)).isoformat(),
                next_attempt_at=(now + timedelta(minutes=3)).isoformat(),
                max_attempts=5,
            ),
        ],
    )

    candidates = queue.candidates_for_replay(
        now=now + timedelta(minutes=2), source="github", board_id="123"
    )
    assert [entry.entry_id for entry in candidates] == ["first", "second"]


def test_legacy_records_load_with_default_retry_metadata(tmp_path) -> None:
    """Old queue records missing new retry fields parse with defaults."""
    payload = {
        "entry_id": "dlq-legacy",
        "source": "github",
        "board_id": "123",
        "item": {"id": "WL-7"},
        "error": "legacy error",
        "status": "pending",
        "attempts": 0,
        "first_failed_at": datetime.now(UTC).isoformat(),
        "last_attempt_at": None,
        "resolved_at": None,
    }
    queue_path = tmp_path / "legacy.jsonl"
    queue_path.write_text(json.dumps(payload).decode() + "\n", encoding="utf-8")

    queue = RemoteWriteDeadLetterQueue(queue_path)
    entries = queue.load()

    assert len(entries) == 1
    entry = entries[0]
    assert entry.max_attempts == DEFAULT_BOARD_DEAD_LETTER_MAX_ATTEMPTS
    assert entry.retry_interval_seconds == DEFAULT_BOARD_DEAD_LETTER_RETRY_DELAY_SECONDS
    assert entry.backoff_multiplier == DEFAULT_BOARD_DEAD_LETTER_BACKOFF_MULTIPLIER


def test_mark_failed_advances_state_with_backoff_metadata(tmp_path) -> None:
    """mark_failed increments attempts and computes next_attempt_at."""
    queue = RemoteWriteDeadLetterQueue(
        tmp_path / "dlq-fail.jsonl", max_attempts=2, retry_interval_seconds=10.0
    )
    record = queue.enqueue(
        source="github",
        board_id="123",
        item={"id": "WL-9"},
        error="temporary failure",
    )

    first_retry = record.mark_failed(now=datetime.now(UTC))
    assert first_retry.attempts == 1
    assert first_retry.status == "pending"
    assert first_retry.next_attempt_at is not None

    final_retry = first_retry.mark_failed(now=datetime.now(UTC))
    assert final_retry.attempts == 2
    assert final_retry.status == "failed"
