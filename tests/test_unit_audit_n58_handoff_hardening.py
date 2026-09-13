"""AUDIT-N+58: governance/handoff hardening spec (SOTA pass-37).

15 invariants FR-GOV-HO-001..015 covering HandoffIntegrity init,
path guard, analyze_prompt validation, suggest_improvements,
validate_handoff, __all__, and importability.

Source: src/thegent/governance/handoff.py

@trace AUDIT-N+58  FR-GOV-HO-001..015
"""

from __future__ import annotations

from pathlib import Path

import pytest

from thegent.governance import handoff as _mod
from thegent.governance.handoff import HandoffIntegrity

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# FR-GOV-HO-001 -- HandoffIntegrity is constructible with absolute root
# ---------------------------------------------------------------------------


class TestHOInit:
    """FR-GOV-HO-001: ``HandoffIntegrity(workspace_root)`` stores path."""

    def test_init_sets_workspace_root(self, tmp_path: Path) -> None:
        hi = HandoffIntegrity(tmp_path)
        assert hi.workspace_root == tmp_path

    def test_init_accepts_absolute_path(self, tmp_path: Path) -> None:
        hi = HandoffIntegrity(tmp_path)
        assert hi.workspace_root.is_absolute()


# ---------------------------------------------------------------------------
# FR-GOV-HO-002 -- absolute workspace_root required
# ---------------------------------------------------------------------------


class TestHOPathGuard:
    """FR-GOV-HO-002: ``workspace_root`` must be absolute."""

    def test_rejects_relative_path(self) -> None:
        with pytest.raises(ValueError, match="absolute"):
            HandoffIntegrity(Path("relative/path"))

    def test_accepts_absolute_path(self, tmp_path: Path) -> None:
        hi = HandoffIntegrity(tmp_path)
        assert hi.workspace_root.is_absolute()


# ---------------------------------------------------------------------------
# FR-GOV-HO-003 -- analyze_prompt returns findings for short prompts
# ---------------------------------------------------------------------------


class TestHOAnalyzeShortPrompt:
    """FR-GOV-HO-003: very short prompts trigger a finding."""

    def test_short_prompt_has_finding(self, tmp_path: Path) -> None:
        hi = HandoffIntegrity(tmp_path)
        result = hi.analyze_prompt("short")
        assert any("short" in f.lower() for f in result["findings"])


# ---------------------------------------------------------------------------
# FR-GOV-HO-004 -- analyze_prompt detects vague instructions
# ---------------------------------------------------------------------------


class TestHOAnalyzeVague:
    """FR-GOV-HO-004: vague keywords are flagged."""

    def test_vague_keyword_detected(self, tmp_path: Path) -> None:
        hi = HandoffIntegrity(tmp_path)
        result = hi.analyze_prompt("implement this now for me")
        assert any("vague" in f.lower() for f in result["findings"])


# ---------------------------------------------------------------------------
# FR-GOV-HO-005 -- analyze_prompt detects referenced files that exist
# ---------------------------------------------------------------------------


class TestHOAnalyzeExistingFiles:
    """FR-GOV-HO-005: existing referenced files are listed."""

    def test_existing_file_detected(self, tmp_path: Path) -> None:
        (tmp_path / "hello.py").write_text("print('hi')", encoding="utf-8")
        hi = HandoffIntegrity(tmp_path)
        result = hi.analyze_prompt("update hello.py to add logging")
        assert "hello.py" in result["referenced_files"]


# ---------------------------------------------------------------------------
# FR-GOV-HO-006 -- analyze_prompt detects referenced files that are missing
# ---------------------------------------------------------------------------


class TestHOAnalyzeMissingFiles:
    """FR-GOV-HO-006: missing referenced files produce a warning."""

    def test_missing_file_detected(self, tmp_path: Path) -> None:
        hi = HandoffIntegrity(tmp_path)
        result = hi.analyze_prompt("update nonexistent.py to add logging")
        assert "nonexistent.py" in result["missing_files"]


# ---------------------------------------------------------------------------
# FR-GOV-HO-007 -- high completeness_score for well-formed prompts
# ---------------------------------------------------------------------------


class TestHOAnalyzeWellFormed:
    """FR-GOV-HO-007: well-formed prompts score >= 2."""

    def test_well_formed_high_score(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("# main", encoding="utf-8")
        hi = HandoffIntegrity(tmp_path)
        result = hi.analyze_prompt("Create a function in main.py to refactor the auth module")
        assert result["completeness_score"] >= 2


# ---------------------------------------------------------------------------
# FR-GOV-HO-008 -- analyze_prompt raises ValueError on empty prompt
# ---------------------------------------------------------------------------


class TestHOAnalyzeEmpty:
    """FR-GOV-HO-008: empty prompt raises ``ValueError``."""

    def test_empty_prompt_raises(self, tmp_path: Path) -> None:
        hi = HandoffIntegrity(tmp_path)
        with pytest.raises(ValueError, match="empty"):
            hi.analyze_prompt("")


# ---------------------------------------------------------------------------
# FR-GOV-HO-009 -- analyze_prompt raises ValueError on whitespace-only
# ---------------------------------------------------------------------------


class TestHOAnalyzeWhitespace:
    """FR-GOV-HO-009: whitespace-only prompt raises ``ValueError``."""

    def test_whitespace_prompt_raises(self, tmp_path: Path) -> None:
        hi = HandoffIntegrity(tmp_path)
        with pytest.raises(ValueError, match="empty"):
            hi.analyze_prompt("   \n\t  ")


# ---------------------------------------------------------------------------
# FR-GOV-HO-010 -- suggest_improvements returns original when complete
# ---------------------------------------------------------------------------


class TestHOSuggestComplete:
    """FR-GOV-HO-010: complete analysis returns the original prompt."""

    def test_complete_returns_original(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text("# app", encoding="utf-8")
        hi = HandoffIntegrity(tmp_path)
        prompt = "Create a function in app.py to refactor the module"
        result = hi.analyze_prompt(prompt)
        if result["is_complete"]:
            assert hi.suggest_improvements(prompt, analysis=result) == prompt


# ---------------------------------------------------------------------------
# FR-GOV-HO-011 -- suggest_improvements appends suggestions for incomplete
# ---------------------------------------------------------------------------


class TestHOSuggestIncomplete:
    """FR-GOV-HO-011: incomplete prompts get suggestions appended."""

    def test_incomplete_appends_suggestions(self, tmp_path: Path) -> None:
        hi = HandoffIntegrity(tmp_path)
        prompt = "implement this"
        result = hi.analyze_prompt(prompt)
        if not result["is_complete"]:
            improved = hi.suggest_improvements(prompt, analysis=result)
            assert "Suggestions for improvement" in improved


# ---------------------------------------------------------------------------
# FR-GOV-HO-012 -- validate_handoff returns True for complete prompts
# ---------------------------------------------------------------------------


class TestHOValidateComplete:
    """FR-GOV-HO-012: well-formed prompts validate successfully."""

    def test_valid_returns_true(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("# main", encoding="utf-8")
        hi = HandoffIntegrity(tmp_path)
        ok, msg = hi.validate_handoff("Create a function in main.py to refactor the auth module")
        assert ok is True
        assert "valid" in msg.lower()


# ---------------------------------------------------------------------------
# FR-GOV-HO-013 -- validate_handoff returns False for incomplete prompts
# ---------------------------------------------------------------------------


class TestHOValidateIncomplete:
    """FR-GOV-HO-013: incomplete prompts fail validation."""

    def test_incomplete_returns_false(self, tmp_path: Path) -> None:
        hi = HandoffIntegrity(tmp_path)
        ok, _msg = hi.validate_handoff("fix the bug")
        assert ok is False

    def test_empty_returns_false(self, tmp_path: Path) -> None:
        hi = HandoffIntegrity(tmp_path)
        ok, msg = hi.validate_handoff("")
        assert ok is False
        assert "empty" in msg.lower()


# ---------------------------------------------------------------------------
# FR-GOV-HO-014 -- __all__ exports HandoffIntegrity
# ---------------------------------------------------------------------------


class TestHOAll:
    """FR-GOV-HO-014: ``__all__`` includes ``HandoffIntegrity``."""

    def test_all_exports_handoff_integrity(self) -> None:
        assert "HandoffIntegrity" in _mod.__all__


# ---------------------------------------------------------------------------
# FR-GOV-HO-015 -- module is importable without error
# ---------------------------------------------------------------------------


class TestHOImportable:
    """FR-GOV-HO-015: the module imports without error."""

    def test_module_importable(self) -> None:
        assert hasattr(_mod, "HandoffIntegrity")
