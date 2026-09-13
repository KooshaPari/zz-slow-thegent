"""WL139 — L30 Onboarding ``thegent init`` Typer sub-app.

A thin facade around :func:`thegent.cli.commands.init_cmd.init_impl`
that exposes the wizard via Typer so::

    thegent init                  # first-run wizard (non-interactive default)
    thegent init --interactive    # first-run wizard with banner
    thegent init --check          # dry-run; never writes
    thegent init --profile=ci     # deterministic CI profile
    thegent init --target=...     # point at a different workspace
    thegent init --force          # overwrite existing thegent-shaped tree

The sub-app is mounted on the root CLI via ``add_typer`` from
``thegent.cli.apps.main`` so it appears in ``thegent --help`` next to
the other sub-apps (``run``, ``cockpit``, ``sota``, ``govern``,
``phench``).

@trace ONBOARD-L30-INIT
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from thegent.cli.commands.init_cmd import (
    InitProfile,
    init_impl,
)

# ---------------------------------------------------------------------------
# Sub-app
# ---------------------------------------------------------------------------

init_app = typer.Typer(
    name="init",
    help=(
        "First-run wizard: scaffold the canonical thegent workspace "
        "(config dir, AGENTS pointer, WORK_STREAM.md, onboarding doc). "
        "Idempotent — safe to re-run. Use --check for a dry-run."
    ),
    no_args_is_help=True,
    invoke_without_command=True,
)


def _render(payload: dict, *, json_only: bool) -> None:
    """Render the wizard payload to stdout.

    * ``--json`` paths emit a single JSON line that downstream tooling
      (CI summaries, the cockpit layer-detail pane) can parse.
    * The default path emits the human banner — the same string we
      print in interactive mode.
    """
    if json_only:
        typer.echo(payload["json"])
        return
    typer.echo(payload["banner"])


# ---------------------------------------------------------------------------
# ``init`` default command
# ---------------------------------------------------------------------------


@init_app.callback(invoke_without_command=True)
def init_callback(  # noqa: PLR0913 — Typer parses ~7 options; each one is a single bool / path
    ctx: typer.Context,
    target: Path | None = typer.Option(
        None,
        "--target",
        "-t",
        help="Target workspace (defaults to current working directory).",
    ),
    profile: str = typer.Option(
        InitProfile.DEV.value,
        "--profile",
        "-p",
        help="Init profile: minimal | dev | ci.",
        case_sensitive=False,
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Run interactively (prints the human banner).",
    ),
    non_interactive: bool = typer.Option(
        True,
        "--non-interactive",
        help="Suppress interactive prompts (default).",
    ),
    check: bool = typer.Option(
        False,
        "--check",
        help="Dry-run: preflight + probe + contract only; never writes.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing thegent-shaped files when scaffolding.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit a single JSON payload (CI-friendly).",
    ),
) -> None:
    """First-run wizard: scaffold the canonical thegent workspace."""
    if ctx.invoked_subcommand is not None:
        # Sub-command will handle its own dispatch.
        return

    payload = init_impl(
        target_dir=target,
        profile=profile,
        non_interactive=not interactive,
        check=check,
        force=force,
    )
    _render(payload, json_only=json_output or non_interactive)


# ---------------------------------------------------------------------------
# ``init check`` sub-command — explicit dry-run
# ---------------------------------------------------------------------------


@init_app.command("check", help="Dry-run: preflight + probe + contract only; never writes.")
def init_check(
    target: Path | None = typer.Option(
        None,
        "--target",
        "-t",
        help="Target workspace (defaults to current working directory).",
    ),
    profile: str = typer.Option(
        InitProfile.DEV.value,
        "--profile",
        "-p",
        help="Init profile: minimal | dev | ci.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit a single JSON payload."),
) -> None:
    """Run the wizard in dry-run mode."""
    payload = init_impl(
        target_dir=target,
        profile=profile,
        non_interactive=True,
        check=True,
        force=False,
    )
    _render(payload, json_only=json_output)


# ---------------------------------------------------------------------------
# ``init verify`` — confirm the workspace is still shaped correctly
# ---------------------------------------------------------------------------


@init_app.command("verify", help="Verify a workspace is still thegent-shaped (no writes).")
def init_verify(
    target: Path | None = typer.Option(
        None,
        "--target",
        "-t",
        help="Target workspace (defaults to current working directory).",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit a single JSON payload."),
) -> None:
    """Re-run the wizard in check mode and report the diff vs the live workspace."""
    payload = init_impl(
        target_dir=target,
        profile=InitProfile.DEV.value,
        non_interactive=True,
        check=True,
        force=False,
    )
    payload["verify"] = True
    if json_output:
        typer.echo(json.dumps(payload, sort_keys=True))
        return
    typer.echo(payload["banner"])


__all__ = ["init_app", "init_callback", "init_check", "init_verify"]
