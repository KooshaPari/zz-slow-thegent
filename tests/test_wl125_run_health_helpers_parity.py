from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from thegent.cli.commands import impl


def test_wl125_hash_health_payload_wrapper_delegates(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(payload):
        captured["payload"] = payload
        return {"algorithm": "sha256", "value": "delegated"}

    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_health_helpers.hash_health_payload", _fake
    )

    payload = {"payload_type": "session_contract_health_gate"}
    result = impl._hash_health_payload(payload)

    assert result == {"algorithm": "sha256", "value": "delegated"}
    assert captured["payload"] == payload


def test_wl125_append_health_snapshot_wrapper_delegates_with_impl_callbacks(
    monkeypatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}
    expected_path = tmp_path / "snapshots.jsonl"

    monkeypatch.setattr(
        "thegent.cli.commands.impl._health_snapshot_log_path", lambda: expected_path
    )
    monkeypatch.setattr(
        "thegent.cli.commands.impl._coerce_issue_types",
        lambda value: ["patched", str(value)],
    )

    def _fake(
        payload, scope_key, *, log_path_resolver, compact_log_fn, coerce_issue_types_fn
    ):
        captured["payload"] = payload
        captured["scope_key"] = scope_key
        captured["resolved_path"] = log_path_resolver()
        captured["coerced"] = coerce_issue_types_fn("x")
        compact_log_fn()

    compact_calls: list[str] = []
    monkeypatch.setattr(
        "thegent.cli.commands.impl._compact_health_snapshot_log",
        lambda: compact_calls.append("called"),
    )
    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_health_helpers.append_health_snapshot", _fake
    )

    payload = {
        "payload_type": "session_contract_health_report",
        "issue_counts": {"A": 1},
    }
    scope_key = {"owner": "dev"}
    impl._append_health_snapshot(payload, scope_key)

    assert captured["payload"] == payload
    assert captured["scope_key"] == scope_key
    assert captured["resolved_path"] == expected_path
    assert captured["coerced"] == ["patched", "x"]
    assert compact_calls == ["called"]


def test_wl125_compact_health_snapshot_log_wrapper_delegates_with_impl_resolvers(
    monkeypatch, tmp_path: Path
) -> None:
    expected_path = tmp_path / "snapshot-log.jsonl"
    monkeypatch.setattr(
        "thegent.cli.commands.impl._health_snapshot_log_path", lambda: expected_path
    )
    monkeypatch.setattr(
        "thegent.cli.commands.impl._health_snapshot_max_lines", lambda: 321
    )
    captured: dict[str, object] = {}

    def _fake(*, log_path_resolver, max_lines_resolver):
        captured["path"] = log_path_resolver()
        captured["max_lines"] = max_lines_resolver()

    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_health_helpers.compact_health_snapshot_log",
        _fake,
    )

    impl._compact_health_snapshot_log()

    assert captured["path"] == expected_path
    assert captured["max_lines"] == 321


def test_wl125_health_snapshot_log_path_wrapper_parity_with_explicit_setting(
    monkeypatch, tmp_path: Path
) -> None:
    configured = tmp_path / "logs" / "health.jsonl"
    fake_settings = SimpleNamespace(
        health_snapshot_path=str(configured), health_snapshot_max_lines=5000
    )
    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_health_helpers.ThegentSettings",
        lambda: fake_settings,
    )

    resolved = impl._health_snapshot_log_path()

    assert resolved == configured
    assert resolved.parent.exists()


def test_wl125_health_snapshot_log_path_wrapper_parity_with_default_home(
    monkeypatch, tmp_path: Path
) -> None:
    fake_settings = SimpleNamespace(
        health_snapshot_path="", health_snapshot_max_lines=5000
    )
    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_health_helpers.ThegentSettings",
        lambda: fake_settings,
    )
    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_health_helpers.Path.home", lambda: tmp_path
    )

    resolved = impl._health_snapshot_log_path()

    assert resolved == tmp_path / ".thegent" / "health-snapshots.jsonl"
    assert resolved.parent.exists()
