# @trace WL-128 B90-W3-F2
"""Toolchain bootstrap verification tests for WL-128."""

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
REPORT = REPO_ROOT / "docs/reports/2026-02-21-B90-W3-F2-toolchain-bootstrap.md"


def test_f2_report_exists():
    assert REPORT.exists(), f"Report not found: {REPORT}"


def test_f2_report_mentions_pass():
    text = REPORT.read_text()
    assert "PASS" in text or "pass" in text.lower(), "Report must mention PASS or pass verdict"


def test_f2_report_mentions_taskfile():
    text = REPORT.read_text()
    assert "Taskfile.yml" in text, "Report must mention 'Taskfile.yml'"
