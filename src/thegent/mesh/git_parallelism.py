"""Compatibility wrapper for worktree parallelism domain module.

This module mirrors the public API expected by `tests/mesh/test_git_parallelism.py`
and the smart-merge compatibility tests, while remaining intentionally lightweight.

It is intentionally compatible with the `thegent_gitops.worktree` implementation.
"""

from __future__ import annotations

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows compatibility path
    fcntl = None  # type: ignore[assignment]

import hashlib
import logging
import os
import shutil
import subprocess
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from thegent.infra.shim_subprocess import run as shim_run

if TYPE_CHECKING:
    from thegent.mesh.smart_merge import SmartMerger

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_WORKTREE_BASE = Path.home() / ".thegent" / "worktrees"
_STATE_FILENAME = "pool_state.txt"


def _project_hash(project_root: Path) -> str:
    """Stable 12-char hex hash of the canonical project root path."""
    return hashlib.sha256(str(project_root.resolve()).encode()).hexdigest()[:12]


def _atomic_write(path: Path, content: str) -> None:
    """Write *content* to *path* atomically via sibling temp + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile_mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, path)
    except Exception:
        with suppress(OSError):
            os.unlink(tmp)
        raise


def tempfile_mkstemp(**kwargs: object) -> tuple[int, str]:
    import tempfile

    return tempfile.mkstemp(**kwargs)


def _run(cmd: list[str], cwd: Path | str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a subprocess command and return `CompletedProcess`."""
    return shim_run([*cmd], cwd=str(cwd), check=check, capture_output=True, text=True)


def _git_available(path: Path | str = ".") -> bool:
    """Return True if git is available and this path is a git repo."""
    try:
        _run(["git", "rev-parse", "--git-dir"], path)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _worktrees_supported(path: Path | str = ".") -> bool:
    """Return True if git worktrees are supported for this repository."""
    try:
        result = _run(["git", "worktree", "list"], path)
        return result.returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WorktreeContext:
    """Snapshot of an acquired worktree."""

    agent_id: str
    path: Path
    branch: str
    project_root: Path
    _pool_ref: WorktreePool | None = field(compare=False, repr=False, default=None)

    def commit_all(self, message: str) -> str | None:
        """Stage all changes in the worktree and create a commit.

        Returns the commit hash on success, None on failure.
        """
        try:
            _run(["git", "add", "-A"], self.path)
            proc = _run(
                ["git", "commit", "--allow-empty", "-m", message],
                self.path,
                check=False,
            )
            if proc.returncode not in (0, 1):
                _log.warning("commit failed in worktree %s: %s", self.path, proc.stderr)
                return None
            result = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(self.path), text=True).strip()
            return result
        except Exception as exc:
            _log.warning("commit_all failed for agent %s: %s", self.agent_id, exc)
            return None

    def release(self) -> bool:
        """Convenience: release this worktree back to its pool."""
        if self._pool_ref is not None:
            return self._pool_ref.release_worktree(self.agent_id)
        return False


# ---------------------------------------------------------------------------
# Pool state file
# ---------------------------------------------------------------------------


class _PoolStateLock:
    """Simple flock-backed state file lock helper."""

    def __init__(self, state_path: Path) -> None:
        self._path = state_path
        self._fh = None

    def __enter__(self) -> _PoolStateLock:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.touch()
        self._fh = open(self._path, "r+", encoding="utf-8")
        if fcntl is not None:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, *args: object) -> None:
        try:
            if self._fh is not None:
                if fcntl is not None:
                    fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
                self._fh.close()
        finally:
            self._fh = None

    def read(self) -> dict[str, str]:
        """Parse state file lines as ``key=value`` pairs."""
        assert self._fh is not None
        self._fh.seek(0)
        state: dict[str, str] = {}
        for line in self._fh:
            line = line.strip()
            if "=" in line:
                key, _, value = line.partition("=")
                state[key] = value
        return state

    def write(self, state: dict[str, str]) -> None:
        """Overwrite state file from *state*."""
        assert self._fh is not None
        self._fh.seek(0)
        self._fh.truncate()
        for key in sorted(state):
            self._fh.write(f"{key}={state[key]}\n")
        self._fh.flush()


# ---------------------------------------------------------------------------
# WorktreePool
# ---------------------------------------------------------------------------


class WorktreePool:
    """Pool for managing worktrees in shared-directory parallel execution mode."""

    def __init__(
        self,
        project_root: Path,
        target_branch: str = "HEAD",
        pool_root: Path | None = None,
        merger: SmartMerger | None = None,
    ) -> None:
        self.project_root = project_root.resolve()
        self.target_branch = target_branch
        self._pool_root = pool_root or _WORKTREE_BASE
        self._phash = _project_hash(self.project_root)
        self._pool_dir = self._pool_root / self._phash
        self._pool_dir.mkdir(parents=True, exist_ok=True)
        self._state_path = self._pool_dir / _STATE_FILENAME
        self._merger: SmartMerger | None = merger
        self._git_ok = _git_available(self.project_root)
        self._worktrees_ok = self._git_ok and _worktrees_supported(self.project_root)
        self.worktrees: list[WorktreeContext] = []

    # Public API

    def acquire_worktree(self, agent_id: str) -> WorktreeContext:
        """Acquire (or reuse) a worktree context for `agent_id`."""
        with _PoolStateLock(self._state_path) as lock:
            state = lock.read()
            if agent_id in state:
                path = Path(state[agent_id])
                return WorktreeContext(
                    agent_id=agent_id,
                    path=path,
                    branch=f"agent/{agent_id}",
                    project_root=self.project_root,
                    _pool_ref=self,
                )

            ctx = self._create_worktree(agent_id) if self._worktrees_ok else self._acquire_shared_fallback(agent_id)
            state[agent_id] = str(ctx.path)
            lock.write(state)
            return ctx

    def release_worktree(self, agent_id: str) -> bool:
        """Release an acquired context and merge/remove it if necessary."""
        with _PoolStateLock(self._state_path) as lock:
            state = lock.read()
            if agent_id not in state:
                return False

            worktree_path = Path(state[agent_id])
            branch = f"agent/{agent_id}"

            if self._worktrees_ok and worktree_path != self.project_root:
                success = self._merge_and_remove(agent_id, worktree_path, branch)
            else:
                success = self._release_shared_fallback(agent_id, worktree_path)

            del state[agent_id]
            lock.write(state)
            return success

    @contextmanager
    def worktree(self, agent_id: str):
        ctx = self.acquire_worktree(agent_id)
        try:
            yield ctx
        finally:
            self.release_worktree(agent_id)

    def active_agents(self) -> list[str]:
        """Return the set of currently tracked agent IDs."""
        with _PoolStateLock(self._state_path) as lock:
            return list(lock.read().keys())

    def cleanup_stale(self) -> int:
        """Remove stale entries from state and return removal count."""
        removed = 0
        with _PoolStateLock(self._state_path) as lock:
            state = lock.read()
            kept: dict[str, str] = {}
            for agent_id, path_str in state.items():
                if Path(path_str).exists():
                    kept[agent_id] = path_str
                    continue

                removed += 1
                if self._worktrees_ok:
                    self._git_worktree_remove(path_str)
                self._try_delete_branch(f"agent/{agent_id}")
            lock.write(kept)
            return removed

    # Internal: worktree mode

    def _create_worktree(self, agent_id: str) -> WorktreeContext:
        branch = f"agent/{agent_id}"
        worktree_path = self._pool_dir / agent_id

        if worktree_path.exists() and any(worktree_path.iterdir()):
            self._git_worktree_remove(str(worktree_path))
            shutil.rmtree(worktree_path, ignore_errors=True)

        worktree_path.mkdir(parents=True, exist_ok=True)

        if not self._branch_exists(branch):
            _run(["git", "branch", branch], self.project_root)

        _run(["git", "worktree", "add", str(worktree_path), branch], self.project_root)

        return WorktreeContext(
            agent_id=agent_id,
            path=worktree_path,
            branch=branch,
            project_root=self.project_root,
            _pool_ref=self,
        )

    def _merge_and_remove(self, agent_id: str, worktree_path: Path, branch: str) -> bool:
        """Merge branch into target and remove worktree."""
        target = self._resolve_target_branch()

        merged = False
        if self._merger is not None:
            merge_result = self._merger.merge_worktree_changes(worktree_path, target)
            merged = merge_result.success
        else:
            try:
                _run([
                    "git",
                    "merge",
                    "--no-ff",
                    "-m",
                    f"Merge agent/{agent_id} into {target}",
                    branch,
                ], self.project_root)
                merged = True
            except subprocess.CalledProcessError:
                merged = False

        removed = self._git_worktree_remove(str(worktree_path))
        if worktree_path.exists():
            shutil.rmtree(worktree_path, ignore_errors=True)
        self._try_delete_branch(branch)

        return bool(merged and removed)

    def _git_worktree_remove(self, path_str: str) -> bool:
        try:
            _run(["git", "worktree", "remove", "--force", path_str], self.project_root)
            return True
        except subprocess.CalledProcessError:
            return False

    def _branch_exists(self, branch: str) -> bool:
        try:
            result = _run(["git", "branch", "--list", branch], self.project_root)
            return branch in result.stdout
        except subprocess.CalledProcessError:
            return False

    def _resolve_target_branch(self) -> str:
        if self.target_branch != "HEAD":
            return self.target_branch
        try:
            result = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], self.project_root)
            return result.stdout.strip() or "main"
        except subprocess.CalledProcessError:
            return "main"

    def _try_delete_branch(self, branch: str) -> None:
        with suppress(subprocess.CalledProcessError):
            _run(["git", "branch", "-D", branch], self.project_root)

    # Internal: fallback shared-tree mode

    def _fallback_lock_path(self, agent_id: str) -> Path:
        return self._pool_dir / f"{agent_id}.fallback.lock"

    def _acquire_shared_fallback(self, agent_id: str) -> WorktreeContext:
        lock_path = self._fallback_lock_path(agent_id)
        _atomic_write(lock_path, f"agent={agent_id}\n")
        return WorktreeContext(
            agent_id=agent_id,
            path=self.project_root,
            branch=self._resolve_target_branch(),
            project_root=self.project_root,
            _pool_ref=self,
        )

    def _release_shared_fallback(self, agent_id: str, _worktree_path: Path) -> bool:
        lock_path = self._fallback_lock_path(agent_id)
        with suppress(OSError):
            lock_path.unlink(missing_ok=True)
            return True
        return False


__all__ = [
    "WorktreeContext",
    "WorktreePool",
    "_project_hash",
    "_atomic_write",
    "_git_available",
    "_worktrees_supported",
    "_PoolStateLock",
    "_run",
]
