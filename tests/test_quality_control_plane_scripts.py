from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import orjson as json


def test_validate_quality_control_plane_script() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/validate_quality_control_plane.py",
            "--contract",
            "contracts/quality-control-plane-v1.json",
            "--schema",
            "schemas/quality-control-plane-v1.schema.json",
            "--strict-adr-match",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout.strip())
    assert payload["status"] == "ok"
    assert payload["selected_plane"] == "github_sarif_native"


def test_quality_control_plane_report_script(tmp_path: Path) -> None:
    contract = tmp_path / "control-plane.json"
    artifact = tmp_path / "existing-artifact.json"
    artifact.write_text("{}", encoding="utf-8")
    contract.write_text(
        json.dumps(
            {
                "version": "1.0.0",
                "selected_plane": "github_sarif_native",
                "policy_mode": "contract_first",
                "adapters": {
                    "github_code_scanning": {"enabled": True, "sarif_required": True},
                    "sonar_bridge": {"enabled": False, "mode": "optional_downstream"},
                },
                "required_artifacts": [str(artifact).decode(), str(tmp_path / "missing.json")],
                "gates": {
                    "allow_missing_artifacts_in_pr": True,
                    "require_contract_validation_in_nightly": True,
                },
            }
        ),
        encoding="utf-8",
    )
    json_out = tmp_path / "out.json"
    md_out = tmp_path / "out.md"

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/quality_control_plane_report.py",
            "--contract",
            str(contract),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["required_artifacts_total"] == 2
    assert payload["required_artifacts_present"] == 1
    assert md_out.exists()
