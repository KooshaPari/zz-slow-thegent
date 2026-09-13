"""Tests for WL-134 deep-lane marker and gating command.

Verifies that:
1. The 'deep' marker is registered in pyproject.toml.
2. At least one test file contains @pytest.mark.deep.
3. Taskfile has test:deep and test:gate tasks.

# @trace WL-134 B90-W2-C3
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
PYPROJECT = ROOT / "pyproject.toml"
TASKFILE = ROOT / "Taskfile.yml"
TESTS_DIR = ROOT / "tests"


class TestDeepMarkerRegistration:
    """deep marker must be registered in pyproject.toml pytest markers list."""

    # @trace WL-134 B90-W2-C3

    def test_deep_marker_in_pyproject(self) -> None:
        """pyproject.toml must have 'deep' in the pytest markers list."""
        text = PYPROJECT.read_text()
        assert '"deep:' in text or '"deep ' in text, (
            "pyproject.toml must have 'deep' marker registered under [tool.pytest.ini_options] markers"
        )

    def test_fast_marker_in_pyproject(self) -> None:
        """pyproject.toml must have 'fast' in the pytest markers list."""
        text = PYPROJECT.read_text()
        assert '"fast:' in text or '"fast ' in text, (
            "pyproject.toml must have 'fast' marker registered under [tool.pytest.ini_options] markers"
        )


class TestDeepMarkerUsage:
    """At least one test file must use @pytest.mark.deep."""

    # @trace WL-134 B90-W2-C3

    def test_at_least_one_deep_marked_test_exists(self) -> None:
        """At least one test file must contain @pytest.mark.deep."""
        deep_files = []
        for py_file in TESTS_DIR.rglob("test_*.py"):
            content = py_file.read_text()
            if "@pytest.mark.deep" in content:
                deep_files.append(str(py_file))
        assert len(deep_files) >= 1, f"No test files found with @pytest.mark.deep. Expected at least one in {TESTS_DIR}"

    def test_deep_tests_are_collectible(self) -> None:
        """pytest --collect-only -m deep must exit 0 (collect without error)."""
        result = subprocess.run(
            ["uv", "run", "pytest", "--collect-only", "-m", "deep", "-q", "--tb=no"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        # exit 5 = no tests collected (acceptable if marker is registered)
        # exit 0 = tests collected
        assert result.returncode in (0, 5), (
            f"pytest collection with -m deep failed (rc={result.returncode}):\n{result.stderr}"
        )


class TestTaskfileGatingTasks:
    """Taskfile must have test:deep and test:gate tasks."""

    # @trace WL-134 B90-W2-C3

    def test_test_deep_task_exists(self) -> None:
        """Taskfile must have a 'test:deep' task."""
        text = TASKFILE.read_text()
        assert "  test:deep:" in text, "Taskfile.yml must have a 'test:deep' task"

    def test_test_gate_task_exists(self) -> None:
        """Taskfile must have a 'test:gate' task."""
        text = TASKFILE.read_text()
        assert "  test:gate:" in text, "Taskfile.yml must have a 'test:gate' task"

    def test_test_fast_lane_task_exists(self) -> None:
        """Taskfile must have a 'test:fast-lane' task."""
        text = TASKFILE.read_text()
        assert "  test:fast-lane:" in text, "Taskfile.yml must have a 'test:fast-lane' task"
