from __future__ import annotations

from pathlib import Path

import pytest

from thegent.cli.services import work_stream_orchestration as orchestration


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_item_id", "expected"),
    [
        ("WL-1", "WL-1"),
        ("  ~WL-2~  ", "WL-2"),
        ("~~~", ""),
        ("", ""),
    ],
)
def test_normalize_item_id(raw_item_id: str, expected: str) -> None:
    assert orchestration._normalize_item_id(raw_item_id) == expected


@pytest.mark.unit
def test_spawn_next_impl_normalizes_and_dedupes_item_ids(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    spawned_ids: list[str] = []

    monkeypatch.setattr(
        orchestration,
        "do_next_impl",
        lambda **_: {
            "next_items": [
                {"id": "  ~WL-101~  ", "prompt_suggestion": "first"},
                {"id": "WL-101", "prompt_suggestion": "duplicate"},
                {"id": "~~", "prompt_suggestion": "invalid"},
                {"id": "WL-102", "prompt_suggestion": "second"},
            ]
        },
    )
    monkeypatch.setattr(
        "thegent.cli.commands.impl._resolve_cwd",
        lambda cd: Path(cd) if cd is not None else tmp_path,
    )
    monkeypatch.setattr("thegent.cli.commands.impl._default_owner_tag", lambda _: "owner")
    monkeypatch.setattr("thegent.config_provider.get_config_provider", lambda: object())
    monkeypatch.setattr("thegent.discovery.get_current_agent_id", lambda: "agent-1")

    def _fake_bg_impl(*, prompt: str, **kwargs):
        item_id = "WL-101" if prompt == "first" else "WL-102"
        spawned_ids.append(item_id)
        return {"session_id": f"sid-{item_id}"}

    monkeypatch.setattr("thegent.cli.commands.impl.bg_impl", _fake_bg_impl)

    result = orchestration.spawn_next_impl(cd=tmp_path, claim=False, limit=10)

    assert result["count"] == 2
    assert result["errors"] == []
    assert [entry["item_id"] for entry in result["spawned"]] == ["WL-101", "WL-102"]
    assert spawned_ids == ["WL-101", "WL-102"]
