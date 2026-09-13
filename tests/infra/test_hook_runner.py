from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

from thegent.infra.hook_runner import run_hook
from thegent.infra.shell_detection import ShellType


def test_run_hook_timeout_handles_text_streams(monkeypatch) -> None:
    """Timeout handling should support text-mode TimeoutExpired streams."""

    monkeypatch.setattr(
        "thegent.infra.hook_runner.get_settings",
        lambda: SimpleNamespace(hook_shell=None),
    )
    monkeypatch.setattr(
        "thegent.infra.hook_runner.get_preferred_shell",
        lambda performance: ShellType.BASH,
    )
    monkeypatch.setattr(
        "thegent.infra.hook_runner.get_shell_executable",
        lambda shell_type: "/bin/bash",
    )

    def _raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd=args[0], timeout=5, output="partial-out", stderr="partial-err"
        )

    monkeypatch.setattr("thegent.infra.hook_runner.subprocess.run", _raise_timeout)

    result = run_hook(Path("hooks/example.sh"), timeout=5)
    assert result.returncode == 124
    assert result.stdout == "partial-out"
    assert result.stderr == "Hook timed out after 5s\npartial-err"


def test_run_hook_builds_powershell_file_command(monkeypatch) -> None:
    """PowerShell shells require the -File invocation mode."""

    monkeypatch.setattr(
        "thegent.infra.hook_runner.get_settings",
        lambda: SimpleNamespace(hook_shell="pwsh"),
    )
    monkeypatch.setattr(
        "thegent.infra.hook_runner.get_shell_executable",
        lambda shell_type: "pwsh",
    )

    calls: list[list[str]] = []

    def _fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr("thegent.infra.hook_runner.subprocess.run", _fake_run)

    result = run_hook(Path("hooks/example.ps1"))
    assert result.returncode == 0
    assert calls[0] == [
        "pwsh",
        "-NoProfile",
        "-NonInteractive",
        "-File",
        "hooks/example.ps1",
    ]
