from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from thegent.shell_cli import shell_app

runner = CliRunner()


def test_shell_reload_reports_success_on_zero_exit(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("thegent.shell_cli.subprocess.run", fake_run)

    result = runner.invoke(shell_app, ["reload"])

    assert result.exit_code == 0
    assert "Shell configuration reloaded" in result.output


def test_shell_reload_reports_stdout_stderr_on_nonzero_exit(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args[0], returncode=23, stdout="bad out", stderr="bad err")

    monkeypatch.setattr("thegent.shell_cli.subprocess.run", fake_run)

    result = runner.invoke(shell_app, ["reload"])

    assert result.exit_code == 1
    assert "Shell reload failed (exit code 23)" in result.output
    assert "stdout:" in result.output
    assert "bad out" in result.output
    assert "stderr:" in result.output
    assert "bad err" in result.output


def test_shell_doctor_surfaces_alias_probe_failures_as_issues(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    (home / ".zshenv").write_text("", encoding="utf-8")
    (home / ".zsh_bundle.zsh").write_text("", encoding="utf-8")

    monkeypatch.setattr("thegent.shell_cli.Path.home", staticmethod(lambda: home))

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=2)

    monkeypatch.setattr("thegent.shell_cli.subprocess.run", fake_run)

    result = runner.invoke(shell_app, ["doctor"])

    assert result.exit_code == 0
    assert "Warnings:" in result.output
    assert "Alias probe timed out:" in result.output
    assert "Check zsh startup time and rerun:" in result.output
    assert "thegent shell doctor --fix" in result.output
