"""Phase 3/4 hardening lane: ``run`` Typer sub-app.

The CLI contract tests in ``tests/test_unit_cli_session.py`` invoke
``thegent run <subcommand>`` patterns:

* ``run agent <prompt> --agent ...`` → dispatch to ``cli.run_cmd``
* ``run stop <session_id>`` → dispatch to ``cli.stop_cmd``
* ``run ps`` → dispatch to ``cli.ps_cmd``
* ``run logs <session_id>`` → dispatch to ``cli.logs_cmd``

The model-first contract test in ``tests/test_unit_cli.py`` invokes
``thegent run -M <model> -P <provider> ... <prompt>`` directly (no
subcommand). To satisfy both contracts, ``run_app`` captures the full
trailing-positional list via ``List[str] = typer.Argument(None)`` and
then manually dispatches: if the first element matches a registered
subcommand name we use ``<cmd>.make_context(...)`` +
``<cmd>.invoke(...)`` to send the rest to that subcommand; otherwise we
treat the list as a single trailing prompt and run the model-first
validation path.

The ``List[str]`` capture pattern (and the manual dispatch) is
necessary because Typer's standard ``invoke_without_command=True``
flow cannot both dispatch ``run agent <prompt>`` (positional
``agent`` consumed as the subcommand) AND accept
``run -M ... <prompt>`` (positional ``prompt`` would otherwise be
interpreted as the subcommand).  The dual contractual surface
``tests/test_unit_cli.py`` (model-first) + ``tests/test_unit_cli_session.py``
(subcommand-first) can only be served from a single Typer root by
bypassing the auto-dispatch and inspecting the trailing arguments
ourselves.

The sub-app is mounted onto the root Typer application via
``add_typer`` so each subcommand preserves its native Typer argument
parsing, ``--help``, exit codes, and error handling.

Subcommand dispatchers are deliberately thin: they re-raise the
underlying ``cli.*`` function exactly so the test mocks at
``thegent.cli.commands.cli.<cmd>`` see the call.  This keeps the
contract test surface stable without coupling the sub-app to the
real implementation logic.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from thegent.ux.cli_errors import exc_text, print_exc

# AUDIT-N+1 (Phase 3/4 sweep lane): every CLI error envelope in
# ``src/thegent/cli/apps/`` must route through ``print_exc`` (or the
# ``exc_text`` escape helper for non-Rich ``typer.echo`` paths) so a
# malicious or buggy exception payload containing Rich markup
# (``[red]…[/red]``) cannot inject colour into an operator terminal.
# ``run_app`` uses a stderr-backed Rich ``Console`` so we get the
# same end-to-end render-safety contract that ``govern`` already has.
err_console = Console(stderr=True)

# Re-export the canonical command functions from ``cli`` so the sub-app
# dispatches to them via the same import path the contract tests mock.
from thegent.cli.commands import cli as _cli

run_app = typer.Typer(
    name="run",
    help=(
        "Run subcommands: agent (foreground), stop, ps (status/wait/pause), "
        "logs (inspect). With no subcommand, performs a model-first prompt "
        "(e.g. ``run -M gpt-4o -P openai prompt``)."
    ),
    invoke_without_command=True,
    no_args_is_help=False,
)

# Names of registered Typer subcommands (populated below at import time
# once the @run_app.command(...) decorators run).  Used by the callback
# to decide whether to forward to a subcommand or run model-first.
_SUBCOMMANDS: set[str] = {"agent", "stop", "ps", "logs"}


def _safe_model_unavailable_line(model: object, provider: object, suffix: str) -> str:
    """Build the AUDIT-N+3-safe ``Model '…' not available via provider '…' …`` line.

    The user-controlled ``model`` and ``provider`` segments are
    routed through :func:`thegent.ux.cli_errors.exc_text` so a
    malicious or buggy value containing Rich markup
    (``[red]…[/red]``) cannot inject colour tags into the
    operator's terminal. The literal ``'…'`` quoting around each
    value is preserved (those characters are part of the trusted
    envelope literal, not user data).

    ``suffix`` is the pre-computed ``" Available: …. "`` line —
    the comma-joined ``provider`` list comes from the in-process
    model catalog (typed ``str``) but ``suffix`` still routes
    through :func:`exc_text` so a future refactor that injects
    additional operator-controlled data into the suffix stays
    safe-by-construction.
    """
    return (
        "Model '"
        + exc_text(model)
        + "' not available via provider '"
        + exc_text(provider)
        + "'."
        + exc_text(suffix)
    )


# ---------------------------------------------------------------------------
# No-subcommand callback: dual-path dispatch (subcommand vs model-first)
# ---------------------------------------------------------------------------
@run_app.callback(invoke_without_command=True)
def _run_callback(
    ctx: typer.Context,
    model: str | None = typer.Option(None, "--model", "-M", help="Model to use."),
    provider: str | None = typer.Option(
        None, "--provider", "-P", help="Provider to use."
    ),
    cd: str | None = typer.Option(None, "--cd", help="Working directory."),
    agent: str | None = typer.Option(None, "--agent", "-a", help="Agent identifier."),
    mode: str | None = typer.Option(None, "--mode", help="Run mode."),
    timeout: int | None = typer.Option(None, "--timeout", help="Timeout in seconds."),
    failover: bool = typer.Option(False, "--failover", help="Allow failover."),
    prompts: list[str] | None = typer.Argument(
        None,
        help=(
            "Trailing positional capture. When ``prompts`` has a leading "
            "element matching a registered subcommand name (``agent``, "
            "``stop``, ``ps``, ``logs``), the rest is forwarded to that "
            "subcommand.  Otherwise the full list is treated as the model-"
            "first prompt."
        ),
    ),
) -> None:
    """Default ``run`` handler.

    Two paths:

    1. The first trailing positional matches a registered subcommand
       name (e.g. ``agent``, ``stop``).  We build a sub-context with
       the remaining args and invoke the subcommand directly, fully
       consuming the trailing positionals as we go.
    2. The first trailing positional does NOT match a subcommand.
       We treat the trailing string (joined back together if it has
       multiple words) as the model-first prompt and validate the
       provider/model pairing with a clear ``Available: ...`` error
       when the pairing is invalid.
    """
    if prompts:
        first = prompts[0]
        if first in _SUBCOMMANDS:
            sub_cmd = _cli_subcommands[first]
            sub_ctx = sub_cmd.make_context(
                first,
                prompts[1:],
                parent=ctx,
                resilient_parsing=True,
            )
            try:
                sub_cmd.invoke(sub_ctx)
            finally:
                sub_ctx.close()
            return

    # No registered subcommand was consumed → model-first path.
    if not prompts:
        typer.echo(ctx.get_help())
        raise typer.Exit(2)

    prompt = " ".join(prompts)

    if model and provider:
        # Provider/model validation. Re-use the same route-resolution
        # path as ``run_execution_core_helpers`` so the error message
        # remains stable with the operator-facing CLI.
        try:
            from thegent.models import normalize_model_id
            from thegent.models.catalog import ModelCatalog, resolve_route

            model_id = normalize_model_id(model)
            route = resolve_route(model_id, provider_hint=provider)
            if route is None:
                routes = ModelCatalog.routes_for(model_id)
                available = (
                    ", ".join(sorted({r.provider for r in routes}))
                    if routes
                    else "none"
                )
                suffix = f" Available: {available}." if available != "none" else ""
                # AUDIT-N+3 — route the operator-controlled ``model``
                # and ``provider`` segments through ``exc_text`` so a
                # malicious value containing Rich markup cannot
                # inject colour into the operator's terminal. The
                # literal ``'…'`` quoting around each value is
                # preserved by the helper above.
                typer.echo(_safe_model_unavailable_line(model, provider, suffix))
                raise typer.Exit(1)
        except typer.Exit:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            # AUDIT-N+1: route through ``print_exc`` so a malicious
            # exception payload (``[red]pwned[/red]``) cannot inject
            # Rich markup into the operator's terminal.
            print_exc(err_console, "run: provider validation failed:", exc)
            raise typer.Exit(1) from exc

    # Resolve cwd (best-effort) and dispatch to run_cmd with the
    # resolved kwargs. We deliberately use the canonical command
    # function so contract tests that mock ``thegent.cli.commands.cli.run_cmd``
    # observe the call.
    cwd_path: Path | None = None
    if cd:
        cwd_path = Path(cd).expanduser().resolve()
    _cli.run_cmd(
        prompt=prompt,
        model=model,
        provider=provider,
        cd=str(cwd_path) if cwd_path else None,
        agent=agent,
        mode=mode,
        timeout=timeout,
        failover=failover,
    )


# ---------------------------------------------------------------------------
# Subcommands — registered AFTER the callback so _SUBCOMMANDS plus the
# ``_cli_subcommands`` dispatch table can be populated once.
# ---------------------------------------------------------------------------
def _register_subcommand_table() -> dict[str, click.Command]:
    """Snapshot the registered Typer subcommands after decorator-time binding.

    Typer stores subcommands as ``CommandInfo`` metadata until
    ``typer.main.get_command`` finalizes the ``click.Group`` with the
    real ``click.Command`` objects.  We force that finalization here so
    the callback above can reference the actual subcommand click
    commands via their ``make_context`` / ``invoke`` protocol.
    """
    from typer.main import get_command

    group = get_command(run_app)
    return dict(group.commands.items())


@run_app.command("agent", help="Run an agent with the given prompt (foreground).")
def _agent(
    prompt: str = typer.Argument(..., help="Prompt to send to the agent."),
    agent: str = typer.Option("claude", "--agent", "-a", help="Agent identifier."),
    model: str | None = typer.Option(
        None, "--model", "-M", help="Optional model override."
    ),
    provider: str | None = typer.Option(
        None, "--provider", "-P", help="Optional provider override."
    ),
    cd: str | None = typer.Option(None, "--cd", help="Working directory."),
    mode: str | None = typer.Option(None, "--mode", help="Run mode."),
    timeout: int | None = typer.Option(None, "--timeout", help="Timeout in seconds."),
    live: bool = typer.Option(False, "--live", help="Stream live output."),
    failover: bool = typer.Option(False, "--failover", help="Allow failover."),
    routing: str | None = typer.Option(None, "--routing", help="Routing preference."),
    include_contract: bool = typer.Option(
        False, "--include-contract", help="Include contract."
    ),
    lane: str | None = typer.Option(None, "--lane", help="Lane identifier."),
    confidence: float | None = typer.Option(
        None, "--confidence", help="Confidence threshold."
    ),
    override: str | None = typer.Option(None, "--override", help="Override spec."),
    domain: str | None = typer.Option(None, "--domain", help="Domain filter."),
    bg_flag: bool = typer.Option(False, "--bg", help="Background mode."),
    owner: str | None = typer.Option(None, "--owner", help="Owner tag."),
    continuation: str | None = typer.Option(
        None, "--continuation", help="Continuation token."
    ),
    idempotency_token: str | None = typer.Option(
        None, "--idempotency-token", help="Idempotency token."
    ),
    arbitration: str | None = typer.Option(
        None, "--arbitration", help="Arbitration policy."
    ),
    fmt: str | None = typer.Option(None, "--format", help="Output format."),
) -> None:
    """Dispatch to ``cli.run_cmd`` (or ``cli.bg_cmd`` when ``--bg``)."""
    if bg_flag:
        _cli.bg_cmd(
            prompt=prompt,
            agent=agent,
            model=model,
            provider=provider,
            cd=cd,
            owner=owner,
            mode=mode,
            timeout=timeout,
            live=live,
            failover=failover,
            routing=routing,
            include_contract=include_contract,
            lane=lane,
            confidence=confidence,
            override=override,
            domain=domain,
            continuation=continuation,
            idempotency_token=idempotency_token,
            arbitration=arbitration,
            format=fmt,
        )
        return
    _cli.run_cmd(
        prompt=prompt,
        agent=agent,
        model=model,
        provider=provider,
        cd=cd,
        mode=mode,
        timeout=timeout,
        live=live,
        failover=failover,
        routing=routing,
        include_contract=include_contract,
        lane=lane,
        confidence=confidence,
        override=override,
        domain=domain,
    )


@run_app.command("stop", help="Stop a running session (delegates to cli.stop_cmd).")
def _stop(
    session_id: str = typer.Argument(..., help="Session ID to stop."),
    force: bool = typer.Option(False, "--force", "-f", help="Force kill."),
    wind_down: bool = typer.Option(
        False, "--wind-down", help="Allow graceful shutdown."
    ),
    grace: int = typer.Option(5, "--grace", help="Grace period in seconds."),
) -> None:
    """Dispatch to ``cli.stop_cmd``."""
    _cli.stop_cmd(session_id=session_id, force=force, wind_down=wind_down, grace=grace)


@run_app.command("ps", help="List running sessions (delegates to cli.ps_cmd).")
def _ps(
    all: bool = typer.Option(False, "--all", help="Show all sessions."),
    owner: str | None = typer.Option(None, "--owner", help="Filter by owner tag."),
    fmt: str | None = typer.Option(None, "--format", help="Output format."),
    include_contract: bool = typer.Option(
        False, "--include-contract", help="Include contract."
    ),
) -> None:
    """Dispatch to ``cli.ps_cmd``."""
    _cli.ps_cmd(all=all, owner=owner, format=fmt, include_contract=include_contract)


@run_app.command("logs", help="Show logs for a session (delegates to cli.logs_cmd).")
def _logs(
    session_id: str = typer.Argument(..., help="Session ID."),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow output."),
    tail: int = typer.Option(20, "--tail", "-n", help="Number of lines."),
    timeout: int | None = typer.Option(None, "--timeout", help="Timeout in seconds."),
    stderr: bool = typer.Option(False, "--stderr", help="Include stderr stream."),
    fmt: str | None = typer.Option(None, "--format", help="Output format."),
) -> None:
    """Dispatch to ``cli.logs_cmd``."""
    _cli.logs_cmd(
        session_id=session_id,
        follow=follow,
        tail=tail,
        timeout=timeout,
        stderr=stderr,
        format=fmt,
    )


# Build the dispatch table AFTER all four subcommands are registered so
# the callback's manual ``make_context`` path can resolve them.
_cli_subcommands: dict[str, typer.Typer] = _register_subcommand_table()
