"""Unit tests for Rust harness passthrough wrappers."""

from __future__ import annotations

import pytest

from thegent import rust_wrappers


def test_dex_wrapper_execs_shim(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, object] = {}

    monkeypatch.setattr(rust_wrappers.shutil, "which", lambda _: "/tmp/thegent-shims")
    monkeypatch.setattr(rust_wrappers.sys, "argv", ["dex", "--native", "resume"])

    def _fake_execv(path: str, argv: list[str]) -> None:
        called["path"] = path
        called["argv"] = argv
        raise SystemExit(0)

    monkeypatch.setattr(rust_wrappers.os, "execv", _fake_execv)

    with pytest.raises(SystemExit) as exc:
        rust_wrappers.dex()

    assert exc.value.code == 0
    assert called["path"] == "/tmp/thegent-shims"
    assert called["argv"] == [
        "thegent-shims",
        "agent",
        "dex",
        "--native",
        "resume",
    ]


def test_wrapper_exits_if_shim_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rust_wrappers.shutil, "which", lambda _: None)

    with pytest.raises(SystemExit) as exc:
        rust_wrappers.clode()

    assert exc.value.code == 127


def test_fanta_wrapper_execs_shim(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, object] = {}

    monkeypatch.setattr(rust_wrappers.shutil, "which", lambda _: "/tmp/thegent-shims")
    monkeypatch.setattr(rust_wrappers.sys, "argv", ["fanta", "resume"])

    def _fake_execv(path: str, argv: list[str]) -> None:
        called["path"] = path
        called["argv"] = argv
        raise SystemExit(0)

    monkeypatch.setattr(rust_wrappers.os, "execv", _fake_execv)

    with pytest.raises(SystemExit) as exc:
        rust_wrappers.fanta()

    assert exc.value.code == 0
    assert called["path"] == "/tmp/thegent-shims"
    assert called["argv"] == [
        "thegent-shims",
        "agent",
        "fanta",
        "resume",
    ]


def test_roid_wrapper_execs_shim(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, object] = {}

    monkeypatch.setattr(rust_wrappers.shutil, "which", lambda _: "/tmp/thegent-shims")
    monkeypatch.setattr(rust_wrappers.sys, "argv", ["roid", "exec", "status"])

    def _fake_execv(path: str, argv: list[str]) -> None:
        called["path"] = path
        called["argv"] = argv
        raise SystemExit(0)

    monkeypatch.setattr(rust_wrappers.os, "execv", _fake_execv)

    with pytest.raises(SystemExit) as exc:
        rust_wrappers.roid()

    assert exc.value.code == 0
    assert called["path"] == "/tmp/thegent-shims"
    assert called["argv"] == [
        "thegent-shims",
        "agent",
        "roid",
        "exec",
        "status",
    ]


def test_droid_wrapper_execs_shim(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, object] = {}

    monkeypatch.setattr(rust_wrappers.shutil, "which", lambda _: "/tmp/thegent-shims")
    monkeypatch.setattr(rust_wrappers.sys, "argv", ["droid", "--native", "exec", "status"])

    def _fake_execv(path: str, argv: list[str]) -> None:
        called["path"] = path
        called["argv"] = argv
        raise SystemExit(0)

    monkeypatch.setattr(rust_wrappers.os, "execv", _fake_execv)

    with pytest.raises(SystemExit) as exc:
        rust_wrappers.droid()

    assert exc.value.code == 0
    assert called["path"] == "/tmp/thegent-shims"
    assert called["argv"] == [
        "thegent-shims",
        "agent",
        "droid",
        "--native",
        "exec",
        "status",
    ]


def test_anen_wrapper_execs_shim(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, object] = {}

    monkeypatch.setattr(rust_wrappers.shutil, "which", lambda _: "/tmp/thegent-shims")
    monkeypatch.setattr(rust_wrappers.sys, "argv", ["anen", "exec", "-p", "status"])

    def _fake_execv(path: str, argv: list[str]) -> None:
        called["path"] = path
        called["argv"] = argv
        raise SystemExit(0)

    monkeypatch.setattr(rust_wrappers.os, "execv", _fake_execv)

    with pytest.raises(SystemExit) as exc:
        rust_wrappers.anen()

    assert exc.value.code == 0
    assert called["path"] == "/tmp/thegent-shims"
    assert called["argv"] == [
        "thegent-shims",
        "agent",
        "anen",
        "exec",
        "-p",
        "status",
    ]


def test_antigma_wrapper_execs_shim(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, object] = {}

    monkeypatch.setattr(rust_wrappers.shutil, "which", lambda _: "/tmp/thegent-shims")
    monkeypatch.setattr(rust_wrappers.sys, "argv", ["antigma", "--model", "flash"])

    def _fake_execv(path: str, argv: list[str]) -> None:
        called["path"] = path
        called["argv"] = argv
        raise SystemExit(0)

    monkeypatch.setattr(rust_wrappers.os, "execv", _fake_execv)

    with pytest.raises(SystemExit) as exc:
        rust_wrappers.antigma()

    assert exc.value.code == 0
    assert called["path"] == "/tmp/thegent-shims"
    assert called["argv"] == [
        "thegent-shims",
        "agent",
        "antigma",
        "--model",
        "flash",
    ]
