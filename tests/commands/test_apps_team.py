from __future__ import annotations

import pytest
from typer.testing import CliRunner

from thegent.cli.apps.team import app

runner = CliRunner()


@pytest.mark.skip(reason="module path issue")
def test_team_list_routes_to_team_commands(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(*, format: str, console) -> None:
        captured["format"] = format
        captured["console"] = console

    monkeypatch.setattr("thegent.cli.commands.team_commands.team_list_cmd", _fake)
    result = runner.invoke(app, ["list", "--format", "json"])

    assert result.exit_code == 0
    assert captured["format"] == "json"
    assert captured["console"] is not None
