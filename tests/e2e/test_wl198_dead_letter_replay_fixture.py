"""E2E fixture replay test for WL-198 dead-letter flow."""

from __future__ import annotations

from pathlib import Path

import orjson as json
import pytest
from typer.testing import CliRunner

from thegent.cli.apps.sync import app
from thegent.commands.sync import SyncCommand


@pytest.mark.e2e
def test_dead_letter_replay_fixture_roundtrip(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fixture = Path("tests/fixtures/workstream_autosync/replay/remote_write_dead_letter_fixture.jsonl")
    queue_path = tmp_path / "dead-letter.jsonl"
    queue_path.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")

    def _always_success(
        self: SyncCommand,
        board_id: str,
        source: str,
        work_stream_items: list[dict[str, str]],
        *,
        write_batch_size: int = 50,
    ) -> dict[str, object]:
        _ = (self, board_id, source, write_batch_size)
        return {
            "synced": len(work_stream_items),
            "failed": 0,
            "updated_items": work_stream_items,
            "errors": [],
            "batches": 1,
        }

    monkeypatch.setattr(SyncCommand, "_perform_board_sync", _always_success)
    monkeypatch.setenv("THGENT_SYNC_DEAD_LETTER_PATH", str(queue_path))

    result = CliRunner().invoke(
        app,
        [
            "dead-letter-replay",
            "--source",
            "github",
            "--board",
            "kooshapari:1",
            "--limit",
            "10",
        ],
    )

    assert result.exit_code == 0
    assert "replayed=2" in result.stdout

    lines = queue_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    payload = [json.loads(line) for line in lines]
    assert all(entry["status"] == "replayed" for entry in payload)
