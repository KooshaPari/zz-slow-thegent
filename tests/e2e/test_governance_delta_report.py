"""Delta-report contracts for required e2e governance registry files."""

from __future__ import annotations

from pathlib import Path

import orjson as json

from tests.e2e.test_split_hygiene import REPO_ROOT

BASELINE_FIXTURE = Path(__file__).with_name("templates") / "governance_registry_baseline.json"


def _load_baseline_payload() -> dict[str, object]:
    payload = json.loads(BASELINE_FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_governance_baseline_fixture_schema_contract() -> None:
    payload = _load_baseline_payload()

    required_fields = {"schema_version", "paths"}
    assert required_fields == set(payload.keys())
    assert payload["schema_version"] == "e2e-governance-registry-baseline-v1"
    assert isinstance(payload["schema_version"], str)
    assert isinstance(payload["paths"], list)
    assert all(isinstance(path, str) for path in payload["paths"])
    assert payload["paths"] == sorted(payload["paths"])


def test_governance_delta_report_added_removed_deterministic_ordering(
    tmp_path: Path,
) -> None:
    baseline_paths = [
        "tests/e2e/test_zeta.py",
        "tests/e2e/test_alpha.py",
        "tests/e2e/test_gamma.py",
    ]
    current_paths = [
        "tests/e2e/test_beta.py",
        "tests/e2e/test_alpha.py",
        "tests/e2e/test_theta.py",
    ]
    baseline_sorted = sorted(baseline_paths)
    current_sorted = sorted(current_paths)
    baseline_set = set(baseline_sorted)
    current_set = set(current_sorted)

    added = sorted(path for path in current_sorted if path not in baseline_set)
    removed = sorted(path for path in baseline_sorted if path not in current_set)

    report = {
        "schema_version": "e2e-governance-delta-report-v1",
        "baseline_fixture": str(BASELINE_FIXTURE.relative_to(REPO_ROOT)),
        "baseline_count": len(baseline_sorted),
        "current_count": len(current_sorted),
        "baseline_paths": baseline_sorted,
        "current_paths": current_sorted,
        "added": added,
        "removed": removed,
    }

    output_path = tmp_path / "e2e-governance-delta-report.json"
    output_path.write_text(json.dumps(report, sort_keys=True).decode(), encoding="utf-8")
    loaded = json.loads(output_path.read_text(encoding="utf-8"))

    assert loaded["added"] == [
        "tests/e2e/test_beta.py",
        "tests/e2e/test_theta.py",
    ]
    assert loaded["removed"] == [
        "tests/e2e/test_gamma.py",
        "tests/e2e/test_zeta.py",
    ]
