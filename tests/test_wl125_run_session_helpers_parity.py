from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace

from thegent.cli.commands import impl
from thegent.cli.services import run_session_helpers


def test_wl125_resolve_agent_model_wrapper_delegates_to_run_session_helpers(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake(*, agent: str, model: str | None, mode: str, settings: object) -> str | None:
        captured["agent"] = agent
        captured["model"] = model
        captured["mode"] = mode
        captured["settings"] = settings
        return "model-from-run-session-helper"

    monkeypatch.setattr("thegent.cli.commands.impl.run_session_helpers.resolve_agent_model", _fake)

    settings = SimpleNamespace(default_codex_model="codex-mini")
    resolved = impl._resolve_agent_model("codex", None, "full", settings)

    assert resolved == "model-from-run-session-helper"
    assert captured == {
        "agent": "codex",
        "model": None,
        "mode": "full",
        "settings": settings,
    }


def test_wl125_session_paths_wrapper_delegates_to_run_session_helpers(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake(*, base: Path, session_id: str) -> dict[str, Path]:
        captured["base"] = base
        captured["session_id"] = session_id
        return {"meta": base / "delegated.json"}

    monkeypatch.setattr("thegent.cli.commands.impl.run_session_helpers.session_paths", _fake)

    base = Path("/tmp/wl125")
    output = impl._session_paths(base, "sess-1")

    assert output == {"meta": base / "delegated.json"}
    assert captured == {"base": base, "session_id": "sess-1"}


def test_wl125_run_session_helpers_path_and_session_id_functional_case(
    tmp_path: Path,
) -> None:
    session_id = run_session_helpers.new_session_id(agent="codex", owner="operator:repo")

    assert re.fullmatch(r"\d{8}T\d{6}Z-codex-p\d+-[0-9a-f]{8}", session_id)

    paths = run_session_helpers.session_paths(base=tmp_path, session_id=session_id)
    assert paths["meta"] == tmp_path / f"{session_id}.json"
    assert paths["stdout"] == tmp_path / f"{session_id}.stdout.log"
    assert paths["stderr"] == tmp_path / f"{session_id}.stderr.log"
    assert paths["rc"] == tmp_path / f"{session_id}.rc"
    assert paths["in"] == tmp_path / f"{session_id}.in"
