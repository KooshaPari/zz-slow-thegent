"""Tests for WL-128 toolchain deduplication.

Verifies that duplicate toolchain invocation paths have been removed and
that canonical entrypoints are present.

# @trace WL-128 B90-W2-C2
"""

from __future__ import annotations

from pathlib import Path

from conftest import _load_script_module

ROOT = Path(__file__).parent.parent
PYPROJECT = ROOT / "pyproject.toml"
TASKFILE = ROOT / "Taskfile.yml"
WL123_SCRIPT = ROOT / "scripts" / "check_deprecated_quality_aliases.py"
WL123_MODULE = _load_script_module("check_deprecated_quality_aliases", WL123_SCRIPT)


class TestPyprojectToolConfig:
    """pyproject.toml must have exactly one [tool.ruff] section."""

    # @trace WL-128 B90-W2-C2

    def test_single_tool_ruff_section(self) -> None:
        """pyproject.toml must contain exactly one [tool.ruff] header."""
        text = PYPROJECT.read_text()
        occurrences = text.count("[tool.ruff]")
        assert occurrences == 1, (
            f"Expected exactly 1 [tool.ruff] section in pyproject.toml, found {occurrences}"
        )

    def test_single_tool_ruff_lint_section(self) -> None:
        """pyproject.toml must contain exactly one [tool.ruff.lint] header."""
        text = PYPROJECT.read_text()
        occurrences = text.count("[tool.ruff.lint]")
        assert occurrences == 1, (
            f"Expected exactly 1 [tool.ruff.lint] section in pyproject.toml, found {occurrences}"
        )

    def test_pyproject_has_pytest_ini_options(self) -> None:
        """pyproject.toml must contain [tool.pytest.ini_options] section."""
        text = PYPROJECT.read_text()
        assert "[tool.pytest.ini_options]" in text, (
            "pyproject.toml must have [tool.pytest.ini_options] section"
        )


class TestTaskfileCanonicalEntrypoints:
    """Taskfile.yml must have lint and typecheck canonical entrypoints."""

    # @trace WL-128 B90-W2-C2

    def test_lint_task_exists(self) -> None:
        """Taskfile must have a 'lint:' canonical task."""
        text = TASKFILE.read_text()
        assert "\n  lint:\n" in text, "Taskfile.yml must have a 'lint:' task"

    def test_typecheck_task_exists(self) -> None:
        """Taskfile must have a 'typecheck:' canonical task."""
        text = TASKFILE.read_text()
        assert "\n  typecheck:\n" in text, "Taskfile.yml must have a 'typecheck:' task"

    def test_format_task_exists(self) -> None:
        """Taskfile must have a 'format:' canonical task."""
        text = TASKFILE.read_text()
        assert "\n  format:\n" in text, "Taskfile.yml must have a 'format:' task"

    def test_test_task_exists(self) -> None:
        """Taskfile must have a 'test:' canonical task."""
        text = TASKFILE.read_text()
        assert "\n  test:\n" in text, "Taskfile.yml must have a 'test:' task"

    def test_no_duplicate_test_cov(self) -> None:
        """test:cov must not exist (it was a duplicate of test:)."""
        text = TASKFILE.read_text()
        assert "  test:cov:" not in text, (
            "test:cov must be removed (duplicate of test:) - WL-128 dedup"
        )

    def test_typecheck_is_canonical_wrapper_and_lint_type_alias_is_removed(
        self,
    ) -> None:
        """typecheck must exist as canonical task and lint:type alias must be removed."""
        text = TASKFILE.read_text()
        assert "\n  typecheck:\n" in text, (
            "Taskfile.yml must keep canonical 'typecheck' task"
        )
        assert "  lint:type:" not in text, (
            "Taskfile.yml must not define deprecated 'lint:type' alias"
        )

    def test_quality_task_is_canonical_and_quality_project_alias_is_removed(
        self,
    ) -> None:
        """quality must be the canonical quality chain and quality_project alias removed."""
        text = TASKFILE.read_text()
        assert "\n  quality:\n" in text, (
            "Taskfile.yml must keep canonical 'quality' task"
        )
        assert "  quality_project:" not in text, (
            "Taskfile.yml must remove duplicate 'quality_project' alias in WL-128 closeout"
        )

    def test_wl123_strict_alias_audit_passes_after_dedup_cleanup(self) -> None:
        """WL-123 strict audit should pass after WL-128 dedup closeout cleanup."""
        exit_code = WL123_MODULE.main(["--taskfile", str(TASKFILE), "--strict"])
        assert exit_code == 0, (
            "Expected WL-123 strict alias audit to pass after removing deprecated aliases "
            "and keeping canonical commands"
        )
