"""Unit tests for CodebaseScanner and related models.

Tests the scanner's ability to run 8 governance dimensions:
test_coverage, lint_violations, doc_disorganization, fragmented_research,
missing_specs, technical_debt, stale_items, agent_failure.

Traces to: FR-GOV-001 (health score computation), FR-GOV-002 (dimension scanning)
"""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest.mock import patch

import orjson as json
import pytest

from thegent.governance.scanner import (
    CodebaseScanner,
    DimensionScan,
    ScanResult,
    _truncate,
)

if TYPE_CHECKING:
    from pathlib import Path


pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory with required structure."""
    (tmp_path / "src").mkdir(parents=True)
    (tmp_path / "src" / "test_module.py").write_text("# test module\n")
    (tmp_path / "tests").mkdir(parents=True)
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "docs" / "guides").mkdir(parents=True)
    (tmp_path / "docs" / "reference").mkdir(parents=True)
    (tmp_path / "docs" / "reports").mkdir(parents=True)
    (tmp_path / "specs").mkdir(parents=True)
    (tmp_path / "specs" / "approved").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def session_dir(tmp_path: Path) -> Path:
    """Create a temporary session directory."""
    session = tmp_path / ".thegent" / "sessions"
    session.mkdir(parents=True)
    return session


@pytest.fixture
def scanner(project_dir: Path, session_dir: Path) -> CodebaseScanner:
    """Return a CodebaseScanner instance."""
    return CodebaseScanner(project_dir, session_dir)


# ---------------------------------------------------------------------------
# _truncate helper
# ---------------------------------------------------------------------------


def test_truncate_under_limit() -> None:
    """Text under limit returns unchanged.

    Traces to: FR-GOV-001
    """
    text = "short text"
    assert _truncate(text, limit=100) == text


def test_truncate_over_limit() -> None:
    """Text over limit gets truncated with ellipsis.

    Traces to: FR-GOV-001
    """
    text = "a" * 600
    result = _truncate(text, limit=500)
    assert len(result) == 514  # 500 + "...[truncated]"
    assert result.endswith("[truncated]")


def test_truncate_exact_limit() -> None:
    """Text at exact limit returns unchanged.

    Traces to: FR-GOV-001
    """
    text = "a" * 500
    assert _truncate(text, limit=500) == text


# ---------------------------------------------------------------------------
# DimensionScan model
# ---------------------------------------------------------------------------


def test_dimension_scan_defaults() -> None:
    """DimensionScan accepts minimal args and fills defaults.

    Traces to: FR-GOV-001
    """
    scan = DimensionScan(
        dimension="test_coverage",
        current_value=75.0,
        target_value=80.0,
        delta=-5.0,
    )
    assert scan.dimension == "test_coverage"
    assert scan.current_value == 75.0
    assert scan.target_value == 80.0
    assert scan.delta == -5.0
    assert scan.raw_output == ""
    assert scan.affected_files == []
    assert scan.scan_duration_s == 0.0


def test_dimension_scan_full() -> DimensionScan:
    """DimensionScan accepts all fields.

    Traces to: FR-GOV-001
    """
    scan = DimensionScan(
        dimension="lint_violations",
        current_value=5.0,
        target_value=0.0,
        delta=-5.0,
        raw_output="5 violations found",
        affected_files=["src/foo.py", "src/bar.py"],
        scan_duration_s=1.234,
    )
    assert scan.raw_output == "5 violations found"
    assert scan.affected_files == ["src/foo.py", "src/bar.py"]
    assert scan.scan_duration_s == 1.234


# ---------------------------------------------------------------------------
# ScanResult model
# ---------------------------------------------------------------------------


def test_scan_result_defaults() -> None:
    """ScanResult fills defaults for empty inputs.

    Traces to: FR-GOV-001
    """
    result = ScanResult(dimensions={})
    assert result.dimensions == {}
    assert result.scanned_at is not None
    assert result.duration_s == 0.0
    assert result.project_dir == ""


def test_scan_result_full() -> None:
    """ScanResult accepts all fields.

    Traces to: FR-GOV-001
    """
    dim_scan = DimensionScan(
        dimension="test_coverage",
        current_value=80.0,
        target_value=80.0,
        delta=0.0,
    )
    result = ScanResult(
        dimensions={"test_coverage": dim_scan},
        duration_s=5.5,
        project_dir="/path/to/project",
    )
    assert result.dimensions["test_coverage"] == dim_scan
    assert result.duration_s == 5.5
    assert result.project_dir == "/path/to/project"


# ---------------------------------------------------------------------------
# CodebaseScanner initialization
# ---------------------------------------------------------------------------


def test_scanner_init(project_dir: Path, session_dir: Path) -> None:
    """Scanner initializes with resolved paths.

    Traces to: FR-GOV-002
    """
    scanner = CodebaseScanner(project_dir, session_dir)
    assert scanner.project_dir == project_dir.resolve()
    assert scanner.session_dir == session_dir.resolve()


def test_scanner_dimensions_list() -> None:
    """Scanner defines all 8 dimensions.

    Traces to: FR-GOV-002
    """
    expected = (
        "test_coverage",
        "lint_violations",
        "doc_disorganization",
        "fragmented_research",
        "missing_specs",
        "technical_debt",
        "stale_items",
        "agent_failure",
    )
    assert expected == CodebaseScanner._DIMENSIONS


# ---------------------------------------------------------------------------
# scan_dimension method
# ---------------------------------------------------------------------------


def test_scan_dimension_valid(scanner: CodebaseScanner) -> None:
    """scan_dimension returns DimensionScan for valid dimension name.

    Traces to: FR-GOV-002
    """
    result = scanner.scan_dimension("test_coverage")
    assert isinstance(result, DimensionScan)
    assert result.dimension == "test_coverage"


def test_scan_dimension_invalid(scanner: CodebaseScanner) -> None:
    """scan_dimension raises ValueError for unknown dimension.

    Traces to: FR-GOV-002
    """
    with pytest.raises(ValueError, match="unknown dimension"):
        scanner.scan_dimension("nonexistent")


# ---------------------------------------------------------------------------
# _scan_test_coverage
# ---------------------------------------------------------------------------


@patch("thegent.governance.scanner._run_tool")
def test_scan_test_coverage_success(mock_run: object, scanner: CodebaseScanner) -> None:
    """_scan_test_coverage parses pytest output correctly.

    Traces to: FR-GOV-002
    """
    mock_proc = type(
        "MockProc",
        (),
        {
            "stdout": "---------- coverage: platform darwin, python 3.12.1-final ---\nTOTAL    100    0   100%",
            "stderr": "",
        },
    )()
    mock_run.return_value = mock_proc

    result = scanner._scan_test_coverage()
    assert result.dimension == "test_coverage"
    assert result.target_value == 80.0
    assert result.current_value == 100.0


@patch("thegent.governance.scanner._run_tool")
def test_scan_test_coverage_no_match(mock_run: object, scanner: CodebaseScanner) -> None:
    """_scan_test_coverage returns 0 when no percentage found.

    Traces to: FR-GOV-002
    """
    mock_proc = type("MockProc", (), {"stdout": "no coverage data", "stderr": ""})()
    mock_run.return_value = mock_proc

    result = scanner._scan_test_coverage()
    assert result.current_value == 0.0


@patch("thegent.governance.scanner._run_tool")
def test_scan_test_coverage_file_not_found(mock_run: object, scanner: CodebaseScanner) -> None:
    """_scan_test_coverage handles pytest not installed gracefully.

    Traces to: FR-GOV-002
    """
    mock_run.side_effect = FileNotFoundError("pytest")

    result = scanner._scan_test_coverage()
    assert result.current_value == 0.0
    assert "pytest" in result.raw_output.lower()


@patch("thegent.governance.scanner._run_tool")
def test_scan_test_coverage_timeout(mock_run: object, scanner: CodebaseScanner) -> None:
    """_scan_test_coverage handles timeout gracefully.

    Traces to: FR-GOV-002
    """
    mock_run.side_effect = subprocess.TimeoutExpired("pytest", 120)

    result = scanner._scan_test_coverage()
    assert result.current_value == 0.0
    assert "timed out" in result.raw_output


# ---------------------------------------------------------------------------
# _scan_lint_violations
# ---------------------------------------------------------------------------


@patch("thegent.governance.scanner._run_tool")
def test_scan_lint_violations_success(mock_run: object, scanner: CodebaseScanner) -> None:
    """_scan_lint_violations counts ruff output lines correctly.

    Traces to: FR-GOV-002
    """
    mock_proc = type(
        "MockProc",
        (),
        {
            "stdout": "src/foo.py:1:1 E501 line too long\nsrc/bar.py:2:2 F401 unused import\n",
            "stderr": "",
        },
    )()
    mock_run.return_value = mock_proc

    result = scanner._scan_lint_violations()
    assert result.dimension == "lint_violations"
    assert result.target_value == 0.0
    assert result.current_value == 2.0


@patch("thegent.governance.scanner._run_tool")
def test_scan_lint_violations_empty(mock_run: object, scanner: CodebaseScanner) -> None:
    """_scan_lint_violations returns 0 for clean output.

    Traces to: FR-GOV-002
    """
    mock_proc = type("MockProc", (), {"stdout": "", "stderr": ""})()
    mock_run.return_value = mock_proc

    result = scanner._scan_lint_violations()
    assert result.current_value == 0.0


@patch("thegent.governance.scanner._run_tool")
def test_scan_lint_violations_file_not_found(mock_run: object, scanner: CodebaseScanner) -> None:
    """_scan_lint_violations handles ruff not installed gracefully.

    Traces to: FR-GOV-002
    """
    mock_run.side_effect = FileNotFoundError("ruff")

    result = scanner._scan_lint_violations()
    assert result.current_value == 0.0


# ---------------------------------------------------------------------------
# _scan_doc_disorganization
# ---------------------------------------------------------------------------


def test_scan_doc_disorganization_all_present(scanner: CodebaseScanner) -> None:
    """_scan_doc_disorganization returns 0 when all dirs exist.

    Traces to: FR-GOV-002
    """
    result = scanner._scan_doc_disorganization()
    assert result.dimension == "doc_disorganization"
    assert result.current_value == 0.0
    assert result.target_value == 0.0
    assert "present" in result.raw_output.lower()


def test_scan_doc_disorganization_missing_dirs(scanner: CodebaseScanner) -> None:
    """_scan_doc_disorganization counts missing required dirs.

    Traces to: FR-GOV-002
    """
    # Remove docs subdirs
    (scanner.project_dir / "docs" / "guides").rmdir()
    (scanner.project_dir / "docs" / "reference").rmdir()

    result = scanner._scan_doc_disorganization()
    assert result.current_value == 2.0
    assert "docs/guides" in result.affected_files
    assert "docs/reference" in result.affected_files


# ---------------------------------------------------------------------------
# _scan_fragmented_research
# ---------------------------------------------------------------------------


def test_scan_fragmented_research_no_research(scanner: CodebaseScanner) -> None:
    """_scan_fragmented_research returns 0 when no docs dir exists.

    Traces to: FR-GOV-002
    """
    result = scanner._scan_fragmented_research()
    assert result.dimension == "fragmented_research"
    assert result.current_value == 0.0


def test_scan_fragmented_research_organized(scanner: CodebaseScanner) -> None:
    """_scan_fragmented_research returns 0 when research in correct location.

    Traces to: FR-GOV-002
    """
    (scanner.project_dir / "docs" / "research").mkdir()
    (scanner.project_dir / "docs" / "research" / "note.md").write_text("# Research")

    result = scanner._scan_fragmented_research()
    assert result.current_value == 0.0


def test_scan_fragmented_research_fragmented(scanner: CodebaseScanner) -> None:
    """_scan_fragmented_research detects files outside docs/research/.

    Traces to: FR-GOV-002
    """
    (scanner.project_dir / "docs" / "guides" / "research_notes.md").write_text("# Notes")

    result = scanner._scan_fragmented_research()
    assert result.current_value == 1.0
    assert "docs/guides/research_notes.md" in result.affected_files


# ---------------------------------------------------------------------------
# _scan_missing_specs
# ---------------------------------------------------------------------------


def test_scan_missing_specs_no_approved_dir(scanner: CodebaseScanner) -> None:
    """_scan_missing_specs returns 0 when no approved dir exists.

    Traces to: FR-GOV-002
    """
    result = scanner._scan_missing_specs()
    assert result.dimension == "missing_specs"
    assert result.current_value == 0.0


def test_scan_missing_specs_all_have_spec(scanner: CodebaseScanner) -> None:
    """_scan_missing_specs returns 0 when all approved specs have SPEC.md.

    Traces to: FR-GOV-002
    """
    approved = scanner.project_dir / "specs" / "approved"
    (approved / "feature_1").mkdir()
    (approved / "feature_1" / "SPEC.md").write_text("# Spec")

    result = scanner._scan_missing_specs()
    assert result.current_value == 0.0


def test_scan_missing_specs_missing_files(scanner: CodebaseScanner) -> None:
    """_scan_missing_specs detects approved dirs without SPEC.md.

    Traces to: FR-GOV-002
    """
    approved = scanner.project_dir / "specs" / "approved"
    (approved / "feature_1").mkdir()
    (approved / "feature_2").mkdir()

    result = scanner._scan_missing_specs()
    assert result.current_value == 2.0
    assert "specs/approved/feature_1" in result.affected_files
    assert "specs/approved/feature_2" in result.affected_files


# ---------------------------------------------------------------------------
# _scan_technical_debt
# ---------------------------------------------------------------------------


@patch("thegent.governance.scanner._run_tool")
def test_scan_technical_debt_success(mock_run: object, scanner: CodebaseScanner) -> None:
    """_scan_technical_debt parses radon output correctly.

    Traces to: FR-GOV-002
    """
    mock_proc = type(
        "MockProc",
        (),
        {
            "stdout": "Average complexity: C (5.2)",
            "stderr": "",
        },
    )()
    mock_run.return_value = mock_proc

    result = scanner._scan_technical_debt()
    assert result.dimension == "technical_debt"
    assert result.target_value == 10.0
    assert result.current_value == 5.2


@patch("thegent.governance.scanner._run_tool")
def test_scan_technical_debt_no_match(mock_run: object, scanner: CodebaseScanner) -> None:
    """_scan_technical_debt returns 0 when no average found.

    Traces to: FR-GOV-002
    """
    mock_proc = type("MockProc", (), {"stdout": "no complexity data", "stderr": ""})()
    mock_run.return_value = mock_proc

    result = scanner._scan_technical_debt()
    assert result.current_value == 0.0


@patch("thegent.governance.scanner._run_tool")
def test_scan_technical_debt_file_not_found(mock_run: object, scanner: CodebaseScanner) -> None:
    """_scan_technical_debt handles radon not installed gracefully.

    Traces to: FR-GOV-002
    """
    mock_run.side_effect = FileNotFoundError("radon")

    result = scanner._scan_technical_debt()
    assert result.current_value == 0.0


# ---------------------------------------------------------------------------
# _scan_stale_items
# ---------------------------------------------------------------------------


def test_scan_stale_items_no_specs_dir(scanner: CodebaseScanner) -> None:
    """_scan_stale_items returns 0 when no specs dir exists.

    Traces to: FR-GOV-002
    """
    result = scanner._scan_stale_items()
    assert result.dimension == "stale_items"
    assert result.current_value == 0.0


def test_scan_stale_items_all_fresh(scanner: CodebaseScanner) -> None:
    """_scan_stale_items returns 0 when all files are recent.

    Traces to: FR-GOV-002
    """
    # Create a recent file
    (scanner.project_dir / "specs" / "test.md").write_text("# Spec")

    result = scanner._scan_stale_items()
    assert result.current_value == 0.0


def test_scan_stale_items_has_stale(scanner: CodebaseScanner) -> None:
    """_scan_stale_items detects files older than 7 days.

    Traces to: FR-GOV-002
    """
    import os
    import time

    stale_file = scanner.project_dir / "specs" / "old.md"
    stale_file.write_text("# Old spec")

    # Set mtime to 10 days ago
    old_time = time.time() - 10 * 86400
    os.utime(stale_file, (old_time, old_time))

    result = scanner._scan_stale_items()
    assert result.current_value == 1.0
    assert "specs/old.md" in result.affected_files


# ---------------------------------------------------------------------------
# _scan_agent_failure
# ---------------------------------------------------------------------------


def test_scan_agent_failure_no_file(scanner: CodebaseScanner) -> None:
    """_scan_agent_failure returns 0 when circuit_breakers.jsonl doesn't exist.

    Traces to: FR-GOV-002
    """
    result = scanner._scan_agent_failure()
    assert result.dimension == "agent_failure"
    assert result.current_value == 0.0


def test_scan_agent_failure_all_closed(scanner: CodebaseScanner) -> None:
    """_scan_agent_failure returns 0 when all breakers are closed.

    Traces to: FR-GOV-002
    """
    cb_file = scanner.session_dir / "circuit_breakers.jsonl"
    cb_file.write_text(
        json.dumps({"name": "agent1", "status": "CLOSED"}).decode()
        + "\n"
        + json.dumps({"name": "agent2", "status": "CLOSED"}).decode()
        + "\n"
    )

    result = scanner._scan_agent_failure()
    assert result.current_value == 0.0


def test_scan_agent_failure_open_breakers(scanner: CodebaseScanner) -> None:
    """_scan_agent_failure counts open circuit breakers.

    Traces to: FR-GOV-002
    """
    cb_file = scanner.session_dir / "circuit_breakers.jsonl"
    cb_file.write_text(
        json.dumps({"name": "agent1", "status": "OPEN"}).decode()
        + "\n"
        + json.dumps({"name": "agent2", "status": "CLOSED"}).decode()
        + "\n"
        + json.dumps({"status": "OPEN"}).decode()
        + "\n"
    )

    result = scanner._scan_agent_failure()
    assert result.current_value == 2.0
    assert "agent1" in result.affected_files
    assert "unknown" in result.affected_files


def test_scan_agent_failure_malformed_json(scanner: CodebaseScanner) -> None:
    """_scan_agent_failure skips malformed JSON lines.

    Traces to: FR-GOV-002
    """
    cb_file = scanner.session_dir / "circuit_breakers.jsonl"
    cb_file.write_text(
        json.dumps({"name": "agent1", "status": "OPEN"}).decode()
        + "\n"
        + "not valid json\n"
        + json.dumps({"name": "agent2", "status": "CLOSED"}).decode()
        + "\n"
    )

    result = scanner._scan_agent_failure()
    assert result.current_value == 1.0


# ---------------------------------------------------------------------------
# scan_all method (full scan)
# ---------------------------------------------------------------------------


def test_scan_all_returns_all_dimensions(scanner: CodebaseScanner) -> None:
    """scan_all returns ScanResult with all 8 dimensions.

    Traces to: FR-GOV-002
    """
    result = scanner.scan_all()
    assert isinstance(result, ScanResult)
    assert len(result.dimensions) == 8
    for dim_name in CodebaseScanner._DIMENSIONS:
        assert dim_name in result.dimensions


def test_scan_all_has_project_dir(scanner: CodebaseScanner) -> None:
    """scan_all populates project_dir in result.

    Traces to: FR-GOV-002
    """
    result = scanner.scan_all()
    assert result.project_dir == str(scanner.project_dir)


def test_scan_all_has_duration(scanner: CodebaseScanner) -> None:
    """scan_all records elapsed time.

    Traces to: FR-GOV-002
    """
    result = scanner.scan_all()
    assert result.duration_s > 0


def test_scan_all_has_timestamp(scanner: CodebaseScanner) -> None:
    """scan_all populates scanned_at timestamp.

    Traces to: FR-GOV-002
    """
    result = scanner.scan_all()
    assert result.scanned_at is not None
    # Verify it's a valid ISO timestamp
    from datetime import datetime

    parsed = datetime.fromisoformat(result.scanned_at)
    assert parsed.year >= 2020


# ---------------------------------------------------------------------------
# Error handling integration
# ---------------------------------------------------------------------------


def test_scanner_handles_nonexistent_project(tmp_path: Path, session_dir: Path) -> None:
    """Scanner handles nonexistent project directory gracefully.

    Traces to: FR-GOV-002
    """
    nonexistent = tmp_path / "nonexistent"
    scanner = CodebaseScanner(nonexistent, session_dir)

    # Directory checks should return 0 for missing dirs
    result = scanner._scan_doc_disorganization()
    assert result.current_value == 3.0  # All 3 required dirs missing
