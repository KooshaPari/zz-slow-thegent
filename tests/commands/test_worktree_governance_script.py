"""Regression tests for core structured worktree governance shell script behavior."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.commands.worktree_governance_script_helpers import init_repo, run_script


@pytest.mark.unit
def test_worktree_governance_structured_lifecycle(tmp_path: Path) -> None:
    """`worktree_governance.sh` creates, moves, lists, and prunes structured worktrees."""
    repo_root = init_repo(tmp_path)
    branch = "backend/m/fix-mcp-timeout"
    anchor = "fix-mcp-timeout"
    active_path = repo_root / ".worktrees" / "backend" / "m" / anchor / "active"
    review_path = repo_root / ".worktrees" / "backend" / "m" / anchor / "review"
    done_path = repo_root / ".worktrees" / "backend" / "m" / anchor / "done"

    create = run_script(repo_root, "new", "backend", "m", anchor)
    assert create.returncode == 0, create.stderr
    assert active_path.as_posix() in create.stdout
    assert active_path.exists()

    path_proc = run_script(repo_root, "path", "backend", "m", anchor, "active")
    assert path_proc.returncode == 0
    assert path_proc.stdout.strip() == active_path.as_posix()

    check = run_script(repo_root, "check")
    assert check.returncode == 0, check.stderr
    assert "[OK] worktree governance check passed" in check.stdout

    move_review = run_script(repo_root, "state", anchor, "review")
    assert move_review.returncode == 0, move_review.stderr
    assert move_review.stdout.strip() == review_path.as_posix()
    assert review_path.exists()
    assert not active_path.exists()

    listed = run_script(repo_root, "list")
    assert listed.returncode == 0, listed.stderr
    assert f"state=review branch={branch}" in listed.stdout
    assert review_path.as_posix() in listed.stdout

    move_done = run_script(repo_root, "state", anchor, "done")
    assert move_done.returncode == 0, move_done.stderr
    assert move_done.stdout.strip() == done_path.as_posix()
    assert done_path.exists()

    shutil.rmtree(done_path)
    assert not done_path.exists()

    dry_run = run_script(repo_root, "prune", "--dry-run")
    assert dry_run.returncode == 0, dry_run.stderr
    assert f"[DRY-RUN] remove done worktree: {done_path.as_posix()}" in dry_run.stdout

    prune = run_script(repo_root, "prune")
    assert prune.returncode == 0, prune.stderr
    assert "[OK] worktree prune complete" in prune.stdout
    assert not done_path.exists()

    final_check = run_script(repo_root, "check")
    assert final_check.returncode == 0, final_check.stderr


@pytest.mark.unit
def test_worktree_governance_state_fails_for_missing_anchor(tmp_path: Path) -> None:
    """`worktree_governance.sh state` fails loudly when no worktree matches the anchor."""
    repo_root = init_repo(tmp_path)
    proc = run_script(repo_root, "state", "missing-anchor", "review")
    assert proc.returncode != 0
    assert "no worktree found for change anchor" in proc.stderr


@pytest.mark.unit
@pytest.mark.parametrize(
    ("args", "expected_error"),
    [
        (("new", "bad/domain", "m", "anchor"), "invalid domain"),
        (("path", "backend", "m", "bad/anchor", "active"), "invalid change anchor"),
        (("state", "bad/anchor", "review"), "invalid change anchor"),
    ],
)
def test_worktree_governance_rejects_unsafe_path_components(
    tmp_path: Path,
    args: tuple[str, ...],
    expected_error: str,
) -> None:
    """`worktree_governance.sh` rejects unsafe path components before building paths."""
    repo_root = init_repo(tmp_path)
    proc = run_script(repo_root, *args)
    assert proc.returncode != 0
    assert expected_error in proc.stderr


@pytest.mark.unit
def test_worktree_governance_rejects_invalid_start_point(tmp_path: Path) -> None:
    """`worktree_governance.sh new` rejects invalid start points before invoking git."""
    repo_root = init_repo(tmp_path)
    proc = run_script(repo_root, "new", "backend", "m", "anchor", "-bad-start")
    assert proc.returncode != 0
    assert "invalid start point" in proc.stderr


@pytest.mark.unit
def test_worktree_governance_state_fails_for_ambiguous_anchor(tmp_path: Path) -> None:
    """`worktree_governance.sh state` fails loudly when multiple worktrees share an anchor."""
    repo_root = init_repo(tmp_path)

    create_one = run_script(repo_root, "new", "backend", "m", "fix-mcp-timeout")
    assert create_one.returncode == 0, create_one.stderr

    create_two = run_script(repo_root, "new", "frontend", "l", "fix-mcp-timeout")
    assert create_two.returncode == 0, create_two.stderr

    proc = run_script(repo_root, "state", "fix-mcp-timeout", "review")
    assert proc.returncode != 0
    assert "ambiguous change anchor" in proc.stderr


@pytest.mark.unit
def test_worktree_governance_check_fails_for_branch_path_mismatch(
    tmp_path: Path,
) -> None:
    """`worktree_governance.sh check` rejects structured paths whose branch disagrees."""
    repo_root = init_repo(tmp_path)
    mismatch_path = repo_root / ".worktrees" / "backend" / "m" / "anchor" / "active"

    add_mismatch = subprocess.run(
        [
            "git",
            "worktree",
            "add",
            "-b",
            "backend/other/anchor",
            str(mismatch_path),
            "main",
        ],
        cwd=repo_root,
        env={**os.environ},
        capture_output=True,
        text=True,
        check=False,
    )
    assert add_mismatch.returncode == 0, add_mismatch.stderr

    proc = run_script(repo_root, "check")
    assert proc.returncode != 0
    assert "worktree branch mismatch" in proc.stderr


@pytest.mark.unit
def test_worktree_governance_check_fails_for_invalid_structured_state(
    tmp_path: Path,
) -> None:
    """`worktree_governance.sh check` rejects structured paths with invalid state labels."""
    repo_root = init_repo(tmp_path)
    invalid_state_path = repo_root / ".worktrees" / "backend" / "m" / "anchor" / "invalid-state"

    add_invalid_state = subprocess.run(
        [
            "git",
            "worktree",
            "add",
            "-b",
            "backend/m/anchor",
            str(invalid_state_path),
            "main",
        ],
        cwd=repo_root,
        env={**os.environ},
        capture_output=True,
        text=True,
        check=False,
    )
    assert add_invalid_state.returncode == 0, add_invalid_state.stderr

    proc = run_script(repo_root, "check")
    assert proc.returncode != 0
    assert "invalid structured state" in proc.stderr


@pytest.mark.unit
def test_worktree_governance_check_rejects_non_inventory_path(tmp_path: Path) -> None:
    """`worktree_governance.sh check` fails when a worktree lives outside the structured inventory root."""
    repo_root = init_repo(tmp_path)
    outside_path = repo_root / "outside" / "backend" / "m" / "escaped-anchor" / "active"

    add_outside = subprocess.run(
        [
            "git",
            "worktree",
            "add",
            "-b",
            "outside/m/escaped-anchor",
            str(outside_path),
            "main",
        ],
        cwd=repo_root,
        env={**os.environ},
        capture_output=True,
        text=True,
        check=False,
    )
    assert add_outside.returncode == 0, add_outside.stderr
    assert outside_path.exists()

    proc = run_script(repo_root, "check")
    assert proc.returncode != 0
    assert "worktree outside required root" in proc.stderr
    assert outside_path.as_posix() in proc.stderr


@pytest.mark.unit
def test_worktree_governance_prune_refuses_live_done_worktree(tmp_path: Path) -> None:
    """`worktree_governance.sh prune` refuses to force-remove a live done worktree."""
    repo_root = init_repo(tmp_path)
    anchor = "live-done-anchor"

    create = run_script(repo_root, "new", "backend", "m", anchor)
    assert create.returncode == 0, create.stderr

    move_done = run_script(repo_root, "state", anchor, "done")
    assert move_done.returncode == 0, move_done.stderr

    proc = run_script(repo_root, "prune")
    assert proc.returncode != 0
    assert "refusing to prune live done worktree" in proc.stderr
