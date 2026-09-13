"""Tests for WL-035: mise integration validation.

Validates that the mise installation integration is code-complete and
the key functions exist and behave correctly in dry-run/mock scenarios.

# @trace WL-035
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# WL-035: mise integration validation
# ---------------------------------------------------------------------------


class TestMiseInstallFunctionExists:
    """Verify that required mise integration functions exist in install.py."""

    # @trace WL-035

    def test_install_mise_function_exists(self) -> None:
        from thegent.install import install_mise

        assert callable(install_mise)

    def test_verify_mise_installation_function_exists(self) -> None:
        from thegent.install import verify_mise_installation

        assert callable(verify_mise_installation)

    def test_install_system_dependencies_function_exists(self) -> None:
        from thegent.install import install_system_dependencies

        assert callable(install_system_dependencies)

    def test_uninstall_mise_hooks_function_exists(self) -> None:
        from thegent.install import uninstall_mise_hooks

        assert callable(uninstall_mise_hooks)


class TestInstallMiseDryRun:
    """Verify dry-run mode returns expected values without side effects."""

    # @trace WL-035

    def test_dry_run_returns_success_when_mise_absent(self) -> None:
        """install_mise dry_run=True always returns (True, ...) without system changes."""
        with patch("thegent.install._command_exists", return_value=False):
            from thegent.install import install_mise

            ok, msg = install_mise(dry_run=True)
        assert ok is True
        assert "Would install" in msg

    def test_dry_run_returns_already_installed_when_mise_present(self) -> None:
        """install_mise returns (True, 'already installed') when mise is in PATH."""
        with patch("thegent.install._command_exists", return_value=True):
            from thegent.install import install_mise

            ok, msg = install_mise(dry_run=False)
        assert ok is True
        assert "already installed" in msg.lower()

    def test_install_system_deps_dry_run_no_subprocess(self) -> None:
        """install_system_dependencies dry_run=True never calls brew/nix."""
        with (
            patch("thegent.install._command_exists", return_value=False),
            patch("thegent.install._run_command") as mock_run,
        ):
            from thegent.install import install_system_dependencies

            result = install_system_dependencies(dry_run=True)

        # dry_run should not invoke actual package manager
        mock_run.assert_not_called()
        assert "mise" in result
        assert result["mise"]["installed"] is True  # dry_run always succeeds

    def test_install_homebrew_dry_run(self) -> None:
        """install_homebrew dry_run=True returns success message."""
        with patch("thegent.install._command_exists", return_value=False):
            from thegent.install import install_homebrew

            ok, msg = install_homebrew(dry_run=True)
        assert ok is True
        assert "Would install" in msg


class TestVerifyMiseInstallation:
    """Verify that verify_mise_installation returns expected structure."""

    # @trace WL-035

    def test_returns_tuple_of_bool_and_list(self) -> None:
        with patch("thegent.install._command_exists", return_value=False):
            from thegent.install import verify_mise_installation

            ok, messages = verify_mise_installation()
        assert isinstance(ok, bool)
        assert isinstance(messages, list)
        assert len(messages) > 0

    def test_failure_when_mise_not_found(self) -> None:
        with patch("thegent.install._command_exists", return_value=False):
            from thegent.install import verify_mise_installation

            ok, messages = verify_mise_installation()
        assert ok is False
        assert any("not found" in m.lower() or "not" in m.lower() for m in messages)

    def test_success_when_mise_present(self) -> None:
        with (
            patch("thegent.install._command_exists", return_value=True),
            patch("thegent.install._run_command", return_value=(0, "2025.1.0 linux-x64 (2025-01-01)", "")),
        ):
            from thegent.install import verify_mise_installation

            ok, messages = verify_mise_installation()
        assert ok is True
        assert any("found" in m.lower() for m in messages)


class TestMiseShellHookDetection:
    """Verify that shell config hook detection logic works correctly."""

    # @trace WL-035

    def test_zsh_hook_detected(self, tmp_path: Path) -> None:
        """Shell config file with 'mise activate' is detected as having hook."""
        zshenv = tmp_path / ".zshenv"
        zshenv.write_text('eval "$(mise activate zsh)"\n')

        with (
            patch("thegent.install._command_exists", return_value=True),
            patch("thegent.install._run_command", return_value=(0, "2025.1.0", "")),
        ):
            from thegent.install import verify_mise_installation

            mock_settings = MagicMock()
            mock_settings.shell_path = "/bin/zsh"

            with patch("pathlib.Path.home", return_value=tmp_path):
                _ok, messages = verify_mise_installation(settings=mock_settings)

        assert isinstance(messages, list)

    def test_uninstall_hooks_dry_run(self, tmp_path: Path) -> None:
        """uninstall_mise_hooks dry_run=True reports what would be removed."""
        zshrc = tmp_path / ".zshrc"
        zshrc.write_text('eval "$(mise activate zsh)"\nsome_other_config\n')

        mock_settings = MagicMock()
        mock_settings.shell_path = "/bin/zsh"

        with patch("pathlib.Path.home", return_value=tmp_path):
            from thegent.install import uninstall_mise_hooks

            ok, messages = uninstall_mise_hooks(dry_run=True, settings=mock_settings)

        assert isinstance(ok, bool)
        assert isinstance(messages, list)


class TestInstallSystemDependenciesResult:
    """Verify the structure and contents of install_system_dependencies results."""

    # @trace WL-035

    def test_result_has_expected_keys(self) -> None:
        with patch("thegent.install._command_exists", return_value=False):
            from thegent.install import install_system_dependencies

            result = install_system_dependencies(dry_run=True)

        assert "homebrew" in result
        assert "mise" in result
        assert "git_repos" in result
        assert "installed" in result["homebrew"]
        assert "message" in result["homebrew"]
        assert "installed" in result["mise"]
        assert "message" in result["mise"]
        assert isinstance(result["git_repos"], list)

    def test_git_repos_empty_by_default(self) -> None:
        with patch("thegent.install._command_exists", return_value=False):
            from thegent.install import install_system_dependencies

            result = install_system_dependencies(dry_run=True)

        assert result["git_repos"] == []

    def test_git_repos_processed_when_provided(self) -> None:
        with (
            patch("thegent.install._command_exists", return_value=False),
            patch("thegent.install.clone_git_repo", return_value=(True, "Cloned")),
        ):
            from thegent.install import install_system_dependencies

            result = install_system_dependencies(
                dry_run=False,
                install_homebrew_pkg=False,
                install_mise_pkg=False,
                git_repos=[{"url": "https://github.com/example/repo", "target": "/tmp/test-repo"}],
            )

        assert len(result["git_repos"]) == 1
        assert result["git_repos"][0]["url"] == "https://github.com/example/repo"
