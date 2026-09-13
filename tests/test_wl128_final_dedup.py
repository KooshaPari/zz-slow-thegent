"""Tests for WL-128 final dedup cleanup validation.

Ensures Taskfile.yml and pyproject.toml have no duplicate task or config sections
after the B90-W2/W3 dedup cleanup passes.

# @trace WL-128 B90-W3-C1
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
TASKFILE = ROOT / "Taskfile.yml"
PYPROJECT = ROOT / "pyproject.toml"


# @trace WL-128 B90-W3-C1
def test_taskfile_no_standalone_test_cov_task() -> None:
    """Taskfile.yml must NOT define test:cov: as a standalone task."""
    text = TASKFILE.read_text(encoding="utf-8")
    # A standalone task definition looks like "  test:cov:" at line start with colon
    lines = text.splitlines()
    standalone_cov_tasks = [line for line in lines if line.strip() == "test:cov:"]
    assert standalone_cov_tasks == [], (
        f"test:cov: is a standalone task in Taskfile.yml ({len(standalone_cov_tasks)} occurrence(s)). "
        "This deprecated alias must be removed."
    )


# @trace WL-128 B90-W3-C1
def test_taskfile_no_duplicate_quality_tasks() -> None:
    """Taskfile.yml must not define both quality: and quality_project: as top-level tasks.

    The `includes:` block legitimately references `quality:` as a namespace include — that
    is NOT a task definition and must not be counted. Only task definitions inside the
    `tasks:` block count.
    """
    text = TASKFILE.read_text(encoding="utf-8")
    # Extract only the tasks: block to avoid counting includes: entries
    # Split on "^tasks:" to isolate the task definitions section
    in_tasks_block = False
    task_quality_defs: list[str] = []
    for line in text.splitlines():
        if line.startswith("tasks:"):
            in_tasks_block = True
            continue
        if in_tasks_block and line.strip() in ("quality:", "quality_project:"):
            task_quality_defs.append(line.strip())

    # At most one canonical quality task definition is allowed in the tasks: block
    assert len(task_quality_defs) <= 1, (
        f"Multiple canonical quality task definitions found in Taskfile.yml tasks: block: {task_quality_defs}. "
        "Only one is allowed (either 'quality:' or 'quality_project:', not both)."
    )


# @trace WL-128 B90-W3-C1
def test_pyproject_no_duplicate_ruff_sections() -> None:
    """pyproject.toml must not contain duplicate [tool.ruff] sections."""
    text = PYPROJECT.read_text(encoding="utf-8")
    count = sum(1 for line in text.splitlines() if line.strip() == "[tool.ruff]")
    assert count <= 1, f"pyproject.toml has {count} [tool.ruff] sections. Only one is allowed."


# @trace WL-128 B90-W3-C1
def test_pyproject_no_duplicate_pytest_sections() -> None:
    """pyproject.toml must not contain duplicate [tool.pytest.ini_options] sections."""
    text = PYPROJECT.read_text(encoding="utf-8")
    count = sum(1 for line in text.splitlines() if line.strip() == "[tool.pytest.ini_options]")
    assert count <= 1, f"pyproject.toml has {count} [tool.pytest.ini_options] sections. Only one is allowed."


# @trace WL-128 B90-W3-C1
def test_taskfile_exists() -> None:
    """Taskfile.yml must exist."""
    assert TASKFILE.exists(), f"Taskfile.yml not found at {TASKFILE}"


# @trace WL-128 B90-W3-C1
def test_pyproject_exists() -> None:
    """pyproject.toml must exist."""
    assert PYPROJECT.exists(), f"pyproject.toml not found at {PYPROJECT}"
