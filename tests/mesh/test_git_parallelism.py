"""Tests for thegent.mesh.git_parallelism — WorktreePool shared-directory coordination.

FR traceability: FR-MESH-006 (git parallelism / worktree pool)
heliosShield Phase 6: TGNT-P6
"""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest import mock

import pytest

from thegent.mesh.git_parallelism import (
    WorktreeContext,
    WorktreePool,
    _atomic_write,
    _git_available,
    _PoolStateLock,
    _project_hash,
    _worktrees_supported,
)

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _init_git_repo(path: Path) -> None:
    """Initialise a minimal git repo at *path* so WorktreePool tests run."""
    subprocess.run(["git", "init"], cwd=str(path), check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=str(path),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(path),
        check=True,
        capture_output=True,
    )
    # Create an initial commit so HEAD exists
    (path / "README.md").write_text("init\n")
    subprocess.run(["git", "add", "."], cwd=str(path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"], cwd=str(path), check=True, capture_output=True
    )


# ---------------------------------------------------------------------------
# FR-MESH-006: _project_hash
# ---------------------------------------------------------------------------


class TestProjectHash:
    """@trace FR-MESH-006"""

    def test_deterministic(self, tmp_path):
        """Same path always produces same hash."""
        h1 = _project_hash(tmp_path)
        h2 = _project_hash(tmp_path)
        assert h1 == h2

    def test_different_paths_differ(self, tmp_path):
        """Different paths produce different hashes."""
        other = tmp_path / "sub"
        other.mkdir()
        assert _project_hash(tmp_path) != _project_hash(other)

    def test_returns_12_hex_chars(self, tmp_path):
        """Hash is exactly 12 hex characters."""
        h = _project_hash(tmp_path)
        assert len(h) == 12
        assert all(c in "0123456789abcdef" for c in h)


# ---------------------------------------------------------------------------
# FR-MESH-006: _atomic_write
# ---------------------------------------------------------------------------


class TestAtomicWrite:
    """@trace FR-MESH-006"""

    def test_creates_file_with_correct_content(self, tmp_path):
        """_atomic_write creates the target file with the given content."""
        target = tmp_path / "state.txt"
        _atomic_write(target, "hello=world\n")
        assert target.exists()
        assert target.read_text() == "hello=world\n"

    def test_creates_parent_directories(self, tmp_path):
        """_atomic_write creates missing parent directories."""
        target = tmp_path / "a" / "b" / "c.txt"
        _atomic_write(target, "data")
        assert target.exists()

    def test_overwrites_existing_content(self, tmp_path):
        """_atomic_write overwrites existing file atomically."""
        target = tmp_path / "f.txt"
        target.write_text("old")
        _atomic_write(target, "new")
        assert target.read_text() == "new"

    def test_no_temp_files_left_on_success(self, tmp_path):
        """No .tmp- files remain after a successful write."""
        target = tmp_path / "out.txt"
        _atomic_write(target, "ok")
        tmp_files = list(tmp_path.glob(".tmp-*"))
        assert tmp_files == []


# ---------------------------------------------------------------------------
# FR-MESH-006: _git_available and _worktrees_supported
# ---------------------------------------------------------------------------


class TestGitAvailability:
    """@trace FR-MESH-006"""

    def test_git_available_true_in_repo(self, tmp_path):
        """_git_available returns True for a git repository."""
        _init_git_repo(tmp_path)
        assert _git_available(tmp_path) is True

    def test_git_available_false_outside_repo(self, tmp_path):
        """_git_available returns False for a plain directory."""
        non_repo = tmp_path / "plain"
        non_repo.mkdir()
        assert _git_available(non_repo) is False

    def test_worktrees_supported_in_repo(self, tmp_path):
        """_worktrees_supported returns True for a normal git repo."""
        _init_git_repo(tmp_path)
        assert _worktrees_supported(tmp_path) is True

    def test_git_available_returns_false_on_missing_git(self, tmp_path):
        """_git_available returns False when git binary is absent."""
        with mock.patch("subprocess.run", side_effect=FileNotFoundError):
            assert _git_available(tmp_path) is False


# ---------------------------------------------------------------------------
# FR-MESH-006: _PoolStateLock
# ---------------------------------------------------------------------------


class TestPoolStateLock:
    """@trace FR-MESH-006"""

    def test_read_empty_returns_empty_dict(self, tmp_path):
        """Reading a fresh state file returns an empty dict."""
        state_path = tmp_path / "pool_state.txt"
        state_path.touch()
        with _PoolStateLock(state_path) as lock:
            assert lock.read() == {}

    def test_write_then_read_roundtrip(self, tmp_path):
        """Data written via write() is recoverable via read()."""
        state_path = tmp_path / "pool_state.txt"
        state_path.touch()
        with _PoolStateLock(state_path) as lock:
            lock.write({"agent-1": "/tmp/path1", "agent-2": "/tmp/path2"})
        with _PoolStateLock(state_path) as lock:
            data = lock.read()
        assert data == {"agent-1": "/tmp/path1", "agent-2": "/tmp/path2"}

    def test_write_overwrites_previous_state(self, tmp_path):
        """Subsequent writes overwrite prior content entirely."""
        state_path = tmp_path / "pool_state.txt"
        state_path.touch()
        with _PoolStateLock(state_path) as lock:
            lock.write({"a": "1"})
        with _PoolStateLock(state_path) as lock:
            lock.write({"b": "2"})
        with _PoolStateLock(state_path) as lock:
            assert lock.read() == {"b": "2"}

    def test_creates_state_file_if_missing(self, tmp_path):
        """_PoolStateLock creates the state file when it does not exist."""
        state_path = tmp_path / "new_state.txt"
        assert not state_path.exists()
        with _PoolStateLock(state_path) as lock:
            lock.write({"x": "y"})
        assert state_path.exists()

    def test_lines_without_equals_are_ignored(self, tmp_path):
        """Lines without '=' in the state file are skipped gracefully."""
        state_path = tmp_path / "state.txt"
        state_path.write_text("garbage line\nagent-1=/path\n")
        with _PoolStateLock(state_path) as lock:
            data = lock.read()
        assert data == {"agent-1": "/path"}


# ---------------------------------------------------------------------------
# FR-MESH-006: WorktreePool — fallback mode (no real git)
# ---------------------------------------------------------------------------


class TestWorktreePoolFallback:
    """WorktreePool with git unavailable falls back to shared-tree mode.

    @trace FR-MESH-006
    """

    def _make_pool(self, tmp_path: Path) -> WorktreePool:
        """Return a WorktreePool configured to operate in fallback mode."""
        pool = WorktreePool(tmp_path, pool_root=tmp_path / ".pool")
        pool._git_ok = False
        pool._worktrees_ok = False
        return pool

    def test_acquire_returns_worktree_context(self, tmp_path):
        """acquire_worktree returns a WorktreeContext pointing at project_root."""
        pool = self._make_pool(tmp_path)
        ctx = pool.acquire_worktree("agent-a")
        assert isinstance(ctx, WorktreeContext)
        assert ctx.agent_id == "agent-a"
        assert ctx.path == pool.project_root

    def test_acquire_records_agent_in_state(self, tmp_path):
        """acquire_worktree persists the agent entry in the pool state file."""
        pool = self._make_pool(tmp_path)
        pool.acquire_worktree("agent-b")
        assert "agent-b" in pool.active_agents()

    def test_release_removes_agent_from_state(self, tmp_path):
        """release_worktree removes the agent entry from pool state."""
        pool = self._make_pool(tmp_path)
        pool.acquire_worktree("agent-c")
        pool.release_worktree("agent-c")
        assert "agent-c" not in pool.active_agents()

    def test_release_returns_false_for_unknown_agent(self, tmp_path):
        """release_worktree returns False when the agent never acquired."""
        pool = self._make_pool(tmp_path)
        assert pool.release_worktree("ghost-agent") is False

    def test_acquire_idempotent_for_same_agent(self, tmp_path):
        """A second acquire for the same agent returns the existing context."""
        pool = self._make_pool(tmp_path)
        ctx1 = pool.acquire_worktree("agent-d")
        ctx2 = pool.acquire_worktree("agent-d")
        assert ctx1.path == ctx2.path
        assert len(pool.active_agents()) == 1

    def test_multiple_agents_can_coexist(self, tmp_path):
        """Multiple agents can hold concurrent (fallback) worktrees."""
        pool = self._make_pool(tmp_path)
        pool.acquire_worktree("agent-x")
        pool.acquire_worktree("agent-y")
        agents = pool.active_agents()
        assert "agent-x" in agents
        assert "agent-y" in agents

    def test_release_creates_fallback_lock_then_removes_it(self, tmp_path):
        """The fallback lock file is created on acquire and removed on release."""
        pool = self._make_pool(tmp_path)
        pool.acquire_worktree("agent-lock")
        lock_file = pool._fallback_lock_path("agent-lock")
        assert lock_file.exists(), "Lock file should exist after acquire"
        pool.release_worktree("agent-lock")
        assert not lock_file.exists(), "Lock file should be removed after release"

    def test_context_manager_acquires_and_releases(self, tmp_path):
        """worktree() context manager acquires and releases correctly."""
        pool = self._make_pool(tmp_path)
        with pool.worktree("agent-cm") as ctx:
            assert ctx.agent_id == "agent-cm"
            assert "agent-cm" in pool.active_agents()
        assert "agent-cm" not in pool.active_agents()

    def test_context_manager_releases_on_exception(self, tmp_path):
        """worktree() context manager releases even if an exception is raised."""
        pool = self._make_pool(tmp_path)
        with pytest.raises(ValueError, match="boom"):
            with pool.worktree("agent-exc"):
                raise ValueError("boom")
        assert "agent-exc" not in pool.active_agents()

    def test_cleanup_stale_removes_missing_paths(self, tmp_path):
        """cleanup_stale removes entries whose path no longer exists."""
        pool = self._make_pool(tmp_path)
        # Manually inject a stale entry
        with _PoolStateLock(pool._state_path) as lock:
            lock.write({"agent-stale": "/nonexistent/path/xyz"})
        removed = pool.cleanup_stale()
        assert removed == 1
        assert pool.active_agents() == []

    def test_cleanup_stale_preserves_live_entries(self, tmp_path):
        """cleanup_stale keeps entries whose path still exists."""
        pool = self._make_pool(tmp_path)
        live_dir = tmp_path / "live"
        live_dir.mkdir()
        with _PoolStateLock(pool._state_path) as lock:
            lock.write({"agent-live": str(live_dir), "agent-stale": "/gone"})
        pool.cleanup_stale()
        assert "agent-live" in pool.active_agents()
        assert "agent-stale" not in pool.active_agents()

    def test_worktree_context_pool_ref_release(self, tmp_path):
        """WorktreeContext.release() delegates to the pool."""
        pool = self._make_pool(tmp_path)
        ctx = pool.acquire_worktree("agent-ref")
        assert "agent-ref" in pool.active_agents()
        result = ctx.release()
        assert result is True
        assert "agent-ref" not in pool.active_agents()

    def test_worktree_context_release_no_pool_ref(self, tmp_path):
        """WorktreeContext.release() returns False when no pool reference is set."""
        ctx = WorktreeContext(
            agent_id="orphan",
            path=tmp_path,
            branch="main",
            project_root=tmp_path,
            _pool_ref=None,
        )
        assert ctx.release() is False


# ---------------------------------------------------------------------------
# FR-MESH-006: WorktreePool — worktree mode (with real git repo)
# ---------------------------------------------------------------------------


class TestWorktreePoolWithGit:
    """WorktreePool using real git worktree operations.

    @trace FR-MESH-006
    """

    def test_acquire_creates_worktree_directory(self, tmp_path):
        """acquire_worktree creates the worktree directory on disk."""
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_git_repo(repo)
        pool_root = tmp_path / "pool"
        pool = WorktreePool(repo, pool_root=pool_root)
        ctx = pool.acquire_worktree("wt-agent")
        try:
            assert ctx.path.exists()
            assert ctx.path.is_dir()
        finally:
            pool.release_worktree("wt-agent")

    def test_acquire_uses_agent_branch(self, tmp_path):
        """acquire_worktree checks out a branch named agent/<agent_id>."""
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_git_repo(repo)
        pool_root = tmp_path / "pool"
        pool = WorktreePool(repo, pool_root=pool_root)
        ctx = pool.acquire_worktree("wt-branchtest")
        try:
            assert ctx.branch == "agent/wt-branchtest"
        finally:
            pool.release_worktree("wt-branchtest")

    def test_release_removes_worktree_directory(self, tmp_path):
        """release_worktree removes the worktree directory after merge."""
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_git_repo(repo)
        pool_root = tmp_path / "pool"
        pool = WorktreePool(repo, pool_root=pool_root)
        ctx = pool.acquire_worktree("wt-cleanup")
        worktree_path = ctx.path
        pool.release_worktree("wt-cleanup")
        assert not worktree_path.exists()

    def test_commit_all_creates_commit_in_worktree(self, tmp_path):
        """WorktreeContext.commit_all stages all changes and creates a commit."""
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_git_repo(repo)
        pool_root = tmp_path / "pool"
        pool = WorktreePool(repo, pool_root=pool_root)
        ctx = pool.acquire_worktree("wt-commit")
        try:
            (ctx.path / "new_file.txt").write_text("agent output\n")
            commit_hash = ctx.commit_all("wt-commit: add output")
            assert commit_hash is not None
            assert len(commit_hash) == 40
        finally:
            pool.release_worktree("wt-commit")

    def test_worktree_context_manager_with_git(self, tmp_path):
        """worktree() context manager works end-to-end with a real git repo."""
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_git_repo(repo)
        pool_root = tmp_path / "pool"
        pool = WorktreePool(repo, pool_root=pool_root)
        with pool.worktree("wt-cm") as ctx:
            assert ctx.path.exists()
            assert "wt-cm" in pool.active_agents()
        assert "wt-cm" not in pool.active_agents()

    def test_second_acquire_reuses_existing_context(self, tmp_path):
        """A second acquire call for the same agent returns the cached context."""
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_git_repo(repo)
        pool_root = tmp_path / "pool"
        pool = WorktreePool(repo, pool_root=pool_root)
        ctx1 = pool.acquire_worktree("wt-idem")
        ctx2 = pool.acquire_worktree("wt-idem")
        try:
            assert ctx1.path == ctx2.path
            assert len(pool.active_agents()) == 1
        finally:
            pool.release_worktree("wt-idem")

    def test_active_agents_reflects_all_held_worktrees(self, tmp_path):
        """active_agents lists all agents that have acquired worktrees."""
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_git_repo(repo)
        pool_root = tmp_path / "pool"
        pool = WorktreePool(repo, pool_root=pool_root)
        pool.acquire_worktree("wt-a1")
        pool.acquire_worktree("wt-a2")
        try:
            agents = pool.active_agents()
            assert "wt-a1" in agents
            assert "wt-a2" in agents
        finally:
            pool.release_worktree("wt-a1")
            pool.release_worktree("wt-a2")


# ---------------------------------------------------------------------------
# FR-MESH-006: WorktreePool — project hash stability after resolve
# ---------------------------------------------------------------------------


class TestWorktreePoolProjectHash:
    """Verify pool_dir uses a stable hash per project. @trace FR-MESH-006"""

    def test_pool_dir_contains_project_hash(self, tmp_path):
        """WorktreePool._pool_dir incorporates the project hash."""
        pool_root = tmp_path / "root"
        project = tmp_path / "proj"
        project.mkdir()
        pool = WorktreePool(project, pool_root=pool_root)
        expected_hash = _project_hash(project.resolve())
        assert pool._pool_dir.name == expected_hash

    def test_two_pools_same_project_share_pool_dir(self, tmp_path):
        """Two WorktreePool instances for the same project share the same pool dir."""
        pool_root = tmp_path / "root"
        project = tmp_path / "proj"
        project.mkdir()
        pool1 = WorktreePool(project, pool_root=pool_root)
        pool2 = WorktreePool(project, pool_root=pool_root)
        assert pool1._pool_dir == pool2._pool_dir

    def test_different_projects_use_different_pool_dirs(self, tmp_path):
        """Different projects get different pool directories."""
        pool_root = tmp_path / "root"
        p1 = tmp_path / "proj1"
        p2 = tmp_path / "proj2"
        p1.mkdir()
        p2.mkdir()
        pool1 = WorktreePool(p1, pool_root=pool_root)
        pool2 = WorktreePool(p2, pool_root=pool_root)
        assert pool1._pool_dir != pool2._pool_dir
