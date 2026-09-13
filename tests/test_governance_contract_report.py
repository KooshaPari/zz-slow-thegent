"""Tests for governance contract strict report generation script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import orjson as json
import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.mark.unit
def test_governance_contract_report_generates_outputs(tmp_path: Path) -> None:
    dispatcher = _repo_root() / "hooks" / "hook-dispatcher" / "target" / "debug" / "hook-dispatcher"
    if not dispatcher.exists():
        pytest.skip("hook-dispatcher binary not built")

    json_out = tmp_path / "governance-contract-report.json"
    md_out = tmp_path / "governance-contract-report.md"
    script = _repo_root() / "scripts" / "governance_contract_report.py"

    proc = subprocess.run(
        [sys.executable, str(script), "--json-out", str(json_out), "--md-out", str(md_out)],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert json_out.exists()
    assert md_out.exists()

    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["total"] >= 1
    assert payload["failed"] == 0
    assert "Governance Contract Strict Report" in md_out.read_text(encoding="utf-8")
