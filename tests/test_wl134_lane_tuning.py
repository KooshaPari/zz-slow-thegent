"""Tests for lane split tuning artifacts (WL-134 B90-W3-E2).
# @trace WL-134 B90-W3-E2
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPORT = ROOT / "docs" / "reports" / "2026-02-21-B90-W3-E2-lane-split-tuning.md"
FAST_INI = ROOT / "pytest-fast.ini"


def test_lane_tuning_report_exists() -> None:
    """The lane split tuning report file must exist."""
    assert REPORT.exists(), f"Expected report at {REPORT}"


def test_lane_tuning_report_mentions_fast_lane() -> None:
    """The report must mention 'fast lane' (case-insensitive)."""
    content = REPORT.read_text(encoding="utf-8")
    assert re.search(r"fast.?lane", content, re.IGNORECASE), "Expected 'fast lane' or 'Fast lane' in lane tuning report"


def test_lane_tuning_report_mentions_test_count() -> None:
    """The report must mention a numeric test count."""
    content = REPORT.read_text(encoding="utf-8")
    # Look for any number >= 3 digits (at least hundreds) as a test count
    assert re.search(r"\b\d{3,}\b", content), "Expected a numeric test count (3+ digits) in lane tuning report"


def test_pytest_fast_ini_exists() -> None:
    """pytest-fast.ini must exist in project root."""
    assert FAST_INI.exists(), f"Expected pytest-fast.ini at {FAST_INI}"
