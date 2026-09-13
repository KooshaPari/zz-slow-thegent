# @trace WL-130 B90-W3-B1
"""Tests for the runtime modularization matrix v2 schema and content.

Validates that contracts/runtime/runtime-modularization-matrix-v2.json:
- Exists and is valid JSON
- Contains at least 5 workload entries
- Has a migration_status field in at least one entry
- All entries with migration_status="done" have a test_file field
"""

from __future__ import annotations

from pathlib import Path

import orjson as json
import pytest

MATRIX_V2_PATH = Path(__file__).parent.parent / "contracts" / "runtime" / "runtime-modularization-matrix-v2.json"


@pytest.fixture(scope="module")
def matrix_v2() -> dict:
    assert MATRIX_V2_PATH.exists(), f"Matrix v2 not found at {MATRIX_V2_PATH}"
    return json.loads(MATRIX_V2_PATH.read_text())


def test_runtime_matrix_v2_file_exists() -> None:
    """The v2 matrix file must exist at the expected path."""
    assert MATRIX_V2_PATH.exists(), f"Expected runtime-modularization-matrix-v2.json at {MATRIX_V2_PATH}"


def test_runtime_matrix_v2_is_valid_json() -> None:
    """The v2 matrix file must be valid JSON."""
    content = MATRIX_V2_PATH.read_text()
    parsed = json.loads(content)
    assert isinstance(parsed, dict), "Matrix v2 must be a JSON object at the root level"


def test_runtime_matrix_v2_has_workloads_key(matrix_v2: dict) -> None:
    """The v2 matrix must have a 'workloads' key."""
    assert "workloads" in matrix_v2, "Matrix v2 must have a 'workloads' key"


def test_runtime_matrix_v2_has_at_least_five_entries(matrix_v2: dict) -> None:
    """The v2 matrix must have at least 5 workload entries."""
    workloads = matrix_v2.get("workloads", [])
    assert len(workloads) >= 5, f"Matrix v2 must have at least 5 entries; got {len(workloads)}"


def test_runtime_matrix_v2_has_migration_status_field(matrix_v2: dict) -> None:
    """At least one workload entry must have a 'migration_status' field."""
    workloads = matrix_v2.get("workloads", [])
    entries_with_status = [w for w in workloads if "migration_status" in w]
    assert len(entries_with_status) >= 1, "At least one workload entry must have a 'migration_status' field"


def test_runtime_matrix_v2_done_entries_have_test_file(matrix_v2: dict) -> None:
    """All entries with migration_status='done' must have a 'test_file' field."""
    workloads = matrix_v2.get("workloads", [])
    done_entries = [w for w in workloads if w.get("migration_status") == "done"]
    for entry in done_entries:
        assert "test_file" in entry, (
            f"Entry '{entry.get('id', '?')}' has migration_status='done' but is missing 'test_file' field"
        )
        assert entry["test_file"] is not None, (
            f"Entry '{entry.get('id', '?')}' has migration_status='done' but 'test_file' is null/empty"
        )
        assert entry["test_file"] != "", (
            f"Entry '{entry.get('id', '?')}' has migration_status='done' but 'test_file' is null/empty"
        )


def test_runtime_matrix_v2_all_entries_have_id(matrix_v2: dict) -> None:
    """Every workload entry must have an 'id' field."""
    workloads = matrix_v2.get("workloads", [])
    for i, entry in enumerate(workloads):
        assert entry.get("id"), f"Workload entry at index {i} is missing 'id' field"


def test_runtime_matrix_v2_migration_status_values_valid(matrix_v2: dict) -> None:
    """All migration_status values must be one of the allowed set."""
    allowed = {"done", "in_progress", "blocked", "planned"}
    workloads = matrix_v2.get("workloads", [])
    for entry in workloads:
        if "migration_status" in entry:
            status = entry["migration_status"]
            assert status in allowed, (
                f"Entry '{entry.get('id', '?')}' has invalid migration_status '{status}'; allowed: {allowed}"
            )


def test_runtime_matrix_v2_wave2_entries_are_present(matrix_v2: dict) -> None:
    """Known Wave-2 entries (parse_model_suffix, zig-abi, mojo-kernel) must be present."""
    workloads = matrix_v2.get("workloads", [])
    ids = {w.get("id") for w in workloads}
    expected_ids = {
        "parse-model-suffixes-rust",
        "parse-model-suffix-python-baseline",
        "zig-abi-contract",
        "mojo-kernel-smoke",
    }
    for expected_id in expected_ids:
        assert expected_id in ids, f"Expected workload id '{expected_id}' not found in v2 matrix"
