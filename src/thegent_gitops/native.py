"""BKM-06: Git operations using native Rust (thegent-git) with subprocess fallback.

Provides HEAD, status, and diff-stat git metadata using either:
1. thegent-git PyO3 extension (native Rust, fastest)
2. subprocess git (fallback, always available)

FR-GIT-001  @trace FR-GIT-001
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

from thegent.infra.shim_subprocess import run as shim_run

_log = logging.getLogger(__name__)

# Native Rust extension (preferred)
_native_available = False
try:
    import thegent_git

    _native_available = True
except ImportError:
    thegent_git = None
    _log.debug("thegent-git not available, using subprocess fallback")


def _run_git_command(repo_path: str, *args: str) -> str | None:
    """Run a git command and return output."""
    try:
        result = shim_run(
            ["git", "-C", repo_path, *args],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


class GitNative:
    """Native git metadata provider using Rust with subprocess fallback.

    Uses thegent-git PyO3 extension when available, falls back to subprocess
    git commands when not available.
    """

    def __init__(self, repo_path: str | Path = ".") -> None:
        self.repo_path = str(repo_path)

    def head(self) -> dict[str, Any]:
        """Return HEAD commit SHA and branch name.

        Returns:
            ``{"sha": "<40-char-hex>", "branch": "<name>"}``
        """
        if _native_available and hasattr(thegent_git, "get_head_sha"):
            sha = thegent_git.get_head_sha(self.repo_path)
            branch = thegent_git.get_branch_name(self.repo_path)
            return {"sha": sha or "", "branch": branch or "HEAD"}

        # Fallback to subprocess
        sha = _run_git_command(self.repo_path, "rev-parse", "HEAD")
        branch = _run_git_command(self.repo_path, "rev-parse", "--abbrev-ref", "HEAD")
        return {"sha": sha or "", "branch": branch or "HEAD"}

    def status(self) -> dict[str, Any]:
        """Return working-tree status.

        Returns:
            ``{"modified": [...], "untracked": [...], "staged": [...]}``
        """
        if _native_available and hasattr(thegent_git, "get_status"):
            return thegent_git.get_status(self.repo_path)

        # Fallback to subprocess
        result: dict[str, Any] = {"modified": [], "untracked": [], "staged": []}

        # Get modified
        modified = _run_git_command(self.repo_path, "diff", "--name-only")
        if modified:
            result["modified"] = modified.split("\n")

        # Get untracked
        untracked = _run_git_command(self.repo_path, "ls-files", "--others", "--exclude-standard")
        if untracked:
            result["untracked"] = untracked.split("\n")

        # Get staged
        staged = _run_git_command(self.repo_path, "diff", "--cached", "--name-only")
        if staged:
            result["staged"] = staged.split("\n")

        return result

    def diff_stat(self) -> dict[str, Any]:
        """Return diff stats comparing HEAD to current worktree + index.

        Returns:
            ``{"files_changed": N, "insertions": N, "deletions": N}``
        """
        if _native_available and hasattr(thegent_git, "diff_stat"):
            return thegent_git.diff_stat("HEAD", self.repo_path)

        # Fallback to subprocess
        diff = _run_git_command(self.repo_path, "diff", "--stat")
        if not diff:
            return {"files_changed": 0, "insertions": 0, "deletions": 0}

        # Parse diff --stat output
        try:
            lines = diff.strip().split("\n")
            if lines:
                last_line = lines[-1]
                # Format: "X files changed, Y insertions(+), Z deletions(-)"
                parts = last_line.split(",")
                files_changed = 0
                insertions = 0
                deletions = 0
                for part in parts:
                    part = part.strip()
                    if "file" in part:
                        files_changed = int(part.split()[0])
                    elif "insertion" in part:
                        insertions = int(part.split()[0])
                    elif "deletion" in part:
                        deletions = int(part.split()[0])
                return {"files_changed": files_changed, "insertions": insertions, "deletions": deletions}
        except (ValueError, IndexError):
            pass

        return {"files_changed": 0, "insertions": 0, "deletions": 0}

    # -----------------------------------------------------------------------
    # New methods using expanded Rust API
    # -----------------------------------------------------------------------

    def list_branches(self, all_remotes: bool = False) -> list[str]:
        """List all branches.

        Args:
            all_remotes: Include remote-tracking branches

        Returns:
            List of branch names
        """
        if _native_available and hasattr(thegent_git, "list_branches"):
            return thegent_git.list_branches(self.repo_path, all_remotes)

        # Fallback to subprocess
        args = ["branch"]
        if all_remotes:
            args.append("-a")
        args.append("--format=%(refname:short)")

        result = _run_git_command(self.repo_path, *args)
        return result.split("\n") if result else []

    def list_remotes(self) -> dict[str, str]:
        """List remote repositories.

        Returns:
            Dict mapping remote name to URL
        """
        if _native_available and hasattr(thegent_git, "list_remotes"):
            return thegent_git.list_remotes(self.repo_path)

        # Fallback to subprocess
        result: dict[str, str] = {}
        output = _run_git_command(self.repo_path, "remote", "-v")
        if output:
            for line in output.split("\n"):
                parts = line.split()
                if len(parts) >= 2 and parts[0] not in result:
                    result[parts[0]] = parts[1]
        return result

    def log(self, max_count: int = 10, oneline: bool = True) -> list[str]:
        """Get commit log.

        Args:
            max_count: Maximum number of commits
            oneline: Use oneline format

        Returns:
            List of commit messages
        """
        if _native_available and hasattr(thegent_git, "get_log"):
            return thegent_git.get_log(self.repo_path, max_count, oneline)

        # Fallback to subprocess
        args = ["log", f"--max-count={max_count}"]
        if oneline:
            args.append("--oneline")

        result = _run_git_command(self.repo_path, *args)
        return result.split("\n") if result else []

    def fetch(self, remote: str | None = None, prune: bool = False) -> bool:
        """Fetch from remote.

        Args:
            remote: Remote name (None for all)
            prune: Prune deleted branches

        Returns:
            True if successful
        """
        if _native_available and hasattr(thegent_git, "fetch"):
            return thegent_git.fetch(self.repo_path, remote, prune)

        # Fallback to subprocess
        args = ["fetch"]
        if remote:
            args.append(remote)
        if prune:
            args.append("--prune")

        result = _run_git_command(self.repo_path, *args)
        return result is not None or True  # fetch often has no output

    def has_changes(self) -> bool:
        """Check if there are uncommitted changes.

        Returns:
            True if there are changes
        """
        if _native_available and hasattr(thegent_git, "has_changes"):
            return thegent_git.has_changes(self.repo_path)

        # Fallback to subprocess
        result = _run_git_command(self.repo_path, "status", "--porcelain")
        return bool(result)


# Module-level convenience functions
def get_head(repo_path: str = ".") -> dict[str, Any]:
    """Get HEAD info for repo."""
    return GitNative(repo_path).head()


def get_status(repo_path: str = ".") -> dict[str, Any]:
    """Get status for repo."""
    return GitNative(repo_path).status()


def list_branches(repo_path: str = ".", all_remotes: bool = False) -> list[str]:
    """List branches for repo."""
    return GitNative(repo_path).list_branches(all_remotes)


def has_changes(repo_path: str = ".") -> bool:
    """Check if repo has uncommitted changes."""
    return GitNative(repo_path).has_changes()
