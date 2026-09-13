"""Tests for governance contract history diff script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import orjson as json
import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.mark.unit
def test_governance_contract_history_diff_handles_missing_previous(tmp_path: Path) -> None:
    current = tmp_path / "current.json"
    current.write_text(
        json.dumps(
            {
                "total": 2,
                "passed": 2,
                "failed": 0,
                "results": [
                    {"name": "a", "ok": True, "details": "ok"},
                    {"name": "b", "ok": True, "details": "ok"},
                ],
            }
        ).decode()
        + "\n",
        encoding="utf-8",
    )
    diff_json = tmp_path / "diff.json"
    diff_md = tmp_path / "diff.md"
    script = _repo_root() / "scripts" / "governance_contract_history_diff.py"

    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--prev-json",
            str(tmp_path / "missing.json"),
            "--current-json",
            str(current),
            "--json-out",
            str(diff_json),
            "--md-out",
            str(diff_md),
        ],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(diff_json.read_text(encoding="utf-8"))
    assert payload["previous_available"] is False
    assert payload["current_failed"] == 0
    assert "Previous available: False" in diff_md.read_text(encoding="utf-8")


@pytest.mark.unit
def test_governance_contract_history_diff_reports_changed_checks(tmp_path: Path) -> None:
    prev = tmp_path / "prev.json"
    current = tmp_path / "current.json"
    prev.write_text(
        json.dumps(
            {
                "total": 2,
                "passed": 2,
                "failed": 0,
                "results": [
                    {"name": "a", "ok": True, "details": "ok"},
                    {"name": "b", "ok": True, "details": "ok"},
                ],
            }
        ).decode()
        + "\n",
        encoding="utf-8",
    )
    current.write_text(
        json.dumps(
            {
                "total": 2,
                "passed": 1,
                "failed": 1,
                "results": [
                    {"name": "a", "ok": False, "details": "fail"},
                    {"name": "b", "ok": True, "details": "ok"},
                ],
            }
        ).decode()
        + "\n",
        encoding="utf-8",
    )
    diff_json = tmp_path / "diff.json"
    diff_md = tmp_path / "diff.md"
    script = _repo_root() / "scripts" / "governance_contract_history_diff.py"

    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--prev-json",
            str(prev),
            "--current-json",
            str(current),
            "--json-out",
            str(diff_json),
            "--md-out",
            str(diff_md),
        ],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(diff_json.read_text(encoding="utf-8"))
    assert payload["previous_available"] is True
    assert payload["failed_delta"] == 1
    assert payload["changed_checks"] == [{"name": "a", "prev_ok": True, "curr_ok": False}]
