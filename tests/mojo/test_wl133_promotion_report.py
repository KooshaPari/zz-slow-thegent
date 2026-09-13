# @trace WL-133 B90-W3-B4
"""Tests for the WL-133 Mojo kernel promotion report.

Validates:
1. The Mojo promotion report document exists at the expected path.
2. The report mentions 'deterministic' (confirms replay validation scope).
3. The report mentions 'kernel' (confirms Mojo kernel promotion context).
"""

from __future__ import annotations

from pathlib import Path

REPORT_PATH = Path(__file__).parent.parent.parent / "docs" / "reports" / "2026-02-21-B90-W3-B4-mojo-promotion.md"


def test_mojo_promotion_report_exists() -> None:
    """The B90-W3-B4 Mojo promotion report must exist at the expected path."""
    assert REPORT_PATH.exists(), f"Expected Mojo promotion report at {REPORT_PATH}"


def test_mojo_promotion_report_mentions_deterministic() -> None:
    """The promotion report must mention 'deterministic' to confirm replay scope."""
    content = REPORT_PATH.read_text()
    assert "deterministic" in content.lower(), "Mojo promotion report must mention 'deterministic'"


def test_mojo_promotion_report_mentions_kernel() -> None:
    """The promotion report must mention 'kernel' to confirm Mojo kernel context."""
    content = REPORT_PATH.read_text()
    assert "kernel" in content.lower(), "Mojo promotion report must mention 'kernel'"
