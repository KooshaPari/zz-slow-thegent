from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import orjson as json


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_unified_quality_summary_aggregator_emits_schema_valid_payload(tmp_path: Path) -> None:
    hooks = tmp_path / "artifacts" / "hooks"
    quality = tmp_path / "artifacts" / "quality"
    hooks.mkdir(parents=True)
    quality.mkdir(parents=True)

    (hooks / "quality-gate-result.json").write_text(
        json.dumps({"schema_version": "thegent-hooks-result/v1", "status": "passed"}).decode(),
        encoding="utf-8",
    )
    (hooks / "security-pipeline-result.json").write_text(
        json.dumps({"schema_version": "thegent-hooks-result/v1", "status": "done"}).decode(),
        encoding="utf-8",
    )
    (quality / "control-plane-readiness.json").write_text(
        json.dumps({"schema_version": "quality-control-plane-readiness/v1"}).decode(),
        encoding="utf-8",
    )
    output = quality / "unified-quality-summary.json"

    proc = subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "scripts" / "aggregate_unified_quality_summary.py"),
            "--output",
            str(output),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "unified-quality-summary/v1"
    assert payload["overall_status"] in {"ok", "warn", "fail"}
    assert any(item["name"] == "quality_gate_result" for item in payload["components"])
