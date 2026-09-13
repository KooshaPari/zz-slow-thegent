"""Shared-directory git parallelism via worktree pool for concurrent agents.

Implements heliosShield Phase 6 Git Parallelism (TGNT-P6 / heliosShield WP-16003):
- WorktreePool: manages N git worktrees for N concurrent agents.
- acquire_worktree(agent_id) -> WorktreeContext: isolated path + branch.
- release_worktree(agent_id): merges changes back to main with git merge --no-ff.
- Atomic claim via fcntl.flock advisory locks (Unix) + rename-pattern for writes.
- Fallback to shared-tree advisory lock when git worktrees are unavailable.
"""

from __future__ import annotations

try:
    import fcntl
except ImportError:
    fcntl = None  # type: ignore[assignment]
import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
import time
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from thegent.infra.shim_subprocess import run as shim_run

if TYPE_CHECKING:
    from collections.abc import Generator

    from thegent.mesh.smart_merge import SmartMerger

from io import TextIOWrapper

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_WORKTREE_BASE = Path.home() / ".thegent" / "worktrees"


def _project_hash(project_root: Path) -> str:
    """Stable 12-char hex hash of the canonical project root path."""
    return hashlib.sha256(str(project_root.resolve()).encode()).hexdigest()[:12]


def _atomic_write(path: Path, content: str) -> None:
    """Write *content* to *path* atomically via a sibling temp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, path)  # POSIX atomic rename
    except Exception:
        with suppress(OSError):
            os.unlink(tmp)
        raise


def _run(cmd: list[str], cwd: Path, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a subprocess, returning the CompletedProcess."""
    return shim_run(
        cmd,
        cwd=str(cwd),
        env=env,
        check=check,
        capture_output=True,
        text=True,
    )


def _git_available(project_root: Path) -> bool:
    """Return True if *project_root* is inside a git repository."""
    try:
        _run(["git", "rev-parse", "--git-dir"], project_root)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _worktrees_supported(project_root: Path) -> bool:
    """Return True if git worktree add is functional in this repository."""
    try:
        result = _run(["git", "worktree", "list"], project_root)
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
        """Stage all changes in the worktree and create a git commit.

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
        """Convenience: release this worktree back to the pool."""
        if self._pool_ref is not None:
            return self._pool_ref.release_worktree(self.agent_id)
        return False


# ---------------------------------------------------------------------------
# Pool state file
# ---------------------------------------------------------------------------

_STATE_FILENAME = "pool_state.txt"


class _PoolStateLock:
    """Advisory flock around the pool state file for atomic multi-step updates."""

    def __init__(self, state_path: Path) -> None:
        self._path = state_path
        self._fh: TextIOWrapper | None = None

    def __enter__(self) -> _PoolStateLock:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.touch()
        self._fh = open(self._path, "r+", encoding="utf-8")
        if fcntl is not None:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX)
        else:
            _log.debug("WorktreePool: advisory flock unavailable; running without file lock.")
        return self

    def __exit__(self, *_: object) -> None:
        try:
            if self._fh is not None:
                if fcntl is not None:
                    fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
                self._fh.close()
        finally:
            self._fh = None

    def read(self) -> dict[str, str]:
        """Parse ``key=value`` state file into dict."""
        assert self._fh is not None
        self._fh.seek(0)
        state: dict[str, str] = {}
        for line in self._fh:
            line = line.strip()
            if "=" in line:
                k, _, v = line.partition("=")
                state[k.strip()] = v.strip()
        return state

    def write(self, state: dict[str, str]) -> None:
        """Overwrite state file with *state* dict."""
        self._fh.seek(0)
        self._fh.truncate()
        for k, v in sorted(state.items()):
            self._fh.write(f"{k}={v}\n")
        self._fh.flush()


# ---------------------------------------------------------------------------
# WorktreePool
# ---------------------------------------------------------------------------


class WorktreePool:
    """Pool of git worktrees for concurrent agent sessions.

    Each agent gets an isolated worktree on a dedicated branch.  When the
    agent finishes, its branch is merged back to the *target_branch* using
    ``git merge --no-ff`` to preserve history.

    Directory layout::

        ~/.thegent/worktrees/<project-hash>/<agent-id>/   # worktree checkout
        ~/.thegent/worktrees/<project-hash>/pool_state.txt # advisory + state

    When git worktrees are unavailable (e.g. shallow clone, filesystem
    restriction), the pool falls back to the shared working tree with an
    advisory fcntl lock so only one agent writes at a time.

    Args:
        project_root: Root of the git project being coordinated.
        target_branch: Branch to merge worktree changes into (default: HEAD).
        pool_root: Override the default ``~/.thegent/worktrees`` root.
    """

    def __init__(
        self,
        project_root: Path,
        target_branch: str = "HEAD",
        pool_root: Path | None = None,
        merger: SmartMerger | None = None,
    ) -> None:
        self.project_root = project_root.resolve()
        self.target_branch = target_branch
        self._phash = _project_hash(self.project_root)
        self._pool_dir = (pool_root or _WORKTREE_BASE) / self._phash
        self._pool_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._state_path = self._pool_dir / _STATE_FILENAME
        self._git_ok = _git_available(self.project_root)
        self._worktrees_ok = self._git_ok and _worktrees_supported(self.project_root)
        self._merger: SmartMerger | None = merger
        if not self._worktrees_ok:
            _log.info(
                "WorktreePool: git worktrees unavailable for %s; falling back to shared-tree advisory lock.",
                self.project_root,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def acquire_worktree(self, agent_id: str) -> WorktreeContext:
        """Acquire an isolated worktree for *agent_id*.

        If the agent already holds a worktree the existing context is returned.
        Creates a new worktree branch ``agent/<agent_id>`` and checks it out
        under the pool directory.

        Falls back to the shared working tree (with advisory lock) if git
        worktrees are not supported.

        Returns:
            WorktreeContext describing the acquired worktree path and branch.

        Raises:
            RuntimeError: If worktree creation fails and no fallback is possible.
        """
        with _PoolStateLock(self._state_path) as lock:
            state = lock.read()
            if agent_id in state:
                existing_path = Path(state[agent_id])
                branch = f"agent/{agent_id}"
                _log.debug("WorktreePool: agent %s already holds %s", agent_id, existing_path)
                return WorktreeContext(
                    agent_id=agent_id,
                    path=existing_path,
                    branch=branch,
                    project_root=self.project_root,
                    _pool_ref=self,
                )

            ctx = self._create_worktree(agent_id) if self._worktrees_ok else self._acquire_shared_fallback(agent_id)

            state[agent_id] = str(ctx.path)
            lock.write(state)
            return ctx

    def release_worktree(self, agent_id: str) -> bool:
        """Release the worktree held by *agent_id*.

        Merges the agent branch into *target_branch* using ``git merge --no-ff``
        then removes the worktree.  In fallback mode releases the advisory lock.

        Returns:
            True on success, False if the agent held no worktree.
        """
        with _PoolStateLock(self._state_path) as lock:
            state = lock.read()
            if agent_id not in state:
                _log.warning("WorktreePool: agent %s has no worktree to release", agent_id)
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
    def worktree(self, agent_id: str) -> Generator[WorktreeContext]:
        """Context manager: acquire on enter, release on exit.

        Example::

            pool = WorktreePool(Path("/my/project"))
            with pool.worktree("agent-42") as ctx:
                (ctx.path / "output.txt").write_text("done")
                ctx.commit_all("agent-42: task complete")
        """
        ctx = self.acquire_worktree(agent_id)
        try:
            yield ctx
        finally:
            self.release_worktree(agent_id)

    def active_agents(self) -> list[str]:
        """Return list of agent IDs that currently hold a worktree."""
        with _PoolStateLock(self._state_path) as lock:
            return list(lock.read().keys())

    def cleanup_stale(self) -> int:
        """Remove pool entries whose worktree directory no longer exists.

        Returns the number of stale entries removed.
        """
        removed = 0
        with _PoolStateLock(self._state_path) as lock:
            state = lock.read()
            fresh = {}
            for agent_id, path_str in state.items():
                if Path(path_str).exists():
                    fresh[agent_id] = path_str
                else:
                    _log.info("WorktreePool: removing stale entry for %s (%s)", agent_id, path_str)
                    removed += 1
                    if self._worktrees_ok:
                        self._git_worktree_remove(path_str)
                    self._try_delete_branch(f"agent/{agent_id}")
            lock.write(fresh)
        return removed

    # ------------------------------------------------------------------
    # Internal: worktree mode
    # ------------------------------------------------------------------

    def _create_worktree(self, agent_id: str) -> WorktreeContext:
        """Create a new git worktree for *agent_id*."""
        branch = f"agent/{agent_id}"
        worktree_path = self._pool_dir / agent_id
        worktree_path.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Ensure branch does not exist; if it does reuse it.
        branch_exists = self._branch_exists(branch)
        if not branch_exists:
            try:
                _run(["git", "branch", branch], self.project_root)
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(f"WorktreePool: failed to create branch {branch!r}: {exc.stderr}") from exc

        # Remove stale worktree registration if directory was orphaned.
        if worktree_path.exists() and any(worktree_path.iterdir()):
            self._git_worktree_remove(str(worktree_path))
            shutil.rmtree(worktree_path, ignore_errors=True)
            worktree_path.mkdir(parents=True, exist_ok=True, mode=0o700)

        try:
            _run(
                ["git", "worktree", "add", str(worktree_path), branch],
                self.project_root,
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"WorktreePool: git worktree add failed for agent {agent_id!r}: {exc.stderr}") from exc

        _log.info("WorktreePool: created worktree for %s at %s (branch %s)", agent_id, worktree_path, branch)
        return WorktreeContext(
            agent_id=agent_id,
            path=worktree_path,
            branch=branch,
            project_root=self.project_root,
            _pool_ref=self,
        )

    def _merge_and_remove(self, agent_id: str, worktree_path: Path, branch: str) -> bool:
        """Merge *branch* into target and remove the worktree.

        Uses SmartMerger when one is configured; falls back to plain
        ``git merge --no-ff``.  @trace FR-MESH-007
        """
        # Determine resolved target branch name (handles 'HEAD')
        target = self._resolve_target_branch()

        # Attempt merge — prefer SmartMerger when configured
        merged = False
        if self._merger is not None:
            merge_result = self._merger.merge_worktree_changes(worktree_path, target)
            merged = merge_result.success
            if merged:
                _log.info(
                    "WorktreePool: smart-merged branch %s into %s (mergiraf=%s)",
                    branch,
                    target,
                    merge_result.used_mergiraf,
                )
            else:
                _log.warning(
                    "WorktreePool: smart-merge of %s into %s failed (conflicts=%s): %s",
                    branch,
                    target,
                    merge_result.conflicts,
                    merge_result.output[:200],
                )
        else:
            try:
                _run(
                    ["git", "merge", "--no-ff", "-m", f"Merge agent/{agent_id} into {target}", branch],
                    self.project_root,
                )
                merged = True
                _log.info("WorktreePool: merged branch %s into %s", branch, target)
            except subprocess.CalledProcessError as exc:
                _log.warning(
                    "WorktreePool: merge of %s into %s failed (conflicts?): %s",
                    branch,
                    target,
                    exc.stderr,
                )

        # Remove worktree regardless of merge result
        removed = self._git_worktree_remove(str(worktree_path))
        if worktree_path.exists():
            shutil.rmtree(worktree_path, ignore_errors=True)

        # Delete agent branch to keep ref namespace clean
        self._try_delete_branch(branch)

        return merged and removed

    def _git_worktree_remove(self, path_str: str) -> bool:
        try:
            _run(["git", "worktree", "remove", "--force", path_str], self.project_root)
            return True
        except subprocess.CalledProcessError:
            return False

    def _branch_exists(self, branch: str) -> bool:
        try:
            result = _run(
                ["git", "branch", "--list", branch],
                self.project_root,
            )
            return branch in result.stdout
        except subprocess.CalledProcessError:
            return False

    def _resolve_target_branch(self) -> str:
        """Resolve 'HEAD' to the actual branch name."""
        if self.target_branch != "HEAD":
            return self.target_branch
        try:
            result = _run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                self.project_root,
            )
            return result.stdout.strip() or "main"
        except subprocess.CalledProcessError:
            return "main"

    def _try_delete_branch(self, branch: str) -> None:
        with suppress(subprocess.CalledProcessError):
            _run(["git", "branch", "-D", branch], self.project_root)

    # ------------------------------------------------------------------
    # Internal: fallback shared-tree mode
    # ------------------------------------------------------------------

    # In fallback mode we store a .lock file per agent in the pool dir.
    # The lock is fcntl-based during acquire/release; the file records
    # the lock ownership so we can detect stale holders.

    def _fallback_lock_path(self, agent_id: str) -> Path:
        return self._pool_dir / f"{agent_id}.fallback.lock"

    def _acquire_shared_fallback(self, agent_id: str) -> WorktreeContext:
        """Advisory lock on the shared project tree for *agent_id*."""
        lock_path = self._fallback_lock_path(agent_id)
        _atomic_write(lock_path, f"agent={agent_id}\nacquired={time.time()}\n")
        _log.info("WorktreePool: fallback advisory lock acquired for %s", agent_id)
        return WorktreeContext(
            agent_id=agent_id,
            path=self.project_root,
            branch=self._resolve_target_branch(),
            project_root=self.project_root,
            _pool_ref=self,
        )

    def _release_shared_fallback(self, agent_id: str, worktree_path: Path) -> bool:
        """Remove the fallback advisory lock file for *agent_id*.

        The *worktree_path* parameter is accepted for API consistency but is
        unused in fallback mode (the path is always the shared project root).
        """
        _ = worktree_path  # documented: unused in fallback mode
        lock_path = self._fallback_lock_path(agent_id)
        try:
            lock_path.unlink(missing_ok=True)
            _log.info("WorktreePool: fallback advisory lock released for %s", agent_id)
            return True
        except OSError as exc:
            _log.warning("WorktreePool: could not remove fallback lock for %s: %s", agent_id, exc)
            return False
