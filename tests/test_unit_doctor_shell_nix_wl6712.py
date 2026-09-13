from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from thegent import doctor_shell_nix


def _result(name: str, category: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, category=category, status="", message="", details=None, fix_hint=None)


def test_check_nix_timeout_is_warn(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        doctor_shell_nix.shutil,
        "which",
        lambda name: "/usr/bin/nix" if name == "nix" else None,
    )
    monkeypatch.setattr(
        doctor_shell_nix,
        "run_subprocess_optimized",
        lambda *args, **kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired(cmd=["nix"], timeout=5)),
    )
    monkeypatch.setattr(doctor_shell_nix, "check_nix_daemon_status", lambda: (True, "Running (systemd)"))

    results = doctor_shell_nix.check_nix(check_result_cls=_result, project_root=tmp_path)

    nix = results[0]
    assert nix.status == "warn"
    assert "timed out" in nix.message.lower()


def test_check_nix_permission_error_is_fail(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        doctor_shell_nix.shutil,
        "which",
        lambda name: "/usr/bin/nix" if name == "nix" else None,
    )
    monkeypatch.setattr(
        doctor_shell_nix,
        "run_subprocess_optimized",
        lambda *args, **kwargs: (_ for _ in ()).throw(PermissionError("denied")),
    )
    monkeypatch.setattr(doctor_shell_nix, "check_nix_daemon_status", lambda: (False, "Not running"))

    results = doctor_shell_nix.check_nix(check_result_cls=_result, project_root=tmp_path)

    nix = results[0]
    assert nix.status == "fail"
    assert "not executable" in nix.message
    assert "PermissionError" in (nix.details or "")


def test_check_nix_nonzero_exit_is_fail(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        doctor_shell_nix.shutil,
        "which",
        lambda name: "/usr/bin/nix" if name == "nix" else None,
    )
    monkeypatch.setattr(
        doctor_shell_nix,
        "run_subprocess_optimized",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, stdout="", stderr="boom"),
    )
    monkeypatch.setattr(doctor_shell_nix, "check_nix_daemon_status", lambda: (False, "Not running"))

    results = doctor_shell_nix.check_nix(check_result_cls=_result, project_root=tmp_path)

    nix = results[0]
    assert nix.status == "fail"
    assert "--version' failed" in nix.message
    assert "boom" in (nix.details or "")


def test_check_nix_success_reports_ok(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        doctor_shell_nix.shutil,
        "which",
        lambda name: "/usr/bin/nix" if name == "nix" else None,
    )
    monkeypatch.setattr(
        doctor_shell_nix,
        "run_subprocess_optimized",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, stdout="nix (Nix) 2.23.1\n", stderr=""),
    )
    monkeypatch.setattr(doctor_shell_nix, "check_nix_daemon_status", lambda: (True, "Running (systemd)"))

    results = doctor_shell_nix.check_nix(check_result_cls=_result, project_root=tmp_path)

    nix = results[0]
    assert nix.status == "ok"
    assert nix.message == "Found Nix: nix (Nix) 2.23.1"
