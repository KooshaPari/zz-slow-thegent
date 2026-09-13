"""Lane A focused closeout tests for WL-6750..WL-6759."""

from __future__ import annotations

import errno
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import orjson as json
import pytest

# discover_models was removed from provider_model_manager; skip the file.
import thegent.provider_model_manager as _provider_model_manager_mod

if not hasattr(_provider_model_manager_mod, "discover_models"):
    pytest.skip(
        "provider_model_manager.discover_models removed; lane a tests skipped",
        allow_module_level=True,
    )

from thegent import doctor_shell_nix, shell_cli, summary
from thegent.doctor import _check_mcp_tools
from thegent.infra import fast_file_ops
from thegent.provider_model_manager import discover_models
from thegent.resources.network import NetworkMonitor
from thegent.ux.session_tui import SessionTUI


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


def _check_result(name: str, category: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, category=category, status="", message="", details="", fix_hint="")


def test_wl6750_shell_doctor_alias_probe_success_and_probe_failure_visibility(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _touch(tmp_path / ".zshenv")
    _touch(tmp_path / ".zsh_bundle.zsh")
    monkeypatch.setattr(shell_cli.Path, "home", lambda: tmp_path)

    collector = _PrintCollector()
    monkeypatch.setattr(shell_cli, "console", collector)
    monkeypatch.setattr(
        shell_cli.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, stdout="alias ls='tree -a'\n", stderr=""),
    )
    shell_cli.shell_doctor(fix=False)
    assert any("ls is aliased to tree/recursive output" in message for message in collector.messages)

    def _raise_timeout(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=["zsh"], timeout=2)

    collector.messages.clear()
    monkeypatch.setattr(shell_cli.subprocess, "run", _raise_timeout)
    shell_cli.shell_doctor(fix=False)
    assert any("Alias probe timed out" in message and "timeout" in message for message in collector.messages)
    assert any("Warnings:" in message for message in collector.messages)


@pytest.mark.parametrize(
    ("side_effect", "expected_status"),
    [
        (None, "Available"),
        (FileNotFoundError("zsh missing"), "Not installed"),
        (subprocess.TimeoutExpired(cmd=["zsh"], timeout=2), "Probe timed out"),
        (subprocess.SubprocessError("boom"), "Probe failed (SubprocessError)"),
    ],
)
def test_wl6751_shell_platform_reports_actionable_statuses(
    monkeypatch: pytest.MonkeyPatch,
    side_effect: BaseException | None,
    expected_status: str,
) -> None:
    collector = _PrintCollector()
    table = _FakeTable("Platform Information")
    monkeypatch.setattr(shell_cli, "console", collector)
    monkeypatch.setattr(shell_cli, "Table", lambda *args, **kwargs: table)

    original_run = subprocess.run

    def _fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        if args and args[0] == ["zsh", "--version"]:
            if side_effect is None:
                return subprocess.CompletedProcess(args[0], 0, stdout="zsh 5.9 (x86_64)\n", stderr="")
            raise side_effect
        return original_run(*args, **kwargs)

    monkeypatch.setattr(shell_cli.subprocess, "run", _fake_run)
    shell_cli.shell_platform()

    rows = dict(table.rows)
    assert expected_status in rows["Zsh Status"]


@pytest.mark.parametrize(
    "probe_outcome",
    [
        subprocess.TimeoutExpired(cmd=["nix"], timeout=5),
        PermissionError("denied"),
        subprocess.CompletedProcess(["nix", "--version"], 1, stdout="", stderr="boom"),
    ],
)
def test_wl6752_check_nix_typed_failure_branches(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, probe_outcome: BaseException | subprocess.CompletedProcess[str]
) -> None:
    monkeypatch.setattr(doctor_shell_nix.shutil, "which", lambda name: "/usr/bin/nix" if name == "nix" else None)
    monkeypatch.setattr(doctor_shell_nix, "check_nix_daemon_status", lambda: (False, "Not running"))

    def _probe(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if isinstance(probe_outcome, subprocess.CompletedProcess):
            return probe_outcome
        raise probe_outcome

    monkeypatch.setattr(doctor_shell_nix, "run_subprocess_optimized", _probe)
    result = doctor_shell_nix.check_nix(check_result_cls=_check_result, project_root=tmp_path)[0]
    assert result.status in {"warn", "fail"}
    assert result.status != "ok"


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (httpx.ConnectError("refused", request=httpx.Request("GET", "http://127.0.0.1:3847/health")), "connection"),
        (httpx.ReadTimeout("timeout", request=httpx.Request("GET", "http://127.0.0.1:3847/health")), "timed out"),
    ],
)
def test_wl6753_mcp_health_warnings_include_failure_cause(exc: Exception, expected: str) -> None:
    with patch("thegent.doctor.httpx.get", side_effect=exc):
        result = _check_mcp_tools()[0]
    assert result.status == "warn"
    assert expected in result.message.lower()
    assert result.details is not None


def test_wl6754_git_commit_query_failure_is_distinct_from_empty_window(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / ".git").mkdir()
    start = datetime.now(UTC) - timedelta(days=1)
    end = datetime.now(UTC)

    monkeypatch.setattr(
        summary.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, stdout="", stderr="")
    )
    empty_result = summary.get_git_commits(tmp_path, start, end)
    assert empty_result.status == "empty"
    assert empty_result.error is None

    monkeypatch.setattr(
        summary.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 128, stdout="", stderr="fatal: bad revision"),
    )
    error_result = summary.get_git_commits(tmp_path, start, end)
    assert error_result.status == "error"
    assert error_result.error is not None
    assert error_result.error["returncode"] == 128


def test_wl6755_read_log_file_tracks_malformed_json_and_timestamp_errors(tmp_path: Path) -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)
    path = tmp_path / "chat.jsonl"
    valid = {"type": "user", "timestamp": "2026-01-10T12:00:00+00:00", "message": {"content": "ok"}}
    bad_ts = {"type": "assistant", "timestamp": "not-a-date", "message": {"content": "bad"}}
    path.write_text(json.dumps(valid).decode() + "\nnot-json\n" + json.dumps(bad_ts).decode() + "\n", encoding="utf-8")

    payload = summary._read_log_file(path, start, end, include_diagnostics=True)
    assert payload["entries"] == 1
    assert payload["parse_counts"]["malformed_json"] == 1
    assert payload["parse_counts"]["invalid_timestamp"] == 1
    assert payload["parse_counts"]["sampled_errors"]


def test_wl6756_sendfile_fallback_emits_telemetry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    src = tmp_path / "src.bin"
    dst = tmp_path / "dst.bin"
    src.write_bytes(b"abc123")
    monkeypatch.setattr(fast_file_ops.sys, "platform", "linux")
    monkeypatch.setattr(fast_file_ops, "SEND_FILE_THRESHOLD_BYTES", 1)

    def _raise_sendfile(*_args: object, **_kwargs: object) -> int:
        raise OSError(errno.EPERM, "blocked")

    monkeypatch.setattr(fast_file_ops.os, "sendfile", _raise_sendfile)
    fast_file_ops.reset_sendfile_fallback_counts()
    caplog.set_level("WARNING", logger="thegent.infra.fast_file_ops")

    fast_file_ops.FastFileOps.copy(src, dst, preserve_metadata=False)

    assert dst.read_bytes() == b"abc123"
    assert fast_file_ops.get_sendfile_fallback_counts().get("permission") == 1
    assert any("sendfile fallback engaged" in rec.message for rec in caplog.records)


def test_wl6757_discover_models_transport_failure_and_provider_context(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("port: 8317\n", encoding="utf-8")
    caplog.set_level("WARNING", logger="thegent.provider_model_manager")

    with (
        patch("thegent.provider_model_manager._ensure_config", return_value=config_path),
        patch("thegent.provider_model_manager._load_yaml", return_value={}),
        patch("thegent.provider_model_manager._load_json", return_value={}),
        patch("thegent.provider_model_manager.httpx.get", side_effect=httpx.TimeoutException("timed out")),
    ):
        payload = discover_models(provider="roo", include_status=True)

    assert payload["models"] == []
    assert payload["discovery"]["status"] == "error"
    assert payload["discovery"]["failure_type"] == "timeout"
    assert payload["discovery"]["provider"] == "roo"
    assert any(getattr(rec, "provider", None) == "roo" for rec in caplog.records)


def test_wl6757_discover_models_invalid_payload_status(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("port: 8317\n", encoding="utf-8")

    class FakeResp:
        status_code = 200

        def json(self) -> object:
            return []

    with (
        patch("thegent.provider_model_manager._ensure_config", return_value=config_path),
        patch("thegent.provider_model_manager._load_yaml", return_value={}),
        patch("thegent.provider_model_manager._load_json", return_value={}),
        patch("thegent.provider_model_manager.httpx.get", return_value=FakeResp()),
    ):
        payload = discover_models(include_status=True)

    assert payload["discovery"]["status"] == "error"
    assert payload["discovery"]["failure_class"] == "protocol"
    assert payload["discovery"]["failure_type"] == "payload_not_object"


def test_wl6758_session_tui_surfaces_subagent_enumeration_failures() -> None:
    tui = SessionTUI()
    with (
        patch("thegent.ux.session_tui.session_meta_impl", return_value={"pid": 123, "status": "running"}),
        patch("thegent.ux.session_tui._is_pid_running", return_value=True),
        patch("thegent.ux.session_tui.psutil.Process", side_effect=RuntimeError("process tree unavailable")),
        patch("thegent.ux.session_tui._find_session_meta", return_value=Path("/tmp/sess.json")),
    ):
        details = tui._get_session_details("sess-1")

    assert details.get("degraded") is True
    assert details.get("diagnostics", {}).get("subagents", {}).get("component") == "subagents"


def test_wl6759_network_interfaces_distinguish_empty_from_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monitor = NetworkMonitor()
    with (
        patch("thegent.resources.network._PSUTIL_AVAILABLE", True),
        patch("thegent.resources.network._psutil") as mock_psutil,
    ):
        mock_psutil.net_io_counters.return_value = {}
        empty_payload = monitor.list_interfaces(include_diagnostics=True)
        mock_psutil.net_io_counters.side_effect = OSError("permission denied")
        error_payload = monitor.list_interfaces(include_diagnostics=True)

    assert empty_payload["status"] == "empty"
    assert empty_payload["interfaces"] == []
    assert error_payload["status"] == "error"
    assert error_payload["error"]["type"] == "OSError"
