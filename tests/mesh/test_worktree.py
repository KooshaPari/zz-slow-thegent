"""Tests for thegent.mesh.worktree — WorktreeManager worktree lifecycle.

FR traceability: TGNT-P15.1 (worktree creation), TGNT-P15.2 (branch coordination),
TGNT-P15.3 (worktree cleanup / orphan detection / health monitor).
"""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest import mock

import orjson as json
import pytest

from thegent.mesh.worktree import (
    BranchCollisionError,
    WorktreeManager,
)

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_manager(tmp_path: Path) -> WorktreeManager:
    """Return a WorktreeManager rooted under *tmp_path*."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    mesh_root = tmp_path / "mesh"
    mesh_root.mkdir()
    return WorktreeManager(project_root, mesh_root)


# ---------------------------------------------------------------------------
# TGNT-P15.1: Worktree creation
# ---------------------------------------------------------------------------


class TestWorktreeCreation:
    """@trace TGNT-P15.1"""

    def test_worktree_path_uses_agent_id(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.1 — path is .mesh/worktrees/agent-{uuid}."""
        mgr = _make_manager(tmp_path)
        with mock.patch("subprocess.run"):
            path = mgr.create_worktree("abc-123", "feature/x")
        assert path == mgr.worktree_base / "agent-abc-123"

    def test_create_invokes_git_worktree_add(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.1 — git worktree add is called with correct args."""
        mgr = _make_manager(tmp_path)
        expected_path = str(mgr.worktree_base / "agent-a1")
        with mock.patch("subprocess.run") as run_mock:
            mgr.create_worktree("a1", "dev")
            run_mock.assert_any_call(
                ["git", "worktree", "add", expected_path, "dev"],
                cwd=mgr.project_root,
                check=True,
                capture_output=True,
            )

    def test_create_removes_existing_worktree_first(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.1 — existing worktree is removed before re-creation."""
        mgr = _make_manager(tmp_path)
        worktree_dir = mgr.worktree_base / "agent-dup"
        worktree_dir.mkdir(parents=True)

        with mock.patch("subprocess.run") as run_mock:
            mgr.create_worktree("dup", "main")
            # First call should be the remove, then the add
            calls = [c[0][0] for c in run_mock.call_args_list]
            assert ["git", "worktree", "remove", "--force", str(worktree_dir)] in calls

    def test_create_registers_branch(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.1 — branch is registered after creation."""
        mgr = _make_manager(tmp_path)
        with mock.patch("subprocess.run"):
            mgr.create_worktree("reg-1", "feature/bar")
        registry = mgr.get_branch_status()
        assert "reg-1" in registry
        assert registry["reg-1"]["branch"] == "feature/bar"

    def test_create_returns_path_on_git_failure(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.1 — path returned even when git subprocess fails."""
        mgr = _make_manager(tmp_path)
        with mock.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
            path = mgr.create_worktree("fail-1", "main")
        assert path == mgr.worktree_base / "agent-fail-1"


# ---------------------------------------------------------------------------
# TGNT-P15.2: Branch coordination
# ---------------------------------------------------------------------------


class TestBranchCoordination:
    """@trace TGNT-P15.2"""

    def test_branch_collision_detected(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.2 — collision when two agents claim the same branch."""
        mgr = _make_manager(tmp_path)
        with mock.patch("subprocess.run"):
            mgr.create_worktree("agent-a", "feature/shared")

        with pytest.raises(BranchCollisionError, match="feature/shared"):
            with mock.patch("subprocess.run"):
                mgr.create_worktree("agent-b", "feature/shared")

    def test_same_agent_can_reclaim_branch(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.2 — same agent re-creating does not collide."""
        mgr = _make_manager(tmp_path)
        with mock.patch("subprocess.run"):
            mgr.create_worktree("agent-x", "feature/mine")
            # Same agent, same branch — should not raise
            mgr.create_worktree("agent-x", "feature/mine")

    def test_registry_tracks_multiple_agents(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.2 — registry tracks all registered agents."""
        mgr = _make_manager(tmp_path)
        with mock.patch("subprocess.run"):
            mgr.create_worktree("a1", "branch/a1")
            mgr.create_worktree("a2", "branch/a2")
            mgr.create_worktree("a3", "branch/a3")

        status = mgr.get_branch_status()
        assert len(status) == 3
        assert status["a1"]["branch"] == "branch/a1"
        assert status["a2"]["branch"] == "branch/a2"
        assert status["a3"]["branch"] == "branch/a3"

    def test_unregister_on_remove(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.2 — remove_worktree unregisters branch."""
        mgr = _make_manager(tmp_path)
        with mock.patch("subprocess.run"):
            mgr.create_worktree("rm-me", "branch/rm")
        assert "rm-me" in mgr.get_branch_status()

        with mock.patch("subprocess.run"):
            mgr.remove_worktree("rm-me")
        assert "rm-me" not in mgr.get_branch_status()

    def test_collision_after_release(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.2 — branch is available after previous agent releases."""
        mgr = _make_manager(tmp_path)
        with mock.patch("subprocess.run"):
            mgr.create_worktree("first", "feature/reuse")
            mgr.remove_worktree("first")
            # Now a different agent should be able to take the same branch
            mgr.create_worktree("second", "feature/reuse")

        status = mgr.get_branch_status()
        assert "second" in status
        assert "first" not in status

    def test_registry_persists_to_disk(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.2 — registry file is valid JSON on disk."""
        mgr = _make_manager(tmp_path)
        with mock.patch("subprocess.run"):
            mgr.create_worktree("persist-1", "b/p1")

        raw = json.loads(mgr._registry_path.read_text(encoding="utf-8"))
        assert "persist-1" in raw
        assert raw["persist-1"]["branch"] == "b/p1"
        assert "ts" in raw["persist-1"]


# ---------------------------------------------------------------------------
# TGNT-P15.3: Worktree cleanup — remove, orphan detection, health
# ---------------------------------------------------------------------------


class TestWorktreeCleanup:
    """@trace TGNT-P15.3"""

    def test_remove_nonexistent_returns_true(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.3 — removing a missing worktree returns True."""
        mgr = _make_manager(tmp_path)
        assert mgr.remove_worktree("nonexistent") is True

    def test_remove_invokes_git_worktree_remove(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.3 — git worktree remove --force is called."""
        mgr = _make_manager(tmp_path)
        worktree_dir = mgr.worktree_base / "agent-rm1"
        worktree_dir.mkdir(parents=True)

        with mock.patch("subprocess.run") as run_mock:
            mgr.remove_worktree("rm1")
            run_mock.assert_any_call(
                ["git", "worktree", "remove", "--force", str(worktree_dir)],
                cwd=mgr.project_root,
                check=True,
                capture_output=True,
            )

    def test_remove_falls_back_to_rmtree(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.3 — shutil.rmtree used when git remove fails."""
        mgr = _make_manager(tmp_path)
        worktree_dir = mgr.worktree_base / "agent-rmfail"
        worktree_dir.mkdir(parents=True)

        with mock.patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "git"),
        ):
            result = mgr.remove_worktree("rmfail")
        assert result is False
        # shutil.rmtree should have cleaned it up
        assert not worktree_dir.exists()

    def test_cleanup_orphans_removes_old_dirs(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.3 — orphan dirs older than grace period are cleaned."""
        mgr = _make_manager(tmp_path)
        orphan_dir = mgr.worktree_base / "agent-orphan1"
        orphan_dir.mkdir(parents=True)

        with mock.patch("subprocess.run"):
            # grace_seconds=0 means any age qualifies
            removed = mgr.cleanup_orphans(grace_seconds=0)
        assert "orphan1" in removed

    def test_cleanup_orphans_respects_grace_period(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.3 — orphan within grace period is NOT removed."""
        mgr = _make_manager(tmp_path)
        orphan_dir = mgr.worktree_base / "agent-young"
        orphan_dir.mkdir(parents=True)

        # With a very large grace period, the directory should be kept
        removed = mgr.cleanup_orphans(grace_seconds=999999)
        assert removed == []
        assert orphan_dir.exists()

    def test_cleanup_orphans_skips_registered(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.3 — registered agents are not orphans."""
        mgr = _make_manager(tmp_path)
        with mock.patch("subprocess.run"):
            mgr.create_worktree("registered", "b/reg")
        # Create the worktree directory (mock doesn't create it)
        (mgr.worktree_base / "agent-registered").mkdir(parents=True, exist_ok=True)

        removed = mgr.cleanup_orphans(grace_seconds=0)
        assert "registered" not in removed

    def test_cleanup_orphans_empty_base(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.3 — no error when worktree base doesn't exist."""
        mgr = _make_manager(tmp_path)
        # worktree_base does not exist
        removed = mgr.cleanup_orphans(grace_seconds=0)
        assert removed == []

    def test_health_check_reports_orphans(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.3 — health_check reports orphan count."""
        mgr = _make_manager(tmp_path)
        # Create one registered and one orphan
        with mock.patch("subprocess.run"):
            mgr.create_worktree("healthy", "b/h")
        (mgr.worktree_base / "agent-healthy").mkdir(parents=True, exist_ok=True)
        (mgr.worktree_base / "agent-orphan-hc").mkdir(parents=True, exist_ok=True)

        health = mgr.health_check()
        assert health["registered_agents"] == 1
        assert health["worktree_dirs"] == 2
        assert health["orphan_dirs"] == 1
        assert "agent-orphan-hc" in health["orphan_names"]

    def test_health_check_empty(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.3 — health_check on fresh manager is clean."""
        mgr = _make_manager(tmp_path)
        health = mgr.health_check()
        assert health["registered_agents"] == 0
        assert health["worktree_dirs"] == 0
        assert health["orphan_dirs"] == 0


# ---------------------------------------------------------------------------
# TGNT-P15.2: list_worktrees parsing
# ---------------------------------------------------------------------------


class TestListWorktrees:
    """@trace TGNT-P15.2"""

    def test_list_parses_porcelain_output(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.2 — porcelain output is parsed correctly."""
        mgr = _make_manager(tmp_path)
        porcelain = (
            "worktree /project\n"
            "branch refs/heads/main\n"
            "\n"
            "worktree /project/.mesh/worktrees/agent-abc\n"
            "branch refs/heads/feature/abc\n"
            "\n"
        )
        with mock.patch("subprocess.check_output", return_value=porcelain):
            result = mgr.list_worktrees()
        assert len(result) == 1
        assert result[0]["path"] == "/project/.mesh/worktrees/agent-abc"
        assert result[0]["branch"] == "refs/heads/feature/abc"

    def test_list_returns_empty_on_error(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.2 — CalledProcessError yields empty list."""
        mgr = _make_manager(tmp_path)
        with mock.patch(
            "subprocess.check_output",
            side_effect=subprocess.CalledProcessError(1, "git"),
        ):
            assert mgr.list_worktrees() == []

    def test_list_filters_non_mesh_worktrees(self, tmp_path: Path) -> None:
        """# @trace TGNT-P15.2 — only .mesh/worktrees paths are returned."""
        mgr = _make_manager(tmp_path)
        porcelain = "worktree /other/path\nbranch refs/heads/other\n\n"
        with mock.patch("subprocess.check_output", return_value=porcelain):
            assert mgr.list_worktrees() == []
