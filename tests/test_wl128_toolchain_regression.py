"""Regression tests for deduped toolchain flow (WL-128 B90-W2-F2).

Verifies that dedup changes to pyproject.toml and Taskfile.yml have not
introduced syntax errors, duplicate sections, or broken the existing
canonical toolchain entrypoints.

# @trace WL-128 B90-W2-F2
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
TASKFILE = ROOT / "Taskfile.yml"


class TestPyprojectTomlValidity:
    """pyproject.toml must parse as valid TOML with no duplicate [tool.X] sections."""

    # @trace WL-128 B90-W2-F2

    def test_pyproject_is_valid_toml(self) -> None:
        """pyproject.toml must parse without errors after dedup changes."""
        import tomllib  # stdlib since 3.11

        content = PYPROJECT.read_text(encoding="utf-8")
        parsed = tomllib.loads(content)
        assert isinstance(parsed, dict), "TOML parse must return a dict"

    def test_no_duplicate_tool_ruff_section(self) -> None:
        """pyproject.toml must contain exactly one [tool.ruff] section."""
        text = PYPROJECT.read_text(encoding="utf-8")
        count = text.count("[tool.ruff]")
        assert count == 1, f"Duplicate [tool.ruff] sections: found {count}, expected 1"

    def test_no_duplicate_tool_pytest_section(self) -> None:
        """pyproject.toml must contain exactly one [tool.pytest.ini_options] section."""
        text = PYPROJECT.read_text(encoding="utf-8")
        count = text.count("[tool.pytest.ini_options]")
        assert count == 1, (
            f"Duplicate [tool.pytest.ini_options] sections: found {count}, expected 1"
        )

    def test_no_duplicate_tool_coverage_run_section(self) -> None:
        """pyproject.toml must contain exactly one [tool.coverage.run] section."""
        text = PYPROJECT.read_text(encoding="utf-8")
        count = text.count("[tool.coverage.run]")
        assert count == 1, (
            f"Duplicate [tool.coverage.run] sections: found {count}, expected 1"
        )

    def test_no_duplicate_tool_mypy_section(self) -> None:
        """pyproject.toml must contain exactly one [tool.mypy] section."""
        text = PYPROJECT.read_text(encoding="utf-8")
        count = text.count("[tool.mypy]")
        assert count == 1, f"Duplicate [tool.mypy] sections: found {count}, expected 1"

    def test_no_duplicate_tool_uv_section(self) -> None:
        """pyproject.toml must contain exactly one [tool.uv] section."""
        text = PYPROJECT.read_text(encoding="utf-8")
        count = text.count("[tool.uv]")
        assert count == 1, f"Duplicate [tool.uv] sections: found {count}, expected 1"


class TestTaskfileYamlValidity:
    """Taskfile.yml must parse as valid YAML with no structural regressions."""

    # @trace WL-128 B90-W2-F2

    def test_taskfile_is_valid_yaml(self) -> None:
        """Taskfile.yml must parse without errors after dedup changes."""
        content = TASKFILE.read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        assert isinstance(parsed, dict), "Taskfile YAML parse must return a dict"

    def test_taskfile_has_tasks_key(self) -> None:
        """Taskfile.yml must have a top-level 'tasks' key."""
        content = TASKFILE.read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        assert "tasks" in parsed, "Taskfile.yml must have a 'tasks' key"

    def test_canonical_quality_task_exists(self) -> None:
        """A 'quality:' canonical task must exist in Taskfile after dedup."""
        text = TASKFILE.read_text(encoding="utf-8")
        # quality_project was the pre-dedup name; the canonical post-dedup
        # task is 'quality:' (defined at Taskfile.yml:34).
        assert "\n  quality:\n" in text or "quality_project:" in text, (
            "Taskfile.yml must have a canonical quality task — either 'quality:' or "
            "'quality_project:' — dedup must not have removed both"
        )

    def test_lint_task_exists(self) -> None:
        """Taskfile must still have a canonical 'lint:' task after dedup."""
        text = TASKFILE.read_text(encoding="utf-8")
        assert "\n  lint:\n" in text, (
            "Taskfile.yml must have a 'lint:' canonical task — dedup must not have removed it"
        )

    def test_test_task_exists(self) -> None:
        """Taskfile must still have a canonical 'test:' task after dedup."""
        text = TASKFILE.read_text(encoding="utf-8")
        assert "\n  test:\n" in text, (
            "Taskfile.yml must have a 'test:' canonical task — dedup must not have removed it"
        )
