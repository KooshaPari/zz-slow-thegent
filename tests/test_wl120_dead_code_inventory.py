# @trace WL-120 B90-W3-D1
"""Tests that verify the dead-code inventory report and split module artifacts exist.

B90-W3-D1: Remove dead code paths from pre-split modules (documentation phase).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

DEAD_CODE_REPORT = REPO_ROOT / "docs" / "reports" / "2026-02-21-B90-W3-D1-dead-code-inventory.md"
CLI_DAG_PATH = REPO_ROOT / "src" / "thegent" / "cli" / "commands" / "cli_dag.py"
CLI_TOOLING_PATH = REPO_ROOT / "src" / "thegent" / "cli" / "commands" / "cli_tooling.py"
IMPL_EXECUTION_PATH = REPO_ROOT / "src" / "thegent" / "cli" / "commands" / "impl_execution.py"


def test_dead_code_inventory_report_exists() -> None:
    """The dead-code inventory report must exist."""
    assert DEAD_CODE_REPORT.exists(), f"Dead code inventory report not found at {DEAD_CODE_REPORT}"


def test_dead_code_report_is_non_empty() -> None:
    """The dead-code inventory report must be non-empty."""
    content = DEAD_CODE_REPORT.read_text()
    assert len(content.strip()) > 100, "Dead code inventory report appears empty"


def test_dead_code_report_mentions_duplicate_functions() -> None:
    """The report must describe duplicate function status."""
    content = DEAD_CODE_REPORT.read_text()
    assert "DUPLICATE" in content, "Dead code report must identify DUPLICATE function entries"


def test_cli_dag_exists() -> None:
    """cli_dag.py must exist (canonical dag command location)."""
    assert CLI_DAG_PATH.exists(), f"cli_dag.py not found at {CLI_DAG_PATH}"


def test_cli_dag_is_non_empty() -> None:
    """cli_dag.py must be non-empty."""
    content = CLI_DAG_PATH.read_text()
    assert len(content.strip()) > 50, "cli_dag.py appears to be empty"


def test_cli_tooling_exists() -> None:
    """cli_tooling.py must exist (canonical tooling surface location)."""
    assert CLI_TOOLING_PATH.exists(), f"cli_tooling.py not found at {CLI_TOOLING_PATH}"


def test_cli_tooling_is_non_empty() -> None:
    """cli_tooling.py must be non-empty."""
    content = CLI_TOOLING_PATH.read_text()
    assert len(content.strip()) > 50, "cli_tooling.py appears to be empty"


def test_impl_execution_exists() -> None:
    """impl_execution.py must exist (execution boundary shim)."""
    assert IMPL_EXECUTION_PATH.exists(), f"impl_execution.py not found at {IMPL_EXECUTION_PATH}"
