from __future__ import annotations

from thegent.cli.commands import cli, infra_cmds


def test_recover_status_wrapper_delegates_to_extracted_module(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(*, console) -> None:
        captured["console"] = console

    monkeypatch.setattr("thegent.cli.commands.recovery_commands.recover_status_cmd", _fake)

    cli.recover_status_cmd()

    assert captured["console"] is cli.recover_status_cmd.__globals__["console"]


def test_forensics_snapshot_wrapper_delegates_to_extracted_module(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(*, run_id, phase, console) -> None:
        captured.update({"run_id": run_id, "phase": phase, "console": console})

    monkeypatch.setattr("thegent.cli.commands.recovery_commands.forensics_snapshot_cmd", _fake)

    cli.forensics_snapshot_cmd(run_id="run-123", phase="build")

    assert captured["run_id"] == "run-123"
    assert captured["phase"] == "build"
    assert captured["console"] is cli.forensics_snapshot_cmd.__globals__["console"]


def test_infra_recover_status_wrapper_delegates_to_extracted_module(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(*, console) -> None:
        captured["console"] = console

    monkeypatch.setattr("thegent.cli.commands.recovery_commands.recover_status_cmd", _fake)

    infra_cmds.recover_status_cmd()

    assert captured["console"] is infra_cmds.recover_status_cmd.__globals__["console"]


def test_infra_forensics_snapshot_wrapper_delegates_to_extracted_module(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(*, run_id, phase, console) -> None:
        captured.update({"run_id": run_id, "phase": phase, "console": console})

    monkeypatch.setattr("thegent.cli.commands.recovery_commands.forensics_snapshot_cmd", _fake)

    infra_cmds.forensics_snapshot_cmd(run_id="run-123", phase="build")

    assert captured["run_id"] == "run-123"
    assert captured["phase"] == "build"
    assert captured["console"] is infra_cmds.forensics_snapshot_cmd.__globals__["console"]
