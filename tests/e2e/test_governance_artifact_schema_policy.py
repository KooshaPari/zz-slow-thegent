"""Schema policy checks for governance artifact producers."""

from __future__ import annotations

from pathlib import Path

import orjson as json

from tests.e2e.test_governance_health_artifact import (
    test_governance_health_artifact_schema_and_counts,
)
from tests.e2e.test_governance_inventory_artifact import _inventory_payload


def test_inventory_schema_version_follows_vN_pattern() -> None:
    payload = _inventory_payload()
    version = payload["schema_version"]
    assert isinstance(version, str)
    assert version.endswith("-v1") or version.endswith("-v2")


def test_health_artifact_schema_stays_versioned(tmp_path: Path) -> None:
    # Reuse the health artifact generator test path; ensures schema exists and is versioned.
    test_governance_health_artifact_schema_and_counts(tmp_path)
    artifact_path = tmp_path / "e2e-governance-health.json"
    loaded = json.loads(artifact_path.read_text(encoding="utf-8"))
    schema = loaded.get("schema_version", "")
    assert isinstance(schema, str)
    assert schema.startswith("e2e-governance-health-")
    assert schema.rsplit("-", 1)[-1].startswith("v")
