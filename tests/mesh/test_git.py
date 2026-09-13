"""Tests for thegent.mesh.git GitParallelismManager."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import orjson as json
import pytest

from thegent.mesh.git import GitParallelismManager


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=str(path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(path), check=True, capture_output=True)
    (path / "README.md").write_text("init\n")
    subprocess.run(["git", "add", "."], cwd=str(path), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(path), check=True, capture_output=True)


def test_related_overlap_sorted() -> None:
    manager = GitParallelismManager(Path(), "agent-test")
    overlap = manager.related_overlap(
        ["b.py", "a.py", "x.md"],
        ["z.py", "a.py", "b.py"],
    )
    assert overlap == ["a.py", "b.py"]


def test_queue_commit_conflict_writes_jsonl(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    manager = GitParallelismManager(tmp_path, "agent-1")
    queue_file = manager.queue_commit_conflict(
        ref="refs/heads/main",
        reason="related_change_overlap",
        ours=["a.py"],
        theirs=["a.py", "b.py"],
        overlap=["a.py"],
        old_hash="old",
        new_hash="new",
    )
    assert queue_file.exists()
    lines = queue_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["reason"] == "related_change_overlap"
    assert record["overlap"] == ["a.py"]


def test_wait_for_index_lock_times_out(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    manager = GitParallelismManager(tmp_path, "agent-2")
    lock_file = tmp_path / ".git" / "index.lock"
    lock_file.write_text("")
    assert manager.wait_for_index_lock(timeout_s=0.2, poll_s=0.05) is False


def test_wait_for_index_lock_removes_stale_lock(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    manager = GitParallelismManager(tmp_path, "agent-7")
    lock_file = tmp_path / ".git" / "index.lock"
    lock_file.write_text("")

    stale_time = time.time() - 120
    os.utime(lock_file, (stale_time, stale_time))

    assert manager.wait_for_index_lock(timeout_s=0.2, poll_s=0.05, stale_after_s=60.0, allow_stale_cleanup=True) is True
    assert not lock_file.exists()


def test_wait_for_index_lock_respects_open_lock_holder(tmp_path: Path, monkeypatch) -> None:
    _init_git_repo(tmp_path)
    manager = GitParallelismManager(tmp_path, "agent-8")
    lock_file = tmp_path / ".git" / "index.lock"
    lock_file.write_text("")
    monkeypatch.setattr(manager, "_has_open_lock_holder", lambda _path: True)

    stale_time = time.time() - 120
    os.utime(lock_file, (stale_time, stale_time))

    assert (
        manager.wait_for_index_lock(timeout_s=0.2, poll_s=0.05, stale_after_s=60.0, allow_stale_cleanup=True) is False
    )
    assert lock_file.exists()


def test_index_lock_status_absent(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    manager = GitParallelismManager(tmp_path, "agent-9")
    assert manager.index_lock_status() == {
        "exists": False,
        "path": str(tmp_path / ".git" / "index.lock"),
        "age_seconds": None,
        "stale_after_seconds": 90.0,
        "is_stale": False,
        "open_holder_detected": False,
    }


def test_index_lock_status_stale_and_open_state(tmp_path: Path, monkeypatch) -> None:
    _init_git_repo(tmp_path)
    manager = GitParallelismManager(tmp_path, "agent-9")
    lock_file = tmp_path / ".git" / "index.lock"
    lock_file.write_text("")
    stale_time = time.time() - 120
    os.utime(lock_file, (stale_time, stale_time))
    monkeypatch.setattr(manager, "_has_open_lock_holder", lambda _path: True)

    status = manager.index_lock_status(stale_after_s=60.0)
    assert status["exists"] is True
    assert status["path"] == str(lock_file)
    assert status["stale_after_seconds"] == 60.0
    assert status["is_stale"] is False
    assert status["open_holder_detected"] is True
    assert status["age_seconds"] == pytest.approx(time.time() - stale_time, rel=1e-2)


def test_index_lock_status_stale_and_no_open_holder(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    manager = GitParallelismManager(tmp_path, "agent-9")
    lock_file = tmp_path / ".git" / "index.lock"
    lock_file.write_text("")
    stale_time = time.time() - 120
    os.utime(lock_file, (stale_time, stale_time))

    status = manager.index_lock_status(stale_after_s=60.0)
    assert status["exists"] is True
    assert status["path"] == str(lock_file)
    assert status["stale_after_seconds"] == 60.0
    assert status["is_stale"] is True
    assert status["open_holder_detected"] is False
    assert status["age_seconds"] == pytest.approx(time.time() - stale_time, rel=1e-2)


def test_changed_files_between_returns_list(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    manager = GitParallelismManager(tmp_path, "agent-3")

    (tmp_path / "a.txt").write_text("a\n")
    subprocess.run(["git", "add", "a.txt"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "a"], cwd=str(tmp_path), check=True, capture_output=True)
    head2 = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(tmp_path), text=True).strip()
    head1 = subprocess.check_output(["git", "rev-parse", "HEAD~1"], cwd=str(tmp_path), text=True).strip()

    changed = manager.changed_files_between(head1, head2)
    assert "a.txt" in changed


def test_try_auto_merge_commit_success_for_disjoint_changes(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    manager = GitParallelismManager(tmp_path, "agent-4")
    default_branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(tmp_path), text=True
    ).strip()

    # Branch A commit
    subprocess.run(["git", "checkout", "-b", "a"], cwd=str(tmp_path), check=True, capture_output=True)
    (tmp_path / "a.txt").write_text("from-a\n")
    subprocess.run(["git", "add", "a.txt"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "a"], cwd=str(tmp_path), check=True, capture_output=True)
    a_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(tmp_path), text=True).strip()

    # Branch B commit from main
    subprocess.run(["git", "checkout", default_branch], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(["git", "checkout", "-b", "b"], cwd=str(tmp_path), check=True, capture_output=True)
    (tmp_path / "b.txt").write_text("from-b\n")
    subprocess.run(["git", "add", "b.txt"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "b"], cwd=str(tmp_path), check=True, capture_output=True)
    b_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(tmp_path), text=True).strip()

    merged = manager.try_auto_merge_commit(a_hash, b_hash, "auto")
    assert merged is not None


def test_try_auto_merge_commit_returns_none_on_conflict(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    manager = GitParallelismManager(tmp_path, "agent-5")
    default_branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(tmp_path), text=True
    ).strip()

    # Branch A modifies same file
    subprocess.run(["git", "checkout", "-b", "a"], cwd=str(tmp_path), check=True, capture_output=True)
    (tmp_path / "README.md").write_text("a\n")
    subprocess.run(["git", "add", "README.md"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "a"], cwd=str(tmp_path), check=True, capture_output=True)
    a_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(tmp_path), text=True).strip()

    # Branch B modifies same file differently
    subprocess.run(["git", "checkout", default_branch], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(["git", "checkout", "-b", "b"], cwd=str(tmp_path), check=True, capture_output=True)
    (tmp_path / "README.md").write_text("b\n")
    subprocess.run(["git", "add", "README.md"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "b"], cwd=str(tmp_path), check=True, capture_output=True)
    b_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(tmp_path), text=True).strip()

    merged = manager.try_auto_merge_commit(a_hash, b_hash, "auto")
    assert merged is None
