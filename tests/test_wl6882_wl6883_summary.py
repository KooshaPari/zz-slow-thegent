"""WL-6882/WL-6883 closeout tests for summary diagnostics."""

import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import orjson as json
import pytest

from thegent import summary


def _time_range() -> tuple[datetime, datetime]:
    end = datetime.now(UTC)
    start = end - timedelta(days=1)
    return start, end


def test_wl6882_get_git_commits_non_repo_path_reports_not_repo(tmp_path: Path) -> None:
    start, end = _time_range()

    result = summary.get_git_commits(tmp_path, start, end)

    assert result.status == "not_repo"
    assert result.commits == []
    assert result.error is not None
    assert result.error["type"] == "not_repo"


def test_wl6882_get_git_commits_git_command_failure_reports_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / ".git").mkdir()
    start, end = _time_range()

    monkeypatch.setattr(
        summary.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            ["git", "log"], 128, stdout="", stderr="fatal: bad revision"
        ),
    )

    result = summary.get_git_commits(tmp_path, start, end)

    assert result.status == "error"
    assert result.commits == []
    assert result.error is not None
    assert result.error["type"] == "git_log_failed"
    assert result.error["returncode"] == 128


def test_wl6882_get_git_commits_empty_range_reports_empty(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    start, end = _time_range()

    monkeypatch.setattr(
        summary.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(["git", "log"], 0, stdout="", stderr=""),
    )

    result = summary.get_git_commits(tmp_path, start, end)

    assert result.status == "empty"
    assert result.commits == []
    assert result.error is None


def test_wl6883_read_log_file_tracks_mixed_valid_and_malformed_lines(tmp_path: Path) -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)
    path = tmp_path / "chat.jsonl"

    valid = {"type": "user", "timestamp": "2026-01-10T12:00:00+00:00", "message": {"content": "ok"}}
    path.write_text(
        "\n".join(
            [
                json.dumps(valid).decode(),
                "not-json",
                json.dumps(valid).decode(),
                "also-bad-json",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    payload = summary._read_log_file(path, start, end, include_diagnostics=True)

    assert payload["status"] == "ok"
    assert payload["entries"] == 2
    assert payload["parse_counts"]["malformed_json"] == 2
    assert len(payload["parse_counts"]["sampled_errors"]) == 2
