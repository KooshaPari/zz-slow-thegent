"""WL-6880 + WL-6881 shell diagnostics checks."""

from __future__ import annotations

import platform as py_platform
import subprocess
from pathlib import Path

import pytest

from thegent import shell_cli


class _PrintCollector:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def print(self, *args: object, **_kwargs: object) -> None:
        self.messages.append(" ".join(str(arg) for arg in args))


class _FakeTable:
    def __init__(self, title: str | None = None) -> None:
        self.title = title
        self.rows: list[tuple[str, str]] = []

    def add_column(self, *_args: object, **_kwargs: object) -> None:
        return None

    def add_row(self, key: str, value: str) -> None:
        self.rows.append((key, value))


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def test_wl6880_shell_doctor_alias_probe_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _touch(tmp_path / ".zshenv")
    _touch(tmp_path / ".zsh_bundle.zsh")
    monkeypatch.setattr(shell_cli.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        shell_cli.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, stdout="alias ls='tree -a'\n", stderr=""),
    )
    collector = _PrintCollector()
    monkeypatch.setattr(shell_cli, "console", collector)

    shell_cli.shell_doctor(fix=False)

    assert any("ls is aliased to tree/recursive output" in message for message in collector.messages)
    assert not any("Alias probe execution failed" in message for message in collector.messages)
    assert not any("Alias probe timed out" in message for message in collector.messages)


def test_wl6880_shell_doctor_alias_probe_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _touch(tmp_path / ".zshenv")
    _touch(tmp_path / ".zsh_bundle.zsh")
    monkeypatch.setattr(shell_cli.Path, "home", lambda: tmp_path)

    def _raise_timeout(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=["zsh"], timeout=2)

    monkeypatch.setattr(shell_cli.subprocess, "run", _raise_timeout)
    collector = _PrintCollector()
    monkeypatch.setattr(shell_cli, "console", collector)

    shell_cli.shell_doctor(fix=False)

    assert any("Alias probe timed out: timeout after 2s." in message for message in collector.messages)


def test_wl6880_shell_doctor_alias_probe_execution_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _touch(tmp_path / ".zshenv")
    _touch(tmp_path / ".zsh_bundle.zsh")
    monkeypatch.setattr(shell_cli.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        shell_cli.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, stdout="", stderr="rc=1 during startup"),
    )
    collector = _PrintCollector()
    monkeypatch.setattr(shell_cli, "console", collector)

    shell_cli.shell_doctor(fix=False)

    assert any(
        "Alias probe execution failed (execution failed (exit 1): rc=1 during startup)." in message
        for message in collector.messages
    )


def test_wl6881_shell_platform_probe_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(py_platform, "system", lambda: "Darwin")
    monkeypatch.setattr(py_platform, "platform", lambda: "Mock Platform")
    monkeypatch.setattr(py_platform, "machine", lambda: "arm64")
    monkeypatch.setattr(py_platform, "python_version", lambda: "3.14.0")
    collector = _PrintCollector()
    table = _FakeTable("Platform Information")
    monkeypatch.setattr(shell_cli, "console", collector)
    monkeypatch.setattr(shell_cli, "Table", lambda *args, **kwargs: table)
    monkeypatch.setattr(
        shell_cli.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, stdout="zsh 5.9 (x86_64-apple-darwin)\n", stderr=""
        ),
    )

    shell_cli.shell_platform()

    rows = dict(table.rows)
    assert rows["Zsh Status"] == "Available"
    assert rows["Zsh Version"] == "5.9"


def test_wl6881_shell_platform_probe_execution_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(py_platform, "system", lambda: "Darwin")
    monkeypatch.setattr(py_platform, "platform", lambda: "Mock Platform")
    monkeypatch.setattr(py_platform, "machine", lambda: "arm64")
    monkeypatch.setattr(py_platform, "python_version", lambda: "3.14.0")
    collector = _PrintCollector()
    table = _FakeTable("Platform Information")
    monkeypatch.setattr(shell_cli, "console", collector)
    monkeypatch.setattr(shell_cli, "Table", lambda *args, **kwargs: table)
    monkeypatch.setattr(
        shell_cli.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, stdout="noop", stderr="bad version output"),
    )

    shell_cli.shell_platform()

    rows = dict(table.rows)
    assert rows["Zsh Status"].startswith("Execution failed (execution failed (exit 1)")
    assert "bad version output" in rows["Zsh Status"]
