"""Lane B tests for WL-6760..WL-6769 targeted diagnostics hardening."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import httpx
import orjson as json
import pytest

from thegent.agents import cliproxy_manager
from thegent.cli.services import run_guard_helpers
from thegent.config import ThegentSettings
from thegent.cross_project.registry import CrossProjectRegistry
from thegent.execution import get_last_poll_session_messages_meta, poll_session_messages


@pytest.mark.unit
def test_wl6765_fetch_provider_metrics_connection_refused_sets_network_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = httpx.Request("GET", "http://127.0.0.1:8317/v1/metrics/providers")
    monkeypatch.setattr(
        cliproxy_manager.httpx,
        "get",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            httpx.ConnectError("refused", request=request)
        ),
    )

    metrics = cliproxy_manager.fetch_provider_metrics(
        settings=ThegentSettings(cliproxy_port=8317)
    )

    assert metrics is None
    status = cliproxy_manager.get_last_provider_metrics_status()
    assert status["status"] == "network_error"


@pytest.mark.unit
def test_wl6765_fetch_provider_metrics_timeout_sets_timeout_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = httpx.Request("GET", "http://127.0.0.1:8317/v1/metrics/providers")
    monkeypatch.setattr(
        cliproxy_manager.httpx,
        "get",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            httpx.ReadTimeout("timed out", request=request)
        ),
    )

    metrics = cliproxy_manager.fetch_provider_metrics(
        settings=ThegentSettings(cliproxy_port=8317)
    )

    assert metrics is None
    status = cliproxy_manager.get_last_provider_metrics_status()
    assert status["status"] == "timeout"


@pytest.mark.unit
def test_wl6765_fetch_provider_metrics_invalid_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Resp:
        is_success = True

        def json(self) -> dict[str, dict]:
            raise json.JSONDecodeError("bad", "{", 0)

    monkeypatch.setattr(
        cliproxy_manager.httpx, "get", lambda *_args, **_kwargs: _Resp()
    )

    metrics = cliproxy_manager.fetch_provider_metrics(
        settings=ThegentSettings(cliproxy_port=8317)
    )

    assert metrics is None
    status = cliproxy_manager.get_last_provider_metrics_status()
    assert status["status"] == "invalid_json"


@pytest.mark.unit
def test_wl6765_fetch_provider_metrics_non_dict_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Resp:
        is_success = True

        @staticmethod
        def json() -> list[str]:
            return ["bad"]

    monkeypatch.setattr(
        cliproxy_manager.httpx, "get", lambda *_args, **_kwargs: _Resp()
    )

    metrics = cliproxy_manager.fetch_provider_metrics(
        settings=ThegentSettings(cliproxy_port=8317)
    )

    assert metrics is None
    status = cliproxy_manager.get_last_provider_metrics_status()
    assert status["status"] == "invalid_payload_shape"


@pytest.mark.unit
def test_wl6766_guardrail_import_failure_records_diagnostic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_module = types.ModuleType("thegent.governance.input_guardrails")
    monkeypatch.setitem(sys.modules, "thegent.governance.input_guardrails", fake_module)

    settings = ThegentSettings(input_guardrails_enabled=True)
    result = run_guard_helpers.enforce_input_guardrails(
        settings=settings,
        prompt="hello",
        agent="codex",
        model="gpt-5",
        cwd=Path.cwd(),
        run_id="rid-1",
    )

    assert result is None
    diagnostic = run_guard_helpers.get_last_guardrail_diagnostic()
    assert diagnostic["status"] == "error"
    assert diagnostic["error_type"] == "import_error"


@pytest.mark.unit
def test_wl6766_guardrail_evaluation_failure_records_diagnostic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Guardrails:
        @staticmethod
        def check(*_args: object, **_kwargs: object) -> object:
            raise RuntimeError("boom")

    fake_module = types.ModuleType("thegent.governance.input_guardrails")
    fake_module.guardrails_from_env = lambda: _Guardrails()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "thegent.governance.input_guardrails", fake_module)

    settings = ThegentSettings(input_guardrails_enabled=True)
    result = run_guard_helpers.enforce_input_guardrails(
        settings=settings,
        prompt="hello",
        agent="codex",
        model="gpt-5",
        cwd=Path.cwd(),
        run_id="rid-2",
    )

    assert result is None
    diagnostic = run_guard_helpers.get_last_guardrail_diagnostic()
    assert diagnostic["status"] == "error"
    assert diagnostic["error_type"] == "evaluation_error"


@pytest.mark.unit
def test_wl6767_registry_malformed_json_sets_corrupt_meta(tmp_path: Path) -> None:
    reg_file = tmp_path / "registry.json"
    reg_file.write_text('{"broken":', encoding="utf-8")

    reg = CrossProjectRegistry(registry_path=reg_file)

    assert reg.registry == {}
    assert reg.registry_load_meta["status"] == "corrupt"


@pytest.mark.unit
def test_wl6767_registry_permission_error_sets_unreadable_meta(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    reg_file = tmp_path / "registry.json"
    reg_file.write_text("{}", encoding="utf-8")
    original_read_text = Path.read_text

    def _deny_read(path: Path, *args: object, **kwargs: object) -> str:
        if path == reg_file:
            raise PermissionError("denied")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", _deny_read)

    reg = CrossProjectRegistry(registry_path=reg_file)

    assert reg.registry == {}
    assert reg.registry_load_meta["status"] == "unreadable"


@pytest.mark.unit
def test_wl6769_poll_session_messages_meta_missing_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_impl = types.ModuleType("thegent.cli.commands.impl")
    fake_impl._find_session_meta = lambda _settings, _session_id: (_ for _ in ()).throw(
        FileNotFoundError("missing")
    )
    monkeypatch.setitem(sys.modules, "thegent.cli.commands.impl", fake_impl)

    payload = poll_session_messages("sess-1", include_meta=True)

    assert payload["messages"] == []
    assert payload["meta"]["status"] == "meta_missing"
    assert get_last_poll_session_messages_meta()["status"] == "meta_missing"


@pytest.mark.unit
def test_wl6769_poll_session_messages_unreadable_message_log(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    session_id = "sess-2"
    meta_path = tmp_path / f"{session_id}.meta.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text("{}", encoding="utf-8")

    fake_impl = types.ModuleType("thegent.cli.commands.impl")
    fake_impl._find_session_meta = lambda _settings, _session_id: meta_path
    monkeypatch.setitem(sys.modules, "thegent.cli.commands.impl", fake_impl)

    from thegent import execution as execution_mod

    monkeypatch.setattr(
        execution_mod.MessageRegistry,
        "list_pending",
        lambda _self: (_ for _ in ()).throw(PermissionError("denied")),
    )

    payload = poll_session_messages(session_id, include_meta=True)

    assert payload["messages"] == []
    assert payload["meta"]["status"] == "unreadable_messages"


@pytest.mark.unit
def test_wl6769_poll_session_messages_parser_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    session_id = "sess-3"
    meta_path = tmp_path / f"{session_id}.meta.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text("{}", encoding="utf-8")

    fake_impl = types.ModuleType("thegent.cli.commands.impl")
    fake_impl._find_session_meta = lambda _settings, _session_id: meta_path
    monkeypatch.setitem(sys.modules, "thegent.cli.commands.impl", fake_impl)

    from thegent import execution as execution_mod

    monkeypatch.setattr(
        execution_mod.MessageRegistry,
        "list_pending",
        lambda _self: (_ for _ in ()).throw(ValueError("parse")),
    )

    payload = poll_session_messages(session_id, include_meta=True)

    assert payload["messages"] == []
    assert payload["meta"]["status"] == "parser_failure"


@pytest.mark.unit
def test_wl6769_poll_session_messages_empty_pending_is_ok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    session_id = "sess-4"
    meta_path = tmp_path / f"{session_id}.meta.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text("{}", encoding="utf-8")

    fake_impl = types.ModuleType("thegent.cli.commands.impl")
    fake_impl._find_session_meta = lambda _settings, _session_id: meta_path
    monkeypatch.setitem(sys.modules, "thegent.cli.commands.impl", fake_impl)

    payload = poll_session_messages(session_id, include_meta=True)

    assert payload["messages"] == []
    assert payload["meta"]["status"] == "ok"
    assert payload["meta"]["pending_count"] == 0
