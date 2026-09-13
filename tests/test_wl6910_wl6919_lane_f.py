"""Lane F closeout tests for WL-6910..WL-6919 diagnostics and failure handling."""

from __future__ import annotations

import contextlib
import subprocess
import sys
from datetime import UTC, datetime
from errno import ESRCH
from pathlib import Path
from types import SimpleNamespace

import orjson as json
import pytest

from thegent import dex_cli_helpers, resources, shared_mcp_manager, shell_cli, summary
from thegent import install as install_module
from thegent.compositor.terminal_pane import TerminalPane
from thegent.ux.session_tui import SessionTUI


class _PrintCollector:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def print(self, *args: object, **_kwargs: object) -> None:
        self.messages.append(" ".join(str(arg) for arg in args))


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def _bootstrap_shared_mcp(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_manage = SimpleNamespace(
        mcp_up=lambda: None,
        _get_mcp_url=lambda *_args, **_kwargs: "http://127.0.0.1:3847/mcp",
    )
    monkeypatch.setitem(sys.modules, "thegent.mcp.manage", fake_manage)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, stdout="12345\n", stderr=""),
    )


def test_wl6910_shell_doctor_alias_probe_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
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


def test_wl6910_shell_doctor_alias_probe_subprocess_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _touch(tmp_path / ".zshenv")
    _touch(tmp_path / ".zsh_bundle.zsh")
    monkeypatch.setattr(shell_cli.Path, "home", lambda: tmp_path)

    def _raise_subprocess_error(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.SubprocessError("bad alias command")

    monkeypatch.setattr(shell_cli.subprocess, "run", _raise_subprocess_error)
    collector = _PrintCollector()
    monkeypatch.setattr(shell_cli, "console", collector)

    shell_cli.shell_doctor(fix=False)

    assert any("Alias probe unavailable" in message and "subprocess error" in message for message in collector.messages)


def test_wl6910_shell_doctor_alias_probe_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
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


def test_wl6911_parse_log_entry_valid_payload() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)
    stats = summary.LogParseStats()

    row = json.dumps(
        {
            "type": "assistant",
            "timestamp": "2026-01-10T10:00:00+00:00",
            "message": {"content": "ok"},
        }
    ).decode()
    parsed = summary._parse_log_entry(row, start, end, stats)

    assert parsed is not None
    assert stats.malformed_json == 0


def test_wl6911_parse_log_entry_malformed_json() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)
    stats = summary.LogParseStats()

    parsed = summary._parse_log_entry("not-json", start, end, stats)

    assert parsed is None
    assert stats.malformed_json == 1


def test_wl6911_parse_log_entry_invalid_timestamp() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)
    stats = summary.LogParseStats()

    row = json.dumps({"type": "assistant", "timestamp": "not-a-time", "message": {"content": "bad"}}).decode()
    parsed = summary._parse_log_entry(row, start, end, stats)

    assert parsed is None
    assert stats.invalid_timestamp == 1


def test_wl6912_read_log_file_readable(tmp_path: Path) -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)
    log_file = tmp_path / "ok.jsonl"
    log_file.write_text(
        json.dumps(
            {
                "type": "user",
                "timestamp": "2026-01-12T09:00:00+00:00",
                "message": {"content": "hello"},
            }
        ).decode()
        + "\n",
        encoding="utf-8",
    )

    payload = summary._read_log_file(log_file, start, end, include_diagnostics=True)

    assert payload["status"] == "ok"
    assert payload["entries"] == 1


def test_wl6912_read_log_file_with_malformed_and_valid_records(tmp_path: Path) -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)
    log_file = tmp_path / "mixed.jsonl"
    log_file.write_text(
        "\n".join(
            [
                "not-json",
                json.dumps(
                    {
                        "type": "assistant",
                        "timestamp": "2026-01-10T10:00:00+00:00",
                        "message": {"content": "ok"},
                    }
                ),
                json.dumps({"type": "assistant", "timestamp": "bad"}).decode(),
                json.dumps(
                    {
                        "type": "system",
                        "timestamp": "2026-01-10T10:00:00+00:00",
                        "message": {"content": "skip"},
                    }
                ),
                json.dumps(
                    {
                        "type": "user",
                        "timestamp": "2026-01-10T10:01:00+00:00",
                        "message": {"content": "valid"},
                    }
                ).decode(),
            ]
        ),
        encoding="utf-8",
    )

    payload = summary._read_log_file(log_file, start, end, include_diagnostics=True)

    assert payload["status"] == "ok"
    assert payload["entries"] == 2
    parse_counts = payload["parse_counts"]
    assert parse_counts["malformed_json"] == 1
    assert parse_counts["invalid_timestamp"] == 1
    assert parse_counts["unsupported_type"] == 1
    assert any("malformed_json" in sample for sample in parse_counts["sampled_errors"])
    assert any("unsupported_type" in sample for sample in parse_counts["sampled_errors"])


def test_wl6912_read_log_file_missing_file(tmp_path: Path) -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)

    payload = summary._read_log_file(tmp_path / "missing.jsonl", start, end, include_diagnostics=True)

    assert payload["status"] == "missing"
    assert payload["error"]["type"] == "FileNotFoundError"


def test_wl6912_read_log_file_permission_denied(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)
    path = tmp_path / "denied.jsonl"
    path.write_text("", encoding="utf-8")
    original_open = Path.open

    def _deny(self: Path, *args: object, **kwargs: object):
        if self == path:
            raise PermissionError("denied")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", _deny)

    payload = summary._read_log_file(path, start, end, include_diagnostics=True)

    assert payload["status"] == "permission_denied"
    assert payload["error"]["type"] == "PermissionError"


def test_wl6913_get_thegent_root_installed_package_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pkg_dir = tmp_path / "site-packages" / "thegent"
    (pkg_dir / "hooks").mkdir(parents=True)
    module = SimpleNamespace(__file__=str(pkg_dir / "__init__.py"))
    monkeypatch.setattr(install_module, "import_module", lambda _name: module)

    root = install_module._get_thegent_root()

    assert root == pkg_dir


def test_wl6913_get_thegent_root_import_failure_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        install_module,
        "import_module",
        lambda _name: (_ for _ in ()).throw(ModuleNotFoundError("no pkg")),
    )

    root = install_module._get_thegent_root()

    assert root == Path(install_module.__file__).resolve().parent.parent.parent


def test_wl6913_get_thegent_root_path_failure_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = SimpleNamespace(__file__=object())
    monkeypatch.setattr(install_module, "import_module", lambda _name: module)

    root = install_module._get_thegent_root()

    assert root == Path(install_module.__file__).resolve().parent.parent.parent


def test_wl6914_shared_mcp_stale_lockfile_cleanup_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(shared_mcp_manager.Path, "home", lambda: tmp_path)
    _scope, lockfile = shared_mcp_manager.get_server_scope()
    lockfile.write_text(json.dumps({"pid": 424242, "port": 3847}).decode(), encoding="utf-8")
    monkeypatch.setattr(
        shared_mcp_manager.os,
        "kill",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError(ESRCH, "")),
    )
    _bootstrap_shared_mcp(monkeypatch)

    is_new, url = shared_mcp_manager.ensure_shared_mcp_server()

    assert is_new is True
    assert url == "http://127.0.0.1:3847/mcp"


def test_wl6914_shared_mcp_invalid_lockfile_content_cleanup_then_start(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(shared_mcp_manager.Path, "home", lambda: tmp_path)
    _scope, lockfile = shared_mcp_manager.get_server_scope()
    lockfile.write_text("{ bad json", encoding="utf-8")
    _bootstrap_shared_mcp(monkeypatch)

    is_new, url = shared_mcp_manager.ensure_shared_mcp_server()

    assert is_new is True
    assert url == "http://127.0.0.1:3847/mcp"
    data = json.loads(lockfile.read_text(encoding="utf-8"))
    assert data["port"] == 3847


def test_wl6914_shared_mcp_unlink_failure_is_explicit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(shared_mcp_manager.Path, "home", lambda: tmp_path)
    _scope, lockfile = shared_mcp_manager.get_server_scope()
    lockfile.write_text("{ bad json", encoding="utf-8")
    original_unlink = Path.unlink

    def _deny_unlink(self: Path, *args: object, **kwargs: object) -> None:
        if self == lockfile:
            raise PermissionError("no unlink")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", _deny_unlink)

    is_new, message = shared_mcp_manager.ensure_shared_mcp_server()

    assert is_new is False
    assert "Failed to remove corrupt lockfile" in (message or "")


def test_wl6915_extract_dex_command_args_normal() -> None:
    args = dex_cli_helpers.extract_dex_command_args(["python", "-m", "thegent", "dex", "--model", "x"])
    assert args == ["--model", "x"]


def test_wl6915_extract_dex_command_args_no_token() -> None:
    args = dex_cli_helpers.extract_dex_command_args(["python", "-m", "thegent"])
    assert args == []


def test_wl6915_extract_dex_command_args_invalid_entry() -> None:
    with pytest.raises(TypeError):
        dex_cli_helpers.extract_dex_command_args(["python", 42, "dex"])  # type: ignore[list-item]


def test_wl6917_session_tui_valid_meta_lookup(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    tui = SessionTUI()
    meta_path = tmp_path / "session.meta.json"

    with (
        pytest.MonkeyPatch.context() as mp,
    ):
        mp.setattr(
            "thegent.ux.session_tui.session_meta_impl",
            lambda _sid: {"pid": 10, "status": "running"},
        )
        mp.setattr(SessionTUI, "_get_subagents_for_session", lambda self, _sid: [])
        mp.setattr(
            "thegent.ux.session_tui._find_session_meta",
            lambda _settings, _sid: meta_path,
        )
        details = tui._get_session_details("sess-ok")

    assert "log_paths" in details
    assert details.get("degraded") is not True


def test_wl6917_session_tui_missing_meta_sets_diagnostic() -> None:
    tui = SessionTUI()

    with (
        pytest.MonkeyPatch.context() as mp,
    ):
        mp.setattr(
            "thegent.ux.session_tui.session_meta_impl",
            lambda _sid: {"pid": 0, "status": "exited"},
        )
        mp.setattr(SessionTUI, "_get_subagents_for_session", lambda self, _sid: [])
        mp.setattr(
            "thegent.ux.session_tui._find_session_meta",
            lambda _settings, _sid: (_ for _ in ()).throw(FileNotFoundError("missing")),
        )
        details = tui._get_session_details("sess-missing")

    assert details.get("degraded") is True
    assert details["diagnostics"]["log_paths"]["failure_type"] == "meta_missing"


def test_wl6917_session_tui_path_error_sets_diagnostic() -> None:
    tui = SessionTUI()

    with (
        pytest.MonkeyPatch.context() as mp,
    ):
        mp.setattr(
            "thegent.ux.session_tui.session_meta_impl",
            lambda _sid: {"pid": 0, "status": "exited"},
        )
        mp.setattr(SessionTUI, "_get_subagents_for_session", lambda self, _sid: [])
        mp.setattr(
            "thegent.ux.session_tui._find_session_meta",
            lambda _settings, _sid: (_ for _ in ()).throw(ValueError("bad path")),
        )
        details = tui._get_session_details("sess-path")

    assert details.get("degraded") is True
    assert details["diagnostics"]["log_paths"]["failure_type"] == "path_resolution_error"


def test_wl6918_get_resource_path_dev_tree_discovery(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import thegent.config as config_module

    dev_file = tmp_path / "src" / "thegent" / "resources" / "__init__.py"
    dev_file.parent.mkdir(parents=True, exist_ok=True)
    dev_file.write_text("# stub", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    target = tmp_path / "contracts" / "dag.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(resources, "__file__", str(dev_file))
    monkeypatch.setattr(config_module, "ThegentSettings", lambda: SimpleNamespace(dev=False))

    path = resources.get_resource_path("contracts/dag.json")

    assert path == target


def test_wl6918_get_resource_path_non_dev_uses_package(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import thegent.config as config_module

    installed_file = tmp_path / "venv" / "site-packages" / "thegent" / "resources" / "__init__.py"
    installed_file.parent.mkdir(parents=True, exist_ok=True)
    installed_file.write_text("# stub", encoding="utf-8")
    packaged = tmp_path / "pkg" / "contracts" / "dag.json"
    packaged.parent.mkdir(parents=True, exist_ok=True)
    packaged.write_text("{}", encoding="utf-8")

    @contextlib.contextmanager
    def _fake_pkg_path(_package: str, _resource: str):
        yield packaged

    monkeypatch.setattr(resources, "__file__", str(installed_file))
    monkeypatch.setattr(config_module, "ThegentSettings", lambda: SimpleNamespace(dev=False))
    monkeypatch.setattr(resources.pkg_resources, "path", _fake_pkg_path)

    path = resources.get_resource_path("contracts/dag.json")

    assert path == packaged


def test_wl6918_get_resource_path_path_detection_error_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import thegent.config as config_module

    def _boom_resolve(self: Path) -> Path:
        raise RuntimeError("resolve failed")

    monkeypatch.setattr(resources.Path, "resolve", _boom_resolve)
    monkeypatch.setattr(config_module, "ThegentSettings", lambda: SimpleNamespace(dev=False))
    monkeypatch.setattr(
        resources.pkg_resources,
        "path",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(FileNotFoundError("no pkg")),
    )

    path = resources.get_resource_path("contracts/dag.json")

    assert path == Path(resources.__file__).parent.parent / "contracts/dag.json"


class _FakeProcess:
    def __init__(
        self,
        *,
        timeout_on_wait: bool = False,
        terminate_error: BaseException | None = None,
    ) -> None:
        self._timeout_on_wait = timeout_on_wait
        self._terminate_error = terminate_error
        self.terminated = False
        self.killed = False

    def poll(self) -> None:
        return None

    def terminate(self) -> None:
        if self._terminate_error is not None:
            raise self._terminate_error
        self.terminated = True

    def wait(self, timeout: float | None = None) -> int:
        if self._timeout_on_wait:
            raise subprocess.TimeoutExpired(cmd=["shell"], timeout=timeout)
        return 0

    def kill(self) -> None:
        self.killed = True


def test_wl6919_terminal_pane_cleanup_graceful_termination() -> None:
    pane = TerminalPane("pane-1", ".")
    pane.process = _FakeProcess()

    pane.cleanup()

    assert pane.process is None
    assert pane.is_active is False
    assert pane.last_cleanup_diagnostic is None


def test_wl6919_terminal_pane_cleanup_timeout_kill_path() -> None:
    pane = TerminalPane("pane-2", ".")
    fake_process = _FakeProcess(timeout_on_wait=True)
    pane.process = fake_process

    pane.cleanup()

    assert fake_process.killed is True
    assert pane.process is None


def test_wl6919_terminal_pane_cleanup_records_exceptions() -> None:
    pane = TerminalPane("pane-3", ".")
    pane.process = _FakeProcess(terminate_error=OSError("terminate denied"))

    pane.cleanup()

    assert pane.process is None
    assert pane.last_cleanup_diagnostic is not None
    assert pane.last_cleanup_diagnostic["failure_type"] == "terminate_failed"
