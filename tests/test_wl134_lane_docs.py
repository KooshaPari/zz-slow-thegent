"""Tests for WL-134: Fast/Deep/Gate lane documentation and opt-in controls.

Validates that the lane documentation and configuration files exist and contain
the required content for developers to understand the test lane system.

# @trace WL-134 B90-W3-C2
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
LANE_DOCS = ROOT / "docs" / "guides" / "FAST_DEEP_LANE.md"
PYTEST_FAST_INI = ROOT / "pytest-fast.ini"
TASKFILE = ROOT / "Taskfile.yml"


# @trace WL-134 B90-W3-C2
def test_fast_deep_lane_doc_exists() -> None:
    """docs/guides/FAST_DEEP_LANE.md must exist."""
    assert LANE_DOCS.exists(), f"FAST_DEEP_LANE.md not found at {LANE_DOCS}. Create it per WL-134 B90-W3-C2 spec."


# @trace WL-134 B90-W3-C2
def test_fast_deep_lane_doc_contains_fast_lane() -> None:
    """FAST_DEEP_LANE.md must document the Fast Lane section."""
    text = LANE_DOCS.read_text(encoding="utf-8")
    assert "Fast Lane" in text, "FAST_DEEP_LANE.md is missing a 'Fast Lane' section."


# @trace WL-134 B90-W3-C2
def test_fast_deep_lane_doc_contains_deep_lane() -> None:
    """FAST_DEEP_LANE.md must document the Deep Lane section."""
    text = LANE_DOCS.read_text(encoding="utf-8")
    assert "Deep Lane" in text, "FAST_DEEP_LANE.md is missing a 'Deep Lane' section."


# @trace WL-134 B90-W3-C2
def test_fast_deep_lane_doc_contains_deep_marker() -> None:
    """FAST_DEEP_LANE.md must show the @pytest.mark.deep marker usage."""
    text = LANE_DOCS.read_text(encoding="utf-8")
    assert "@pytest.mark.deep" in text, "FAST_DEEP_LANE.md does not show @pytest.mark.deep usage example."


# @trace WL-134 B90-W3-C2
def test_pytest_fast_ini_exists() -> None:
    """pytest-fast.ini must exist."""
    assert PYTEST_FAST_INI.exists(), f"pytest-fast.ini not found at {PYTEST_FAST_INI}."


# @trace WL-134 B90-W3-C2
def test_pytest_fast_ini_has_addopts() -> None:
    """pytest-fast.ini must define addopts to restrict which tests run."""
    text = PYTEST_FAST_INI.read_text(encoding="utf-8")
    assert "addopts" in text, (
        "pytest-fast.ini does not contain an 'addopts' directive. "
        "The fast lane requires addopts to restrict test markers."
    )


# @trace WL-134 B90-W3-C2
def test_taskfile_contains_test_deep() -> None:
    """Taskfile.yml must define a test:deep task."""
    text = TASKFILE.read_text(encoding="utf-8")
    assert "test:deep" in text, (
        "Taskfile.yml does not contain a 'test:deep' task. Required by WL-134 for deep lane opt-in."
    )
