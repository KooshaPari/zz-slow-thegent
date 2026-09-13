from __future__ import annotations

import subprocess
from pathlib import Path

import orjson as json


def test_wl358_cross_schema_validator_fails_without_evidence_policy(tmp_path: Path) -> None:
    req = tmp_path / "requirement.json"
    evidence = tmp_path / "evidence.json"
    attestation = tmp_path / "attestation.json"

    req.write_text(json.dumps({"id": "FR-TEST-001"}).decode(), encoding="utf-8")
    evidence.write_text(json.dumps({"requirement_id": "FR-TEST-001", "kind": "artifact"}).decode(), encoding="utf-8")
    attestation.write_text(json.dumps({"subject": []}).decode(), encoding="utf-8")

    script = Path(__file__).resolve().parents[1] / "hooks" / "qa-cross-schema-validator.sh"
    result = subprocess.run(
        ["bash", str(script), str(req), str(evidence), str(attestation)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "missing evidence_policy.required kinds" in result.stdout
