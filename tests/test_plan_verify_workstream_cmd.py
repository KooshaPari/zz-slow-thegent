from __future__ import annotations

from pathlib import Path

import pytest
import typer

from thegent.cli.apps.plan import app as plan_app
from thegent.cli.commands import cli as cli_shim
from thegent.cli.commands.plan_cmds import (
    plan_lint_workstream_cmd,
    plan_normalize_workstream_cmd,
    plan_verify_workstream_cmd,
)


def _write_work_stream_with_overlap(base: Path) -> None:
    docs_ref = base / "docs" / "reference"
    docs_ref.mkdir(parents=True, exist_ok=True)
    (docs_ref / "WORK_STREAM.md").write_text(
        "\n".join(
            [
                "# Unified Work Stream",
                "",
                "## CLAIMED",
                "| ID | Agent | Started |",
                "|----|-------|---------|",
                "| wp-1 | agent-1 | 2026-01-01T00:00:00Z |",
                "",
                "## COMPLETED",
                "| ID | Agent | Completed |",
                "|----|-------|-----------|",
                "| wp-1 | agent-1 | 2026-01-02T00:00:00Z |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_plan_app_registers_verify_workstream_command() -> None:
    names = [command.name for command in plan_app.registered_commands]
    assert "verify-workstream" in names
    assert "lint-workstream" in names
    assert "normalize-workstream" in names


def test_cli_shim_exports_plan_verify_workstream_cmd() -> None:
    assert cli_shim.plan_verify_workstream_cmd is plan_verify_workstream_cmd


def test_cli_shim_exports_plan_lint_workstream_cmd() -> None:
    assert cli_shim.plan_lint_workstream_cmd is plan_lint_workstream_cmd


@pytest.mark.requirement("WL-225")
def test_cli_shim_exports_plan_normalize_workstream_cmd() -> None:
    assert cli_shim.plan_normalize_workstream_cmd is plan_normalize_workstream_cmd


@pytest.mark.requirement("WL-224")
def test_plan_verify_workstream_exits_nonzero_on_invariant_violation(
    tmp_path: Path,
) -> None:
    _write_work_stream_with_overlap(tmp_path)
    with pytest.raises(typer.Exit) as exc:
        plan_verify_workstream_cmd(cd=tmp_path)
    assert exc.value.exit_code == 1
