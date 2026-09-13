from __future__ import annotations

from thegent.cli.commands import impl


def test_wl125_is_pid_running_wrapper_delegates(monkeypatch) -> None:
    captured = {"pid": None}

    def _fake(pid: int) -> bool:
        captured["pid"] = pid
        return True

    monkeypatch.setattr("thegent.cli.commands.impl.process_helpers.is_pid_running", _fake)

    running = impl._is_pid_running(4242)

    assert running is True
    assert captured["pid"] == 4242
