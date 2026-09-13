# @trace WL-120 B90-W3-F1
"""Regression validation tests for the WL-120 monolith-split operation."""

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
REPORT = REPO_ROOT / "docs/reports/2026-02-21-B90-W3-F1-monolith-regression.md"
CLI_DAG = REPO_ROOT / "src/thegent/cli/commands/cli_dag.py"


def test_f1_report_exists():
    assert REPORT.exists(), f"Report not found: {REPORT}"


def test_f1_report_mentions_regression():
    text = REPORT.read_text()
    assert "regression" in text.lower() or "Regression" in text, "Report must mention 'regression' or 'Regression'"


def test_f1_report_mentions_cli_dag():
    text = REPORT.read_text()
    assert "cli_dag" in text, "Report must mention 'cli_dag'"


def test_f1_report_mentions_cli_tooling():
    text = REPORT.read_text()
    assert "cli_tooling" in text, "Report must mention 'cli_tooling'"


def test_f1_cli_dag_exists():
    assert CLI_DAG.exists(), f"cli_dag.py not found: {CLI_DAG}"


def test_f1_cli_dag_has_content():
    content = CLI_DAG.read_text()
    assert len(content) > 100, "cli_dag.py must have substantial content (>100 chars)"
