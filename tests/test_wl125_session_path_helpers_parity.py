from __future__ import annotations

from pathlib import Path

from thegent.cli.commands import impl


def test_wl125_session_paths_wrapper_delegates(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(*, base: Path, session_id: str) -> dict[str, Path]:
        captured["base"] = base
        captured["session_id"] = session_id
        return {"meta": base / "x.json"}

    monkeypatch.setattr("thegent.cli.commands.impl.session_path_helpers.session_paths", _fake)

    base = Path("/tmp/wl125")
    output = impl._session_paths(base, "sess-1")

    assert output == {"meta": base / "x.json"}
    assert captured["base"] == base
    assert captured["session_id"] == "sess-1"
