from __future__ import annotations

from datetime import UTC, datetime

import pytest

import thegent.execution_jsonl_parsers as module


@pytest.mark.unit
def test_parse_checkpoint_by_id_uses_native_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Native:
        @staticmethod
        def parse_checkpoint_by_id(line: str, checkpoint_id: str) -> dict[str, str] | None:
            assert line == '{"checkpoint_id":"cp-1","status":"ok"}'
            assert checkpoint_id == "cp-1"
            return {"checkpoint_id": "cp-1", "status": "native"}

    monkeypatch.setattr(module, "_get_native_parser", lambda: _Native())
    parsed = module.parse_checkpoint_by_id('{"checkpoint_id":"cp-1","status":"ok"}', "cp-1")
    assert parsed == {"checkpoint_id": "cp-1", "status": "native"}


@pytest.mark.unit
def test_parse_checkpoint_by_id_falls_back_to_python(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(module, "_get_native_parser", lambda: None)
    parsed = module.parse_checkpoint_by_id('{"checkpoint_id":"cp-2","status":"ok"}', "cp-2")
    assert parsed == {"checkpoint_id": "cp-2", "status": "ok"}


@pytest.mark.unit
def test_parse_dlq_item_uses_native_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Native:
        @staticmethod
        def parse_dlq_item(line: str, status: str | None, run_id: str | None) -> dict[str, str] | None:
            assert line == '{"run_id":"r-1","status":"pending_review"}'
            assert status == "pending_review"
            assert run_id == "r-1"
            return {"run_id": "r-1", "status": "native"}

    monkeypatch.setattr(module, "_get_native_parser", lambda: _Native())
    parsed = module.parse_dlq_item('{"run_id":"r-1","status":"pending_review"}', "pending_review", "r-1")
    assert parsed == {"run_id": "r-1", "status": "native"}


@pytest.mark.unit
def test_parse_dlq_item_falls_back_to_python(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "_get_native_parser", lambda: None)
    parsed = module.parse_dlq_item('{"run_id":"r-2","status":"pending_review"}', "pending_review", "r-2")
    assert parsed == {"run_id": "r-2", "status": "pending_review"}


@pytest.mark.unit
def test_process_dlq_line_updates_expected_shape() -> None:
    original = '{"run_id":"r-3","status":"pending_review"}'
    updated, changed = module.process_dlq_line(original, "r-3", "resolved")
    assert changed is True
    assert '"status": "resolved"' in updated


@pytest.mark.unit
def test_parse_override_unexpired_returns_false_on_invalid_json() -> None:
    now = datetime.now(UTC)
    assert module.parse_override_unexpired("not-json", owner="ops", now=now) is False


@pytest.mark.unit
def test_parse_checkpoint_line_uses_native_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Native:
        @staticmethod
        def parse_checkpoint_line(line: str) -> dict[str, str] | None:
            assert line == '{"checkpoint_id":"cp-9","status":"ok"}'
            return {"checkpoint_id": "cp-9", "status": "native"}

    monkeypatch.setattr(module, "_get_native_parser", lambda: _Native())
    parsed = module.parse_checkpoint_line('{"checkpoint_id":"cp-9","status":"ok"}')
    assert parsed == {"checkpoint_id": "cp-9", "status": "native"}


@pytest.mark.unit
def test_parse_override_unexpired_uses_native_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime.now(UTC)

    class _Native:
        @staticmethod
        def parse_override_unexpired(line: str, owner: str, now_iso: str) -> bool:
            assert line == '{"owner":"ops","expires_at_utc":"2099-01-01T00:00:00+00:00"}'
            assert owner == "ops"
            assert now_iso == now.isoformat()
            return True

    monkeypatch.setattr(module, "_get_native_parser", lambda: _Native())
    parsed = module.parse_override_unexpired(
        '{"owner":"ops","expires_at_utc":"2099-01-01T00:00:00+00:00"}',
        owner="ops",
        now=now,
    )
    assert parsed is True


@pytest.mark.unit
def test_parse_fatigue_line_uses_native_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime.now(UTC)

    class _Native:
        @staticmethod
        def parse_fatigue_line(line: str, now_iso: str, window_s: int) -> int:
            assert line == '{"timestamp":"2026-02-21T00:00:00+00:00"}'
            assert now_iso == now.isoformat()
            assert window_s == 60
            return 1

    monkeypatch.setattr(module, "_get_native_parser", lambda: _Native())
    parsed = module.parse_fatigue_line('{"timestamp":"2026-02-21T00:00:00+00:00"}', now=now, window_s=60)
    assert parsed == 1


@pytest.mark.unit
def test_parse_circuit_failure_uses_native_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime.now(UTC)

    class _Native:
        @staticmethod
        def parse_circuit_failure(
            line: str,
            target: str,
            category: str,
            now_iso: str,
            window_s: int,
        ) -> tuple[int, str | None]:
            assert line == '{"target":"runner","category":"agent","event":"failure"}'
            assert target == "runner"
            assert category == "agent"
            assert now_iso == now.isoformat()
            assert window_s == 300
            return 1, "2026-02-21T00:00:00+00:00"

    monkeypatch.setattr(module, "_get_native_parser", lambda: _Native())
    count, ts = module.parse_circuit_failure(
        '{"target":"runner","category":"agent","event":"failure"}',
        target="runner",
        category="agent",
        now=now,
        window_s=300,
    )
    assert count == 1
    assert ts == datetime.fromisoformat("2026-02-21T00:00:00+00:00")


@pytest.mark.unit
def test_native_python_parity_for_jsonl_helpers_if_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    thegent_parser = pytest.importorskip("thegent_parser")
    required = (
        "parse_checkpoint_by_id",
        "parse_dlq_item",
        "parse_checkpoint_line",
        "parse_override_unexpired",
        "parse_fatigue_line",
        "parse_circuit_failure",
    )
    if any(not hasattr(thegent_parser, name) for name in required):
        pytest.skip("thegent_parser missing required WL-131 helper exports")

    now = datetime(2026, 2, 21, 12, 0, 0, tzinfo=UTC)
    fresh = '{"target":"runner","category":"agent","event":"failure","timestamp":"2026-02-21T11:59:00+00:00"}'
    override = '{"owner":"ops","expires_at_utc":"2026-02-22T00:00:00+00:00"}'
    fatigue = '{"timestamp":"2026-02-21T11:59:30+00:00"}'
    checkpoint = '{"checkpoint_id":"cp-11","status":"ok"}'
    dlq = '{"run_id":"r-11","status":"pending_review"}'

    monkeypatch.setattr(module, "_get_native_parser", lambda: None)
    py_checkpoint = module.parse_checkpoint_by_id(checkpoint, "cp-11")
    py_dlq = module.parse_dlq_item(dlq, "pending_review", "r-11")
    py_checkpoint_line = module.parse_checkpoint_line(checkpoint)
    py_override = module.parse_override_unexpired(override, "ops", now)
    py_fatigue = module.parse_fatigue_line(fatigue, now, 120)
    py_failure = module.parse_circuit_failure(fresh, "runner", "agent", now, 120)

    monkeypatch.setattr(module, "_get_native_parser", lambda: thegent_parser)
    native_checkpoint = module.parse_checkpoint_by_id(checkpoint, "cp-11")
    native_dlq = module.parse_dlq_item(dlq, "pending_review", "r-11")
    native_checkpoint_line = module.parse_checkpoint_line(checkpoint)
    native_override = module.parse_override_unexpired(override, "ops", now)
    native_fatigue = module.parse_fatigue_line(fatigue, now, 120)
    native_failure = module.parse_circuit_failure(fresh, "runner", "agent", now, 120)

    assert native_checkpoint == py_checkpoint
    assert native_dlq == py_dlq
    assert native_checkpoint_line == py_checkpoint_line
    assert native_override == py_override
    assert native_fatigue == py_fatigue
    assert native_failure == py_failure
