# @trace WL-133 B90-W3-D4
"""Tests that validate the Mojo kernel fallback behavior report exists and is well-formed.

B90-W3-D4: Validate Mojo kernel fallback behavior.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent

MOJO_FALLBACK_REPORT = REPO_ROOT / "docs" / "reports" / "2026-02-21-B90-W3-D4-mojo-fallback.md"


def test_mojo_fallback_report_exists() -> None:
    """The Mojo fallback behavior report must exist."""
    assert MOJO_FALLBACK_REPORT.exists(), f"Mojo fallback report not found at {MOJO_FALLBACK_REPORT}"


def test_mojo_fallback_report_mentions_fallback() -> None:
    """The report must mention fallback behavior."""
    content = MOJO_FALLBACK_REPORT.read_text()
    assert "fallback" in content.lower(), "Mojo fallback report must mention 'fallback'"


def test_mojo_fallback_report_mentions_skip() -> None:
    """The report must mention skip or SKIP behavior (not hard-fail)."""
    content = MOJO_FALLBACK_REPORT.read_text()
    assert "skip" in content.lower(), "Mojo fallback report must mention 'skip' or 'SKIP' gate behavior"


def test_mojo_fallback_report_is_non_empty() -> None:
    """The Mojo fallback report must be non-empty."""
    content = MOJO_FALLBACK_REPORT.read_text()
    assert len(content.strip()) > 100, "Mojo fallback report appears empty"
