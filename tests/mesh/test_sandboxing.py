"""Mesh sandbox policy tests for SCLI-P10.x."""

from pathlib import Path

from thegent.mesh.sandbox import AutonomyTier, Sandboxing


def test_bubblewrap_args_for_worktree_tier(tmp_path: Path) -> None:
    """SCLI-P10.1 generates a worktree bind for non-read-only operations."""
    sandbox = Sandboxing(tmp_path, "agent-1")
    args = sandbox.get_bubblewrap_args(AutonomyTier.WORKTREE)

    assert "bwrap" in args
    assert str(tmp_path / ".mesh" / "worktrees" / "agent-agent-1") in args
    assert "--unshare-net" in args


def test_bubblewrap_args_for_read_only_tier(tmp_path: Path) -> None:
    """SCLI-P10.1 uses read-only binds for the read-only tier."""
    sandbox = Sandboxing(tmp_path, "agent-2")
    args = sandbox.get_bubblewrap_args(AutonomyTier.READ_ONLY)

    assert "--ro-bind" in args
    assert str(tmp_path) in args


def test_seatbelt_profile_read_only(tmp_path: Path) -> None:
    """SCLI-P10.2 returns a deny-default profile for read-only mode."""
    sandbox = Sandboxing(tmp_path, "agent-3")
    profile = sandbox.get_seatbelt_profile(AutonomyTier.READ_ONLY)

    assert "(deny default)" in profile
    assert f'(subpath "{tmp_path}")' in profile


def test_classify_operation_tiers() -> None:
    """SCLI-P10.4 applies command-based classification."""
    sandbox = Sandboxing(Path("/tmp"), "agent-4")

    assert sandbox.classify_operation("ls -la", "src") == AutonomyTier.READ_ONLY
    assert sandbox.classify_operation("git status", "src") == AutonomyTier.GIT_SCOPED
    assert sandbox.classify_operation("git commit -am", "src") == AutonomyTier.SHARED_MESH
    assert sandbox.classify_operation("rm -rf dist", "src") == AutonomyTier.PRODUCTION
    assert sandbox.classify_operation("python run.py", "src") == AutonomyTier.WORKTREE


def test_check_autonomy_limits(tmp_path: Path) -> None:
    """SCLI-P10.3 succeeds only when current tier is sufficient."""
    sandbox = Sandboxing(tmp_path, "agent-5")

    assert sandbox.check_autonomy(AutonomyTier.WORKTREE, AutonomyTier.READ_ONLY) is True
    assert sandbox.check_autonomy(AutonomyTier.READ_ONLY, AutonomyTier.WORKTREE) is False
