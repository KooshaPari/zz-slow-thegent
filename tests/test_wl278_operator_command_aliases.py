"""WL-278 operator command aliases tests."""

from typer.testing import CliRunner

import thegent.shell_cli as shell_cli_module
import thegent.terminal_cli as terminal_cli_module

runner = CliRunner()


def test_terminal_ls_alias_invokes_list(monkeypatch) -> None:
    calls: list[bool] = []

    def _fake_list(*, all: bool) -> None:
        calls.append(all)

    monkeypatch.setattr(terminal_cli_module, "list_terminals", _fake_list)
    result = runner.invoke(terminal_cli_module.app, ["ls", "--all"])
    assert result.exit_code == 0
    assert calls == [True]


def test_terminal_snd_alias_invokes_send(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    def _fake_send(*, pane_id: str, text: str) -> None:
        calls.append((pane_id, text))

    monkeypatch.setattr(terminal_cli_module, "send_to_terminal", _fake_send)
    result = runner.invoke(terminal_cli_module.app, ["snd", "%1", "echo hi"])
    assert result.exit_code == 0
    assert calls == [("%1", "echo hi")]


def test_shell_aliases_delegate(monkeypatch) -> None:
    status_called: list[bool] = []
    doctor_called: list[bool] = []

    monkeypatch.setattr(shell_cli_module, "shell_status", lambda: status_called.append(True))
    monkeypatch.setattr(shell_cli_module, "shell_doctor", lambda *, fix=False: doctor_called.append(fix))

    status_result = runner.invoke(shell_cli_module.shell_app, ["stat"])
    doctor_result = runner.invoke(shell_cli_module.shell_app, ["doc", "--fix"])
    assert status_result.exit_code == 0
    assert doctor_result.exit_code == 0
    assert status_called == [True]
    assert doctor_called == [True]
