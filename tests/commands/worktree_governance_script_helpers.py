"""Shared helpers for worktree governance shell-script tests."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_NAME = "worktree_governance.sh"


def init_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "worktree-governance-repo"
    scripts_root = repo_root / "scripts"
    scripts_root.mkdir(parents=True)

    shutil.copy2(REPO_ROOT / "scripts" / SCRIPT_NAME, scripts_root / SCRIPT_NAME)
    (scripts_root / SCRIPT_NAME).chmod(0o755)

    subprocess.run(
        ["git", "init", "-q", "-b", "main"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )

    (repo_root / "README.md").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "seed"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    return repo_root


def run_script(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(repo_root / "scripts" / SCRIPT_NAME), *args],
        cwd=repo_root,
        env={**os.environ},
        capture_output=True,
        text=True,
        check=False,
    )


def setup_canary_remote(repo_root: Path) -> Path:
    remote_root = repo_root.parent / "worktree-governance-remote.git"
    subprocess.run(
        ["git", "init", "--bare", "-q", str(remote_root)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "remote", "add", "origin", str(remote_root)],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "push", "-q", "-u", "origin", "main"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )

    subprocess.run(
        ["git", "checkout", "-q", "-b", "canary"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    (repo_root / "README.md").write_text("seed\ncanary\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "canary"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "push", "-q", "-u", "origin", "canary"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "-q", "main"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    return remote_root


def push_remote_branch(
    repo_root: Path,
    branch_name: str,
    file_name: str,
    content: str,
    commit_msg: str,
) -> None:
    temp_branch = "refresh-source"
    subprocess.run(
        ["git", "checkout", "-q", "-b", temp_branch],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    (repo_root / file_name).write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", file_name], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", commit_msg],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "push", "-q", "origin", f"HEAD:refs/heads/{branch_name}"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "-q", "main"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
