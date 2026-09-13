# @trace WL-138 B90-W3-F5
"""B90 program closeout report validation for WL-138."""

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
REPORT = REPO_ROOT / "docs/reports/2026-02-21-B90-W3-F5-closeout.md"


def test_f5_report_exists():
    assert REPORT.exists(), f"Report not found: {REPORT}"


def test_f5_report_mentions_closeout():
    text = REPORT.read_text()
    assert "Closeout" in text or "closeout" in text.lower(), "Report must mention 'Closeout' or 'closeout'"


def test_f5_report_mentions_all_waves():
    text = REPORT.read_text()
    assert "Wave-1" in text, "Report must mention 'Wave-1'"
    assert "Wave-2" in text, "Report must mention 'Wave-2'"
    assert "Wave-3" in text, "Report must mention 'Wave-3'"


def test_f5_report_mentions_next_cycle():
    text = REPORT.read_text()
    assert "Next Cycle" in text or "next cycle" in text.lower() or "Wave-4" in text, (
        "Report must mention 'Next Cycle' or 'Wave-4'"
    )
