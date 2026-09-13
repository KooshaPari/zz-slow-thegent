"""Tests for WL-138: Wave retrospective notes validation.

Validates that the B90 wave retrospective document exists and contains
the required sections summarizing all three waves.

# @trace WL-138 B90-W3-C5
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
RETRO_DOC = ROOT / "docs" / "reports" / "2026-02-21-B90-W3-C5-wave-retrospective.md"


# @trace WL-138 B90-W3-C5
def test_retrospective_doc_exists() -> None:
    """The wave retrospective document must exist."""
    assert RETRO_DOC.exists(), f"Retrospective document not found at {RETRO_DOC}."


# @trace WL-138 B90-W3-C5
def test_retrospective_mentions_wave_1() -> None:
    """Retrospective must mention Wave-1."""
    text = RETRO_DOC.read_text(encoding="utf-8")
    assert "Wave-1" in text, "Retrospective document does not mention 'Wave-1'."


# @trace WL-138 B90-W3-C5
def test_retrospective_mentions_wave_2() -> None:
    """Retrospective must mention Wave-2."""
    text = RETRO_DOC.read_text(encoding="utf-8")
    assert "Wave-2" in text, "Retrospective document does not mention 'Wave-2'."


# @trace WL-138 B90-W3-C5
def test_retrospective_mentions_wave_3() -> None:
    """Retrospective must mention Wave-3."""
    text = RETRO_DOC.read_text(encoding="utf-8")
    assert "Wave-3" in text, "Retrospective document does not mention 'Wave-3'."


# @trace WL-138 B90-W3-C5
def test_retrospective_mentions_anti_patterns() -> None:
    """Retrospective must document anti-patterns encountered during the B90 waves."""
    text = RETRO_DOC.read_text(encoding="utf-8")
    # Accept either capitalisation
    assert "anti-pattern" in text.lower() or "Anti-pattern" in text or "Anti-Pattern" in text, (
        "Retrospective document does not mention anti-patterns."
    )
