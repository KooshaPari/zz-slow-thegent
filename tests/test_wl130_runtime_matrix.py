# @trace WL-130 B90-W2-B1
"""Tests for the runtime modularization matrix artifact.

Validates that contracts/runtime/runtime-modularization-matrix.json
conforms to the expected schema and contains complete, non-empty data
for all required workloads.
"""

from __future__ import annotations

from pathlib import Path

import orjson as json
import pytest

MATRIX_PATH = (
    Path(__file__).parent.parent
    / "contracts"
    / "runtime"
    / "runtime-modularization-matrix.json"
)

REQUIRED_TOP_LEVEL_FIELDS = {"version", "generated", "source", "workloads"}
REQUIRED_WORKLOAD_FIELDS = {
    "id",
    "description",
    "current_surface",
    "target_runtime",
    "priority",
    "benchmark_gate",
    "rollback_strategy",
    "owner",
    "migration_status",
}
EXPECTED_WORKLOAD_IDS = {
    "cli-dispatch",
    "policy-gate-evaluation",
    "mcp-transport",
    "low-level-memory",
    "deterministic-scoring",
}


@pytest.fixture(scope="module")
def matrix() -> dict:
    assert MATRIX_PATH.exists(), f"Matrix artifact not found at {MATRIX_PATH}"
    return json.loads(MATRIX_PATH.read_text())


def test_matrix_file_exists():
    assert MATRIX_PATH.exists(), f"Expected matrix at {MATRIX_PATH}"


def test_top_level_fields_present(matrix: dict):
    missing = REQUIRED_TOP_LEVEL_FIELDS - matrix.keys()
    assert not missing, f"Missing top-level fields: {missing}"


def test_version_field_non_empty(matrix: dict):
    assert matrix["version"], "version must be non-empty"


def test_generated_field_non_empty(matrix: dict):
    assert matrix["generated"], "generated must be non-empty"


def test_source_references_wl130(matrix: dict):
    assert "WL-130" in matrix["source"], "source must reference WL-130"


def test_workloads_is_list(matrix: dict):
    assert isinstance(matrix["workloads"], list), "workloads must be a list"


def test_exactly_five_workloads(matrix: dict):
    assert len(matrix["workloads"]) == 5, (
        f"Expected 5 workloads, got {len(matrix['workloads'])}"
    )


def test_all_expected_workload_ids_present(matrix: dict):
    ids = {w["id"] for w in matrix["workloads"]}
    missing = EXPECTED_WORKLOAD_IDS - ids
    assert not missing, f"Missing workload ids: {missing}"


@pytest.mark.parametrize(
    "workload_id",
    list(EXPECTED_WORKLOAD_IDS),
)
def test_workload_has_required_fields(matrix: dict, workload_id: str):
    workload = next((w for w in matrix["workloads"] if w["id"] == workload_id), None)
    assert workload is not None, f"Workload {workload_id!r} not found"
    missing = REQUIRED_WORKLOAD_FIELDS - workload.keys()
    assert not missing, f"Workload {workload_id!r} missing fields: {missing}"


@pytest.mark.parametrize(
    "workload_id",
    list(EXPECTED_WORKLOAD_IDS),
)
def test_workload_benchmark_gate_non_empty(matrix: dict, workload_id: str):
    workload = next(w for w in matrix["workloads"] if w["id"] == workload_id)
    gate = workload.get("benchmark_gate", "")
    assert gate and gate.strip(), f"Workload {workload_id!r} has empty benchmark_gate"


@pytest.mark.parametrize(
    "workload_id",
    list(EXPECTED_WORKLOAD_IDS),
)
def test_workload_rollback_strategy_non_empty(matrix: dict, workload_id: str):
    workload = next(w for w in matrix["workloads"] if w["id"] == workload_id)
    strategy = workload.get("rollback_strategy", "")
    assert strategy and strategy.strip(), (
        f"Workload {workload_id!r} has empty rollback_strategy"
    )


@pytest.mark.parametrize(
    "workload_id",
    list(EXPECTED_WORKLOAD_IDS),
)
def test_workload_priority_valid(matrix: dict, workload_id: str):
    workload = next(w for w in matrix["workloads"] if w["id"] == workload_id)
    priority = workload.get("priority", "")
    assert priority in {"P0", "P1", "P2", "P3"}, (
        f"Workload {workload_id!r} has invalid priority: {priority!r}"
    )


def test_workload_ids_are_unique(matrix: dict):
    ids = [w["id"] for w in matrix["workloads"]]
    assert len(ids) == len(set(ids)), "Workload ids must be unique"


def test_all_workloads_have_non_empty_description(matrix: dict):
    for w in matrix["workloads"]:
        assert w.get("description", "").strip(), (
            f"Workload {w['id']!r} has empty description"
        )


def test_all_workloads_have_non_empty_owner(matrix: dict):
    for w in matrix["workloads"]:
        assert w.get("owner", "").strip(), f"Workload {w['id']!r} has empty owner"


# noqa: PT018
