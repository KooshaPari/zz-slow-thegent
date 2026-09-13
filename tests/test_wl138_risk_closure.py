# @trace WL-138 B90-W3-D5
"""Tests that validate the Wave-3 risk closure status report.

B90-W3-D5: Add final risk closure status report.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

RISK_CLOSURE_REPORT = REPO_ROOT / "docs" / "reports" / "2026-02-21-B90-W3-D5-risk-closure.md"


def test_risk_closure_report_exists() -> None:
    """The risk closure report must exist."""
    assert RISK_CLOSURE_REPORT.exists(), f"Risk closure report not found at {RISK_CLOSURE_REPORT}"


def test_risk_closure_report_mentions_open_risks() -> None:
    """The report must mention OPEN risks."""
    content = RISK_CLOSURE_REPORT.read_text()
    assert "OPEN" in content, "Risk closure report must mention OPEN risks"


def test_risk_closure_report_mentions_resolved_risk() -> None:
    """The report must mention at least one RESOLVED risk."""
    content = RISK_CLOSURE_REPORT.read_text()
    assert "RESOLVED" in content or "closed" in content.lower(), (
        "Risk closure report must mention RESOLVED or closed risks"
    )


def test_risk_closure_report_has_at_least_five_risks() -> None:
    """The report must enumerate at least 5 risks."""
    content = RISK_CLOSURE_REPORT.read_text()
    # Count Risk N: lines (headings) or Risk entries in table
    risk_count = content.count("### Risk ") + content.count("| R")
    assert risk_count >= 5, f"Risk closure report must enumerate at least 5 risks; found indicators: {risk_count}"


def test_risk_closure_report_is_non_empty() -> None:
    """The risk closure report must be non-empty."""
    content = RISK_CLOSURE_REPORT.read_text()
    assert len(content.strip()) > 100, "Risk closure report appears empty"


def test_risk_closure_report_mentions_wave_4_actions() -> None:
    """The report must describe Wave-4 actions for open risks."""
    content = RISK_CLOSURE_REPORT.read_text()
    assert "Wave-4" in content or "wave-4" in content.lower(), "Risk closure report must reference Wave-4 action items"
