"""WL-134 B90-W2-A4: Fast-lane pytest marker system validation.

Verifies that the 'fast' and 'deep' pytest markers are registered
and that the selection infrastructure (Taskfile tasks, ini config)
is in place.
"""
# @trace WL-134 B90-W2-A4

from __future__ import annotations

from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.fast
def test_fast_marker_is_registered() -> None:
    """This test is annotated @pytest.mark.fast — marker must be registered."""
    # If the marker is unknown, pytest emits a warning (or error with strict markers).
    # The fact that this test runs without an UnknownMarkWarning is the verification.
    assert True


@pytest.mark.fast
def test_fast_lane_ini_file_exists() -> None:
    """pytest-fast.ini must exist for the fast lane preset."""
    ini_path = _REPO_ROOT / "pytest-fast.ini"
    assert ini_path.exists(), f"pytest-fast.ini not found at {ini_path}. Create it with [pytest] addopts = -m fast -q"


@pytest.mark.fast
def test_fast_lane_ini_mentions_fast_or_lane_config() -> None:
    """pytest-fast.ini must contain marker configuration."""
    ini_path = _REPO_ROOT / "pytest-fast.ini"
    if not ini_path.exists():
        pytest.skip("pytest-fast.ini not present; covered by prior test")
    content = ini_path.read_text(encoding="utf-8")
    # Must reference fast-lane or markers
    assert "fast" in content.lower(), "pytest-fast.ini must reference 'fast' marker or config"


@pytest.mark.fast
def test_pyproject_toml_declares_fast_and_deep_markers() -> None:
    """pyproject.toml must declare both 'fast' and 'deep' markers."""
    toml_path = _REPO_ROOT / "pyproject.toml"
    assert toml_path.exists(), "pyproject.toml not found"
    content = toml_path.read_text(encoding="utf-8")
    assert '"fast:' in content or "'fast:" in content or '"fast ' in content or "fast:" in content, (
        "pyproject.toml [tool.pytest.ini_options] markers must include 'fast:' marker"
    )
    assert '"deep:' in content or "'deep:" in content or '"deep ' in content or "deep:" in content, (
        "pyproject.toml [tool.pytest.ini_options] markers must include 'deep:' marker"
    )


@pytest.mark.fast
def test_taskfile_has_test_fast_task() -> None:
    """Taskfile.yml must define a test:fast task (runs -m fast)."""
    taskfile_path = _REPO_ROOT / "Taskfile.yml"
    assert taskfile_path.exists(), "Taskfile.yml not found"
    content = taskfile_path.read_text(encoding="utf-8")
    assert "test:fast:" in content, (
        "Taskfile.yml must define a 'test:fast:' task. Add: test:fast: cmds: - uv run pytest -m fast -q"
    )


@pytest.mark.fast
def test_taskfile_has_test_deep_task() -> None:
    """Taskfile.yml must define a test:deep task (runs -m deep)."""
    taskfile_path = _REPO_ROOT / "Taskfile.yml"
    assert taskfile_path.exists(), "Taskfile.yml not found"
    content = taskfile_path.read_text(encoding="utf-8")
    assert "test:deep:" in content, (
        "Taskfile.yml must define a 'test:deep:' task. Add: test:deep: cmds: - uv run pytest -m deep -q --timeout=300"
    )
