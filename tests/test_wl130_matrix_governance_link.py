"""Tests for WL-130 runtime matrix governance link.

# @trace WL-130 B90-W2-E3
"""

from __future__ import annotations

from pathlib import Path

import orjson as json

ROOT = Path(__file__).parent.parent
MATRIX_JSON = ROOT / "contracts" / "runtime" / "runtime-modularization-matrix.json"
GOVERNANCE_SUMMARY = ROOT / "docs" / "governance" / "GOVERNANCE_SUMMARY.md"
MODERNIZATION_PLAN = ROOT / "docs" / "plans" / "2026-02-21-MODERNIZATION-MASTER-PLAN.md"


def test_runtime_matrix_json_exists() -> None:
    """Machine-readable runtime modularization matrix must exist."""
    assert MATRIX_JSON.exists(), f"Expected {MATRIX_JSON} to exist"


def test_runtime_matrix_json_is_valid() -> None:
    """Runtime matrix JSON must be valid and contain expected structure."""
    data = json.loads(MATRIX_JSON.read_text(encoding="utf-8"))
    assert "workloads" in data, "Matrix must have 'workloads' key"
    assert isinstance(data["workloads"], list), "'workloads' must be a list"
    assert len(data["workloads"]) > 0, "Matrix must have at least one workload entry"


def test_governance_summary_mentions_runtime_matrix() -> None:
    """GOVERNANCE_SUMMARY.md must reference the runtime-modularization-matrix."""
    content = GOVERNANCE_SUMMARY.read_text(encoding="utf-8")
    assert "runtime-modularization-matrix" in content, (
        "GOVERNANCE_SUMMARY.md must reference 'runtime-modularization-matrix'"
    )


def test_governance_summary_has_wl130_section() -> None:
    """GOVERNANCE_SUMMARY.md must have a Runtime Modularization Matrix section."""
    content = GOVERNANCE_SUMMARY.read_text(encoding="utf-8")
    assert "Runtime Modularization Matrix" in content, (
        "GOVERNANCE_SUMMARY.md must include '## Runtime Modularization Matrix' section"
    )


def test_governance_summary_has_wl130_table() -> None:
    """GOVERNANCE_SUMMARY.md Runtime Modularization section must have a table."""
    content = GOVERNANCE_SUMMARY.read_text(encoding="utf-8")
    assert "| Workload |" in content, "GOVERNANCE_SUMMARY.md must include workload table"


def test_modernization_plan_references_machine_readable_contract() -> None:
    """Modernization master plan must reference the machine-readable contract file."""
    content = MODERNIZATION_PLAN.read_text(encoding="utf-8")
    assert "contracts/runtime/runtime-modularization-matrix.json" in content, (
        "Modernization plan must reference the machine-readable contract path"
    )
