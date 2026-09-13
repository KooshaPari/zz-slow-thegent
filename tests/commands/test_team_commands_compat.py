from __future__ import annotations

from thegent.cli.commands import cli


def test_team_create_wrapper_delegates_to_extracted_module(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(*, name: str, leader: str | None, teammates: str | None, console) -> None:
        captured.update({"name": name, "leader": leader, "teammates": teammates, "console": console})

    monkeypatch.setattr("thegent.cli.commands.team_commands.team_create_cmd", _fake)
    cli.team_create_cmd(name="alpha", leader="codex", teammates="d1,d2")

    assert captured["name"] == "alpha"
    assert captured["leader"] == "codex"
    assert captured["teammates"] == "d1,d2"
    assert captured["console"] is cli.team_create_cmd.__globals__["console"]


def test_team_task_wrappers_delegate_to_extracted_module(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    shared_console = cli.team_task_add_cmd.__globals__["console"]

    def _fake_add(*, team_id: str, title: str, description: str, console) -> None:
        calls.append(("add", f"{team_id}:{title}:{description}:{console is shared_console}"))

    def _fake_list(*, team_id: str, console) -> None:
        calls.append(("list", f"{team_id}:{console is shared_console}"))

    monkeypatch.setattr("thegent.cli.commands.team_commands.team_task_add_cmd", _fake_add)
    monkeypatch.setattr("thegent.cli.commands.team_commands.team_task_list_cmd", _fake_list)

    cli.team_task_add_cmd(team_id="t-1", title="task", description="desc")
    cli.team_task_list_cmd(team_id="t-1")

    assert calls == [("add", "t-1:task:desc:True"), ("list", "t-1:True")]
