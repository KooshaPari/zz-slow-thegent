"""Regression tests for worktree governance legacy migration behavior."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.commands.worktree_governance_script_helpers import init_repo, run_script


@pytest.mark.unit
def test_worktree_governance_migrate_legacy_moves_clean_legacy_worktree(
    tmp_path: Path,
) -> None:
    """`worktree_governance.sh migrate-legacy` relocates a clean legacy worktree into the canonical root."""
    repo_root = init_repo(tmp_path)
    legacy_path = repo_root.parent / "legacy-cache"

    subprocess.run(
        [
            "git",
            "worktree",
            "add",
            "-q",
            "-b",
            "feat/migrate-cache",
            str(legacy_path),
            "main",
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )

    migrate = run_script(
        repo_root,
        "migrate-legacy",
        str(legacy_path),
        "infra",
        "m",
        "migrate-cache",
        "blocked",
    )
    assert migrate.returncode == 0, migrate.stderr
    assert "[OK] migrated legacy worktree" in migrate.stdout

    target_path = repo_root / ".worktrees" / "infra" / "m" / "migrate-cache" / "blocked"
    assert target_path.exists()
    assert not legacy_path.exists()
    assert (
        subprocess.run(
            ["git", "-C", str(target_path), "branch", "--show-current"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        == "infra/m/migrate-cache"
    )

    final_check = run_script(repo_root, "check")
    assert final_check.returncode == 0, final_check.stderr
