from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

import orjson as json
import pytest

from thegent import summary


def test_get_git_commits_reports_error_metadata(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 2, tzinfo=UTC)

    monkeypatch.setattr(
        summary.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 128, stdout="", stderr="fatal: bad revision"),
    )

    result = summary.get_git_commits(tmp_path, start, end)

    assert result.status == "error"
    assert result.error is not None
    assert result.error["type"] == "git_log_failed"
    assert result.error["returncode"] == 128


def test_read_log_file_tracks_invalid_timestamp_and_json_sample(tmp_path: Path) -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)
    path = tmp_path / "chat.jsonl"

    valid = {"type": "user", "timestamp": "2026-01-10T12:00:00+00:00", "message": {"content": "ok"}}
    bad_ts = {"type": "assistant", "timestamp": "not-a-date", "message": {"content": "bad"}}
    path.write_text(
        json.dumps(valid).decode() + "\n" + "not-json\n" + json.dumps(bad_ts).decode() + "\n", encoding="utf-8"
    )

    payload = summary._read_log_file(path, start, end, include_diagnostics=True)

    assert payload["entries"] == 1
    assert payload["parse_counts"]["malformed_json"] == 1
    assert payload["parse_counts"]["invalid_timestamp"] == 1
    assert payload["parse_counts"]["sampled_errors"]


def test_read_log_file_tracks_mixed_valid_and_malformed_lines_with_bounded_samples(tmp_path: Path) -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)
    path = tmp_path / "chat.jsonl"
    long_bad = "x" * 1000

    valid = {"type": "user", "timestamp": "2026-01-10T12:00:00+00:00", "message": {"content": "ok"}}
    path.write_text(
        "\n".join(
            [
                json.dumps(valid).decode(),
                "not-json",
                long_bad,
                json.dumps(valid).decode(),
                "not-json-again",
                long_bad * 2,
                "also-bad",
            ]
            + ["not-json"] * 20
        )
        + "\n",
        encoding="utf-8",
    )

    payload = summary._read_log_file(path, start, end, include_diagnostics=True)

    assert payload["entries"] == 2
    assert payload["parse_counts"]["malformed_json"] == 25
    assert len(payload["parse_counts"]["sampled_errors"]) == 5
    assert all(len(sample) <= 300 for sample in payload["parse_counts"]["sampled_errors"])
