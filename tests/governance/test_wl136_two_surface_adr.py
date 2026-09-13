"""Tests for WL-136 B90-W3-A2 two-surface architecture ADR documents.

Verifies the existence and content of the three ADR docs in
docs/changes/two-surface-architecture/.
"""
# @trace WL-136 B90-W3-A2

from __future__ import annotations

from pathlib import Path

_ADR_DIR = Path(__file__).parent.parent.parent / "docs" / "changes" / "two-surface-architecture"


def test_proposal_md_exists() -> None:
    """docs/changes/two-surface-architecture/proposal.md must exist."""
    assert (_ADR_DIR / "proposal.md").is_file(), "proposal.md not found"


def test_design_md_exists() -> None:
    """docs/changes/two-surface-architecture/design.md must exist."""
    assert (_ADR_DIR / "design.md").is_file(), "design.md not found"


def test_tasks_md_exists() -> None:
    """docs/changes/two-surface-architecture/tasks.md must exist."""
    assert (_ADR_DIR / "tasks.md").is_file(), "tasks.md not found"


def test_proposal_mentions_core_and_tooling() -> None:
    """proposal.md must mention both 'core' and 'tooling' surfaces."""
    content = (_ADR_DIR / "proposal.md").read_text(encoding="utf-8")
    assert "core" in content, "proposal.md must mention 'core' surface"
    assert "tooling" in content, "proposal.md must mention 'tooling' surface"


def test_design_mentions_import_boundary() -> None:
    """design.md must document the import boundary rule."""
    content = (_ADR_DIR / "design.md").read_text(encoding="utf-8")
    assert "import boundary" in content.lower(), "design.md must mention 'import boundary'"


def test_tasks_mentions_wave4_extractions() -> None:
    """tasks.md must reference Wave-4 remaining extractions."""
    content = (_ADR_DIR / "tasks.md").read_text(encoding="utf-8")
    assert "Wave-4" in content or "wave-4" in content.lower(), "tasks.md must mention Wave-4 remaining extractions"
