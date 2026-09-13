from __future__ import annotations

from thegent.cli.commands import impl


def test_wl125_new_session_id_wrapper_delegates(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(*, agent: str | None, owner: str) -> str:
        captured["agent"] = agent
        captured["owner"] = owner
        return "session-from-helper"

    monkeypatch.setattr("thegent.cli.commands.impl.session_id_helpers.new_session_id", _fake)

    session_id = impl._new_session_id("codex", "operator:repo")

    assert session_id == "session-from-helper"
    assert captured == {"agent": "codex", "owner": "operator:repo"}
