"""Tests for WL-040 WBS Phase 4 UX — CLI Polish and Intuitive Design.

Covers:
  WP-4001  Actionable error messages (format_error)
  WP-4002  --json output format for CLI commands
  WP-4003  Shell completions wired in (add_completion=True verified)
  WP-4004  thegent help <command> inline examples
  WP-4005  Progress spinners (smoke test that _apply_fixes has spinner import)
  WP-4006  thegent doctor proactive fix improvements (DoctorRunner new checks)

# @trace WL-040 WP-4001 WP-4002 WP-4003 WP-4004 WP-4005 WP-4006
"""

from __future__ import annotations

import os
import sys
from datetime import UTC
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson as json

# ---------------------------------------------------------------------------
# WP-4001: Actionable Error Messages
# ---------------------------------------------------------------------------


class TestFormatError:
    """Tests for thegent.infra.enhanced_errors.format_error.

    # @trace WL-040 WP-4001
    """

    def test_file_not_found_error(self) -> None:
        from thegent.infra.enhanced_errors import format_error

        exc = FileNotFoundError(2, "No such file or directory", "/tmp/missing.yaml")
        result = format_error(exc)
        assert "/tmp/missing.yaml" in result
        assert "doctor --fix" in result

    def test_file_not_found_without_filename(self) -> None:
        from thegent.infra.enhanced_errors import format_error

        exc = FileNotFoundError("missing file")
        result = format_error(exc)
        assert "File not found" in result
        assert "doctor --fix" in result

    def test_permission_error(self) -> None:
        from thegent.infra.enhanced_errors import format_error

        exc = PermissionError(13, "Permission denied", "/etc/shadow")
        result = format_error(exc)
        assert "/etc/shadow" in result
        assert "Permission denied" in result

    def test_connection_error(self) -> None:
        from thegent.infra.enhanced_errors import format_error

        exc = ConnectionError("Connection refused to localhost:3847")
        result = format_error(exc)
        assert "Cannot connect" in result
        assert "thegent status" in result

    def test_key_error_with_key(self) -> None:
        from thegent.infra.enhanced_errors import format_error

        exc = KeyError("api_key")
        result = format_error(exc)
        assert "api_key" in result
        assert "config wizard" in result

    def test_key_error_without_args(self) -> None:
        from thegent.infra.enhanced_errors import format_error

        # Construct KeyError manually without args to hit the fallback branch
        exc = KeyError()
        exc.args = ()
        result = format_error(exc)
        assert "Missing config key" in result

    def test_generic_exception_returns_str(self) -> None:
        from thegent.infra.enhanced_errors import format_error

        exc = ValueError("something unexpected")
        result = format_error(exc)
        assert result == "something unexpected"

    def test_format_error_exported_from_infra(self) -> None:
        from thegent.infra import format_error  # noqa: F401 — just checks import

        assert callable(format_error)


# ---------------------------------------------------------------------------
# WP-4002: --json Output for CLI Commands
# ---------------------------------------------------------------------------


class TestJsonOutputRegistryList:
    """Tests for registry_list --format json.

    # @trace WL-040 WP-4002
    """

    def _make_persona_record(self, name: str, project: str, caps: list[str]) -> MagicMock:
        from datetime import datetime

        rec = MagicMock()
        rec.name = name
        rec.project_root = Path(project)
        rec.capabilities = caps

        rec.last_seen = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
        return rec

    def test_json_format_empty_registry(self, capsys) -> None:
        from thegent.commands.registry import registry_list

        mock_reg = MagicMock()
        mock_reg.get_all.return_value = []
        with patch("thegent.commands.registry._load_registry", return_value=mock_reg):
            registry_list(format="json")

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data == []

    def test_json_format_with_records(self, capsys) -> None:
        from thegent.commands.registry import registry_list

        records = [
            self._make_persona_record("alice", "/projects/alpha", ["code-review"]),
            self._make_persona_record("bob", "/projects/beta", ["testing", "docs"]),
        ]
        mock_reg = MagicMock()
        mock_reg.get_all.return_value = records
        with patch("thegent.commands.registry._load_registry", return_value=mock_reg):
            registry_list(format="json")

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 2
        names = {r["name"] for r in data}
        assert names == {"alice", "bob"}
        # Verify structure
        for row in data:
            assert "name" in row
            assert "project" in row
            assert "capabilities" in row
            assert "last_seen" in row

    def test_rich_format_does_not_emit_json(self, capsys) -> None:
        """Rich output should not produce parseable JSON on stdout."""
        from thegent.commands.registry import registry_list

        mock_reg = MagicMock()
        mock_reg.get_all.return_value = []
        with patch("thegent.commands.registry._load_registry", return_value=mock_reg):
            registry_list(format="rich")
        captured = capsys.readouterr()
        # Should NOT be JSON array
        assert not captured.out.startswith("[")


class TestJsonOutputProjectList:
    """Tests for project_list_cmd --format json.

    # @trace WL-040 WP-4002
    """

    def test_json_no_projects_file(self, capsys, tmp_path) -> None:
        from thegent.cli.commands.cli import project_list_cmd

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        with patch("thegent.cli.commands.cli.ThegentSettings", return_value=mock_settings):
            project_list_cmd(format="json")

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data == []

    def test_json_with_projects(self, capsys, tmp_path) -> None:
        from thegent.cli.commands.cli import project_list_cmd

        projects_file = tmp_path / "projects.jsonl"
        projects_file.write_text(
            '{"name": "alpha", "path": "/projects/alpha"}\n{"name": "beta", "path": "/projects/beta"}\n',
            encoding="utf-8",
        )
        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        with patch("thegent.cli.commands.cli.ThegentSettings", return_value=mock_settings):
            project_list_cmd(format="json")

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 2
        names = {r["name"] for r in data}
        assert names == {"alpha", "beta"}


# ---------------------------------------------------------------------------
# WP-4003: Shell Completions
# ---------------------------------------------------------------------------


class TestShellCompletions:
    """Verify that the main typer app has add_completion=True.

    # @trace WL-040 WP-4003
    """

    def test_main_app_has_completion_enabled(self) -> None:
        from typer.main import get_command

        from thegent.cli.apps.main import app

        click_cmd = get_command(app)
        # When add_completion=True typer injects --install-completion and
        # --show-completion into the resulting Click command's params.
        param_names = {p.name for p in click_cmd.params}
        assert "install_completion" in param_names, (
            "Main app must expose --install-completion (typer add_completion=True). "
            f"Found params: {sorted(param_names)}"
        )

    def test_install_completions_script_exists(self) -> None:
        script = Path(__file__).parent.parent / "scripts" / "install_completions.sh"
        assert script.exists(), "scripts/install_completions.sh must exist (WP-4003)"
        content = script.read_text(encoding="utf-8")
        assert "thegent --install-completion" in content


# ---------------------------------------------------------------------------
# WP-4004: Inline Help Examples
# ---------------------------------------------------------------------------


class TestHelpExamples:
    """Tests for thegent.cli.help_examples.

    # @trace WL-040 WP-4004
    """

    def test_command_examples_dict_populated(self) -> None:
        from thegent.cli.help_examples import COMMAND_EXAMPLES

        assert isinstance(COMMAND_EXAMPLES, dict)
        required_keys = {
            "free",
            "run",
            "plan",
            "registry",
            "status",
            "doctor",
            "govern",
            "mcp",
        }
        for key in required_keys:
            assert key in COMMAND_EXAMPLES, f"Missing examples for command: {key}"
            examples = COMMAND_EXAMPLES[key]
            assert isinstance(examples, list)
            assert len(examples) >= 1, f"At least one example required for: {key}"

    def test_show_help_examples_known_command(self, capsys) -> None:
        from thegent.cli.help_examples import show_help_examples

        show_help_examples("run")
        captured = capsys.readouterr()
        assert "thegent run" in captured.out

    def test_show_help_examples_unknown_command(self, capsys) -> None:
        from thegent.cli.help_examples import show_help_examples

        show_help_examples("nonexistent_command_xyz")
        captured = capsys.readouterr()
        assert "No examples found" in captured.out or "Available" in captured.out

    def test_show_help_examples_case_insensitive(self, capsys) -> None:
        from thegent.cli.help_examples import show_help_examples

        show_help_examples("RUN")
        captured = capsys.readouterr()
        assert "thegent run" in captured.out

    def test_help_cmd_registered_in_app(self) -> None:
        from thegent.cli.apps.main import app

        cmd_names = [cmd.name for cmd in app.registered_commands]
        assert "help" in cmd_names, "help command must be registered on the main typer app"

    def test_main_app_supports_version_option(self) -> None:
        from typer.testing import CliRunner

        from thegent import __version__
        from thegent.cli.apps.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout


# ---------------------------------------------------------------------------
# WP-4005: Progress Spinners
# ---------------------------------------------------------------------------


class TestProgressSpinners:
    """Smoke tests verifying spinner support in long-running doctor operations.

    # @trace WL-040 WP-4005
    """

    def test_run_doctor_uses_progress_import(self) -> None:
        """Verify that doctor.py imports Progress for spinner support."""
        import inspect

        import thegent.doctor as doctor_mod

        src = inspect.getsource(doctor_mod.run_doctor)
        assert "Progress" in src or "SpinnerColumn" in src, (
            "run_doctor must use rich Progress for spinner feedback (WP-4005)"
        )

    def test_apply_fixes_has_spinner_import_reference(self) -> None:
        """Verify that _apply_fixes references rich.progress.Progress."""
        import inspect

        import thegent.doctor as doctor_mod

        src = inspect.getsource(doctor_mod._apply_fixes)
        assert "Progress" in src, "_apply_fixes must reference rich Progress for spinner feedback (WP-4005)"

    def test_spinner_context_available(self) -> None:
        """Verify that spinner_context exists in infra.progress."""
        from thegent.infra import spinner_context  # noqa: F401

        assert callable(spinner_context)


# ---------------------------------------------------------------------------
# WP-4006: thegent doctor proactive fix improvements
# ---------------------------------------------------------------------------


class TestDoctorRunnerChecks:
    """Tests for new DoctorRunner checks added in WP-4006.

    # @trace WL-040 WP-4006
    """

    def _runner(self):
        from thegent.commands.doctor import DoctorRunner

        return DoctorRunner()

    # --- Python version check ---

    def test_python_version_ok_current_interpreter(self) -> None:
        runner = self._runner()
        check = runner._check_python_version()
        # The test suite must be run on Python 3.11+, so we expect ok
        major, minor = sys.version_info[:2]
        if major > 3 or (major == 3 and minor >= 11):
            assert check.status == "ok"
        else:
            assert check.status == "warn"

    def test_python_version_fail_for_old_version(self) -> None:
        runner = self._runner()
        with patch("sys.version_info", (3, 10, 0)):
            check = runner._check_python_version()
        assert check.status == "warn"
        assert "3.10" in check.message

    # --- ~/.thegent/ writable ---

    def test_thegent_dir_writable_ok_when_dir_writable(self, tmp_path) -> None:
        runner = self._runner()
        with patch("pathlib.Path.home", return_value=tmp_path):
            thegent_dir = tmp_path / ".thegent"
            thegent_dir.mkdir()
            check = runner._check_thegent_dir_writable()
        assert check.status == "ok"

    def test_thegent_dir_writable_ok_when_not_exists(self, tmp_path) -> None:
        """When the dir doesn't exist, the check reports ok (other check handles creation)."""
        runner = self._runner()
        with patch("pathlib.Path.home", return_value=tmp_path):
            check = runner._check_thegent_dir_writable()
        assert check.status == "ok"

    def test_thegent_dir_not_writable(self, tmp_path) -> None:
        runner = self._runner()
        thegent_dir = tmp_path / ".thegent"
        thegent_dir.mkdir()
        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch("os.access", return_value=False):
                check = runner._check_thegent_dir_writable()
        assert check.status == "error"
        assert check.fixable is True

    # --- config.yaml YAML validity ---

    def test_config_yaml_not_present(self, tmp_path) -> None:
        runner = self._runner()
        with patch("pathlib.Path.home", return_value=tmp_path):
            (tmp_path / ".thegent").mkdir()
            check = runner._check_config_yaml()
        assert check.status == "ok"
        assert "not present" in check.message

    def test_config_yaml_valid(self, tmp_path) -> None:
        runner = self._runner()
        thegent_dir = tmp_path / ".thegent"
        thegent_dir.mkdir()
        (thegent_dir / "config.yaml").write_text("key: value\n", encoding="utf-8")
        with patch("pathlib.Path.home", return_value=tmp_path):
            check = runner._check_config_yaml()
        assert check.status == "ok"

    def test_config_yaml_invalid(self, tmp_path) -> None:
        runner = self._runner()
        thegent_dir = tmp_path / ".thegent"
        thegent_dir.mkdir()
        # Write invalid YAML (unbalanced brace)
        (thegent_dir / "config.yaml").write_text("key: {bad yaml: [unclosed\n", encoding="utf-8")
        with patch("pathlib.Path.home", return_value=tmp_path):
            check = runner._check_config_yaml()
        assert check.status == "error"
        assert "invalid YAML" in check.message or "YAML" in check.message

    # --- shadow dirs count ---

    def test_shadow_dirs_count_ok(self, tmp_path) -> None:
        runner = self._runner()
        # Create 3 shadow dirs — well under threshold
        for i in range(3):
            (tmp_path / f".shadow-test{i}").mkdir()
        with patch("pathlib.Path.cwd", return_value=tmp_path / "project"):
            (tmp_path / "project").mkdir(exist_ok=True)
            check = runner._check_shadow_dirs_count()
        assert check.status == "ok"

    def test_shadow_dirs_count_warn_over_threshold(self, tmp_path) -> None:
        runner = self._runner()
        # Create 55 shadow dirs
        parent = tmp_path
        for i in range(55):
            (parent / f".shadow-testdir{i:03d}").mkdir()
        # Make cwd a subdir of parent so parent is cwd.parent
        cwd = parent / "subproject"
        cwd.mkdir()
        with patch("pathlib.Path.cwd", return_value=cwd):
            with patch.dict(os.environ, {"THGENT_SHADOW_COUNT_WARN": "50"}):
                check = runner._check_shadow_dirs_count()
        assert check.status == "warn"
        assert "55" in check.message
        assert "prune" in check.message.lower()

    # --- run_checks includes new checks ---

    def test_run_checks_returns_expected_check_names(self) -> None:
        runner = self._runner()
        # Patch out side-effects — the DoctorCheck.name must match what we assert
        with (
            patch.object(runner, "_check_python_version", return_value=_ok("python_version")),
            patch.object(
                runner,
                "_check_anthropic_api_key",
                return_value=_ok("anthropic_api_key"),
            ),
            patch.object(runner, "_check_thegent_dir", return_value=_ok("thegent_home_dir")),
            patch.object(
                runner,
                "_check_thegent_dir_writable",
                return_value=_ok("thegent_dir_writable"),
            ),
            patch.object(runner, "_check_thegent_sessions_dir", return_value=_ok("sessions")),
            patch.object(runner, "_check_pyproject_toml", return_value=_ok("pyproject")),
            patch.object(runner, "_check_config_yaml", return_value=_ok("config_yaml")),
            patch.object(runner, "_check_ruff", return_value=_ok("ruff")),
            patch.object(runner, "_check_cargo", return_value=_ok("cargo")),
            patch.object(runner, "_check_mcp_config_dir", return_value=_ok("mcp_config")),
            patch.object(runner, "_check_stale_shadow_dirs", return_value=_ok("stale")),
            patch.object(
                runner,
                "_check_shadow_dirs_count",
                return_value=_ok("shadow_dirs_count"),
            ),
        ):
            checks = runner.run_checks()

        names = {c.name for c in checks}
        assert "thegent_dir_writable" in names
        assert "config_yaml" in names
        assert "shadow_dirs_count" in names


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ok(name: str):
    from thegent.commands.doctor import DoctorCheck

    return DoctorCheck(name=name, status="ok", message=f"{name} ok")
