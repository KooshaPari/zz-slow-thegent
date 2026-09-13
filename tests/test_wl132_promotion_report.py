# @trace WL-132 B90-W3-B3
"""Tests for the WL-132 Zig ABI promotion report.

Validates:
1. The Zig promotion report document exists at the expected path.
2. The report mentions '1.0.0' (the ABI contract version).
3. The report mentions 'promotion' or 'ABI' (confirms scope).
"""

from __future__ import annotations

from pathlib import Path

REPORT_PATH = Path(__file__).parent.parent / "docs" / "reports" / "2026-02-21-B90-W3-B3-zig-promotion.md"


def test_zig_promotion_report_exists() -> None:
    """The B90-W3-B3 Zig promotion report must exist at the expected path."""
    assert REPORT_PATH.exists(), f"Expected Zig promotion report at {REPORT_PATH}"


def test_zig_promotion_report_mentions_version_1_0_0() -> None:
    """The promotion report must mention '1.0.0' (the ABI contract version)."""
    content = REPORT_PATH.read_text()
    assert "1.0.0" in content, "Zig promotion report must mention ABI contract version '1.0.0'"


def test_zig_promotion_report_mentions_promotion_or_abi() -> None:
    """The promotion report must mention 'promotion' or 'ABI' to confirm scope."""
    content = REPORT_PATH.read_text()
    assert "promotion" in content.lower() or "abi" in content.lower(), (
        "Zig promotion report must mention 'promotion' or 'ABI'"
    )
