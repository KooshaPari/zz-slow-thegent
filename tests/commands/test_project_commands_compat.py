from __future__ import annotations

from thegent.cli.commands import cli


def test_project_register_wrapper_delegates_to_extracted_module(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}

    def _fake(*, path, name, console) -> None:
        captured.update({"path": path, "name": name, "console": console})

    monkeypatch.setattr("thegent.cli.commands.project_commands.project_register_cmd", _fake)
    cli.project_register_cmd(path=tmp_path, name="demo")

    assert captured["path"] == tmp_path
    assert captured["name"] == "demo"
    assert captured["console"] is cli.project_register_cmd.__globals__["console"]


def test_project_list_wrapper_delegates_to_extracted_module(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(*, format, console) -> None:
        captured.update({"format": format, "console": console})

    monkeypatch.setattr("thegent.cli.commands.project_commands.project_list_cmd", _fake)
    cli.project_list_cmd(format="json")

    assert captured["format"] == "json"
    assert captured["console"] is cli.project_list_cmd.__globals__["console"]
