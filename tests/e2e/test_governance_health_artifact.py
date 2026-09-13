"""Governance health artifact sanity checks."""

from __future__ import annotations

from pathlib import Path

import orjson as json

from tests.e2e.test_split_hygiene import (
    REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND,
    REQUIRED_E2E_GOVERNANCE_FILES,
)


def _bundle_paths() -> list[str]:
    return [
        token
        for token in REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND.split()
        if token.startswith("tests/") and token.endswith(".py")
    ]


def test_governance_health_artifact_schema_and_counts(tmp_path: Path) -> None:
    missing_files = [str(path) for path in REQUIRED_E2E_GOVERNANCE_FILES if not path.exists()]
    bundle_paths = _bundle_paths()

    artifact = {
        "schema_version": "e2e-governance-health-v1",
        "required_files_count": len(REQUIRED_E2E_GOVERNANCE_FILES),
        "bundle_paths_count": len(bundle_paths),
        "missing_files": missing_files,
    }

    output_path = tmp_path / "e2e-governance-health.json"
    output_path.write_text(json.dumps(artifact, sort_keys=True).decode(), encoding="utf-8")

    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded["schema_version"] == "e2e-governance-health-v1"
    assert loaded["required_files_count"] >= 1
    assert loaded["bundle_paths_count"] >= 1
    assert loaded["missing_files"] == []
