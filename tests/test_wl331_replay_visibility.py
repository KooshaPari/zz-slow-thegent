"""CLI visibility tests for dead-letter replay candidates.

# @trace WL-331
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from typer.testing import CliRunner

from thegent.cli.apps.sync import app
from thegent.sync.dead_letter_queue import (
    RemoteWriteDeadLetterQueue,
    RemoteWriteDeadLetterRecord,
)


def _seed_dead_letter_queue(tmp_path) -> None:
    queue_path = (
        tmp_path / "docs" / "reference" / "workstream_remote_writes_dead_letter.jsonl"
    )
    queue = RemoteWriteDeadLetterQueue(queue_path)
    now = datetime.now(UTC)

    queue.append(
        RemoteWriteDeadLetterRecord(
            entry_id="dlq-due-001",
            source="github",
            board_id="B-1",
            item={"id": "WL-331", "title": "Visible replay candidate"},
            error="sync write failed",
            status="pending",
            attempts=1,
            first_failed_at=(now - timedelta(minutes=5)).isoformat(),
            next_attempt_at=(now - timedelta(minutes=1)).isoformat(),
        )
    )

    queue.append(
        RemoteWriteDeadLetterRecord(
            entry_id="dlq-future-002",
            source="github",
            board_id="B-1",
            item={"id": "WL-332", "title": "Not yet due"},
            error="rate limited",
            status="pending",
            attempts=1,
            first_failed_at=now.isoformat(),
            next_attempt_at=(now + timedelta(hours=1)).isoformat(),
        )
    )


def test_dead_letter_queue_table_output_shows_due_candidates(tmp_path) -> None:
    _seed_dead_letter_queue(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "dead-letter-queue",
            "--project",
            str(tmp_path),
            "--source",
            "github",
            "--board",
            "B-1",
            "--limit",
            "10",
        ],
    )

    assert result.exit_code == 0
    assert "pending=2 due=1 selected=1" in result.stdout
    assert "dlq-due-001" in result.stdout
    assert "WL-331" in result.stdout
    assert "dlq-future-002" not in result.stdout


def test_dead_letter_queue_json_shape(tmp_path) -> None:
    _seed_dead_letter_queue(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "dead-letter-queue",
            "--project",
            str(tmp_path),
            "--source",
            "github",
            "--board",
            "B-1",
            "--limit",
            "1",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["operation"] == "dead-letter-queue"
    assert payload["filters"] == {"source": "github", "board_id": "B-1", "limit": 1}
    assert payload["counts"] == {"pending_total": 2, "due_total": 1, "selected": 1}
    assert isinstance(payload["candidates"], list)
    assert len(payload["candidates"]) == 1
    candidate = payload["candidates"][0]
    assert candidate["entry_id"] == "dlq-due-001"
    assert candidate["source"] == "github"
    assert candidate["board_id"] == "B-1"
    assert candidate["item_id"] == "WL-331"
    assert candidate["status"] == "pending"
    assert "attempts" in candidate
    assert "max_attempts" in candidate
    assert "error" in candidate
