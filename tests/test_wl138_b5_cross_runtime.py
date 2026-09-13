# @trace WL-138 B90-W3-B5
"""Tests for the B90-W3-B5 cross-runtime promotion summary.

Validates:
1. The cross-runtime summary report exists at the expected path.
2. The report mentions all 4 runtimes: Python, Rust, Zig, Mojo.
3. The report contains Wave-4 or next-action guidance.
"""

from __future__ import annotations

from pathlib import Path

REPORT_PATH = Path(__file__).parent.parent / "docs" / "reports" / "2026-02-21-B90-W3-B5-cross-runtime-summary.md"


def test_cross_runtime_summary_exists() -> None:
    """The B90-W3-B5 cross-runtime summary must exist at the expected path."""
    assert REPORT_PATH.exists(), f"Expected cross-runtime summary at {REPORT_PATH}"


def test_cross_runtime_summary_mentions_python() -> None:
    """The summary must mention 'Python' as one of the 4 runtimes."""
    content = REPORT_PATH.read_text()
    assert "Python" in content, "Cross-runtime summary must mention 'Python'"


def test_cross_runtime_summary_mentions_rust() -> None:
    """The summary must mention 'Rust' as one of the 4 runtimes."""
    content = REPORT_PATH.read_text()
    assert "Rust" in content, "Cross-runtime summary must mention 'Rust'"


def test_cross_runtime_summary_mentions_zig() -> None:
    """The summary must mention 'Zig' as one of the 4 runtimes."""
    content = REPORT_PATH.read_text()
    assert "Zig" in content, "Cross-runtime summary must mention 'Zig'"


def test_cross_runtime_summary_mentions_mojo() -> None:
    """The summary must mention 'Mojo' as one of the 4 runtimes."""
    content = REPORT_PATH.read_text()
    assert "Mojo" in content, "Cross-runtime summary must mention 'Mojo'"


def test_cross_runtime_summary_has_wave4_or_next_action() -> None:
    """The summary must contain Wave-4 or next-action guidance."""
    content = REPORT_PATH.read_text()
    assert "Wave-4" in content or "next action" in content.lower(), (
        "Cross-runtime summary must mention 'Wave-4' or 'next action' guidance"
    )
