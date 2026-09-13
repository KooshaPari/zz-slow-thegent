"""Tests for VS Code extension status document (WL-117 B90-W3-E4).
# @trace WL-117 B90-W3-E4
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
STATUS_DOC = ROOT / "docs" / "plans" / "WL-117-VSCODE-EXTENSION-STATUS-2026-02-21.md"


def test_extension_status_doc_exists() -> None:
    """WL-117 VS Code extension status document must exist."""
    assert STATUS_DOC.exists(), f"Expected status doc at {STATUS_DOC}"


def test_extension_status_doc_references_wl104() -> None:
    """Status doc must reference WL-104 dependency."""
    content = STATUS_DOC.read_text(encoding="utf-8")
    assert "WL-104" in content or "WL104" in content, "Expected 'WL-104' or 'WL104' reference in extension status doc"


def test_extension_status_doc_mentions_decision() -> None:
    """Status doc must mention DEFERRED, BLOCKED, or scaffold."""
    content = STATUS_DOC.read_text(encoding="utf-8")
    assert any(keyword in content for keyword in ("DEFERRED", "BLOCKED", "scaffold")), (
        "Expected 'DEFERRED', 'BLOCKED', or 'scaffold' in extension status doc"
    )
