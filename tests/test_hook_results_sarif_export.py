from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import orjson as json


def test_export_hook_results_to_sarif(tmp_path: Path) -> None:
    quality = tmp_path / "quality.json"
    quality.write_text(
        json.dumps(
            {
                "schema_version": "thegent-hooks-result/v1",
                "hook": "quality-gate",
                "generated_at": "2026-02-22T00:00:00Z",
                "status": "failed",
                "exit_code": 1,
                "summary": {"duration_ms": 100},
                "checks": [{"name": "Python (ruff).decode()", "status": "failed"}],
            }
        ),
        encoding="utf-8",
    )
    security = tmp_path / "security.json"
    security.write_text(
        json.dumps(
            {
                "schema_version": "thegent-hooks-result/v1",
                "hook": "security-pipeline",
                "generated_at": "2026-02-22T00:00:01Z",
                "status": "done",
                "exit_code": 0,
                "summary": {"total_findings": 1},
                "checks": [{"name": "Layer 1 - Secrets", "status": "warn", "findings": 1}],
            }
        ).decode(),
        encoding="utf-8",
    )
    output = tmp_path / "hooks.sarif"

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/export_hook_results_to_sarif.py",
            "--input",
            str(quality),
            str(security),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["version"] == "2.1.0"
    run = payload["runs"][0]
    assert len(run["results"]) == 2
    levels = sorted(result["level"] for result in run["results"])
    assert levels == ["error", "warning"]
