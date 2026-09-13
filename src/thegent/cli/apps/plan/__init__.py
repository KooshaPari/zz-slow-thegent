"""Plan Typer app — verify/lint/normalize WORK_STREAM.md and other plan ops.

WL-224/WL-225 contract: registers verify-workstream, lint-workstream,
normalize-workstream commands backed by plan_cmds implementations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from thegent.cli.commands.plan_cmds import (
    plan_lint_workstream_cmd,
    plan_normalize_workstream_cmd,
    plan_verify_workstream_cmd,
)

try:
    from typer import Typer as _TyperClass
except ImportError:  # pragma: no cover - fallback for stubbed test envs
    _TyperClass = None
    app = None
else:
    app = _TyperClass(help="Plan operations: verify/lint/normalize WORK_STREAM.md.")

if app is not None:

    @app.command(
        "verify-workstream",
        help="Verify WORK_STREAM.md invariants (exits 1 on violations).",
    )
    def _verify_workstream(
        cd: Path | None = typer.Option(None, "--cd", help="Project root containing docs/reference/WORK_STREAM.md"),
    ) -> None:
        plan_verify_workstream_cmd(cd=cd)

    @app.command(
        "lint-workstream",
        help="Lint WORK_STREAM.md schema (warnings to stdout, errors exit 1).",
    )
    def _lint_workstream(
        cd: Path | None = typer.Option(None, "--cd", help="Project root containing docs/reference/WORK_STREAM.md"),
    ) -> None:
        plan_lint_workstream_cmd(cd=cd)

    @app.command(
        "normalize-workstream",
        help="Normalize WORK_STREAM.md (idempotent; reports changes).",
    )
    def _normalize_workstream(
        cd: Path | None = typer.Option(None, "--cd", help="Project root containing docs/reference/WORK_STREAM.md"),
    ) -> None:
        plan_normalize_workstream_cmd(cd=cd)


__all__ = ["app"]
