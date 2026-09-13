"""Coverage lifecycle contract checks."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TASKFILE = REPO_ROOT / "Taskfile.yml"
PYPROJECT = REPO_ROOT / "pyproject.toml"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def test_taskfile_defines_explicit_coverage_lifecycle_tasks() -> None:
    text = TASKFILE.read_text(encoding="utf-8")
    for task_name in ("coverage:clean:", "coverage:run:", "coverage:report:", "coverage:ci:"):
        assert task_name in text, f"Taskfile.yml must define `{task_name[:-1]}`"


def test_coverage_run_enforces_clean_before_pytest() -> None:
    text = TASKFILE.read_text(encoding="utf-8")
    pattern = re.compile(
        r"(?ms)^  coverage:run:\n.*?^\s+cmds:\n(?:^\s+.*\n)*?^\s+- task: coverage:clean\n(?:^\s+.*\n)*?^\s+- uv run pytest -q --cov=src --cov-context=test --cov-report= -p no:tach\n"
    )
    assert pattern.search(text), "coverage:run must invoke coverage:clean before pytest --cov"


def test_coverage_report_and_ci_keep_fail_fast_contract() -> None:
    text = TASKFILE.read_text(encoding="utf-8")
    report_pattern = re.compile(
        r"(?ms)^  coverage:report:\n.*?^\s+cmds:\n(?:^\s+.*\n)*?^\s+- uv run coverage report --show-missing --skip-covered\n(?:^\s+.*\n)*?^\s+- uv run coverage xml\n"
    )
    ci_pattern = re.compile(
        r"(?ms)^  coverage:ci:\n.*?^\s+cmds:\n(?:^\s+.*\n)*?^\s+- task: coverage:run\n(?:^\s+.*\n)*?^\s+- task: coverage:report\n"
    )
    assert report_pattern.search(text), "coverage:report must run coverage report and coverage xml"
    assert ci_pattern.search(text), "coverage:ci must chain coverage:run then coverage:report"


def test_pyproject_coverage_config_handles_stale_paths_without_error_masking() -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    assert "relative_files = true" in text, "coverage.run must set relative_files = true"
    assert "ignore_errors = false" in text, "coverage.report must keep ignore_errors = false"
    assert "fail_under = 100" in text, "coverage.report must keep fail_under = 100"


def test_ci_workflow_enforces_preflight_then_coverage_gate_ordering() -> None:
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "  preflight:" in text, "CI workflow must define preflight job"
    assert "  test:" in text, "CI workflow must define test job"
    assert "  quality:" in text, "CI workflow must define quality job"
    assert "  coverage:" in text, "CI workflow must define coverage job"
    assert "  integration:" in text, "CI workflow must define integration job"
    assert text.index("  preflight:") < text.index("  test:")
    assert text.index("  test:") < text.index("  quality:")
    assert text.index("  quality:") < text.index("  coverage:")
    assert text.index("  coverage:") < text.index("  integration:")


def test_ci_workflow_is_fail_closed_for_coverage_gate() -> None:
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "  needs: [preflight]" in text
    assert "  needs: [test, quality]" in text
    assert "  needs: [coverage]" in text
    assert text.count("task ci:preflight") == 1
    assert "task coverage:ci" in text
