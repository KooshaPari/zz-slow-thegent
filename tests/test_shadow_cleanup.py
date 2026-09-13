"""Tests for WL-036: Stale shadow directory cleanup.

Covers:
1. mcp_prune shadow cleanup via _prune_stale_shadow_and_logs
2. doctor.py _check_project_hints stale shadow detection and fix_hint
3. NeverIdleLoop periodic shadow cleanup step in gardening

# @trace WL-036
"""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# WL-036: mcp_prune shadow cleanup
# ---------------------------------------------------------------------------


class TestPruneStalesShadowAndLogs:
    """Unit tests for _prune_stale_shadow_and_logs."""

    # @trace WL-036

    def test_removes_shadow_dir_older_than_cutoff(self, tmp_path: Path) -> None:
        """Shadow dir with mtime older than cutoff is removed in non-dry-run.

        _prune_stale_shadow_and_logs searches root.parent (parent of cwd),
        so the .shadow-* dirs must be siblings of the cwd, not children.
        """
        # workspace is the project cwd; .shadow-old is at the same level (tmp_path)
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        shadow = tmp_path / ".shadow-old"
        shadow.mkdir()

        # Set mtime to 48h ago
        old_time = time.time() - (48 * 3600)
        import os

        os.utime(shadow, (old_time, old_time))

        from thegent.orchestration.pruning.prune import _prune_stale_shadow_and_logs

        # cwd = workspace; root.parent = tmp_path; globs .shadow-* in tmp_path
        with patch("thegent.orchestration.pruning.prune.Path.cwd", return_value=workspace):
            shadow_count, _logs = _prune_stale_shadow_and_logs(
                dry_run=False,
                shadow_max_age_hours=24,
                quality_log_max_age_days=7,
            )

        assert shadow_count == 1
        assert not shadow.exists()

    def test_dry_run_does_not_remove_shadow_dir(self, tmp_path: Path) -> None:
        """Dry-run reports shadow dirs but does not remove them."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        shadow = tmp_path / ".shadow-old"
        shadow.mkdir()

        old_time = time.time() - (48 * 3600)
        import os

        os.utime(shadow, (old_time, old_time))

        from thegent.orchestration.pruning.prune import _prune_stale_shadow_and_logs

        with patch("thegent.orchestration.pruning.prune.Path.cwd", return_value=workspace):
            shadow_count, _logs = _prune_stale_shadow_and_logs(
                dry_run=True,
                shadow_max_age_hours=24,
                quality_log_max_age_days=7,
            )

        assert shadow_count == 1
        assert shadow.exists()  # Not removed in dry_run

    def test_recent_shadow_dir_not_removed(self, tmp_path: Path) -> None:
        """Shadow dir newer than cutoff is not removed."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        shadow = tmp_path / ".shadow-new"
        shadow.mkdir()
        # mtime is current - much newer than 24h cutoff

        from thegent.orchestration.pruning.prune import _prune_stale_shadow_and_logs

        with patch("thegent.orchestration.pruning.prune.Path.cwd", return_value=workspace):
            shadow_count, _logs = _prune_stale_shadow_and_logs(
                dry_run=False,
                shadow_max_age_hours=24,
                quality_log_max_age_days=7,
            )

        assert shadow_count == 0
        assert shadow.exists()

    def test_multiple_shadow_dirs_counted(self, tmp_path: Path) -> None:
        """Multiple stale shadow dirs are all counted and removed."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        old_time = time.time() - (72 * 3600)
        import os

        for name in [".shadow-a420", ".shadow-b540", ".shadow-c660"]:
            d = tmp_path / name
            d.mkdir()
            os.utime(d, (old_time, old_time))

        from thegent.orchestration.pruning.prune import _prune_stale_shadow_and_logs

        with patch("thegent.orchestration.pruning.prune.Path.cwd", return_value=workspace):
            shadow_count, _logs = _prune_stale_shadow_and_logs(
                dry_run=False,
                shadow_max_age_hours=24,
                quality_log_max_age_days=7,
            )

        assert shadow_count == 3

    def test_non_directory_shadow_files_ignored(self, tmp_path: Path) -> None:
        """Files matching .shadow-* pattern but not directories are skipped."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        old_time = time.time() - (72 * 3600)
        import os

        # A file, not a dir
        shadow_file = tmp_path / ".shadow-notadir"
        shadow_file.write_text("not a dir")
        os.utime(shadow_file, (old_time, old_time))

        from thegent.orchestration.pruning.prune import _prune_stale_shadow_and_logs

        with patch("thegent.orchestration.pruning.prune.Path.cwd", return_value=workspace):
            shadow_count, _logs = _prune_stale_shadow_and_logs(
                dry_run=False,
                shadow_max_age_hours=24,
                quality_log_max_age_days=7,
            )

        assert shadow_count == 0


class TestMcpPruneShadowIntegration:
    """Integration tests for mcp_prune shadow cleanup path."""

    # @trace WL-036

    def test_mcp_prune_calls_shadow_cleanup(self) -> None:
        """mcp_prune calls _prune_stale_shadow_and_logs after process pruning.

        shadow cleanup runs after the process kill loop completes (including when
        there are no processes to kill - the function returns early in that case).
        We verify the behavior by providing a process that passes all filters and
        ensuring shadow cleanup is invoked.
        """
        # Simulate ps output with a node process that will match as a candidate
        fake_ps_output = "  PID  PPID TTY    RSS COMMAND\n99999  1    ??    1000 node /fake/pyright-langserver\n"
        with (
            patch("thegent.orchestration.pruning.prune.run_subprocess_optimized") as mock_ps,
            patch("thegent.orchestration.pruning.prune._prune_stale_shadow_and_logs") as mock_shadow,
            patch("thegent.orchestration.pruning.prune.list_tmux_panes", return_value=[]),
            patch("thegent.orchestration.pruning.prune.kill_process", return_value=True),
            patch("thegent.orchestration.pruning.prune.is_orphan_by_ppid", return_value=True),
        ):
            mock_ps.return_value = MagicMock(stdout=fake_ps_output, returncode=0)
            mock_shadow.return_value = (0, 0)

            from thegent.orchestration.pruning.prune import mcp_prune

            mcp_prune(dry_run=False, shadow_max_age_hours=12, caller_info="test")

        mock_shadow.assert_called_once_with(
            dry_run=False,
            shadow_max_age_hours=12,
            quality_log_max_age_days=7,
        )

    def test_mcp_prune_default_shadow_age_is_24h(self) -> None:
        """mcp_prune default shadow_max_age_hours is 24."""
        import inspect

        from thegent.orchestration.pruning.prune import mcp_prune

        sig = inspect.signature(mcp_prune)
        assert sig.parameters["shadow_max_age_hours"].default == 24

    def test_mcp_prune_dry_run_shadow_cleanup(self) -> None:
        """mcp_prune dry_run=True passes dry_run=True to shadow cleanup."""
        with (
            patch("thegent.orchestration.pruning.prune.run_subprocess_optimized") as mock_ps,
            patch("thegent.orchestration.pruning.prune._prune_stale_shadow_and_logs") as mock_shadow,
            patch("thegent.orchestration.pruning.prune.list_tmux_panes", return_value=[]),
        ):
            mock_ps.return_value = MagicMock(stdout="  PID  PPID TTY    RSS COMMAND\n", returncode=0)
            mock_shadow.return_value = (2, 0)

            from thegent.orchestration.pruning.prune import mcp_prune

            mcp_prune(dry_run=True, caller_info="test-dry")

        mock_shadow.assert_called_once_with(
            dry_run=True,
            shadow_max_age_hours=24,
            quality_log_max_age_days=7,
        )


# ---------------------------------------------------------------------------
# WL-036: doctor --fix shadow cleanup
# ---------------------------------------------------------------------------


class TestDoctorShadowDetection:
    """Verify doctor _check_project_hints detects stale shadow dirs."""

    # @trace WL-036

    def test_stale_shadow_dir_produces_warn_result(self, tmp_path: Path) -> None:
        """_check_project_hints returns a CheckResult with warn status for stale shadows."""
        import os

        parent = tmp_path
        shadow = parent / ".shadow-stale"
        shadow.mkdir()
        old_time = time.time() - (48 * 3600)
        os.utime(shadow, (old_time, old_time))

        # Patch project root so it looks in tmp_path.parent for .shadow-* dirs
        project_root_mock = parent / "project"
        project_root_mock.mkdir()

        with patch("thegent.doctor._project_root_cache", project_root_mock):
            from thegent.doctor import _check_project_hints

            results = _check_project_hints()

        shadow_results = [r for r in results if "shadow" in r.name.lower()]
        assert len(shadow_results) == 1
        assert shadow_results[0].status == "warn"
        assert shadow_results[0].fix_hint is not None

    def test_no_stale_shadows_no_shadow_result(self, tmp_path: Path) -> None:
        """_check_project_hints returns no shadow result when no stale dirs exist."""
        project_root_mock = tmp_path / "project"
        project_root_mock.mkdir()

        with patch("thegent.doctor._project_root_cache", project_root_mock):
            from thegent.doctor import _check_project_hints

            results = _check_project_hints()

        shadow_results = [r for r in results if "shadow" in r.name.lower()]
        assert len(shadow_results) == 0

    def test_shadow_fix_hint_references_prune_command(self, tmp_path: Path) -> None:
        """The fix_hint for stale shadows references thegent mcp prune."""
        import os

        parent = tmp_path
        project_root_mock = parent / "project"
        project_root_mock.mkdir()

        shadow = parent / ".shadow-old"
        shadow.mkdir()
        old_time = time.time() - (48 * 3600)
        os.utime(shadow, (old_time, old_time))

        with patch("thegent.doctor._project_root_cache", project_root_mock):
            from thegent.doctor import _check_project_hints

            results = _check_project_hints()

        shadow_results = [r for r in results if "shadow" in r.name.lower()]
        if shadow_results:
            hint = shadow_results[0].fix_hint or ""
            # The hint should reference a cleanup mechanism
            assert any(kw in hint.lower() for kw in ["prune", "cleanup", "mcp", "thegent"])


# ---------------------------------------------------------------------------
# WL-036: NeverIdleLoop periodic shadow cleanup
# ---------------------------------------------------------------------------


class TestNeverIdleLoopShadowCleanup:
    """Verify that NeverIdleLoop includes a shadow cleanup step."""

    # @trace WL-036

    def test_shadow_cleanup_step_in_gardening_steps(self) -> None:
        """NeverIdleLoop GARDENING_STEPS includes shadow_cleanup."""
        from thegent.sitback.never_idle import NeverIdleLoop

        assert "shadow_cleanup" in NeverIdleLoop.GARDENING_STEPS

    def test_gardening_manager_has_shadow_cleanup_handler(self) -> None:
        """GardeningManager.run_step handles shadow_cleanup step."""
        import asyncio

        from thegent.sitback.gardening import GardeningManager

        manager = GardeningManager()
        result = asyncio.run(manager.run_step("shadow_cleanup"))
        assert isinstance(result, dict)
        assert "success" in result

    def test_gardening_shadow_cleanup_calls_prune(self, tmp_path: Path) -> None:
        """GardeningManager shadow_cleanup step delegates to _prune_stale_shadow_and_logs."""
        import asyncio

        with patch(
            "thegent.orchestration.pruning.prune._prune_stale_shadow_and_logs",
            return_value=(3, 0),
        ) as mock_prune:
            from thegent.sitback.gardening import GardeningManager

            manager = GardeningManager(project_root=tmp_path)
            result = asyncio.run(manager.run_step("shadow_cleanup"))

        assert result["success"] is True
        mock_prune.assert_called_once()
        call_kwargs = mock_prune.call_args
        assert call_kwargs is not None

    def test_shadow_cleanup_result_includes_removed_count(self, tmp_path: Path) -> None:
        """shadow_cleanup step result includes shadow_removed count."""
        import asyncio

        with patch(
            "thegent.orchestration.pruning.prune._prune_stale_shadow_and_logs",
            return_value=(5, 2),
        ):
            from thegent.sitback.gardening import GardeningManager

            manager = GardeningManager(project_root=tmp_path)
            result = asyncio.run(manager.run_step("shadow_cleanup"))

        assert result["success"] is True
        assert result.get("shadow_removed") == 5
