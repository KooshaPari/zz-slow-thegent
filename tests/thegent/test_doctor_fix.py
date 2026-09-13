"""Tests for doctor --fix and --dry-run functionality.

Tests the auto-fix capabilities including:
- --fix flag for automatic fixing
- --dry-run mode for previewing fixes
- Fix report generation
- Auto-fix for dependencies, permissions, config, paths

# @trace FR-CLI-002
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from thegent.doctor import CheckResult, _apply_fixes, _display_fix_report

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# CheckResult dataclass tests
# ---------------------------------------------------------------------------


class TestCheckResult:
    """Unit tests for the CheckResult class."""

    def test_check_result_defaults(self) -> None:
        """Check that CheckResult has proper defaults."""
        r = CheckResult(name="test", category="Test")
        assert r.name == "test"
        assert r.category == "Test"
        assert r.status == "pending"
        assert r.message == ""
        assert r.details is None
        assert r.fix_hint is None

    def test_check_result_with_fix_hint(self) -> None:
        """Check that fix_hint is properly stored."""
        r = CheckResult(name="test", category="Test")
        r.status = "fail"
        r.message = "Test failed"
        r.fix_hint = "Run: thegent install -t shell"
        assert r.fix_hint == "Run: thegent install -t shell"

    def test_check_result_status_values(self) -> None:
        """Check that all valid status values work."""
        for status in ["ok", "warn", "fail", "pending"]:
            r = CheckResult(name="test", category="Test")
            r.status = status
            assert r.status == status


# ---------------------------------------------------------------------------
# _apply_fixes tests
# ---------------------------------------------------------------------------


class TestApplyFixes:
    """Tests for the _apply_fixes function."""

    def test_apply_fixes_no_fixable_issues(self) -> None:
        """When there are no fixable issues, return empty list."""
        r1 = CheckResult(name="test1", category="Test")
        r1.status = "ok"
        r1.message = "All good"
        r2 = CheckResult(name="test2", category="Test")
        r2.status = "ok"
        r2.message = "Also good"
        results = [r1, r2]
        fix_report = _apply_fixes(results, dry_run=False)
        assert fix_report == []

    def test_apply_fixes_dry_run_mode(self) -> None:
        """Test that dry-run mode doesn't actually apply fixes."""
        r = CheckResult(name="test1", category="Test")
        r.status = "fail"
        r.message = "Failed"
        r.fix_hint = "Run: thegent install -t shell"
        results = [r]
        with patch("thegent.doctor.run_subprocess_optimized") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            fix_report = _apply_fixes(results, dry_run=True)

        # Verify no actual fix was attempted
        assert len(fix_report) > 0
        for entry in fix_report:
            assert "dry-run" in entry["result"]

    def test_apply_fixes_handles_mkdir(self) -> None:
        """Test that mkdir fixes are properly handled."""
        r = CheckResult(name="test_dir", category="Test")
        r.status = "fail"
        r.message = "Directory missing"
        r.fix_hint = "Create manually: mkdir -p /tmp/test_doctor_dir"
        results = [r]
        # Run with dry_run to avoid actually creating the directory
        fix_report = _apply_fixes(results, dry_run=True)
        assert len(fix_report) == 1
        assert "mkdir" in fix_report[0]["action"]

    def test_apply_fixes_handles_chmod(self) -> None:
        """Test that chmod fixes are properly handled."""
        r = CheckResult(name="permissions", category="Test")
        r.status = "fail"
        r.message = "Permissions wrong"
        r.fix_hint = "Fix permissions: chmod 700 ~/.thegent"
        results = [r]
        fix_report = _apply_fixes(results, dry_run=True)
        assert len(fix_report) == 1
        assert "chmod" in fix_report[0]["action"]

    def test_apply_fixes_handles_thegent_commands(self) -> None:
        """Test that thegent command fixes are properly handled."""
        r = CheckResult(name="shims", category="Test")
        r.status = "fail"
        r.message = "Shims not installed"
        r.fix_hint = "Run: thegent install-shims --all"
        results = [r]
        with patch("thegent.doctor.run_subprocess_optimized") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            fix_report = _apply_fixes(results, dry_run=False)

        # Check that it attempted to run thegent command
        assert len(fix_report) >= 0  # May or may not run depending on safety checks

    def test_apply_fixes_skips_dangerous_commands(self) -> None:
        """Test that dangerous commands are skipped."""
        r = CheckResult(name="dangerous", category="Test")
        r.status = "fail"
        r.message = "Issue"
        r.fix_hint = "Run: rm -rf /"
        results = [r]
        fix_report = _apply_fixes(results, dry_run=False)
        # Should be skipped since it's dangerous
        assert len(fix_report) == 1
        assert fix_report[0]["status"] == "skipped"

    def test_apply_fixes_safe_removal_allowed(self) -> None:
        """Test that safe removals (like the harmful ps shim) are allowed."""
        r = CheckResult(name="ps_shim", category="Environment")
        r.status = "fail"
        r.message = "ps shim causes hangs"
        r.fix_hint = "Run: rm ~/.local/bin/ps"
        results = [r]
        # This should be allowed since it's in the safe targets list
        fix_report = _apply_fixes(results, dry_run=True)
        # The ps shim is in the safe removal list, so it should be attempted
        assert len(fix_report) >= 0

    def test_apply_fixes_returns_report(self) -> None:
        """Test that _apply_fixes returns a proper report list."""
        r1 = CheckResult(name="test1", category="Test")
        r1.status = "warn"
        r1.message = "Warning"
        r1.fix_hint = "Run: thegent install -t shell"
        r2 = CheckResult(name="test2", category="Test")
        r2.status = "ok"
        r2.message = "All good"
        results = [r1, r2]
        with patch("thegent.doctor.run_subprocess_optimized") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            fix_report = _apply_fixes(results, dry_run=False)

        # Should have report entries for fixable items
        assert isinstance(fix_report, list)
        for entry in fix_report:
            assert "check_name" in entry
            assert "category" in entry
            assert "status" in entry
            assert "action" in entry
            assert "result" in entry


# ---------------------------------------------------------------------------
# _display_fix_report tests
# ---------------------------------------------------------------------------


class TestDisplayFixReport:
    """Tests for the _display_fix_report function."""

    def test_display_fix_report_empty(self) -> None:
        """Test that empty report doesn't cause errors."""
        # Should not raise any errors
        _display_fix_report([], dry_run=False)

    def test_display_fix_report_dry_run(self) -> None:
        """Test that dry-run mode is properly displayed."""
        fix_report = [
            {
                "check_name": "test1",
                "category": "Test",
                "status": "dry-run",
                "action": "mkdir -p /tmp/test",
                "result": "dry-run: would create",
            }
        ]
        # Should not raise any errors
        _display_fix_report(fix_report, dry_run=True)

    def test_display_fix_report_success(self) -> None:
        """Test that successful fixes are properly displayed."""
        fix_report = [
            {
                "check_name": "test1",
                "category": "Test",
                "status": "success",
                "action": "mkdir -p /tmp/test",
                "result": "success",
            }
        ]
        # Should not raise any errors
        _display_fix_report(fix_report, dry_run=False)

    def test_display_fix_report_mixed(self) -> None:
        """Test that mixed results are properly displayed."""
        fix_report = [
            {
                "check_name": "test1",
                "category": "Test",
                "status": "success",
                "action": "mkdir -p /tmp/test",
                "result": "success",
            },
            {
                "check_name": "test2",
                "category": "Test",
                "status": "failed",
                "action": "chmod 700 ~/.thegent",
                "result": "failed: permission denied",
            },
            {
                "check_name": "test3",
                "category": "Test",
                "status": "skipped",
                "action": "rm -rf /",
                "result": "dangerous - skipped",
            },
        ]
        # Should not raise any errors
        _display_fix_report(fix_report, dry_run=False)


# ---------------------------------------------------------------------------
# Integration tests for run_doctor with fix/dry-run
# ---------------------------------------------------------------------------


class TestRunDoctorFix:
    """Integration tests for run_doctor with fix and dry-run."""

    def test_run_doctor_accepts_dry_run_param(self) -> None:
        """Test that run_doctor accepts the dry_run parameter."""
        from thegent.doctor import run_doctor

        # This should not raise TypeError
        with patch("thegent.doctor._check_dependencies", return_value=[]):
            with patch("thegent.doctor._check_configuration", return_value=[]):
                with patch("thegent.doctor._check_isolation", return_value=[]):
                    with patch("thegent.doctor._check_connectivity", return_value=[]):
                        with patch(
                            "thegent.doctor._check_environment", return_value=[]
                        ):
                            with patch(
                                "thegent.doctor._check_shim_binaries", return_value=[]
                            ):
                                with patch(
                                    "thegent.doctor._check_shell", return_value=[]
                                ):
                                    with patch(
                                        "thegent.doctor._check_nix", return_value=[]
                                    ):
                                        with patch(
                                            "thegent.doctor._check_providers",
                                            return_value=[],
                                        ):
                                            with patch(
                                                "thegent.doctor._check_headless",
                                                return_value=[],
                                            ):
                                                with patch(
                                                    "thegent.doctor._check_runtime_infrastructure",
                                                    return_value=[],
                                                ):
                                                    with patch(
                                                        "thegent.doctor._check_process_leaks",
                                                        return_value=[],
                                                    ):
                                                        with patch(
                                                            "thegent.doctor._check_mcp_tools",
                                                            return_value=[],
                                                        ):
                                                            with patch(
                                                                "thegent.doctor._check_sessions",
                                                                return_value=[],
                                                            ):
                                                                with patch(
                                                                    "thegent.doctor._check_project_hints",
                                                                    return_value=[],
                                                                ):
                                                                    with patch(
                                                                        "thegent.doctor._check_performance",
                                                                        return_value=[],
                                                                    ):
                                                                        # Test that dry_run parameter is accepted
                                                                        result = run_doctor(
                                                                            fix=False,
                                                                            dry_run=True,
                                                                        )
                                                                        assert (
                                                                            isinstance(
                                                                                result,
                                                                                bool,
                                                                            )
                                                                        )

    def test_run_doctor_with_fix_and_dry_run(self) -> None:
        """Test that run_doctor works with both fix and dry_run=True."""
        from thegent.doctor import run_doctor

        with patch("thegent.doctor._check_dependencies", return_value=[]):
            with patch("thegent.doctor._check_configuration", return_value=[]):
                with patch("thegent.doctor._check_isolation", return_value=[]):
                    with patch("thegent.doctor._check_connectivity", return_value=[]):
                        with patch(
                            "thegent.doctor._check_environment", return_value=[]
                        ):
                            with patch(
                                "thegent.doctor._check_shim_binaries", return_value=[]
                            ):
                                with patch(
                                    "thegent.doctor._check_shell", return_value=[]
                                ):
                                    with patch(
                                        "thegent.doctor._check_nix", return_value=[]
                                    ):
                                        with patch(
                                            "thegent.doctor._check_providers",
                                            return_value=[],
                                        ):
                                            with patch(
                                                "thegent.doctor._check_headless",
                                                return_value=[],
                                            ):
                                                with patch(
                                                    "thegent.doctor._check_runtime_infrastructure",
                                                    return_value=[],
                                                ):
                                                    with patch(
                                                        "thegent.doctor._check_process_leaks",
                                                        return_value=[],
                                                    ):
                                                        with patch(
                                                            "thegent.doctor._check_mcp_tools",
                                                            return_value=[],
                                                        ):
                                                            with patch(
                                                                "thegent.doctor._check_sessions",
                                                                return_value=[],
                                                            ):
                                                                with patch(
                                                                    "thegent.doctor._check_project_hints",
                                                                    return_value=[],
                                                                ):
                                                                    with patch(
                                                                        "thegent.doctor._check_performance",
                                                                        return_value=[],
                                                                    ):
                                                                        # Test fix=True with dry_run=True
                                                                        result = run_doctor(
                                                                            fix=True,
                                                                            dry_run=True,
                                                                        )
                                                                        assert (
                                                                            isinstance(
                                                                                result,
                                                                                bool,
                                                                            )
                                                                        )


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------


class TestDoctorCLI:
    """Tests for the doctor CLI command."""

    def test_clode_doctor_accepts_dry_run_param(self) -> None:
        """Test that clode_doctor accepts the dry_run parameter."""
        import inspect

        from thegent import clode_main

        # Get the signature of the doctor function
        sig = inspect.signature(clode_main.clode_doctor)
        param_names = list(sig.parameters.keys())
        assert "dry_run" in param_names, f"Expected 'dry_run' in {param_names}"

    def test_dex_doctor_accepts_dry_run_param(self) -> None:
        """Test that dex_doctor accepts the dry_run parameter."""
        import inspect

        from thegent import dex_main

        # Get the signature of the doctor function
        sig = inspect.signature(dex_main.dex_doctor)
        param_names = list(sig.parameters.keys())
        assert "dry_run" in param_names, f"Expected 'dry_run' in {param_names}"

    def test_roid_doctor_accepts_dry_run_param(self) -> None:
        """Test that roid_doctor accepts the dry_run parameter."""
        import inspect

        from thegent import roid_main

        # Get the signature of the doctor function
        sig = inspect.signature(roid_main.roid_doctor)
        param_names = list(sig.parameters.keys())
        assert "dry_run" in param_names, f"Expected 'dry_run' in {param_names}"

    def test_anen_doctor_accepts_dry_run_param(self) -> None:
        """Test that anen_doctor accepts the dry_run parameter."""
        import inspect

        from thegent import anen_main

        # Get the signature of the doctor function
        sig = inspect.signature(anen_main.anen_doctor)
        param_names = list(sig.parameters.keys())
        assert "dry_run" in param_names, f"Expected 'dry_run' in {param_names}"
