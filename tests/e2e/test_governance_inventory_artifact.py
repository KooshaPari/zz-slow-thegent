"""Governance inventory artifact contracts."""

from __future__ import annotations

from pathlib import Path

import orjson as json

from tests.e2e.test_split_hygiene import REQUIRED_E2E_GOVERNANCE_FILES


def _inventory_payload() -> dict[str, object]:
    paths = sorted(str(path) for path in REQUIRED_E2E_GOVERNANCE_FILES)
    return {
        "schema_version": "e2e-governance-inventory-v1",
        "count": len(paths),
        "paths": paths,
    }


def test_governance_inventory_artifact_schema(tmp_path: Path) -> None:
    payload = _inventory_payload()
    out = tmp_path / "e2e-governance-inventory.json"
    out.write_text(json.dumps(payload, sort_keys=True).decode(), encoding="utf-8")

    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["schema_version"] == "e2e-governance-inventory-v1"
    assert isinstance(loaded["count"], int)
    assert loaded["count"] >= 1
    assert isinstance(loaded["paths"], list)
    assert len(loaded["paths"]) == loaded["count"]


def test_governance_inventory_paths_are_sorted_and_unique() -> None:
    paths = _inventory_payload()["paths"]
    assert isinstance(paths, list)
    assert paths == sorted(paths)
    assert len(paths) == len(set(paths))
