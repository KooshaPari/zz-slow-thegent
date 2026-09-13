"""Regression tests for worktree governance refresh behavior."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.commands.worktree_governance_script_helpers import (
    init_repo,
    push_remote_branch,
    run_script,
    setup_canary_remote,
)


@pytest.mark.unit
def test_worktree_governance_refresh_rebases_onto_remote_ref(tmp_path: Path) -> None:
    """`worktree_governance.sh refresh` replays local work on top of a remote canary ref."""
    repo_root = init_repo(tmp_path)
    remote_root = setup_canary_remote(repo_root)
    assert remote_root.exists()

    anchor = "fix-mcp-timeout"
    active_path = repo_root / ".worktrees" / "backend" / "m" / anchor / "active"

    create = run_script(repo_root, "new", "backend", "m", anchor, "main")
    assert create.returncode == 0, create.stderr
    assert active_path.exists()

    local_file = active_path / "local-change.txt"
    local_file.write_text("local\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", local_file.name],
        cwd=active_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "local"],
        cwd=active_path,
        check=True,
        capture_output=True,
    )

    refresh = run_script(repo_root, "refresh", anchor, "--remote", "origin", "--ref", "origin/canary")
    assert refresh.returncode == 0, refresh.stderr
    assert "[OK] refreshed worktree" in refresh.stdout
    assert "origin/canary" in refresh.stdout

    readme = (active_path / "README.md").read_text(encoding="utf-8")
    assert "canary" in readme
    assert local_file.read_text(encoding="utf-8") == "local\n"


@pytest.mark.unit
def test_worktree_governance_refresh_uses_default_remote_branch(tmp_path: Path) -> None:
    """`worktree_governance.sh refresh` falls back to the remote branch matching the worktree branch."""
    repo_root = init_repo(tmp_path)
    setup_canary_remote(repo_root)

    anchor = "fix-mcp-timeout"
    branch_name = f"backend/m/{anchor}"
    push_remote_branch(repo_root, branch_name, "default-track.txt", "default-track\n", "default-track")

    active_path = repo_root / ".worktrees" / "backend" / "m" / anchor / "active"
    create = run_script(repo_root, "new", "backend", "m", anchor, "main")
    assert create.returncode == 0, create.stderr

    local_file = active_path / "local-change.txt"
    local_file.write_text("local\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", local_file.name],
        cwd=active_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "local"],
        cwd=active_path,
        check=True,
        capture_output=True,
    )

    refresh = run_script(repo_root, "refresh", anchor, "--remote", "origin")
    assert refresh.returncode == 0, refresh.stderr
    assert "[OK] refreshed worktree" in refresh.stdout
    assert f"origin/{branch_name}" in refresh.stdout

    default_track = (active_path / "default-track.txt").read_text(encoding="utf-8")
    assert "default-track" in default_track


@pytest.mark.unit
def test_worktree_governance_refresh_supports_merge_strategy(tmp_path: Path) -> None:
    """`worktree_governance.sh refresh` supports explicit merge refreshes."""
    repo_root = init_repo(tmp_path)
    setup_canary_remote(repo_root)

    anchor = "fix-mcp-timeout"
    active_path = repo_root / ".worktrees" / "backend" / "m" / anchor / "active"

    create = run_script(repo_root, "new", "backend", "m", anchor, "main")
    assert create.returncode == 0, create.stderr

    local_file = active_path / "local-change.txt"
    local_file.write_text("local\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", local_file.name],
        cwd=active_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "local"],
        cwd=active_path,
        check=True,
        capture_output=True,
    )

    refresh = run_script(
        repo_root,
        "refresh",
        anchor,
        "--remote",
        "origin",
        "--ref",
        "origin/canary",
        "--strategy",
        "merge",
    )
    assert refresh.returncode == 0, refresh.stderr
    assert "[OK] refreshed worktree" in refresh.stdout
    assert "origin/canary" in refresh.stdout

    readme = (active_path / "README.md").read_text(encoding="utf-8")
    assert "canary" in readme


@pytest.mark.unit
def test_worktree_governance_refresh_fails_on_dirty_worktree(tmp_path: Path) -> None:
    """`worktree_governance.sh refresh` fails loudly when the worktree is dirty."""
    repo_root = init_repo(tmp_path)
    setup_canary_remote(repo_root)

    anchor = "fix-mcp-timeout"
    create = run_script(repo_root, "new", "backend", "m", anchor, "main")
    assert create.returncode == 0, create.stderr

    dirty_file = repo_root / ".worktrees" / "backend" / "m" / anchor / "active" / "dirty.txt"
    dirty_file.write_text("dirty\n", encoding="utf-8")

    proc = run_script(repo_root, "refresh", anchor, "--remote", "origin", "--ref", "origin/canary")
    assert proc.returncode != 0
    assert "worktree has uncommitted changes" in proc.stderr


@pytest.mark.unit
@pytest.mark.parametrize(
    ("args", "expected_error"),
    [
        (
            (
                "refresh",
                "fix-mcp-timeout",
                "--remote",
                "bad/remote",
                "--ref",
                "origin/canary",
            ),
            "invalid remote name",
        ),
        (
            (
                "refresh",
                "fix-mcp-timeout",
                "--remote",
                "origin",
                "--ref",
                "origin/missing",
            ),
            "invalid upstream ref",
        ),
        (
            ("refresh", "fix-mcp-timeout", "--remote", "origin", "--strategy", "bad"),
            "invalid strategy",
        ),
    ],
)
def test_worktree_governance_refresh_rejects_invalid_inputs(
    tmp_path: Path,
    args: tuple[str, ...],
    expected_error: str,
) -> None:
    """`worktree_governance.sh refresh` rejects invalid remote, ref, and strategy inputs."""
    repo_root = init_repo(tmp_path)
    setup_canary_remote(repo_root)
    create = run_script(repo_root, "new", "backend", "m", "fix-mcp-timeout", "main")
    assert create.returncode == 0, create.stderr

    proc = run_script(repo_root, *args)
    assert proc.returncode != 0
    assert expected_error in proc.stderr
