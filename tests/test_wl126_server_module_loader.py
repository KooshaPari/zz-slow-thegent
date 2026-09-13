from __future__ import annotations

from pathlib import Path

import pytest

from thegent.mcp import server as server_module
from thegent.mcp.server_module_loader import load_server_module


def test_wl126_server_module_loader_loads_neighbor_module(tmp_path: Path) -> None:
    server_file = tmp_path / "server.py"
    server_file.write_text("# stub\n", encoding="utf-8")
    neighbor_dir = tmp_path / "server"
    neighbor_dir.mkdir()
    (neighbor_dir / "tool.py").write_text("VALUE = 7\n", encoding="utf-8")

    module = load_server_module(
        server_file=server_file,
        module_filename="tool.py",
        module_import_name="tmp.server.tool",
        failure_message="unable",
    )

    assert module.VALUE == 7


def test_wl126_server_module_loader_raises_clear_error_on_missing_module(
    tmp_path: Path,
) -> None:
    server_file = tmp_path / "server.py"
    server_file.write_text("# stub\n", encoding="utf-8")

    with pytest.raises(RuntimeError) as excinfo:
        load_server_module(
            server_file=server_file,
            module_filename="missing.py",
            module_import_name="tmp.server.missing",
            failure_message="unable to load helper module",
        )

    assert "unable to load helper module" in str(excinfo.value)
    assert "missing.py" in str(excinfo.value)


def test_wl126_server_loader_wrapper_delegates_for_prompt_and_handoff(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake(
        *,
        server_file: Path,
        module_filename: str,
        module_import_name: str,
        failure_message: str,
    ) -> object:
        captured["server_file"] = server_file
        captured["module_filename"] = module_filename
        captured["module_import_name"] = module_import_name
        captured["failure_message"] = failure_message
        return {"ok": True}

    monkeypatch.setattr(server_module, "_load_server_module_shared", _fake)

    result = server_module._load_server_tools_prompt_and_handoff_module()

    assert result == {"ok": True}
    assert captured["module_filename"] == "tools_prompt_and_handoff.py"
    assert (
        captured["module_import_name"] == "thegent.mcp._server_tools_prompt_and_handoff"
    )
    assert captured["failure_message"] == "Unable to load prompt/handoff tool wrappers"


def test_wl126_server_loader_wrapper_delegates_for_locking_planning(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake(
        *,
        server_file: Path,
        module_filename: str,
        module_import_name: str,
        failure_message: str,
    ) -> object:
        captured["server_file"] = server_file
        captured["module_filename"] = module_filename
        captured["module_import_name"] = module_import_name
        captured["failure_message"] = failure_message
        return {"ok": True}

    monkeypatch.setattr(server_module, "_load_server_module_shared", _fake)

    result = server_module._load_server_tools_locking_planning_module()

    assert result == {"ok": True}
    assert captured["module_filename"] == "tools_locking_planning.py"
    assert (
        captured["module_import_name"] == "thegent.mcp._server_tools_locking_planning"
    )
    assert captured["failure_message"] == "Unable to load locking/planning tool helpers"


def test_wl126_server_loader_wrapper_delegates_for_planning(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(
        *,
        server_file: Path,
        module_filename: str,
        module_import_name: str,
        failure_message: str,
    ) -> object:
        captured["server_file"] = server_file
        captured["module_filename"] = module_filename
        captured["module_import_name"] = module_import_name
        captured["failure_message"] = failure_message
        return {"ok": True}

    monkeypatch.setattr(server_module, "_load_server_module_shared", _fake)

    result = server_module._load_server_tools_planning_module()

    assert result == {"ok": True}
    assert captured["module_filename"] == "tools_planning.py"
    assert captured["module_import_name"] == "thegent.mcp._server_tools_planning"
    assert captured["failure_message"] == "Unable to load planning tool helpers"


def test_wl126_server_loader_wrapper_delegates_for_queue(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(
        *,
        server_file: Path,
        module_filename: str,
        module_import_name: str,
        failure_message: str,
    ) -> object:
        captured["server_file"] = server_file
        captured["module_filename"] = module_filename
        captured["module_import_name"] = module_import_name
        captured["failure_message"] = failure_message
        return {"ok": True}

    monkeypatch.setattr(server_module, "_load_server_module_shared", _fake)

    result = server_module._load_server_tools_queue_module()

    assert result == {"ok": True}
    assert captured["module_filename"] == "tools_queue.py"
    assert captured["module_import_name"] == "thegent.mcp._server_tools_queue"
    assert captured["failure_message"] == "Unable to load queue tool helpers"


def test_wl126_server_loader_wrapper_delegates_for_terminal(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(
        *,
        server_file: Path,
        module_filename: str,
        module_import_name: str,
        failure_message: str,
    ) -> object:
        captured["server_file"] = server_file
        captured["module_filename"] = module_filename
        captured["module_import_name"] = module_import_name
        captured["failure_message"] = failure_message
        return {"ok": True}

    monkeypatch.setattr(server_module, "_load_server_module_shared", _fake)

    result = server_module._load_server_tools_terminal_module()

    assert result == {"ok": True}
    assert captured["module_filename"] == "tools_terminal.py"
    assert captured["module_import_name"] == "thegent.mcp._server_tools_terminal"
    assert captured["failure_message"] == "Unable to load terminal tool helpers"


def test_wl126_server_loader_wrapper_delegates_for_governance(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(
        *,
        server_file: Path,
        module_filename: str,
        module_import_name: str,
        failure_message: str,
    ) -> object:
        captured["server_file"] = server_file
        captured["module_filename"] = module_filename
        captured["module_import_name"] = module_import_name
        captured["failure_message"] = failure_message
        return {"ok": True}

    monkeypatch.setattr(server_module, "_load_server_module_shared", _fake)

    result = server_module._load_server_tools_governance_module()

    assert result == {"ok": True}
    assert captured["module_filename"] == "tools_governance.py"
    assert captured["module_import_name"] == "thegent.mcp._server_tools_governance"
    assert captured["failure_message"] == "Unable to load governance tool helpers"
