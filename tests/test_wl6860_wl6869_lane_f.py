"""Lane F closeout tests for WL-6860..WL-6869 diagnostics and failure handling."""

from __future__ import annotations

import builtins
import io
import sys
from pathlib import Path
from types import SimpleNamespace

import orjson as json
import pytest

from thegent import (
    cliproxy_models_transform,
    clode_config_isolation,
    config_provider,
    execution,
    thegent_platform,
)
from thegent.execution import (
    ConcurrencyController,
    HandoffManager,
    MessageEntry,
    RunMeta,
    RunRegistry,
)


@pytest.fixture(autouse=True)
def _reset_lane_diagnostics() -> None:
    config_provider.get_last_provider_metadata()
    thegent_platform.reset_platform_detection_diagnostics()
    clode_config_isolation.reset_isolation_diagnostics()
    cliproxy_models_transform.reset_transform_models_diagnostics()
    execution.reset_execution_diagnostics()


def test_wl6860_control_plane_not_configured_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("THGENT_CONTROL_PLANE_URL", raising=False)

    provider = config_provider.get_config_provider()

    metadata = config_provider.get_last_provider_metadata()
    assert isinstance(provider, config_provider.EnvConfigProvider)
    assert metadata["control_plane_configured"] is False
    assert metadata["dependency_missing"] is False


def test_wl6860_control_plane_import_failure_records_metadata(monkeypatch: pytest.MonkeyPatch, caplog) -> None:
    monkeypatch.setenv("THGENT_CONTROL_PLANE_URL", "https://cp.example")
    real_import = builtins.__import__

    def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "thegent.control_plane.client":
            raise ImportError("missing control-plane client")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    provider = config_provider.get_config_provider()

    metadata = config_provider.get_last_provider_metadata()
    assert isinstance(provider, config_provider.EnvConfigProvider)
    assert metadata["control_plane_configured"] is True
    assert metadata["dependency_missing"] is True
    assert metadata["degraded"] is True
    assert "provider import failed" in caplog.text


def test_wl6860_control_plane_success_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("THGENT_CONTROL_PLANE_URL", "https://cp.example")
    fake_module = SimpleNamespace(ControlPlaneConfigProvider=lambda url: {"url": url})
    monkeypatch.setitem(sys.modules, "thegent.control_plane.client", fake_module)

    provider = config_provider.get_config_provider()

    metadata = config_provider.get_last_provider_metadata()
    assert provider["url"] == "https://cp.example"
    assert provider["provider_metadata"]["source"] == "control_plane"
    assert metadata["source"] == "control_plane"
    assert metadata["degraded"] is False


def test_wl6861_detect_platform_reads_proc_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(thegent_platform.platform, "system", lambda: "Linux")
    monkeypatch.setattr(thegent_platform.os.path, "exists", lambda _: True)
    monkeypatch.setattr(builtins, "open", lambda *_args, **_kwargs: io.StringIO("Microsoft WSL"))

    detected = thegent_platform.detect_platform()

    assert detected == thegent_platform.Platform.WSL2


def test_wl6861_detect_platform_proc_read_failure_uses_env_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(thegent_platform.platform, "system", lambda: "Linux")
    monkeypatch.setattr(thegent_platform.os.path, "exists", lambda _: True)

    def _raise_open(*_args: object, **_kwargs: object):
        raise OSError("cannot read")

    monkeypatch.setattr(builtins, "open", _raise_open)
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")

    detected = thegent_platform.detect_platform()
    diagnostics = thegent_platform.get_platform_detection_diagnostics()

    assert detected == thegent_platform.Platform.WSL2
    assert diagnostics["proc_version_read_failures"] == 1
    assert diagnostics["last_proc_version_error_type"] == "OSError"


def test_wl6861_detect_platform_proc_read_failure_linux_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(thegent_platform.platform, "system", lambda: "Linux")
    monkeypatch.setattr(thegent_platform.os.path, "exists", lambda _: True)
    monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)
    monkeypatch.delenv("WSL_INTEROP", raising=False)

    def _raise_open(*_args: object, **_kwargs: object):
        raise OSError("cannot read")

    monkeypatch.setattr(builtins, "open", _raise_open)

    detected = thegent_platform.detect_platform()

    assert detected == thegent_platform.Platform.LINUX


def test_wl6862_settings_copy_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    global_dir = home / ".claude"
    config_dir = tmp_path / "isolated"
    global_dir.mkdir(parents=True)
    config_dir.mkdir(parents=True)
    (global_dir / "settings.json").write_text('{"theme": "light"}', encoding="utf-8")
    monkeypatch.setattr(clode_config_isolation.Path, "home", lambda: home)

    clode_config_isolation.ensure_claude_config_isolation(config_dir)

    diagnostics = clode_config_isolation.get_isolation_diagnostics()
    assert diagnostics["settings_copy"]["status"] == "copied"
    assert (config_dir / "settings.json").exists()


def test_wl6862_settings_copy_malformed_source(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    global_dir = home / ".claude"
    config_dir = tmp_path / "isolated"
    global_dir.mkdir(parents=True)
    config_dir.mkdir(parents=True)
    (global_dir / "settings.json").write_text('{"broken":', encoding="utf-8")
    monkeypatch.setattr(clode_config_isolation.Path, "home", lambda: home)

    clode_config_isolation.ensure_claude_config_isolation(config_dir)

    diagnostics = clode_config_isolation.get_isolation_diagnostics()
    assert diagnostics["settings_copy"]["status"] == "parse_error"
    assert diagnostics["settings_copy"]["error_type"] == "JSONDecodeError"


def test_wl6862_settings_copy_unwritable_target(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    global_dir = home / ".claude"
    config_dir = tmp_path / "isolated"
    global_dir.mkdir(parents=True)
    config_dir.mkdir(parents=True)
    (global_dir / "settings.json").write_text('{"theme":"light"}', encoding="utf-8")
    monkeypatch.setattr(clode_config_isolation.Path, "home", lambda: home)

    original_write = Path.write_text

    def _deny_write(self: Path, *args: object, **kwargs: object):
        if self == config_dir / "settings.json":
            raise PermissionError("denied")
        return original_write(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", _deny_write)

    clode_config_isolation.ensure_claude_config_isolation(config_dir)

    diagnostics = clode_config_isolation.get_isolation_diagnostics()
    assert diagnostics["settings_copy"]["status"] == "write_error"
    assert diagnostics["settings_copy"]["error_type"] == "PermissionError"


def test_wl6863_cleanup_removes_file_target(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    global_dir = home / ".claude"
    config_dir = tmp_path / "isolated"
    global_dir.mkdir(parents=True)
    config_dir.mkdir(parents=True)
    (global_dir / "tooling").write_text("ok", encoding="utf-8")
    (config_dir / "tooling").write_text("stale", encoding="utf-8")
    monkeypatch.setattr(clode_config_isolation.Path, "home", lambda: home)

    clode_config_isolation.ensure_claude_config_isolation(config_dir)

    assert (config_dir / "tooling").is_symlink()


def test_wl6863_cleanup_removes_directory_target(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    global_dir = home / ".claude"
    config_dir = tmp_path / "isolated"
    global_dir.mkdir(parents=True)
    (global_dir / "states").mkdir()
    config_dir.mkdir(parents=True)
    (config_dir / "states").mkdir(parents=True)
    monkeypatch.setattr(clode_config_isolation.Path, "home", lambda: home)

    clode_config_isolation.ensure_claude_config_isolation(config_dir)

    assert (config_dir / "states").is_symlink()


def test_wl6863_cleanup_permission_denied_records_diagnostics(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    global_dir = home / ".claude"
    config_dir = tmp_path / "isolated"
    global_dir.mkdir(parents=True)
    config_dir.mkdir(parents=True)
    (global_dir / "file_a").write_text("ok", encoding="utf-8")
    stale = config_dir / "file_a"
    stale.write_text("stale", encoding="utf-8")
    monkeypatch.setattr(clode_config_isolation.Path, "home", lambda: home)

    original_unlink = Path.unlink

    def _deny_unlink(self: Path, *args: object, **kwargs: object) -> None:
        if self == stale:
            raise PermissionError("no unlink")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", _deny_unlink)

    clode_config_isolation.ensure_claude_config_isolation(config_dir)

    diagnostics = clode_config_isolation.get_isolation_diagnostics()
    cleanup = diagnostics["cleanup"]
    assert cleanup["permission_denied"] == 1
    assert cleanup["failure_count"] == 1


def test_wl6864_transform_success_payload() -> None:
    raw = b'{"data": [{"id": "m1"}], "object": "list"}'

    transformed = cliproxy_models_transform.transform_models_response(raw)

    assert transformed is not None
    parsed = json.loads(transformed[0])
    assert parsed["models"][0]["id"] == "m1"


def test_wl6864_transform_malformed_json_records_diagnostics() -> None:
    transformed = cliproxy_models_transform.transform_models_response(b"not-json")

    diagnostics = cliproxy_models_transform.get_transform_models_diagnostics()
    assert transformed is None
    assert diagnostics["last_failure_type"] == "json_decode_error"


def test_wl6864_transform_wrong_shape_records_diagnostics() -> None:
    transformed = cliproxy_models_transform.transform_models_response(b'{"data": {"id": "m1"}}')

    diagnostics = cliproxy_models_transform.get_transform_models_diagnostics()
    assert transformed is None
    assert diagnostics["last_failure_type"] == "models_not_list"


def _patch_ps_impl(monkeypatch: pytest.MonkeyPatch) -> None:
    from thegent.cli.commands import impl

    monkeypatch.setattr(impl, "ps_impl", lambda all_flag=True: [])


def test_wl6865_optional_module_present(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_ps_impl(monkeypatch)
    controller = ConcurrencyController(Path("/tmp"), max_concurrency=3, use_load_based=True)

    admitted = controller.acquire(run_id="r1", owner="owner")

    diagnostics = execution.get_execution_diagnostics()
    assert isinstance(admitted, bool)
    assert diagnostics["optional_gate_import_failures"] == 0


def test_wl6865_optional_module_missing_logs_once(monkeypatch: pytest.MonkeyPatch, caplog) -> None:
    _patch_ps_impl(monkeypatch)
    real_import = builtins.__import__

    def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "thegent.orchestration.resource.resource_management":
            raise ImportError("missing resource management")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    controller = ConcurrencyController(Path("/tmp"), max_concurrency=3, use_load_based=True)

    controller.acquire(run_id="r1", owner="owner")
    controller.acquire(run_id="r2", owner="owner")

    diagnostics = execution.get_execution_diagnostics()
    assert diagnostics["optional_gate_import_failures"] >= 1
    assert caplog.text.count("Concurrency admission degraded") == 1


def test_wl6866_release_unregister_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_ps_impl(monkeypatch)
    called = {"count": 0}

    class _Monitor:
        def unregister(self, _run_id: str) -> None:
            called["count"] += 1

    import thegent.orchestration.resource.load_based_limits as limits

    monkeypatch.setattr(limits, "get_deadline_monitor", lambda: _Monitor())
    controller = ConcurrencyController(Path("/tmp"), max_concurrency=3, use_load_based=False)

    controller.release(owner="owner", run_id="run-1", elapsed_ms=1.0)

    assert called["count"] == 1


def test_wl6866_release_import_failure_records_diagnostics(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_ps_impl(monkeypatch)
    controller = ConcurrencyController(Path("/tmp"), max_concurrency=3, use_load_based=False)
    real_import = builtins.__import__

    def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "thegent.orchestration.resource.load_based_limits":
            raise ImportError("missing monitor")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    controller.release(owner="owner", run_id="run-1", elapsed_ms=1.0)

    diagnostics = execution.get_execution_diagnostics()["deadline_unregister"]
    assert diagnostics["import_failures"] == 1


def test_wl6866_release_runtime_failure_records_diagnostics(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_ps_impl(monkeypatch)

    class _BrokenMonitor:
        def unregister(self, _run_id: str) -> None:
            raise RuntimeError("broken unregister")

    import thegent.orchestration.resource.load_based_limits as limits

    monkeypatch.setattr(limits, "get_deadline_monitor", lambda: _BrokenMonitor())
    controller = ConcurrencyController(Path("/tmp"), max_concurrency=3, use_load_based=False)

    controller.release(owner="owner", run_id="run-1", elapsed_ms=1.0)

    diagnostics = execution.get_execution_diagnostics()["deadline_unregister"]
    assert diagnostics["runtime_failures"] == 1
    assert diagnostics["last_error_type"] == "RuntimeError"


def test_wl6867_handoff_high_confidence_confirmation(tmp_path: Path) -> None:
    manager = HandoffManager(tmp_path, warning_threshold=0.8, escalation_threshold=0.6)
    snapshot_id = manager.create_snapshot(owner="alice", run_ids=["run-1"])

    ok = manager.confirm_handoff(snapshot_id, incoming_owner="bob", confidence=0.95)

    assert ok is True
    lines = [json.loads(line) for line in manager.path.read_text(encoding="utf-8").splitlines() if line.strip()]
    confirmed = [line for line in lines if line.get("event_type") == "handoff_confirmed"]
    assert confirmed[-1]["confidence_state"] == "high"


def test_wl6867_handoff_low_confidence_logs_escalation(tmp_path: Path) -> None:
    manager = HandoffManager(tmp_path, warning_threshold=0.8, escalation_threshold=0.7)
    snapshot_id = manager.create_snapshot(owner="alice", run_ids=["run-1", "run-2"])

    ok = manager.confirm_handoff(snapshot_id, incoming_owner="bob", confidence=0.5)

    assert ok is True
    lines = [json.loads(line) for line in manager.path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(line.get("event_type") == "handoff_low_confidence_escalation" for line in lines)


def test_wl6867_invalid_snapshot_handling(tmp_path: Path) -> None:
    manager = HandoffManager(tmp_path)

    ok = manager.confirm_handoff("snap_missing", incoming_owner="bob", confidence=0.9)

    assert ok is False
    lines = [json.loads(line) for line in manager.path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines[-1]["event_type"] == "handoff_invalid_snapshot"


def test_wl6868_parse_message_valid_pending() -> None:
    line = MessageEntry(content="hi", status="pending").model_dump_json()

    parsed = execution._parse_message_line(line)

    assert parsed is not None
    assert parsed.status == "pending"


def test_wl6868_parse_message_malformed_records_diagnostics() -> None:
    parsed = execution._parse_message_line("not-json")

    diagnostics = execution.get_execution_diagnostics()["message_parse"]
    assert parsed is None
    assert diagnostics["invalid_rows"] == 1
    assert diagnostics["last_error_type"] in {"ValidationError", "JSONDecodeError"}


def test_wl6868_parse_message_non_pending_records_counter() -> None:
    line = MessageEntry(content="done", status="delivered").model_dump_json()

    parsed = execution._parse_message_line(line)

    diagnostics = execution.get_execution_diagnostics()["message_parse"]
    assert parsed is None
    assert diagnostics["non_pending_rows"] == 1


def test_wl6869_get_last_hash_empty_registry_status(tmp_path: Path) -> None:
    reg = RunRegistry(tmp_path)
    reg.registry_path.unlink(missing_ok=True)

    value = reg._get_last_hash()

    assert value is None
    assert reg.get_last_hash_status()["status"] == "empty_registry"


def test_wl6869_get_last_hash_valid_hash_status(tmp_path: Path) -> None:
    reg = RunRegistry(tmp_path)
    reg.register_start(RunMeta(run_id="run-1", agent="codex", prompt="p", cwd="/tmp", owner="u"))

    value = reg._get_last_hash()

    assert value is not None
    assert reg.get_last_hash_status()["status"] == "ok"


def test_wl6869_get_last_hash_malformed_record_status(tmp_path: Path) -> None:
    reg = RunRegistry(tmp_path)
    reg.registry_path.write_text("{not-json\n", encoding="utf-8")

    value = reg._get_last_hash()

    assert value is None
    assert reg.get_last_hash_status()["status"] == "malformed_record"


def test_wl6869_get_last_hash_io_failure_status(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    reg = RunRegistry(tmp_path)
    reg.registry_path.write_text("{}\n", encoding="utf-8")
    original_open = Path.open

    def _raise_open(self: Path, *args: object, **kwargs: object):
        if self == reg.registry_path:
            raise OSError("cannot read")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", _raise_open)

    value = reg._get_last_hash()

    assert value is None
    assert reg.get_last_hash_status()["status"] == "io_error"
