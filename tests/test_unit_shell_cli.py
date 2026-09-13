"""Unit tests for thegent.shell_cli error handling."""

import platform as py_platform
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

import thegent.shell_cli as shell_cli_module


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_shell_reload_exits_nonzero_on_source_failure(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    def _failed_run(*args, **kwargs):  # noqa: ANN002, ANN003
        return subprocess.CompletedProcess(
            args=["zsh", "-c", "source ~/.zshrc"],
            returncode=7,
            stdout="",
            stderr="bad zshrc",
        )

    monkeypatch.setattr(shell_cli_module.subprocess, "run", _failed_run)

    result = runner.invoke(shell_cli_module.shell_app, ["reload"])
    assert result.exit_code == 1
    assert "Shell reload failed" in result.output
    assert "bad zshrc" in result.output


def test_shell_doctor_alias_probe_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, runner: CliRunner) -> None:
    (tmp_path / ".zshenv").write_text("export TEST=1\n", encoding="utf-8")
    (tmp_path / ".zsh_bundle.zsh").write_text("echo bundle\n", encoding="utf-8")
    monkeypatch.setattr(shell_cli_module.Path, "home", lambda: tmp_path)

    def _probe_success(*args, **kwargs):  # noqa: ANN002, ANN003
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(shell_cli_module.subprocess, "run", _probe_success)

    result = runner.invoke(shell_cli_module.shell_app, ["doctor"])
    assert result.exit_code == 0
    assert "Alias probe failed" not in result.output
    assert "Alias probe skipped" not in result.output
    assert "Warnings:" not in result.output
    assert "No issues found. Shell environment is healthy." in result.output


def test_shell_doctor_records_alias_probe_timeout_warning(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, runner: CliRunner
) -> None:
    (tmp_path / ".zshenv").write_text("export TEST=1\n", encoding="utf-8")
    (tmp_path / ".zsh_bundle.zsh").write_text("echo bundle\n", encoding="utf-8")
    monkeypatch.setattr(shell_cli_module.Path, "home", lambda: tmp_path)

    def _timeout_run(*args, **kwargs):  # noqa: ANN002, ANN003
        raise subprocess.TimeoutExpired(cmd=["zsh", "-c", "alias ls"], timeout=2)

    monkeypatch.setattr(shell_cli_module.subprocess, "run", _timeout_run)

    result = runner.invoke(shell_cli_module.shell_app, ["doctor"])
    assert result.exit_code == 0
    assert "Warnings:" in result.output
    assert "Alias probe timed out: timeout after 2s." in result.output
    assert "thegent shell doctor --fix" in result.output


def test_shell_doctor_records_alias_probe_os_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, runner: CliRunner
) -> None:
    (tmp_path / ".zshenv").write_text("export TEST=1\n", encoding="utf-8")
    (tmp_path / ".zsh_bundle.zsh").write_text("echo bundle\n", encoding="utf-8")
    monkeypatch.setattr(shell_cli_module.Path, "home", lambda: tmp_path)

    def _error_run(*args, **kwargs):  # noqa: ANN002, ANN003
        raise FileNotFoundError(2, "No such file or directory", "zsh")

    monkeypatch.setattr(shell_cli_module.subprocess, "run", _error_run)

    result = runner.invoke(shell_cli_module.shell_app, ["doctor"])
    assert result.exit_code == 0
    assert "Warnings:" in result.output
    assert "Alias probe unavailable (zsh executable not found)." in result.output


def test_shell_doctor_records_alias_probe_execution_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, runner: CliRunner
) -> None:
    (tmp_path / ".zshenv").write_text("export TEST=1\n", encoding="utf-8")
    (tmp_path / ".zsh_bundle.zsh").write_text("echo bundle\n", encoding="utf-8")
    monkeypatch.setattr(shell_cli_module.Path, "home", lambda: tmp_path)

    def _error_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=args[0], returncode=2, stdout="", stderr="rc=2 during startup")

    monkeypatch.setattr(shell_cli_module.subprocess, "run", _error_run)

    result = runner.invoke(shell_cli_module.shell_app, ["doctor"])
    assert result.exit_code == 0
    assert "Warnings:" in result.output
    normalized_output = " ".join(result.output.split())
    assert "Alias probe execution failed (execution failed (exit 2): rc=2 during startup)." in normalized_output


def _set_platform_stubs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(py_platform, "system", lambda: "Darwin")
    monkeypatch.setattr(py_platform, "platform", lambda: "Mock Platform")
    monkeypatch.setattr(py_platform, "machine", lambda: "arm64")
    monkeypatch.setattr(py_platform, "python_version", lambda: "3.14.0")


def test_shell_platform_probe_success(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    _set_platform_stubs(monkeypatch)

    def _version_run(*args, **kwargs):  # noqa: ANN002, ANN003
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="zsh 5.9 (x86_64-apple-darwin)\n",
            stderr="",
        )

    monkeypatch.setattr(shell_cli_module.subprocess, "run", _version_run)

    result = runner.invoke(shell_cli_module.shell_app, ["platform"])
    assert result.exit_code == 0
    assert "Zsh Status" in result.output
    assert "Available" in result.output
    assert "5.9" in result.output


def test_shell_platform_probe_timeout(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    _set_platform_stubs(monkeypatch)

    def _timeout_run(*args, **kwargs):  # noqa: ANN002, ANN003
        raise subprocess.TimeoutExpired(cmd=["zsh", "--version"], timeout=2)

    monkeypatch.setattr(shell_cli_module.subprocess, "run", _timeout_run)

    result = runner.invoke(shell_cli_module.shell_app, ["platform"])
    assert result.exit_code == 0
    assert "Probe failed (timeout after 2s)" in result.output


def test_shell_platform_probe_missing_binary(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    _set_platform_stubs(monkeypatch)

    def _missing_run(*args, **kwargs):  # noqa: ANN002, ANN003
        raise FileNotFoundError(2, "No such file or directory", "zsh")

    monkeypatch.setattr(shell_cli_module.subprocess, "run", _missing_run)

    result = runner.invoke(shell_cli_module.shell_app, ["platform"])
    assert result.exit_code == 0
    assert "Probe failed (zsh executable not found)" in result.output


def test_shell_platform_probe_subprocess_error(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    _set_platform_stubs(monkeypatch)

    def _error_run(*args, **kwargs):  # noqa: ANN002, ANN003
        raise subprocess.SubprocessError("zsh probe failed")

    monkeypatch.setattr(shell_cli_module.subprocess, "run", _error_run)

    result = runner.invoke(shell_cli_module.shell_app, ["platform"])
    assert result.exit_code == 0
    assert "Probe failed (subprocess error (SubprocessError):" in result.output
    assert "zsh probe" in result.output
    assert "failed)" in result.output
