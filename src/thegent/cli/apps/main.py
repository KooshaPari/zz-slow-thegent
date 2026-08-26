"""Main CLI application entry point.

This module provides the main Typer application that serves as the
entry point for the thegent CLI.

Phase 3/4 hardening lane: ``run`` is mounted as a Typer sub-app
(see ``thegent.cli.apps.run_app``) so the contract test surface in
``tests/test_unit_cli_session.py`` (which exercises
``run agent``/``run stop``/``run ps``/``run logs`` subcommands) and
the model-first contract test in ``tests/test_unit_cli.py`` (which
exercises ``run -M <model> -P <provider> <prompt>``) can both be
served from a single root command.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    help="thegent - Unified agent orchestration CLI for Factory skills, droids, and multi-agent workflows.",
    invoke_without_command=True,
)


@app.callback()
def main_callback(
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit"),
) -> None:
    """Main callback for the thegent CLI."""
    if version:
        typer.echo("thegent version 0.1.0")
        raise typer.Exit()


# ---------------------------------------------------------------------------
# Phase 3/4 hardening lane: bg / status / ps / resume flat commands
# ---------------------------------------------------------------------------
#
# These flat commands satisfy the contract tests in
# ``tests/test_unit_cli.py`` and ``tests/test_unit_cli_session.py``.
# They wrap the canonical ``thegent.cli.commands.cli.*`` functions so
# the test mocks at that import path continue to work.


def _resolve_session_dir() -> Path:
    """Resolve the session directory from the ``THGENT_SESSION_DIR`` env var.

    Mirrors the helper inside ``thegent.cli.commands._cli_shared``
    without creating a new dependency edge from the root app into the
    shared module (which itself imports the full ``thegent`` surface).
    """
    base = os.environ.get("THGENT_SESSION_DIR", "/tmp/thegent/sessions")
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    return p


@app.command("bg", help="Run an agent in the background.")
def bg_cmd(
    prompt: str = typer.Argument(..., help="The prompt to send to the agent"),
    agent: str = typer.Argument("claude", help="Agent identifier (cursor-agent, claude, ...)."),
    cd: str | None = typer.Option(None, "--cd", help="Working directory."),
    owner: str | None = typer.Option(None, "--owner", help="Owner tag."),
) -> None:
    """Spawn an agent subprocess and register session metadata.

    The metadata file (``<session_dir>/<owner>/<sid>.json``) carries
    the session_id, agent, owner, and pid so follow-up commands
    (``status``, ``stop``, ``logs``, ``ps``) can locate the session.
    """
    session_dir = _resolve_session_dir()
    owner_tag = owner or "default"
    owner_dir = session_dir / owner_tag.replace(":", "_")
    owner_dir.mkdir(parents=True, exist_ok=True)

    # Generate a stable session id and a process handle.
    import uuid

    sid = uuid.uuid4().hex[:12]
    cwd = cd or os.getcwd()
    cmd = [agent, prompt]
    proc = subprocess.Popen(cmd, cwd=cwd)

    meta = {
        "session_id": sid,
        "agent": agent,
        "owner": owner_tag,
        "pid": proc.pid,
        "prompt": prompt,
        "cwd": cwd,
    }
    meta_path = owner_dir / f"{sid}.json"
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    typer.echo(json.dumps({"session_id": sid, "pid": proc.pid, "owner": owner_tag, "agent": agent}))


@app.command("status", help="Show status of a session.")
def status_cmd(
    session_id: str = typer.Argument(..., help="Session ID to check"),
) -> None:
    """Show session status as JSON.

    Reads ``<THGENT_SESSION_DIR>/<owner>/<session_id>.json`` and the
    matching ``.rc`` exit-code file (if present). Emits a single JSON
    object on stdout with at least ``status`` (e.g. ``"exited:0"``,
    ``"running"``) so downstream tooling can parse the output without
    text-grepping.
    """
    session_dir = _resolve_session_dir()
    meta_path: Path | None = None
    rc_path: Path | None = None

    # Look up the meta file directly, then walk one level deep for the
    # owner-scoped layout (``<session_dir>/<owner>/<sid>.json``).
    direct = session_dir / f"{session_id}.json"
    if direct.exists():
        meta_path = direct
        rc_path = session_dir / f"{session_id}.rc"
    else:
        for child in session_dir.iterdir():
            if not child.is_dir():
                continue
            candidate = child / f"{session_id}.json"
            if candidate.exists():
                meta_path = candidate
                rc_path = child / f"{session_id}.rc"
                break

    if meta_path is None:
        typer.echo(json.dumps({"status": "not_found", "session_id": session_id}))
        raise typer.Exit(1)

    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    status_value = "running"
    if rc_path is not None and rc_path.exists():
        try:
            rc = int(rc_path.read_text(encoding="utf-8").strip())
        except ValueError:
            rc = 0
        status_value = f"exited:{rc}"

    payload = {**meta, "status": status_value}
    typer.echo(json.dumps(payload))


@app.command("stop", help="Stop a running session.")
def stop_cmd(
    session_id: str = typer.Argument(..., help="Session ID to stop"),
    force: bool = typer.Option(False, "--force", "-f", help="Force kill"),
) -> None:
    """Stop a session by delegating to ``cli.stop_cmd``."""
    from thegent.cli.commands.cli import stop_cmd as _impl

    _impl(session_id=session_id, force=force)


@app.command("logs", help="Show logs for a session.")
def logs_cmd(
    session_id: str = typer.Argument(..., help="Session ID"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    tail: int = typer.Option(20, "--tail", "-n", help="Number of lines to show"),
) -> None:
    """Show session logs by delegating to ``cli.logs_cmd``."""
    from thegent.cli.commands.cli import logs_cmd as _impl

    _impl(session_id=session_id, follow=follow, tail=tail)


@app.command("ps", help="List running sessions (delegates to cli.ps_cmd).")
def ps_cmd(
    all: bool = typer.Option(False, "--all", help="Show all sessions."),
    owner: str | None = typer.Option(None, "--owner", help="Filter by owner tag."),
    fmt: str | None = typer.Option(None, "--format", help="Output format."),
    include_contract: bool = typer.Option(False, "--include-contract", help="Include contract."),
) -> None:
    """Flat ``ps`` dispatcher. The ``run ps`` subcommand also reaches ``cli.ps_cmd``."""
    from thegent.cli.commands.cli import ps_cmd as _impl

    _impl(all=all, owner=owner, format=fmt, include_contract=include_contract)


@app.command("resume", help="Resume a paused session (delegates to cli.resume_cmd).")
def resume_cmd(
    session_id: str = typer.Argument("default", help="Session ID to resume."),
) -> None:
    """Flat ``resume`` dispatcher for the contract test surface."""
    from thegent.cli.commands.cli import resume_cmd as _impl

    _impl(session_id=session_id)


# Import sub-apps
from thegent.cli.apps import govern, phench  # noqa: E402

# Phase 3/4 hardening lane: ``run`` sub-app (model-first + agent/stop/ps/logs).
from thegent.cli.apps.run_app import run_app  # noqa: E402

# Phase 3/4 hardening lane: cockpit + traffic + policy pre-check CLI.
# Mounted as a Typer sub-app so `thegent cockpit ...` parses sub-commands
# natively and respects `--help`, exit codes, and error handling.
from thegent.ux.cli_cockpit import app as cockpit_app  # noqa: E402

# Phase 3/4 hardening lane: SOTA audit-replay CLI.
# Adds `thegent sota replay` with multi-format snapshot ingestion
# (json/yaml/toml) and structured report emission (text/json/junitxml)
# so CI pipelines can ingest replay diffs natively.
from thegent.ux.cli_sota import app as sota_app  # noqa: E402

# Phase 3/4 hardening lane: onboarding first-run wizard.
# Adds `thegent init` (interactive + non-interactive + check + verify)
# plus a flat `init` sub-app for the L30 onboarding surface. The
# wizard is idempotent and contract-pinned by
# ``tests/unit/onboarding/test_init_wizard.py``.
from thegent.cli.apps.init_app import init_app  # noqa: E402


@app.command("govern", help="Governance operations.")
def govern_cmd() -> None:
    """Governance operations."""
    govern.app()


@app.command("phench", help="Phenotyperench operations.")
def phench_cmd() -> None:
    """Phenotyperench operations."""
    phench.app()


# Register the ``run`` sub-app so ``thegent run <sub> --flag value`` and
# ``thegent run -M <model> -P <provider> <prompt>`` (model-first) both
# flow through to its native Typer parser with the
# ``invoke_without_command=True`` callback handling the model-first path.
app.add_typer(run_app, name="run")

# Register the cockpit sub-app so `thegent cockpit <sub> --flag value`
# flows through to its native Typer parser.
app.add_typer(cockpit_app, name="cockpit")

# Register the SOTA replay sub-app so `thegent sota replay --batch ... --compare ...`
# flows through to its native Typer parser.
app.add_typer(sota_app, name="sota")

# Register the first-run wizard sub-app so `thegent init`,
# `thegent init check`, and `thegent init verify` all flow through
# to the native Typer parser. Top-level `thegent init` is also
# reachable via the callback above (no_args_is_help=True).
app.add_typer(init_app, name="init")


if __name__ == "__main__":
    app()
