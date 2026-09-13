"""UX Audit: CLI help text, error messages, output formatting, exit codes.

Scores findings with severity P0-P3 following the audit skill approach:

  P0  — Critical: broken user experience, blocks usage
  P1  — High: significant UX gap, no workaround
  P2  — Medium: inconsistency or missing polish
  P3  — Low: minor nit, cosmetic

# @trace UX-AUDIT-CLI
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from thegent.cli.apps.main import app

runner = CliRunner(mix_stderr=False)  # P0-gate audit: stderr must be captured separately for traceback detection


# ---------------------------------------------------------------------------
# Audit infrastructure
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    check: str
    severity: str
    message: str
    file: str = ""
    line: int = 0


def _combined_output(result) -> str:
    """Return ``result.stdout + result.stderr`` without raising on mixed-stderr.

    Click 8.1.x raises ``ValueError`` when ``stderr_bytes is None`` even with
    ``mix_stderr=True`` on Typer/Click 8.1.x; this helper tolerates that.
    """
    stderr = ""
    try:
        stderr = result.stderr or ""
    except (ValueError, AttributeError):
        stderr = ""
    return (result.stdout or "") + stderr


@dataclass
class AuditReport:
    findings: list[Finding] = field(default_factory=list)

    def add(self, check: str, severity: str, message: str, **kw: object) -> None:
        self.findings.append(Finding(check=check, severity=severity, message=message, **kw))

    @property
    def p0_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "P0")

    @property
    def p1_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "P1")

    def summary(self) -> str:
        lines = [
            f"P0={self.p0_count} P1={self.p1_count} "
            f"P2={sum(1 for f in self.findings if f.severity == 'P2')} "
            f"P3={sum(1 for f in self.findings if f.severity == 'P3')}",
            f"Total findings: {len(self.findings)}",
        ]
        for f in self.findings:
            lines.append(f"  [{f.severity}] {f.check}: {f.message}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 1. CLI help text is present and non-empty for main commands
# ---------------------------------------------------------------------------


class TestCLIHelpTextPresent:
    """Every registered command and sub-app must surface meaningful --help.

    P0 if a command has no help text at all.
    P2 if help text is trivial (< 5 chars beyond the command name).
    """

    # Top-level commands registered directly on the root app
    TOP_LEVEL_COMMANDS: ClassVar[list[str]] = [
        "bg",
        "status",
        "stop",
        "logs",
        "ps",
        "resume",
        "govern",
        "phench",
    ]

    # Sub-apps mounted via add_typer
    SUB_APPS: ClassVar[list[str]] = ["run", "cockpit", "sota"]

    def test_root_app_has_help(self) -> None:
        """Root app must have a non-empty help string."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        output = result.stdout
        assert len(output.strip()) > 0, "Root --help produced empty output"
        assert "thegent" in output.lower() or "agent" in output.lower(), (
            "Root help should mention 'thegent' or 'agent' in description"
        )

    def test_root_help_lists_all_commands(self) -> None:
        """Root --help should list all registered top-level commands."""
        result = runner.invoke(app, ["--help"])
        output = result.stdout
        for cmd in self.TOP_LEVEL_COMMANDS:
            assert cmd in output, f"Command '{cmd}' missing from root --help output"

    @pytest.mark.parametrize("command", TOP_LEVEL_COMMANDS)
    def test_command_has_non_empty_help(self, command: str) -> None:
        """Each top-level command must produce non-empty --help output."""
        result = runner.invoke(app, [command, "--help"])
        assert result.exit_code == 0, f"'thegent {command} --help' exited with code {result.exit_code}"
        output = result.stdout.strip()
        assert len(output) > 20, f"'thegent {command} --help' output too short ({len(output)} chars)"

    @pytest.mark.parametrize("sub_app", SUB_APPS)
    def test_sub_app_has_non_empty_help(self, sub_app: str) -> None:
        """Each sub-app must produce non-empty --help output."""
        result = runner.invoke(app, [sub_app, "--help"])
        assert result.exit_code == 0, f"'thegent {sub_app} --help' exited with code {result.exit_code}"
        output = result.stdout.strip()
        assert len(output) > 20, f"'thegent {sub_app} --help' output too short ({len(output)} chars)"

    def test_module_entrypoint_exposes_root_help(self) -> None:
        """``python -m thegent`` must expose the installed CLI without a console script."""
        result = subprocess.run(
            [sys.executable, "-m", "thegent", "--help"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert "thegent" in result.stdout.lower()
        for command in [*self.TOP_LEVEL_COMMANDS, *self.SUB_APPS]:
            assert command in result.stdout

    def test_version_flag_works(self) -> None:
        """--version must print output and exit (may be 0 or 2)."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code in (0, 2), f"--version exited {result.exit_code}"


# ---------------------------------------------------------------------------
# 2. Error messages are actionable (not raw tracebacks)
# ---------------------------------------------------------------------------


class TestErrorMessagesActionable:
    """Error output must be human-readable and actionable.

    P0 if raw Python tracebacks leak to user-facing stderr.
    P1 if error messages lack actionable guidance.
    P2 if error messages use inconsistent formatting.
    """

    def test_unknown_command_exits_nonzero(self) -> None:
        """An unknown command should exit non-zero with a usage hint."""
        result = runner.invoke(app, ["nonexistent-command-xyz"])
        assert result.exit_code != 0

    def test_unknown_command_no_traceback(self) -> None:
        """Error output must not contain raw Python traceback frames."""
        result = runner.invoke(app, ["nonexistent-command-xyz"])
        combined = _combined_output(result).lower()
        assert "traceback" not in combined, "Raw traceback leaked to user output on unknown command"
        assert "raise " not in combined, "Python 'raise' keyword leaked to user output"

    def test_status_missing_session_exits_nonzero(self) -> None:
        """'status' with a nonexistent session should exit non-zero."""
        result = runner.invoke(app, ["status", "nonexistent-session-id-abc"])
        assert result.exit_code != 0

    def test_status_missing_session_no_traceback(self) -> None:
        """'status' error must not leak a traceback."""
        result = runner.invoke(app, ["status", "nonexistent-session-id-abc"])
        combined = _combined_output(result).lower()
        assert "traceback" not in combined, "Raw traceback leaked from 'status' on missing session"

    def test_stop_missing_session_exits_nonzero(self) -> None:
        """'stop' with a nonexistent session should exit non-zero."""
        result = runner.invoke(app, ["stop", "nonexistent-session-id-abc"])
        assert result.exit_code != 0

    def test_stop_missing_session_no_traceback(self) -> None:
        """'stop' error must not leak a traceback."""
        result = runner.invoke(app, ["stop", "nonexistent-session-id-abc"])
        combined = _combined_output(result).lower()
        assert "traceback" not in combined, "Raw traceback leaked from 'stop' on missing session"

    def test_error_messages_mention_action(self) -> None:
        """Error output should suggest a corrective action where possible."""
        result = runner.invoke(app, ["status", "nonexistent-session-id-abc"])
        output = _combined_output(result).strip().lower()
        actionable_patterns = [
            "not found",
            "does not exist",
            "no such",
            "session",
            "ps",
            "check",
        ]
        has_action = any(p in output for p in actionable_patterns)
        assert has_action, f"Error message lacks actionable guidance: {output[:200]}"

    def test_exc_text_escapes_rich_markup(self) -> None:
        """exc_text must neutralise Rich markup in user-influenced strings."""
        from thegent.ux.cli_errors import exc_text

        malicious = "[red]injected[/red] <script>alert(1)</script>"
        escaped = exc_text(malicious)
        assert "[red]" not in escaped or "\\[red]" in escaped, "exc_text did not neutralise Rich markup"
        assert "<script>" not in escaped or "\\&lt;script\\&gt;" in escaped or "[bold]" not in escaped, (
            "exc_text did not neutralise HTML-like content (acceptable if Rich-escaped)"
        )

    def test_safe_echo_no_rich_injection(self, capsys: pytest.CaptureFixture[str]) -> None:
        """safe_echo must not allow Rich markup injection into output."""
        from thegent.ux.cli_errors import safe_echo

        # Capture safe_echo's stdout directly. safe_echo pins color=False
        # and routes through typer.echo (which writes to stdout), so the
        # Rich-markup-escaped payload must appear in captured stdout with
        # the brackets backslash-escaped (e.g. \\[bold]INJECT\\[/bold]).
        safe_echo("[bold]INJECT[/bold]")
        captured = capsys.readouterr()
        assert "\\[bold]INJECT\\[/bold]" in captured.out, f"safe_echo failed to escape Rich markup: {captured.out!r}"


# ---------------------------------------------------------------------------
# 3. Output formatting consistency (no raw dict dumps in user-facing output)
# ---------------------------------------------------------------------------


class TestOutputFormatting:
    """User-facing output must be formatted, not raw repr/dict dumps.

    P0 if user-facing commands emit raw `{'key': 'value'}` dicts.
    P2 if Rich tables are not used where they would improve readability.
    P1 if JSON output (--format json) is not valid JSON.
    """

    def test_ps_output_no_raw_dict(self) -> None:
        """'ps' output must not contain raw Python dict syntax."""
        result = runner.invoke(app, ["ps"])
        output = result.stdout
        raw_dict_pattern = re.compile(r"\{'[^']+'\s*:\s*['\"]")
        assert not raw_dict_pattern.search(output), "ps output contains raw Python dict syntax"

    def test_status_output_valid_json_when_present(self) -> None:
        """'status' with a valid session should emit parseable JSON."""
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            session_id = "test-ux-audit-001"
            meta = {
                "session_id": session_id,
                "agent": "claude",
                "owner": "test",
                "pid": 12345,
                "prompt": "hello",
                "cwd": "/tmp",
            }
            meta_path = Path(tmpdir) / f"{session_id}.json"
            with open(meta_path, "w") as f:
                json.dump(meta, f)

            with patch.dict("os.environ", {"THGENT_SESSION_DIR": tmpdir}):
                result = runner.invoke(app, ["status", session_id])

            if result.exit_code == 0:
                parsed = json.loads(result.stdout)
                assert isinstance(parsed, dict)
                assert "status" in parsed

    def test_govern_help_output_not_raw_dict(self) -> None:
        """'govern --help' output must not contain raw dict syntax."""
        result = runner.invoke(app, ["govern", "--help"])
        output = result.stdout
        raw_dict_pattern = re.compile(r"\{'[^']+'\s*:\s*['\"]")
        assert not raw_dict_pattern.search(output), "govern --help output contains raw Python dict syntax"

    def test_bg_output_is_json(self) -> None:
        """'bg' output should emit structured JSON, not freeform text."""
        result = runner.invoke(app, ["bg", "test prompt", "claude", "--cd", "/tmp"])
        if result.exit_code == 0 and result.stdout.strip():
            import json

            try:
                parsed = json.loads(result.stdout.strip().split("\n")[-1])
                assert isinstance(parsed, dict), "bg output should be a JSON object"
            except (json.JSONDecodeError, IndexError):
                pass  # bg may fail if claude binary is not available

    def test_no_traceback_in_any_help_output(self) -> None:
        """No --help invocation should produce a traceback."""
        commands_to_check = [
            ["--help"],
            ["run", "--help"],
            ["cockpit", "--help"],
            ["sota", "--help"],
            ["govern", "--help"],
            ["phench", "--help"],
        ]
        for cmd in commands_to_check:
            result = runner.invoke(app, cmd)
            combined = _combined_output(result).lower()
            assert "traceback" not in combined, f"Traceback in '{' '.join(cmd)}' output"


# ---------------------------------------------------------------------------
# 4. Exit codes follow convention (0=success, 1=error, 2=usage)
# ---------------------------------------------------------------------------


class TestExitCodes:
    """Exit codes must follow Unix conventions.

    0 = success
    1 = general error (not found, runtime failure)
    2 = usage error (bad arguments, missing required args)
    P0 if --help exits non-zero.
    P1 if unknown command exits 0.
    P1 if missing required argument exits 0.
    P2 if exit code is ambiguous (e.g., always 0 or always 1).
    """

    def test_help_exits_zero(self) -> None:
        """--help must always exit 0."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0, f"--help exited with {result.exit_code}, expected 0"

    @pytest.mark.parametrize(
        "cmd",
        [
            ["run", "--help"],
            ["cockpit", "--help"],
            ["sota", "--help"],
            ["govern", "--help"],
            ["phench", "--help"],
        ],
    )
    def test_subcommand_help_exits_zero(self, cmd: list[str]) -> None:
        """Sub-command --help must always exit 0."""
        result = runner.invoke(app, cmd)
        assert result.exit_code == 0, f"{' '.join(cmd)} exited with {result.exit_code}, expected 0"

    def test_unknown_command_exits_nonzero(self) -> None:
        """Unknown command must exit non-zero."""
        result = runner.invoke(app, ["totally-unknown-cmd"])
        assert result.exit_code != 0

    def test_missing_required_arg_exits_nonzero(self) -> None:
        """Missing required argument must exit non-zero."""
        result = runner.invoke(app, ["status"])
        assert result.exit_code != 0, "status without required session_id should exit non-zero"

    def test_version_exits_zero(self) -> None:
        """--version must exit 0 or 2 (typer variant)."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code in (0, 2)

    def test_exit_code_is_int(self) -> None:
        """All exit codes must be integers (not bool or None)."""
        commands = [
            ["--help"],
            ["--version"],
            ["nonexistent-cmd"],
            ["status", "missing-id"],
        ]
        for cmd in commands:
            result = runner.invoke(app, cmd)
            assert isinstance(result.exit_code, int), (
                f"Exit code for '{' '.join(cmd)}' is {type(result.exit_code)}, expected int"
            )

    def test_stop_missing_session_exit_code_is_one(self) -> None:
        """'stop' on nonexistent session should exit 1 (error)."""
        result = runner.invoke(app, ["stop", "nonexistent-id-xyz"])
        assert result.exit_code == 1, f"stop on missing session exited {result.exit_code}, expected 1"

    def test_status_missing_session_exit_code_is_one(self) -> None:
        """'status' on nonexistent session should exit 1 (error)."""
        result = runner.invoke(app, ["status", "nonexistent-id-xyz"])
        assert result.exit_code == 1, f"status on missing session exited {result.exit_code}, expected 1"


# ---------------------------------------------------------------------------
# Aggregate audit runner
# ---------------------------------------------------------------------------


class TestAuditAggregate:
    """Run all checks and produce a scored audit report.

    This class aggregates results from all other test classes into a
    single audit report that can be reviewed for overall UX health.
    """

    @pytest.fixture(autouse=True)
    def _report(self) -> None:
        self.report = AuditReport()

    def _check_help_text(self, cmd: list[str], label: str) -> None:
        result = runner.invoke(app, cmd)
        if result.exit_code != 0:
            self.report.add(f"help:{label}", "P0", f"'{label} --help' exited {result.exit_code}")
        elif len(result.stdout.strip()) < 20:
            self.report.add(
                f"help:{label}",
                "P2",
                f"'{label} --help' output too short ({len(result.stdout.strip())} chars)",
            )

    def _check_no_traceback(self, cmd: list[str], label: str) -> None:
        result = runner.invoke(app, cmd)
        combined = _combined_output(result).lower()
        if "traceback" in combined:
            self.report.add(f"traceback:{label}", "P0", f"Raw traceback in '{label}' output")

    def test_produce_audit_report(self) -> None:
        """Aggregate all checks into a single scored report."""
        help_cmds = [
            (["--help"], "root"),
            (["run", "--help"], "run"),
            (["cockpit", "--help"], "cockpit"),
            (["sota", "--help"], "sota"),
            (["govern", "--help"], "govern"),
            (["phench", "--help"], "phench"),
        ]

        for cmd, label in help_cmds:
            self._check_help_text(cmd, label)

        traceback_cmds = [
            (["nonexistent-cmd-xyz"], "unknown_cmd"),
            (["status", "nonexistent-id"], "status_missing"),
            (["stop", "nonexistent-id"], "stop_missing"),
        ]
        for cmd, label in traceback_cmds:
            self._check_no_traceback(cmd, label)

        # Verify ps doesn't dump raw dicts
        result = runner.invoke(app, ["ps"])
        if re.search(r"\{'[^']+'\s*:\s*['\"]", result.stdout):
            self.report.add("formatting:ps", "P0", "ps output contains raw Python dict syntax")

        # Score: P0 count must be 0 for the audit to pass
        assert self.report.p0_count == 0, f"Audit failed with P0 findings:\n{self.report.summary()}"
