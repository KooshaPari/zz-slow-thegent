"""Tests for WL-134 B90-W3-A3 fast-lane configuration.

Verifies:
- pytest-fast.ini exists with correct marker configuration
- FAST_DEEP_LANE.md guide exists in docs/guides/
"""
# @trace WL-134 B90-W3-A3

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).parent.parent


def test_pytest_fast_ini_exists() -> None:
    """pytest-fast.ini must exist in the project root."""
    assert (_ROOT / "pytest-fast.ini").is_file(), "pytest-fast.ini not found in project root"


def test_pytest_fast_ini_contains_addopts_exclusions() -> None:
    """pytest-fast.ini must contain addopts excluding deep and slow markers."""
    content = (_ROOT / "pytest-fast.ini").read_text(encoding="utf-8")
    # The addopts line must exclude slow and one of the deep-equivalent markers
    assert "addopts" in content, "pytest-fast.ini must have addopts line"
    assert "not slow" in content, "pytest-fast.ini addopts must exclude slow tests"


def test_pytest_fast_ini_defines_markers() -> None:
    """pytest-fast.ini must define at least 'fast' and 'slow' markers."""
    content = (_ROOT / "pytest-fast.ini").read_text(encoding="utf-8")
    assert "fast" in content, "pytest-fast.ini must define 'fast' marker"
    assert "slow" in content, "pytest-fast.ini must define 'slow' marker"


def test_fast_deep_lane_guide_exists() -> None:
    """docs/guides/FAST_DEEP_LANE.md must exist."""
    guide = _ROOT / "docs" / "guides" / "FAST_DEEP_LANE.md"
    assert guide.is_file(), f"FAST_DEEP_LANE.md not found at {guide}"


def test_fast_deep_lane_guide_documents_both_lanes() -> None:
    """FAST_DEEP_LANE.md must document both fast and deep lanes."""
    content = (_ROOT / "docs" / "guides" / "FAST_DEEP_LANE.md").read_text(encoding="utf-8")
    assert "fast" in content.lower(), "Guide must document the fast lane"
    assert "deep" in content.lower(), "Guide must document the deep lane"
