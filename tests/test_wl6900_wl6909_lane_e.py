"""Lane E closeout tests for WL-6900..WL-6909 diagnostics and error handling."""

from __future__ import annotations

import subprocess
import sys
from datetime import UTC, datetime, timedelta
from errno import ESRCH
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import orjson as json
import pytest

from thegent import doctor_setup_checks, shared_mcp_manager, shell_cli, summary
from thegent.resources.network import NetworkMonitor


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


def test_wl6900_shell_doctor_alias_probe_success_branch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
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


def test_wl6900_shell_doctor_records_probe_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _touch(tmp_path / ".zshenv")
    _touch(tmp_path / ".zsh_bundle.zsh")
    monkeypatch.setattr(shell_cli.Path, "home", lambda: tmp_path)

    def _raise_timeout(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=["zsh"], timeout=2)

    monkeypatch.setattr(shell_cli.subprocess, "run", _raise_timeout)
    collector = _PrintCollector()
    monkeypatch.setattr(shell_cli, "console", collector)

    shell_cli.shell_doctor(fix=False)

    assert any("Alias probe timed out" in message and "timeout" in message for message in collector.messages)


def test_wl6901_shell_platform_reports_success_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    collector = _PrintCollector()
    table = _FakeTable("Platform Information")
    monkeypatch.setattr(shell_cli, "console", collector)
    monkeypatch.setattr(shell_cli, "Table", lambda *args, **kwargs: table)
    original_run = subprocess.run

    def _fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        if args and args[0] == ["zsh", "--version"]:
            return subprocess.CompletedProcess(args[0], 0, stdout="zsh 5.9 (x86_64)\n", stderr="")
        return original_run(*args, **kwargs)

    monkeypatch.setattr(shell_cli.subprocess, "run", _fake_run)

    shell_cli.shell_platform()

    assert ("Zsh Version", "5.9") in table.rows


@pytest.mark.parametrize(
    ("side_effect", "expected"),
    [
        (subprocess.TimeoutExpired(cmd=["zsh"], timeout=2), "Probe timed out"),
        (FileNotFoundError("zsh missing"), "Not installed"),
        (subprocess.SubprocessError("boom"), "Probe failed (SubprocessError)"),
    ],
)
def test_wl6901_shell_platform_reports_degraded_causes(
    monkeypatch: pytest.MonkeyPatch, side_effect: BaseException, expected: str
) -> None:
    collector = _PrintCollector()
    table = _FakeTable("Platform Information")
    monkeypatch.setattr(shell_cli, "console", collector)
    monkeypatch.setattr(shell_cli, "Table", lambda *args, **kwargs: table)
    original_run = subprocess.run

    def _fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        if args and args[0] == ["zsh", "--version"]:
            raise side_effect
        return original_run(*args, **kwargs)

    monkeypatch.setattr(shell_cli.subprocess, "run", _fake_run)

    shell_cli.shell_platform()

    zsh_rows = dict(table.rows)
    assert expected in zsh_rows["Zsh Status"]


def test_wl6902_get_git_commits_non_repo_reports_not_repo(tmp_path: Path) -> None:
    start = datetime.now(UTC) - timedelta(days=1)
    end = datetime.now(UTC)

    payload = summary.get_git_commits(tmp_path, start, end)

    assert payload.status == "not_repo"
    assert payload.commits == []
    assert payload.error["type"] == "not_repo"


def test_wl6902_get_git_commits_command_failure_reports_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    start = datetime.now(UTC) - timedelta(days=1)
    end = datetime.now(UTC)

    monkeypatch.setattr(
        summary.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 128, stdout="", stderr="fatal: not a git repo"),
    )

    payload = summary.get_git_commits(tmp_path, start, end)

    assert payload.status == "error"
    assert payload.commits == []
    assert payload.error["type"] == "git_log_failed"


def test_wl6902_get_git_commits_empty_window_keeps_empty_status(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / ".git").mkdir()
    start = datetime.now(UTC) - timedelta(days=1)
    end = datetime.now(UTC)
    monkeypatch.setattr(
        summary.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, stdout="", stderr=""),
    )

    payload = summary.get_git_commits(tmp_path, start, end)

    assert payload.status == "empty"
    assert payload.commits == []


def test_wl6903_read_log_file_tracks_malformed_json_and_out_of_window(
    tmp_path: Path,
) -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)
    path = tmp_path / "chat.jsonl"
    valid = {
        "type": "user",
        "timestamp": "2026-01-10T12:00:00+00:00",
        "message": {"content": "ok"},
    }
    old = {
        "type": "assistant",
        "timestamp": "2025-12-10T12:00:00+00:00",
        "message": {"content": "old"},
    }
    path.write_text(
        json.dumps(valid).decode() + "\nnot-json\n" + json.dumps(old).decode() + "\n",
        encoding="utf-8",
    )

    payload = summary._read_log_file(path, start, end, include_diagnostics=True)

    assert payload["status"] == "ok"
    assert payload["entries"] == 1
    assert payload["parse_counts"]["malformed_json"] == 1
    assert payload["parse_counts"]["out_of_window"] == 1


def test_wl6904_read_log_file_missing_file_reports_explicit_status(
    tmp_path: Path,
) -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)

    payload = summary._read_log_file(tmp_path / "missing.jsonl", start, end, include_diagnostics=True)

    assert payload["status"] == "missing"
    assert payload["error"]["type"] == "FileNotFoundError"


def test_wl6904_read_log_file_permission_denied_reports_status(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)
    path = tmp_path / "denied.jsonl"
    path.write_text("", encoding="utf-8")
    original_open = Path.open

    def _deny(self: Path, *args: object, **kwargs: object):  # type: ignore[no-untyped-def]
        if self == path:
            raise PermissionError("denied")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", _deny)

    payload = summary._read_log_file(path, start, end, include_diagnostics=True)

    assert payload["status"] == "permission_denied"
    assert payload["error"]["type"] == "PermissionError"


def test_wl6905_ensure_mcp_running_healthy_preflight_short_circuits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = SimpleNamespace(mcp_host="127.0.0.1", mcp_port=3847)
    collector = _PrintCollector()
    monkeypatch.setattr(
        doctor_setup_checks.httpx,
        "get",
        lambda *args, **kwargs: httpx.Response(200, request=httpx.Request("GET", args[0])),
    )

    assert doctor_setup_checks.ensure_mcp_running(settings=settings, console=collector) is True


def test_wl6905_ensure_mcp_running_records_timeout_preflight(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = SimpleNamespace(mcp_host="127.0.0.1", mcp_port=3847)
    collector = _PrintCollector()
    monkeypatch.setattr(
        doctor_setup_checks.httpx,
        "get",
        MagicMock(side_effect=httpx.ReadTimeout("timeout")),
    )
    fake_manage = SimpleNamespace(mcp_up=lambda: (False, "not started"))
    monkeypatch.setitem(sys.modules, "thegent.mcp.manage", fake_manage)

    assert doctor_setup_checks.ensure_mcp_running(settings=settings, console=collector, timeout=1) is False
    assert any("preflight health check failed" in message and "timeout" in message for message in collector.messages)


def test_wl6906_ensure_mcp_running_retry_diagnostics_transient_then_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = SimpleNamespace(mcp_host="127.0.0.1", mcp_port=3847)
    collector = _PrintCollector()
    request = httpx.Request("GET", "http://127.0.0.1:3847/health")
    responses = [
        httpx.ConnectError("refused"),
        httpx.ConnectError("refused"),
        httpx.Response(200, request=request),
    ]
    monkeypatch.setattr(doctor_setup_checks.httpx, "get", MagicMock(side_effect=responses))
    fake_manage = SimpleNamespace(mcp_up=lambda: (True, "started"))
    monkeypatch.setitem(sys.modules, "thegent.mcp.manage", fake_manage)
    monkeypatch.setattr(doctor_setup_checks.time, "sleep", lambda *_args, **_kwargs: None)

    assert doctor_setup_checks.ensure_mcp_running(settings=settings, console=collector, timeout=2) is True
    assert any("retry diagnostics" in message and "connection_error=1" in message for message in collector.messages)


def test_wl6906_ensure_mcp_running_retry_diagnostics_persistent_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = SimpleNamespace(mcp_host="127.0.0.1", mcp_port=3847)
    collector = _PrintCollector()
    monkeypatch.setattr(
        doctor_setup_checks.httpx,
        "get",
        MagicMock(side_effect=httpx.ConnectError("refused")),
    )
    fake_manage = SimpleNamespace(mcp_up=lambda: (True, "started"))
    monkeypatch.setitem(sys.modules, "thegent.mcp.manage", fake_manage)
    monkeypatch.setattr(doctor_setup_checks.time, "sleep", lambda *_args, **_kwargs: None)

    assert doctor_setup_checks.ensure_mcp_running(settings=settings, console=collector, timeout=1) is False
    assert any("retry diagnostics" in message and "connection_error=" in message for message in collector.messages)


@pytest.mark.parametrize(
    ("proxy_behavior", "expected_message"),
    [
        (
            httpx.Response(503, request=httpx.Request("GET", "http://127.0.0.1:8317/v1/models")),
            "returned 503",
        ),
        (httpx.ReadTimeout("timeout"), "request timed out"),
        (httpx.ConnectError("refused"), "connection error"),
    ],
)
def test_wl6907_check_connectivity_cliproxy_categorizes_failures(
    monkeypatch: pytest.MonkeyPatch, proxy_behavior: object, expected_message: str
) -> None:
    settings = SimpleNamespace(mcp_host="127.0.0.1", mcp_port=3847)
    mcp_url = f"http://{settings.mcp_host}:{settings.mcp_port}/health"
    proxy_url = "http://127.0.0.1:8317/v1/models"
    request = httpx.Request("GET", mcp_url)

    def _fake_get(url: str, timeout: float) -> httpx.Response:  # type: ignore[override]
        if url == mcp_url:
            return httpx.Response(200, request=request)
        if url == proxy_url:
            if isinstance(proxy_behavior, BaseException):
                raise proxy_behavior
            return proxy_behavior
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(doctor_setup_checks, "ThegentSettings", lambda: settings)
    monkeypatch.setattr(doctor_setup_checks.httpx, "get", _fake_get)

    results = doctor_setup_checks.check_connectivity(
        check_result_cls=_check_result,
        console=_PrintCollector(),
        auto_start=False,
    )

    cliproxy_result = results[1]
    assert cliproxy_result.status in {"ok", "warn"}
    assert expected_message in cliproxy_result.message


def test_wl6908_shared_mcp_cleans_only_stale_lockfile(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(shared_mcp_manager.Path, "home", lambda: tmp_path)
    _scope, lockfile = shared_mcp_manager.get_server_scope()
    lockfile.write_text(json.dumps({"pid": 424242, "port": 3847}).decode(), encoding="utf-8")
    monkeypatch.setattr(
        shared_mcp_manager.os,
        "kill",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError(ESRCH, "")),
    )

    fake_manage = SimpleNamespace(
        mcp_up=lambda: (True, "started"),
        _get_mcp_url=lambda *_args, **_kwargs: "http://127.0.0.1:3847/mcp",
    )
    monkeypatch.setitem(sys.modules, "thegent.mcp.manage", fake_manage)

    is_new, url = shared_mcp_manager.ensure_shared_mcp_server()
    assert is_new is True
    assert url == "http://127.0.0.1:3847/mcp"
    data = json.loads(lockfile.read_text(encoding="utf-8"))
    assert data["port"] == 3847


def test_wl6908_shared_mcp_malformed_json_does_not_delete_lockfile(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(shared_mcp_manager.Path, "home", lambda: tmp_path)
    _scope, lockfile = shared_mcp_manager.get_server_scope()
    lockfile.write_text("{ not json", encoding="utf-8")

    is_new, message = shared_mcp_manager.ensure_shared_mcp_server()

    assert is_new is False
    assert "Malformed lockfile" in (message or "")
    assert lockfile.exists()
    assert lockfile.read_text(encoding="utf-8") == "{ not json"


def test_wl6908_shared_mcp_read_error_does_not_delete_lockfile(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(shared_mcp_manager.Path, "home", lambda: tmp_path)
    _scope, lockfile = shared_mcp_manager.get_server_scope()
    lockfile.write_text(json.dumps({"pid": 1, "port": 3847}).decode(), encoding="utf-8")

    import builtins

    original_open = builtins.open

    def _deny_open(file: object, *args: object, **kwargs: object):  # type: ignore[no-untyped-def]
        if str(file) == str(lockfile):
            raise PermissionError("denied")
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", _deny_open)

    is_new, message = shared_mcp_manager.ensure_shared_mcp_server()

    assert is_new is False
    assert "permission denied" in (message or "").lower()
    assert lockfile.exists()


def test_wl6909_network_interface_diagnostics_distinguish_error_from_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monitor = NetworkMonitor()
    mock_psutil = MagicMock()
    monkeypatch.setattr("thegent.resources.network._PSUTIL_AVAILABLE", True)
    monkeypatch.setattr("thegent.resources.network._psutil", mock_psutil)

    mock_psutil.net_io_counters.return_value = {}
    empty_payload = monitor.list_interfaces(include_diagnostics=True)

    mock_psutil.net_io_counters.side_effect = RuntimeError("boom")
    error_payload = monitor.list_interfaces(include_diagnostics=True)

    assert empty_payload["status"] == "empty"
    assert error_payload["status"] == "error"
    assert error_payload["error"]["type"] == "RuntimeError"
