"""Tests for WL-138 B90-W3-A5 decomposition signoff document.

Verifies:
- The signoff document exists
- It contains Wave-1, Wave-2, and Wave-3 sections
- It contains the DONE marker
"""
# @trace WL-138 B90-W3-A5

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).parent.parent
_SIGNOFF_DOC = _ROOT / "docs" / "reports" / "2026-02-21-B90-W3-A5-decomposition-signoff.md"


def test_signoff_doc_exists() -> None:
    """docs/reports/2026-02-21-B90-W3-A5-decomposition-signoff.md must exist."""
    assert _SIGNOFF_DOC.is_file(), f"Signoff doc not found at {_SIGNOFF_DOC}"


def test_signoff_doc_contains_all_three_waves() -> None:
    """Signoff document must contain Wave-1, Wave-2, and Wave-3 sections."""
    content = _SIGNOFF_DOC.read_text(encoding="utf-8")
    assert "Wave-1" in content, "Signoff must contain Wave-1 section"
    assert "Wave-2" in content, "Signoff must contain Wave-2 section"
    assert "Wave-3" in content, "Signoff must contain Wave-3 section"


def test_signoff_doc_contains_done_marker() -> None:
    """Signoff document must contain at least one DONE marker."""
    content = _SIGNOFF_DOC.read_text(encoding="utf-8")
    assert "DONE" in content, "Signoff must contain at least one DONE marker"
