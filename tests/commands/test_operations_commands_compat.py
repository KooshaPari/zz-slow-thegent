from __future__ import annotations

from thegent.cli.commands import infra_cmds


def test_infra_operations_wrapper_delegates_to_extracted_module(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(*, format, operation, console) -> None:
        captured["format"] = format
        captured["operation"] = operation
        captured["console"] = console

    monkeypatch.setattr("thegent.cli.commands.operations_commands.operations_cmd", _fake)

    infra_cmds.operations_cmd(format="json", operation="recover")

    assert captured["format"] == "json"
    assert captured["operation"] == "recover"
    assert captured["console"] is infra_cmds.operations_cmd.__globals__["console"]
