"""Tests for WL-134 fast lane fail-fast enforcement.

# @trace WL-134 B90-W2-E2
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
PYTEST_FAST_INI = ROOT / "pytest-fast.ini"
PYPROJECT = ROOT / "pyproject.toml"
TASKFILE = ROOT / "Taskfile.yml"


def test_pytest_fast_ini_exists() -> None:
    """pytest-fast.ini must exist for opt-in fail-fast fast lane (WL-134)."""
    assert PYTEST_FAST_INI.exists(), "pytest-fast.ini must exist at project root"


def test_pytest_fast_ini_has_exitfirst() -> None:
    """pytest-fast.ini must configure --exitfirst for fail-fast behavior."""
    content = PYTEST_FAST_INI.read_text(encoding="utf-8")
    assert "--exitfirst" in content, "pytest-fast.ini must include --exitfirst in addopts"


def test_pytest_fast_ini_excludes_slow_markers() -> None:
    """pytest-fast.ini must exclude slow/integration/e2e/load markers."""
    content = PYTEST_FAST_INI.read_text(encoding="utf-8")
    assert "not slow" in content, "pytest-fast.ini must exclude 'slow' marker"
    assert "not integration" in content, "pytest-fast.ini must exclude 'integration' marker"
    assert "not e2e" in content, "pytest-fast.ini must exclude 'e2e' marker"


def test_pyproject_fast_lane_marker_defined() -> None:
    """pyproject.toml must define the fast lane marker expression."""
    content = PYPROJECT.read_text(encoding="utf-8")
    assert "fast_lane_marker" in content, "pyproject.toml must define fast_lane_marker in [tool.thegent.pytest_lanes]"


def test_pyproject_addopts_not_globally_set_to_exitfirst() -> None:
    """Global addopts in pyproject.toml must NOT include --exitfirst (fail-fast is opt-in only)."""
    content = PYPROJECT.read_text(encoding="utf-8")
    # Find the [tool.pytest.ini_options] section and verify --exitfirst is absent
    in_pytest_section = False
    for line in content.splitlines():
        if "[tool.pytest.ini_options]" in line:
            in_pytest_section = True
        if in_pytest_section and line.startswith("[") and "[tool.pytest.ini_options]" not in line:
            break
        if in_pytest_section and "--exitfirst" in line:
            raise AssertionError(
                "--exitfirst must NOT appear in global [tool.pytest.ini_options] addopts; "
                "it is opt-in via pytest-fast.ini only"
            )


def test_taskfile_fast_lane_uses_fast_ini() -> None:
    """Taskfile.yml test:fast-lane must use pytest-fast.ini for opt-in fail-fast."""
    content = TASKFILE.read_text(encoding="utf-8")
    assert "pytest-fast.ini" in content, "Taskfile.yml test:fast-lane must reference pytest-fast.ini"
