"""Unit tests for git lock cleanup discovery.

Covers worktree-safe .git resolution and lock file indexing.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from unittest.mock import Mock

from thegent import git_lock_manage as glm


def test_resolve_git_dir_with_worktree_pointer(tmp_path: Path) -> None:
    """Resolve .git files that point at a separate gitdir path."""
    project = tmp_path / "project"
    project.mkdir()
    shared_git = tmp_path / "shared" / "gitdir"
    shared_git.mkdir(parents=True)
    (shared_git / "index.lock").write_text("lock")

    (project / ".git").write_text(f"gitdir: {shared_git}\n")
    resolved = glm._resolve_git_dir(project / ".git")

    assert resolved == shared_git
    assert (resolved / "index.lock").exists()


def test_find_lock_files_scans_gitdir_and_worktrees(tmp_path: Path) -> None:
    """Yield both primary gitdir index and worktree index.lock files."""
    project = tmp_path / "project"
    project.mkdir()
    git_dir = project / ".git"
    git_dir.mkdir()
    (git_dir / "index.lock").write_text(f"{time.time()}")

    wt_meta = git_dir / "worktrees" / "ci"
    wt_meta.mkdir(parents=True)
    (wt_meta / "index.lock").write_text(f"{time.time()}")

    (tmp_path / "simple").mkdir()
    (tmp_path / "simple" / ".git").mkdir()
    (tmp_path / "simple" / ".git" / "index.lock").write_text(f"{time.time()}")

    locks = sorted(glm._find_lock_files([project, tmp_path / "simple"]))
    assert (git_dir / "index.lock") in locks
    assert (wt_meta / "index.lock") in locks
    assert tmp_path / "simple" / ".git" / "index.lock" in locks


def test_run_lock_cleanup_skips_when_lsof_unavailable(tmp_path: Path, monkeypatch) -> None:
    """Skip deletion when lsof is unavailable (avoid unsafe stale assumptions)."""
    lock_path = tmp_path / ".git" / "index.lock"
    lock_path.parent.mkdir(parents=True)
    lock_path.write_text("locked")
    old = time.time() - 120
    os.utime(lock_path, (old, old))

    monkeypatch.setattr(glm, "run_subprocess_optimized", Mock(side_effect=FileNotFoundError("lsof")))
    removed, skipped = glm.run_lock_cleanup(paths=[tmp_path], max_age=60)

    assert removed == 0
    assert skipped == 1
    assert lock_path.exists()


def test_run_lock_cleanup_skips_on_uncertain_lsof_error(tmp_path: Path, monkeypatch) -> None:
    """Skip deletion when lsof returns an uncertain non-zero state."""
    lock_path = tmp_path / ".git" / "index.lock"
    lock_path.parent.mkdir(parents=True)
    lock_path.write_text("locked")
    old = time.time() - 120
    os.utime(lock_path, (old, old))

    result = Mock(returncode=1, stdout="", stderr="operation not permitted")
    monkeypatch.setattr(glm, "run_subprocess_optimized", Mock(return_value=result))
    removed, skipped = glm.run_lock_cleanup(paths=[tmp_path], max_age=60)

    assert removed == 0
    assert skipped == 1
    assert lock_path.exists()


def test_find_lock_files_handles_unreadable_worktree_dir(tmp_path: Path, monkeypatch) -> None:
    """Ignore worktree metadata directory read failures and still discover repo lock."""
    project = tmp_path / "project"
    project.mkdir()
    git_dir = project / ".git"
    git_dir.mkdir()
    (git_dir / "index.lock").write_text(f"{time.time()}")

    worktrees = git_dir / "worktrees"
    worktrees.mkdir()
    (worktrees / "ci").mkdir(parents=True)

    original_iterdir = Path.iterdir

    def _broken_iterdir(self):
        if self == worktrees:
            raise PermissionError("blocked")
        return original_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", _broken_iterdir)

    locks = list(glm._find_lock_files([project]))
    assert (git_dir / "index.lock") in locks
