"""Tests for runtime matrix sync into governance summary (WL-130 B90-W3-E3).
# @trace WL-130 B90-W3-E3
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
GOVERNANCE_SUMMARY = ROOT / "docs" / "governance" / "GOVERNANCE_SUMMARY.md"
RUNTIME_MATRIX = ROOT / "contracts" / "runtime" / "runtime-modularization-matrix.json"


def test_governance_summary_exists() -> None:
    """docs/governance/GOVERNANCE_SUMMARY.md must exist."""
    assert GOVERNANCE_SUMMARY.exists(), f"Expected {GOVERNANCE_SUMMARY} to exist"


def test_governance_summary_contains_runtime_matrix_reference() -> None:
    """GOVERNANCE_SUMMARY.md must mention Runtime Matrix or runtime-modularization-matrix."""
    content = GOVERNANCE_SUMMARY.read_text(encoding="utf-8")
    assert "Runtime Matrix" in content or "runtime-modularization-matrix" in content, (
        "Expected 'Runtime Matrix' or 'runtime-modularization-matrix' in GOVERNANCE_SUMMARY.md"
    )


def test_runtime_matrix_json_exists() -> None:
    """contracts/runtime/runtime-modularization-matrix.json must exist."""
    assert RUNTIME_MATRIX.exists(), f"Expected {RUNTIME_MATRIX} to exist"


def test_runtime_matrix_json_valid() -> None:
    """runtime-modularization-matrix.json must be valid JSON with workloads list."""
    import json

    data = json.loads(RUNTIME_MATRIX.read_text(encoding="utf-8"))
    assert "workloads" in data, "Expected 'workloads' key in runtime-modularization-matrix.json"
    assert isinstance(data["workloads"], list), "Expected 'workloads' to be a list"
    assert len(data["workloads"]) > 0, "Expected at least one workload in matrix"
