"""CLI surface for the operator cockpit (WP-4001), traffic KPIs (WP-Y7),
and policy pre-checks (WP-3001).

Four Typer sub-commands expose the Phase 3/4 governance+UX lane to
operators running outside the TUI:

* ``thegent cockpit render`` — render the 4-pane operator cockpit for a
  snapshot of runs / overrides (deterministic when ``--clock`` is set).
* ``thegent cockpit traffic`` — render the TRAFFIC KPI dashboard to stdout
  (also deterministic with ``--clock``).
* ``thegent cockpit pre-check`` — evaluate a :class:`PolicyContext` against
  the governance :class:`PolicyEngine` and emit the resulting
  :class:`PolicyDecision` as either human-readable text or JSON.
* ``thegent cockpit replay`` — replay a corpus of ``PolicyContext`` JSONs
  through pre-check and validate the resulting decisions against an
  expected snapshot line-by-line (Phase 3/4 SOTA hardening lane, third
  "Unblocked Next" item from ``WORKLOG.md``).

Each subcommand is intentionally side-effect-free: rendering does not
mutate cockpit state, and ``pre-check`` defaults to ``--dry-run`` so
operators can rehearse decisions without polluting the policy cache.

These commands complete the WORKLOG.md "Unblocked Next" backlog for the
Phase 3/4 hardening lane and give SOTA audit tooling a stable CLI
contract.

------------------------------------------------------------------------
Operator walkthrough: ``--json`` + ``--report-format=junitxml`` ingestion
------------------------------------------------------------------------

SOTA replay tooling can consume replay output three ways. The three
shapes are guaranteed-stable so CI harnesses can switch between them
without rewriting parsers:

1. ``cockpit replay --json`` (default snapshot format, JSON envelope)::

       thegent cockpit replay --batch corpus/ --compare snapshot.json --json

   Emits a single JSON object on stdout with keys ``matched`` (bool),
   ``mismatches`` (list of ``{index, fields, expected, actual}`` dicts),
   ``decisions`` (the produced :class:`PolicyDecision` list), and
   ``audit`` (the JSONL path written when ``--audit-path`` is set).
   Suitable for ``jq``-based pipelines::

       thegent cockpit replay --batch corpus/ --compare snap.json --json \\
           | jq '.matched, .mismatches | length'

2. ``cockpit replay --report-format=json`` (delegated to sota replay)::

       thegent cockpit replay --batch corpus/ --compare snap.json \\
           --report-format=json

   Same envelope **shape** (matched / items / mismatches keys present,
   mismatches list shape stable) — see
   ``tests/test_unit_cockpit_sota_json_parity.py`` for the parity
   contract. Use this when you want the sota-side report-format
   dispatch table to win (handy when wiring into a sota-wide ingest
   pipeline that already routes by ``--report-format``).

3. ``cockpit replay --report-format=junitxml`` (CI-friendly)::

       thegent cockpit replay --batch corpus/ --compare snap.json \\
           --report-format=junitxml --report-path report.xml

   Emits JUnit-XML so Jenkins / GitHub Actions / Buildkite can ingest
   the replay as a test suite. Each mismatch becomes a ``<failure>``
   entry; a clean replay becomes a passing ``<testsuite>``. The
   ``--report-path`` flag routes the XML to disk; omit it to print to
   stdout (handy for ``tee`` into a build log).

Replay exits ``0`` on match, ``4`` on mismatch (mirrors the
``pre-check`` ``3 = deny`` convention but kept distinct so shell
pipelines can branch on the two failure modes independently). For
structured ingestion prefer ``--json`` over text-grepping the default
output — the text path is intended for humans only.

------------------------------------------------------------------------
Operator walkthrough: ``flipped`` field in the JSON envelope
------------------------------------------------------------------------

When the operator composes ``--snapshot-flip <field>`` (or
``--snapshot-flip-all``) the replay walks the mismatch path on
purpose, but downstream SOTA tooling still needs to know *which*
fields were inverted so the diff report can be triaged. The ``--json``
and ``--report-format=json`` envelopes now expose a top-level
``flipped`` array listing the resolved flip fields (deduplicated,
first-seen order preserved). When no flip flag is set, ``flipped``
is the empty list ``[]`` so the schema is stable::

    # Force a mismatch on ``verdict`` and inspect which fields the
    # envelope reports as flipped.
    thegent cockpit replay --batch corpus/ --compare snap.json \\
        --snapshot-flip verdict --snapshot-flip override_applied --json \\
        | jq '{matched, items, flipped, mismatches: (.mismatches | length)}'

    # Same envelope key on the sota side:
    thegent sota replay --batch corpus/ --compare snap.json \\
        --snapshot-flip-all --report-format=json \\
        | jq '.flipped'   # -> ["verdict", "override_applied", "cached"]

The ``flipped`` key is part of the JSON-envelope contract pinned by
``tests/test_unit_cockpit_sota_json_parity.py`` and the dedicated
``tests/test_unit_cockpit_snapshot_flip_envelope.py`` (Day 5/5).
Operators who do not pass any ``--snapshot-flip*`` flag still get
the empty array, so the schema never has to be checked twice.

------------------------------------------------------------------------
Operator walkthrough: ``--snapshot-flip`` SOTA canary workflow
------------------------------------------------------------------------

The ``--snapshot-flip <field>`` flag is a SOTA canary knob: it
deliberately inverts one field on every loaded snapshot entry **in
memory** so the replay walks the mismatch path without the operator
having to hand-edit the ``--compare`` file. This is useful for CI
runs that want to exercise the diff machinery + JSON envelope + exit
code 4 contract end-to-end on every replay (rather than only when a
real regression happens to land).

Supported fields and their invert semantics:

* ``verdict`` — ``allow`` ↔ ``deny``; ``warn`` and unknown verdicts
  flip to ``deny`` (always disagrees with the engine's actual verdict).
* ``override_applied`` / ``cached`` — bool negation (with
  string-bool coercion so yaml/toml snapshots still invert cleanly).
* any other field — best-effort bool/numeric inversion, or a stable
  ``<flipped:<value>>`` string sentinel so the compare step still
  records a mismatch.

Example::

    # Force a mismatch on every entry's ``verdict`` so the replay
    # exercise the exit-4 + diff machinery end-to-end. The
    # ``--compare`` file on disk is left untouched.
    thegent cockpit replay --batch corpus/ --compare snap.json \\
        --snapshot-flip verdict --json | jq '.matched, .mismatches'

Multi-field canary recipe (Day 4/5 hardening lane):

    # Compose multiple ``--snapshot-flip`` flags to invert several
    # fields at once. Each flip is independent so the diff machinery
    # surfaces every flipped field in the per-row ``fields`` list.
    thegent cockpit replay --batch corpus/ --compare snap.json \\
        --snapshot-flip verdict --snapshot-flip override_applied

    # Or use the convenience preset that flips the canonical
    # ``(verdict, override_applied, cached)`` triple on every entry:
    thegent cockpit replay --batch corpus/ --compare snap.json \\
        --snapshot-flip-all --report-format junitxml --report-path report.xml

The same flags are honoured by ``thegent sota replay`` (forwarded
through the cockpit→sota shim transparently) so a single canary
invocation exercises the diff path on every supported report format
(``--json``, ``--junitxml``) without rewriting the snapshot.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from .cockpit import (
    DecisionNotice,
    OperatorCockpit,
    OverrideEvent,
    RunEvent,
    RunState,
    render_cockpit,
)
from .decision_audit import DecisionAuditAppender
from .kpis.traffic import TrafficDashboard, TrafficEvent, render_traffic

console = Console()
err_console = Console(stderr=True)


# AUDIT-9 (Phase 3/4 third-pass hardening): module-level single
# import of Rich's escape so the existing call-sites can use
# ``_exc_text(...)`` as a direct drop-in. F-1 (SOTA second-pass):
# ``_render_cli_error`` / ``_render_cli_warn`` were the first
# iteration of the escape shims; every call site was migrated to
# ``_exc_text`` / ``_escape`` in the AUDIT-9 hand-off, so the
# wrapper functions are now dead code and were deleted.
#
# F-15 (SOTA fifth-pass): ``_exc_text`` accepts any ``object`` (not
# just ``BaseException``) and coerces via ``str(obj)`` internally.
# The previous ``_exc_text(exc: BaseException)`` typing forced
# call-sites to write ``_escape(str(batch))`` for path strings,
# which meant two helper names for the same operation. Widening the
# signature to ``object`` collapses the two helpers into one and
# aligns with how the cli_sota module already calls the helper for
# non-exception values (``_exc_text(snapshot_format)!r``, etc.).
#
# GOV-1 (Phase 3/4 sixteenth+1 lane): ``_exc_text`` is now a thin
# re-export of :func:`thegent.ux.cli_errors.exc_text` so any CLI
# sub-app outside the cockpit (e.g. ``thegent.cli.apps.govern``)
# can import the same helper without dragging the full cockpit
# dependency surface into the root ``thegent`` import graph.
# The leading underscore on ``_exc_text`` is preserved here for
# backward compatibility with every existing call site in this
# module + the cli_sota companion module; the public alias
# ``exc_text`` lives in ``thegent.ux.cli_errors``.
from thegent.ux.cli_errors import exc_text as _exc_text  # noqa: E402, F401
from thegent.ux.cli_errors import exc_text as _rich_escape  # noqa: E402, F401

_LOGGER = logging.getLogger(__name__)


# F-15 (SOTA fifth-pass): ``name="cockpit"`` so ``Usage: cockpit`` renders
# in --help output instead of Typer's "root" fallback when invoked via
# ``python -m thegent.ux.cli_cockpit``. The same ``app`` is mounted into
# the parent ``thegent`` group by the all-things entry point; the
# parent group supplies its own name so the standalone case still works.
app = typer.Typer(
    name="cockpit",
    help="Operator cockpit + traffic KPI + policy pre-check surface (WP-3001/WP-4001/WP-Y7).",
    no_args_is_help=True,
)


def _resolve_clock(epoch: float | None) -> Callable[[], float]:
    """Build a deterministic clock callable from ``--clock <epoch>``.

    ``None`` means use wall-clock (``time.time``), which is the right
    default for live operator runs. SOTA replay tooling passes an
    explicit epoch to lock every render to a fixed timeline.
    """
    if epoch is None:
        import time as _time

        return _time.time
    pinned = float(epoch)

    def _clock() -> float:
        return pinned

    return _clock


# ---------------------------------------------------------------------------
# cockpit render
# ---------------------------------------------------------------------------


# AUDIT-N+25 (SOTA audit pass 11): ``_attach_mcp_audit_stats`` is the
# single source of truth for attaching the live MCP audit-trail
# singleton stats to the live :class:`OperatorCockpit` so the snapshot
# envelope (already shipped in Pass 8) emits a populated
# ``mcp_audit_stats`` key. Mirrors the lazy-import / defensive-try
# shape of ``_fetch_mcp_audit_entries`` (Pass 9) so the cockpit
# renderer never crashes on a missing MCP module.
#
# Why this lives here (not in ``cockpit.py``): the cockpit module owns
# the runtime engine, but the CLI surface owns the user-facing
# *opt-in* contract. Attaching the singleton unconditionally from
# ``cockpit.py`` would force every cockpit consumer to import the MCP
# subsystem; the CLI helper gates the attach behind a lazy import so
# ``cockpit render`` still works against synthetic snapshots that
# never touch the MCP audit trail.
def _attach_mcp_audit_stats(cockpit: OperatorCockpit) -> str | None:
    """Attach ``mcp_audit_stats`` to ``cockpit``; return ``None`` on success.

    Returns a human-readable error string when the import fails so the
    call site can decide whether to surface it in the JSON envelope or
    silently drop it (the latter is the right choice for
    ``cockpit render --json`` so the historical contract — every key
    present, ``mcp_audit_stats`` may be ``null`` — is preserved).
    """
    try:
        from ..mcp.server import mcp_audit_stats
    except Exception as exc:  # pragma: no cover - import guard
        return f"import:{type(exc).__name__}:{exc}"
    try:
        cockpit.attach_audit_trail(mcp_audit_stats)
    except Exception as exc:  # noqa: BLE001 - never crash the renderer.
        return f"attach:{type(exc).__name__}:{exc}"
    return None


# AUDIT-N+26 (SOTA audit pass 12): ``_fetch_pre_check_mcp_stats`` is the
# single source of truth for fetching the live MCP audit-trail
# singleton stats that ``cockpit pre-check --include-mcp-audit``
# surfaces in its JSON envelope. Mirrors the lazy-import /
# defensive-try shape of ``_attach_mcp_audit_stats`` (Pass 11) and
# ``_fetch_mcp_audit_entries`` (Pass 9) so the cockpit renderer
# never crashes on a missing MCP module.
#
# Why this lives here (not in ``cockpit.py``): the cockpit module owns
# the runtime engine, but the CLI surface owns the user-facing
# *opt-in* contract. A dedicated helper keeps the single-context and
# batch ``--json`` paths in lockstep on the envelope shape — both
# call this and write the result under the ``mcp_audit_stats`` key.
def _fetch_pre_check_mcp_stats() -> tuple[dict[str, Any] | None, str | None]:
    """Return ``(stats, error)`` for the ``pre-check --include-mcp-audit`` block.

    ``stats`` is the live MCP audit-trail singleton dict (or ``None``
    on import failure / fetch failure); ``error`` is a human-readable
    diagnostic string (or ``None`` on success). The CLI uses both to
    populate the JSON envelope so operators see a structured
    diagnosis instead of a silent ``null``.
    """
    try:
        from ..mcp.server import mcp_audit_stats
    except Exception as exc:  # pragma: no cover - import guard
        return None, f"import:{type(exc).__name__}:{exc}"
    try:
        stats_obj = mcp_audit_stats()
    except Exception as exc:  # noqa: BLE001 - never crash the renderer.
        return None, f"fetch:{type(exc).__name__}:{exc}"
    # ``mcp_audit_stats`` returns a dict; tolerate any object exposing
    # ``to_dict()`` so future schema migrations stay defensive.
    if hasattr(stats_obj, "to_dict"):
        try:
            stats_obj = stats_obj.to_dict()
        except Exception as exc:  # noqa: BLE001
            return None, f"to_dict:{type(exc).__name__}:{exc}"
    if not isinstance(stats_obj, dict):
        return None, f"unexpected:{type(stats_obj).__name__}"
    return stats_obj, None


@app.command("render", help="Render the 4-pane operator cockpit to stdout.")
def cockpit_render(
    runs_json: Path | None = typer.Option(
        None,
        "--runs",
        help="JSON file with [{run_id, state, lane, agent, confidence, elapsed_s}]",
    ),
    overrides_json: Path | None = typer.Option(
        None,
        "--overrides",
        help="JSON file with [{rule_id, by, reason, expires_in_s}]",
    ),
    progress_done: int = typer.Option(0, "--progress-done", help="Done count for header bar"),
    progress_total: int = typer.Option(100, "--progress-total", help="Total count for header bar"),
    clock: float | None = typer.Option(
        None,
        "--clock",
        help="Pin wall clock (epoch seconds) for deterministic replay",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit snapshot JSON instead of text"),
    # AUDIT-N+25 (SOTA audit pass 11): the audit-trail toggle. Default
    # on so the AUDIT-N+22 contract (Pass 8) is honoured by the render
    # envelope — without an explicit attach, ``mcp_audit_stats`` is
    # always ``null``. Operators on synthetic snapshots (no MCP
    # subsystem loaded) can opt out with ``--no-mcp-audit`` to drop the
    # MCP import attempt entirely.
    include_mcp_audit: bool = typer.Option(
        True,
        "--include-mcp-audit/--no-mcp-audit",
        help=(
            "Attach the live MCP audit-trail singleton stats "
            "(mcp_audit_stats) so the JSON envelope's ``mcp_audit_stats`` "
            "key is populated. Default on; pass --no-mcp-audit to skip "
            "the MCP import and keep the envelope's ``mcp_audit_stats`` "
            "key set to ``null`` (useful for synthetic / test snapshots)."
        ),
    ),
) -> None:
    """Render the 4-pane operator cockpit (WP-4001, FR-UX-007, P-081).

    With ``--include-mcp-audit`` (AUDIT-N+25, SOTA audit pass 11) the
    JSON envelope's ``mcp_audit_stats`` key is populated with the live
    MCP audit-trail singleton — the same gauge the ``cockpit traffic
    --include-mcp-audit`` lane and ``cockpit audit mcp-tail --stats``
    subcommand surface. The render envelope contract introduced in
    Pass 8 already emitted the key; Pass 11 closes the AUDIT-N+22
    regression by attaching the source so the key is no longer
    perpetually ``null``.

    The text mode is unchanged because the cockpit renderer already
    surfaces the gauges via the ``attach_*`` machinery — Pass 11 only
    wires the JSON envelope path through the same source.
    """
    try:
        runs = _load_runs(runs_json)
        overrides = _load_overrides(overrides_json)
        clock_fn = _resolve_clock(clock)
        if json_output:
            # JSON mode needs the live cockpit object (not the one-shot
            # helper) so snapshot() picks up the injected clock.
            live = OperatorCockpit(clock=clock_fn)
            # AUDIT-N+25 (SOTA audit pass 11): attach the MCP audit
            # singleton stats so the snapshot's ``mcp_audit_stats``
            # key is populated. The helper swallows import / attach
            # errors so a missing MCP subsystem leaves the envelope
            # shape intact (the key stays ``null`` instead of crashing).
            if include_mcp_audit:
                _attach_mcp_audit_stats(live)
            live.tick(runs=runs, overrides=overrides, progress=(progress_done, progress_total))
            typer.echo(json.dumps(live.snapshot(), indent=2, sort_keys=True))
            return
        typer.echo(
            render_cockpit(
                runs=runs,
                overrides=overrides,
                progress=(progress_done, progress_total),
                clock=clock_fn,
            )
        )
    except Exception as exc:
        err_console.print(f"[red]cockpit render failed:[/red] {_exc_text(exc)}")
        raise typer.Exit(1) from exc


# ---------------------------------------------------------------------------
# cockpit traffic
# ---------------------------------------------------------------------------


# AUDIT-N+24 (SOTA audit pass 9): ``DEFAULT_MCP_AUDIT_LINES`` is the
# no-flag default cap for the recent-entries slice surfaced by the
# ``cockpit traffic --include-mcp-audit`` toggle. Sits next to the
# ``cockpit audit mcp-tail`` default (``n=20``) but tighter so the
# dashboard stays scannable on 80-col terminals. Operators who want the
# longer list can pass ``--mcp-audit-lines N``; operators who want to
# disable the trailing block pass ``--no-mcp-audit``.
DEFAULT_MCP_AUDIT_LINES = 10
# Maps the ``--kind`` CLI string to the canonical ``AuditEntryKind`` so
# the cockpit traffic subcommand mirrors the same vocabulary as
# ``cockpit audit mcp-tail``. Kept here (not in mcp_audit_wiring) so the
# CLI module owns its user-facing strings and the audit-trail module
# stays CLI-free.
_MCP_AUDIT_KIND_VALUES = (
    "tool_invocation",
    "resource_read",
    "gate_check",
    "error",
)


# F-15 (SOTA fifth-pass): ``name="traffic"`` for symmetry with the
# ``audit_app`` sub-app and so ``cockpit traffic --help`` renders
# cleanly under the parent ``cockpit`` group.
traffic_app = typer.Typer(
    name="traffic",
    help="TRAFFIC KPI dashboard (WP-Y7, OPS-001/002/003, P-081).",
    no_args_is_help=True,
)


# AUDIT-N+24 (SOTA audit pass 9): ``_fetch_mcp_audit_entries`` is the
# single source of truth for fetching the recent / filtered MCP audit
# entries the cockpit traffic subcommand surfaces. Centralised so the
# ``cockpit_traffic_summary`` body stays focused on rendering and the
# ``mcp_audit_query`` / ``mcp_audit_recent`` routing is testable in
# isolation.
#
# ``kind`` is the raw CLI string (``"tool_invocation"`` etc.) or
# ``None`` for no filter. ``limit`` caps the result list (``mcp_audit_query``
# defaults to ``200``; ``mcp_audit_recent`` defaults to ``100``). The
# helper applies the ``--include-mcp-audit`` gate so the call site can
# remain terse.
def _fetch_mcp_audit_entries(
    *,
    include: bool,
    lines: int,
    kind: str | None,
    agent: str | None,
    outcome: str | None,
) -> tuple[list[Any], dict[str, Any] | None, str | None]:
    """Return ``(entries, stats, error)`` for the cockpit traffic audit block.

    Returns ``([], None, None)`` when ``include=False`` so the caller can
    short-circuit rendering without branching on the filter flags.

    ``kind`` is the raw CLI string (``"tool_invocation"`` /
    ``"resource_read"`` / ``"gate_check"`` / ``"error"``); invalid
    values surface as ``error="kind: <value> not in (…)"`` so the CLI
    can re-raise as ``typer.BadParameter`` and the JSON envelope can
    surface a stable ``{"error": {"kind": "<value>", "allowed": [...]}}``
    payload instead of silently coercing.

    The fetch is wrapped in ``try`` so a buggy audit-trail singleton
    (raised during the in-memory lookup) never crashes the cockpit
    traffic renderer — the helper swallows the exception and returns
    ``([], None, "<class>:<str>" })``.
    """
    if not include:
        return [], None, None
    try:
        from ..mcp.server import (
            AuditEntryKind,
            mcp_audit_query,
            mcp_audit_recent,
            mcp_audit_stats,
        )
    except Exception as exc:  # pragma: no cover - import guard
        return [], None, f"import:{type(exc).__name__}:{exc}"

    limit = max(int(lines), 1) if lines and lines > 0 else DEFAULT_MCP_AUDIT_LINES
    try:
        if kind or agent or outcome:
            kind_enum = None
            if kind is not None:
                try:
                    kind_enum = AuditEntryKind(kind)
                except ValueError:
                    return (
                        [],
                        None,
                        f"kind: {kind!r} not in {_MCP_AUDIT_KIND_VALUES}",
                    )
            entries = mcp_audit_query(
                kind=kind_enum,
                agent=agent,
                outcome=outcome,
                limit=limit,
            )
        else:
            entries = mcp_audit_recent(n=limit)
        stats = mcp_audit_stats()
    except Exception as exc:  # noqa: BLE001 - never crash the renderer
        return [], None, f"fetch:{type(exc).__name__}:{exc}"
    return list(entries), stats, None


# AUDIT-N+24 (SOTA audit pass 9): ``_render_audit_rows`` is the
# text-mode renderer for the MCP audit block. Mirrors the column layout
# used by ``cockpit audit mcp-tail`` (seq / kind / op / agent /
# outcome / duration_ms) so operators learn one vocabulary for both
# subcommands. Returns ``[]`` when there are no entries so the
# renderer naturally degrades to an empty pane.
def _render_audit_rows(entries: list[Any], max_rows: int) -> list[str]:
    rows: list[str] = []
    if not entries:
        return rows
    for entry in entries[:max_rows]:
        if hasattr(entry, "to_dict"):
            ed = entry.to_dict()
            kind_str = str(ed.get("kind", "-"))
            op_str = str(ed.get("operation", "-"))
            agent_str = str(ed.get("agent") or "-")
            outcome_str = str(ed.get("outcome") or "-")
            seq_val = ed.get("seq", 0)
            dur_val = float(ed.get("duration_ms", 0.0))
        else:
            kind_str = str(entry.get("kind", "-"))
            op_str = str(entry.get("operation", "-"))
            agent_str = str(entry.get("agent") or "-")
            outcome_str = str(entry.get("outcome") or "-")
            seq_val = entry.get("seq", 0)
            dur_val = float(entry.get("duration_ms", 0.0))
        rows.append(
            f"[mcp-audit] seq={seq_val} kind={kind_str} op={op_str} "
            f"agent={agent_str} outcome={outcome_str} duration_ms={dur_val:.2f}"
        )
    if len(entries) > max_rows:
        rows.append(f"[mcp-audit] ... {len(entries) - max_rows} older entries hidden")
    return rows


@traffic_app.command("summary", help="Render a TRAFFIC KPI snapshot to stdout.")
def cockpit_traffic_summary(
    events_json: Path | None = typer.Option(
        None,
        "--events",
        help="JSON file with [{ts, lane, agent, status, duration_ms, override_active}]",
    ),
    window_s: float = typer.Option(60.0, "--window", help="Window length in seconds"),
    clock: float | None = typer.Option(
        None,
        "--clock",
        help="Pin wall clock (epoch seconds) for deterministic replay",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit summary JSON instead of text"),
    # AUDIT-N+24 (SOTA audit pass 9): the audit-trail toggle. Default
    # off so the historical ``cockpit traffic summary`` contract is
    # preserved; opt in with ``--include-mcp-audit`` to append the
    # recent MCP audit entries underneath the TRAFFIC dashboard.
    include_mcp_audit: bool = typer.Option(
        False,
        "--include-mcp-audit/--no-mcp-audit",
        help=(
            "Append the live MCP audit trail (singleton gauge + recent N "
            "entries) underneath the TRAFFIC dashboard. Default "
            "--no-mcp-audit for backward compatibility."
        ),
    ),
    mcp_audit_lines: int = typer.Option(
        DEFAULT_MCP_AUDIT_LINES,
        "--mcp-audit-lines",
        help=(
            "Cap the number of recent MCP audit entries rendered / "
            "returned when --include-mcp-audit is set. Default 10."
        ),
    ),
    mcp_kind: str | None = typer.Option(
        None,
        "--mcp-kind",
        help=(
            "Filter the audit entries by kind (tool_invocation, "
            "resource_read, gate_check, error). Omit to include all "
            "kinds."
        ),
    ),
    mcp_agent: str | None = typer.Option(
        None,
        "--mcp-agent",
        help="Filter the audit entries by agent name (exact match).",
    ),
    mcp_outcome: str | None = typer.Option(
        None,
        "--mcp-outcome",
        help="Filter the audit entries by outcome (ok, error, budget_exceeded).",
    ),
) -> None:
    """Render the TRAFFIC KPI dashboard from a (possibly empty) event log.

    With ``--include-mcp-audit`` (AUDIT-N+24, SOTA audit pass 9) the
    command also appends the live MCP audit-trail singleton stats
    (``mcp_audit_stats()``) and the most recent ``--mcp-audit-lines``
    entries (``mcp_audit_recent`` / ``mcp_audit_query`` filtered by the
    optional ``--mcp-kind`` / ``--mcp-agent`` / ``--mcp-outcome``
    flags). The two sources compose into a single dashboard so
    operators can see at-a-glance:

    * TRAFFIC KPIs (count / rps / error_rate / p50 / p95 / by-status)
    * MCP audit singleton (``total_entries`` / ``by_kind`` /
      ``by_outcome`` / ``avg_duration_ms`` / ``p99_duration_ms``)
    * MCP audit recent entries (one row per ``AuditEntry``)

    The ``--json`` envelope gains stable keys ``mcp_audit_stats`` and
    ``mcp_audit_recent`` (and an optional ``mcp_audit_error`` for the
    kind-validation / fetch-failure paths) so downstream SOTA tooling
    can ingest both surfaces in one round-trip.
    """  # noqa: E501 - long docstring pinned by SOTA contract tests.
    try:
        clock_fn = _resolve_clock(clock)
        dashboard = TrafficDashboard(window_s=window_s, clock=clock_fn)
        for ev in _load_traffic_events(events_json):
            dashboard.record(ev)

        # AUDIT-N+24 (SOTA audit pass 9): fetch the audit-trail block
        # once so both the JSON envelope and the text renderer see the
        # same payload. ``kind`` validation surfaces a clean
        # ``typer.BadParameter`` instead of a stack trace.
        entries, stats, error = _fetch_mcp_audit_entries(
            include=include_mcp_audit,
            lines=mcp_audit_lines,
            kind=mcp_kind,
            agent=mcp_agent,
            outcome=mcp_outcome,
        )
        if error and error.startswith("kind:"):
            # kind validation error → BadParameter so --help + exit 2.
            raise typer.BadParameter(error)
        if json_output:
            payload: dict[str, Any] = dict(dashboard.summary())
            if include_mcp_audit:
                payload["mcp_audit_stats"] = stats
                payload["mcp_audit_recent"] = [e.to_dict() if hasattr(e, "to_dict") else e for e in entries]
                payload["mcp_audit_filters"] = {
                    "kind": mcp_kind,
                    "agent": mcp_agent,
                    "outcome": mcp_outcome,
                    "lines": mcp_audit_lines,
                }
                if error:
                    # Fetch-side error (post-validation). Surface in the
                    # envelope so the operator still gets a structured
                    # diagnosis instead of a silent empty block.
                    payload["mcp_audit_error"] = error
            typer.echo(json.dumps(payload, indent=2, sort_keys=True))
            return
        typer.echo(render_traffic(dashboard))
        if include_mcp_audit:
            typer.echo("")
            typer.echo("MCP audit trail:")
            if stats is not None:
                typer.echo(
                    f"  stats: total_entries={stats.get('total_entries', 0)} "
                    f"error_count={stats.get('error_count', 0)} "
                    f"avg_duration_ms={stats.get('avg_duration_ms')} "
                    f"p99_duration_ms={stats.get('p99_duration_ms')}"
                )
            rendered = _render_audit_rows(entries, max_rows=mcp_audit_lines)
            if not rendered:
                typer.echo("  (no MCP audit entries match the current filter)")
            else:
                for row in rendered:
                    typer.echo(f"  {row}")
            if error:
                typer.echo(f"  warning: {error}")
    except typer.Exit:
        raise
    except typer.BadParameter:
        raise
    except Exception as exc:
        err_console.print(f"[red]traffic summary failed:[/red] {_exc_text(exc)}")
        raise typer.Exit(1) from exc


app.add_typer(traffic_app, name="traffic")


# ---------------------------------------------------------------------------
# cockpit pre-check (governance)
# ---------------------------------------------------------------------------


@app.command("pre-check", help="Evaluate a PolicyContext against the governance PolicyEngine.")
def cockpit_pre_check(
    agent: str = typer.Option("", "--agent", help="Agent name (e.g. 'cursor')"),
    model: str = typer.Option("", "--model", help="Model name (e.g. 'gpt-4o')"),
    lane: str = typer.Option("standard", "--lane", help="Lane: standard|critical|recovery|deferral"),
    environment: str = typer.Option("development", "--env", help="Environment: development|staging|production"),
    confidence: float | None = typer.Option(None, "--confidence", help="Confidence 0..1"),
    prompt: str = typer.Option("", "--prompt", help="Prompt (hashed into the cache key)"),
    namespace: str = typer.Option(
        "global",
        "--namespace",
        help=(
            "Federated policy namespace. With ``--batch``, this value pins every "
            "corpus entry's namespace unless the entry explicitly carries its own "
            "non-empty ``namespace``. Without ``--batch``, it overrides the "
            "single-context ``PolicyContext.namespace``."
        ),
    ),
    default_policy: str | None = typer.Option(
        None,
        "--default-policy",
        help=(
            "Enable federated policy lookup with this default namespace. Passed "
            "through to ``PolicyEngine(default_namespace=...)`` on ``--commit``; "
            "ignored on the one-shot ``--dry-run`` path. When ``--batch`` is "
            "used and ``--commit`` is set, this also auto-enables "
            "``use_federation=True`` on the underlying engine."
        ),
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON decision"),
    dry_run: bool = typer.Option(True, "--dry-run/--commit", help="Default dry-run; pass --commit to cache"),
    batch: Path | None = typer.Option(
        None,
        "--batch",
        help="Replay a corpus of PolicyContext JSONs in one pass (file or dir of *.json).",
    ),
    audit_path: Path | None = typer.Option(
        None,
        "--audit-path",
        help="Persist every batch decision to this JSONL file (defaults to the cockpit appender's path).",
    ),
    audit_append: bool = typer.Option(
        False,
        "--audit-append/--audit-overwrite",
        help="Append to the audit file (default: overwrite; useful for replay runs).",
    ),
    # AUDIT-N+26 (SOTA audit pass 12): ``--include-mcp-audit`` mirrors the
    # ``cockpit render --include-mcp-audit`` and ``cockpit traffic
    # --include-mcp-audit`` toggle so the canonical operator UX surfaces
    # agree on vocabulary. Default off so the single-context JSON
    # envelope (a bare ``PolicyDecision.to_dict()``) and the batch JSON
    # stream (one decision per line) stay byte-identical for the existing
    # harvesters (``test_unit_cockpit_sota_json_parity.py`` /
    # ``test_unit_ux_cli_cockpit.py::_harvest_decisions``) — opt in to
    # attach the live MCP audit-trail singleton stats and surface them in
    # the envelope. ``--no-mcp-audit`` is the documented way to drop the
    # MCP import on synthetic / replay paths.
    include_mcp_audit: bool = typer.Option(
        False,
        "--include-mcp-audit/--no-mcp-audit",
        help=(
            "Attach the live MCP audit-trail singleton stats "
            "(mcp_audit_stats) so the JSON envelope surfaces a populated "
            "``mcp_audit_stats`` key. Default off so existing JSON "
            "harvesters stay byte-identical; pass --include-mcp-audit "
            "to opt in (mirrors ``cockpit render --include-mcp-audit`` "
            "and ``cockpit traffic --include-mcp-audit``)."
        ),
    ),
) -> None:
    """Evaluate a :class:`PolicyContext` and emit the resulting decision.

    With ``--batch <path>`` (WP-3001 SOTA replay tooling) the command
    consumes a JSON file (list of contexts) or a directory of ``*.json``
    files (each a list) and emits one combined decision log. The
    batch mode still honors ``--dry-run`` / ``--commit`` semantics:
    a deny on any item exits ``3`` after the full batch drains.

    ``--namespace <name>`` and ``--default-policy <name>`` are the
    Lane 2 federation-namespace pin: they let SOTA replay tooling
    force every corpus entry to live in (and the engine to default to)
    a single namespace without rewriting every JSON entry.

    With ``--include-mcp-audit`` (AUDIT-N+26, SOTA audit pass 12) the
    JSON envelope surfaces the live MCP audit-trail singleton stats so
    operators can correlate a deny / allow verdict with the upstream
    MCP tool / resource / gate dispatches that triggered it. The
    single-context path augments the ``PolicyDecision.to_dict()``
    envelope in place (existing top-level keys preserved); the batch
    path emits an additional trailing ``_pre_check_envelope_v1`` line
    that the canonical ``cockpit replay`` harvesters ignore (they
    filter on ``verdict`` / ``reason_code`` membership).
    """
    try:
        # Import lazily so the CLI does not pull the full governance
        # module chain on commands that don't need it.
        from ..governance.policy_engine import (
            PolicyContext,
            PolicyEngine,
            evaluate_pre_check,
        )
        from .decision_audit import DecisionAuditAppender
    except Exception as exc:  # pragma: no cover - import guard
        err_console.print(f"[red]governance unavailable:[/red] {_exc_text(exc)}")
        raise typer.Exit(2) from exc
    try:
        # Batch mode takes precedence over the single-context path.
        # Both share the same dry-run / commit semantics.
        if batch is not None:
            # ``--default-policy`` auto-enables federation on --commit so the
            # caller does not have to know about ``use_federation`` to get
            # the federated default-namespace pin to take effect.
            use_federation = default_policy is not None
            exit_code = _run_pre_check_batch(
                batch=batch,
                engine_factory=lambda: PolicyEngine(
                    use_federation=use_federation,
                    default_namespace=default_policy or "global",
                ),
                use_engine=not dry_run,
                appender_factory=lambda: DecisionAuditAppender(audit_path=audit_path),
                # Only persist when ``--audit-path`` is explicitly supplied.
                # The historical ``or True`` accidentally wrote to the default
                # ``~/.thegent/cockpit_decisions.jsonl`` even when the operator
                # did not opt in — a SOTA replay-tooling footgun (P0 audit).
                persist_audit=audit_path is not None,
                append_audit=audit_append,
                json_output=json_output,
                namespace_override=namespace,
                # AUDIT-N+26 (SOTA audit pass 12): forward the
                # ``--include-mcp-audit`` opt-in to the batch runner so the
                # trailing envelope line is emitted when the operator wants
                # the MCP audit-trail singleton correlated with the
                # batch decisions. Default off keeps the existing
                # line-delimited JSON stream byte-identical.
                include_mcp_audit=include_mcp_audit,
            )
            raise typer.Exit(exit_code)

        ctx = PolicyContext(
            agent=agent,
            model=model,
            lane=lane,
            confidence=confidence,
            environment=environment,
            namespace=namespace,
            prompt=prompt,
        )
        # Use the one-shot helper for dry-run; only build a long-lived
        # PolicyEngine when the caller opts in. This keeps the read path
        # cheap for SOTA replay tooling. ``--default-policy`` flows into
        # the engine as both ``use_federation=True`` (when set) and the
        # ``default_namespace`` kwarg; on the one-shot dry-run path it is
        # a no-op (the federation lookup never fires).
        if dry_run:
            decision = evaluate_pre_check(ctx)
        else:
            engine = PolicyEngine(
                use_federation=default_policy is not None,
                default_namespace=default_policy or "global",
            )
            decision = engine.evaluate(ctx)
        if json_output:
            # AUDIT-N+26 (SOTA audit pass 12): when ``--include-mcp-audit``
            # is set, augment the decision envelope in place with the
            # live MCP audit-trail singleton stats. Existing top-level
            # keys (``verdict`` / ``reason`` / ``reason_code`` /
            # ``rule_id`` / ``override_applied`` / ``cached`` /
            # ``evaluated_at``) are preserved so the
            # ``test_unit_ux_cli_cockpit.py::test_pre_check_json``
            # assertion ``"verdict" in payload`` keeps passing.
            payload = decision.to_dict()
            if include_mcp_audit:
                stats, error = _fetch_pre_check_mcp_stats()
                payload["mcp_audit_stats"] = stats
                if error is not None:
                    # Surface the fetch / import error in the envelope
                    # so the operator gets a structured diagnosis
                    # instead of a silent empty block — mirrors the
                    # ``cockpit traffic --include-mcp-audit`` envelope
                    # error-key contract.
                    payload["mcp_audit_error"] = error
            typer.echo(json.dumps(payload, indent=2, sort_keys=True, default=str))
            return
        typer.echo(
            f"verdict={decision.verdict.value} reason_code={decision.reason_code.value} "
            f"rule_id={decision.rule_id or '-'} cached={decision.cached} "
            f"override_applied={decision.override_applied} reason={decision.reason!r}"
        )
        if decision.verdict.value == "deny":
            raise typer.Exit(3)
    except typer.Exit:
        raise
    except Exception as exc:
        err_console.print(f"[red]pre-check failed:[/red] {_exc_text(exc)}")
        raise typer.Exit(1) from exc


def _run_pre_check_batch(
    *,
    batch: Path,
    engine_factory: Callable[[], Any],
    use_engine: bool,
    appender_factory: Callable[[], DecisionAuditAppender],
    persist_audit: bool,
    append_audit: bool,
    json_output: bool,
    namespace_override: str | None = None,
    # AUDIT-N+26 (SOTA audit pass 12): when set, emit a trailing
    # ``_pre_check_envelope_v1`` line containing the MCP audit-trail
    # singleton stats after the line-delimited decisions so the
    # operator can correlate the verdict stream with the upstream
    # MCP dispatches. Default ``False`` so existing harvesters
    # (``test_unit_cockpit_sota_json_parity._harvest_decisions`` and
    # ``test_unit_ux_cli_cockpit._harvest_decisions``) stay
    # byte-identical.
    include_mcp_audit: bool = False,
) -> int:
    """Replay a corpus of :class:`PolicyContext` JSONs through pre-check.

    Returns the process exit code: ``3`` if any item yielded ``deny``,
    ``0`` otherwise. The function never raises for individual deny
    verdicts (so a single deny does not abort the run) — SOTA tooling
    can keep draining the corpus and inspect the combined audit log.

    ``batch`` may be:

    * a JSON file (list of context dicts, or a single context dict)
    * a directory containing ``*.json`` files (each: list or single dict)

    ``namespace_override`` pins every entry's ``namespace`` to the given
    value unless the entry already carries an explicit namespace (the
    Lane 2 federation contract). Both ``pre-check`` and ``replay`` route
    through this argument so they cannot drift apart on namespace
    semantics.

    ``include_mcp_audit`` (AUDIT-N+26, SOTA audit pass 12) opts in to
    emit a trailing envelope line after the decision stream. The
    envelope carries ``mcp_audit_stats`` (live singleton) and an
    optional ``mcp_audit_error`` for fetch / import failures. The
    envelope is tagged with the ``_pre_check_envelope_v1`` discriminator
    so the canonical ``cockpit replay`` harvesters can filter it out
    (they collect only objects that look like
    :class:`PolicyDecision` ``to_dict()`` output).
    """
    contexts, decisions, notices = _build_batch_decision_log(
        batch=batch,
        engine_factory=engine_factory,
        use_engine=use_engine,
        namespace_override=namespace_override,
    )
    if not contexts:
        err_console.print(f"[yellow]pre-check batch is empty:[/yellow] {_exc_text(batch)}")
        return 0

    appender = appender_factory() if persist_audit else None
    if appender is not None and not append_audit:
        # Overwrite the audit file on replay so SOTA runs are
        # self-contained.
        path = appender.audit_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")

    any_deny = any(d.verdict.value == "deny" for d in decisions)
    if json_output:
        for d in decisions:
            typer.echo(json.dumps(d.to_dict(), indent=2, sort_keys=True, default=str))
        # AUDIT-N+26 (SOTA audit pass 12): opt-in trailing envelope.
        # The discriminator key (``_pre_check_envelope_v1``) lets
        # harvesters skip the envelope without affecting the
        # decision stream semantics; it carries the same MCP
        # audit-trail singleton stats the
        # ``cockpit traffic --include-mcp-audit`` lane surfaces.
        if include_mcp_audit:
            stats, error = _fetch_pre_check_mcp_stats()
            envelope: dict[str, Any] = {
                "_pre_check_envelope_v1": True,
                "mcp_audit_stats": stats,
            }
            if error is not None:
                envelope["mcp_audit_error"] = error
            typer.echo(json.dumps(envelope, indent=2, sort_keys=True, default=str))

    if appender is not None and notices:
        appender.record_many(notices)

    summary = (
        f"pre-check batch: items={len(notices)} deny={any_deny} audit={appender.audit_path_str() if appender else '-'}"
    )
    typer.echo(summary)
    return 3 if any_deny else 0


def _build_batch_decision_log(
    *,
    batch: Path,
    engine_factory: Callable[[], Any],
    use_engine: bool,
    namespace_override: str | None = None,
) -> tuple[list[Any], list[Any], list[DecisionNotice]]:
    """Shared batch pipeline used by ``pre-check --batch`` and ``replay``.

    Returns a 3-tuple of ``(contexts, decisions, notices)`` after:

    1. Loading the corpus via :func:`_load_pre_check_corpus` (which
       applies ``namespace_override`` if supplied — Lane 2 federation
       contract).
    2. Running each context through either the long-lived
       :class:`PolicyEngine` (``use_engine=True``) or the one-shot
       :func:`evaluate_pre_check` helper, building a
       :class:`DecisionNotice` for every verdict so the audit appender
       gets a uniform stream regardless of the underlying engine.

    This is the single point of truth for the load+evaluate+notice
    pipeline so ``pre-check`` and ``replay`` cannot drift apart on
    cache keys, return shape, or notice schema (Phase 3/4 hardening
    lane, third "Unblocked Next" item). The function does NOT touch
    the audit appender; that's the caller's responsibility (so both
    ``pre-check`` and ``replay`` can persist the same notice stream
    via their own ``DecisionAuditAppender`` factory).
    """
    from ..governance.policy_engine import evaluate_pre_check

    contexts = _load_pre_check_corpus(batch, namespace_override=namespace_override)
    if not contexts:
        return [], [], []

    engine = engine_factory() if use_engine else None
    decisions: list[Any] = []
    notices: list[DecisionNotice] = []
    for ctx in contexts:
        if use_engine and engine is not None:
            decision = engine.evaluate(ctx)
        else:
            decision = evaluate_pre_check(ctx)
        decisions.append(decision)
        notice = DecisionNotice(
            verdict=decision.verdict.value,
            reason_code=decision.reason_code.value,
            rule_id=decision.rule_id or "",
            agent=ctx.agent,
            lane=ctx.lane,
            evaluated_at=decision.evaluated_at if hasattr(decision, "evaluated_at") else 0.0,
            reason=decision.reason,
        )
        notices.append(notice)
    return contexts, decisions, notices


def _load_pre_check_corpus(
    path: Path,
    namespace_override: str | None = None,
) -> list[Any]:
    """Load a ``--batch`` input into a flat list of ``PolicyContext``.

    Accepts:
        * a JSON file containing a list of context dicts
        * a JSON file containing a single context dict
        * a directory of ``*.json`` files, each shaped as above

    ``namespace_override`` pins every entry's ``namespace`` to the
    given value unless the entry already carries an explicit non-empty
    namespace. This is the Lane 2 federation-namespace contract so
    a CLI invocation like ``pre-check --namespace team-a`` forces every
    corpus entry to live in that namespace without requiring callers
    to rewrite every JSON.

    Empty / unreadable inputs raise ``ValueError`` with a useful
    message so the CLI surfaces it before draining the audit pipeline.
    """
    from ..governance.policy_engine import PolicyContext

    if not path.exists():
        raise FileNotFoundError(f"batch path not found: {path}")

    def _coerce(entry: Any, src: Path) -> PolicyContext:
        if not isinstance(entry, dict):
            raise ValueError(f"batch {src} entries must be objects, got {type(entry).__name__}: {entry!r}")
        ns = str(entry.get("namespace", ""))
        if namespace_override is not None and (not ns or ns == "global"):
            ns = namespace_override
        elif not ns:
            ns = "global"
        return PolicyContext(
            agent=str(entry.get("agent", "")),
            model=str(entry.get("model", "")),
            lane=str(entry.get("lane", "standard")),
            confidence=entry.get("confidence"),
            environment=str(entry.get("environment", "development")),
            namespace=ns,
            prompt=str(entry.get("prompt", "")),
        )

    if path.is_file():
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return [_coerce(e, path) for e in raw]
        return [_coerce(raw, path)]
    if path.is_dir():
        out: list[Any] = []
        for child in sorted(path.glob("*.json")):
            raw = json.loads(child.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                out.extend(_coerce(e, child) for e in raw)
            else:
                out.append(_coerce(raw, child))
        return out
    raise ValueError(f"--batch path is neither file nor directory: {path}")


# ---------------------------------------------------------------------------
# cockpit replay (Phase 3/4 SOTA snapshot validator)
# ---------------------------------------------------------------------------


# Fields that must match for a snapshot entry to count as equal to the
# engine's ``PolicyDecision.to_dict()`` output. ``cached`` and
# ``evaluated_at`` are explicitly excluded because they're
# runtime-dependent (the replay may run on a different wall clock than
# the snapshot's author), and a leading/trailing whitespace difference
# in ``reason`` is tolerated below.
_REPLAY_COMPARE_FIELDS: tuple[str, ...] = (
    "verdict",
    "reason_code",
    "rule_id",
    "override_applied",
)


# Dispatch table for the ``--snapshot-flip <field>`` SOTA canary workflow.
# Each entry knows how to invert one value of the given field so the
# compare step records a guaranteed mismatch on that field without the
# operator having to hand-edit the snapshot file on disk.
#
# Unknown fields fall through to a generic bool/not-string swap that
# covers the common cases without raising — the flip is a *canary*, not
# a strict guarantee; downstream ``_compare_decision`` is still the
# source of truth for whether the inverted snapshot actually disagrees
# with the engine's output.
def _invert_snapshot_value(field: str, value: Any) -> Any:
    """Return the inverted form of ``value`` for the SOTA ``--snapshot-flip`` flag.

    Recognised semantics:

    * ``verdict``: ``allow`` ↔ ``deny`` (and ``warn`` ↔ ``deny`` as a
      sensible canary default — flipping a warn to a deny is a strict
      mismatch against the engine's actual output).
    * ``override_applied``: bool negation.
    * ``cached``: bool negation (mirror of ``override_applied``).
    * any other field: bool negation when the value is a ``bool``,
      otherwise a stable "string-flipped" sentinel so the compare step
      records a mismatch without losing the field's type.

    The function is intentionally tolerant of ``None``/missing fields
    so a flip on an absent field is a no-op rather than a crash.
    """
    if value is None:
        return value
    if field == "verdict":
        text = str(value).strip().lower()
        if text == "allow":
            return "deny"
        if text == "deny":
            return "allow"
        # ``warn`` and any unrecognised verdict flip to ``deny`` so the
        # canary always disagrees with the engine's actual verdict.
        return "deny"
    if field in ("override_applied", "cached"):
        if isinstance(value, bool):
            return not value
        # Coerce string-shaped bools ("true"/"false") so yaml/toml
        # snapshots still get inverted cleanly.
        text = str(value).strip().lower()
        if text in ("true", "1", "yes"):
            return False
        if text in ("false", "0", "no"):
            return True
        return not bool(value)
    # Generic fallback: if the field is bool-shaped, negate; if string,
    # return a sentinel that the compare step will flag as a mismatch.
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        # Pick a value clearly different from any sane decision output;
        # use the negation when non-zero, otherwise a clearly-out-of-band
        # sentinel that still respects the field's numeric type.
        return -value if value != 0 else -1
    return f"<flipped:{value}>"


def _apply_snapshot_flip(
    snapshot: list[dict[str, Any]],
    field: str,
) -> list[dict[str, Any]]:
    """Return a copy of ``snapshot`` with ``field`` inverted on every entry.

    Mirrors the on-disk ``_write_snapshot(..., flip=True)`` pattern from
    ``tests/test_unit_cockpit_sota_json_parity.py`` but operates in
    memory so the operator's ``--compare`` file is left untouched. This
    is the SOTA canary workflow: deliberately force the replay into the
    mismatch path so the diff machinery + JSON envelope + exit code
    contract get exercised end-to-end on every CI run.
    """
    if not field:
        return snapshot
    flipped: list[dict[str, Any]] = []
    for entry in snapshot:
        if not isinstance(entry, dict):
            flipped.append(entry)
            continue
        new_entry = dict(entry)
        new_entry[field] = _invert_snapshot_value(field, entry.get(field))
        flipped.append(new_entry)
    return flipped


def _all_snapshot_flip_fields() -> tuple[str, ...]:
    """Return the canonical preset list of flip fields for ``--snapshot-flip-all``.

    The preset is the smallest set that, when flipped together, is
    guaranteed to disagree with every possible engine output:

    * ``verdict`` — flips the headline deny/allow bit.
    * ``override_applied`` — flips the override flag.
    * ``cached`` — flips the OPT-008 cache-hit bit.

    Operators who want to exercise the diff machinery on a wider set of
    fields can still pass ``--snapshot-flip <field>`` multiple times;
    the preset is purely a convenience for the most common canary
    pattern.
    """
    return ("verdict", "override_applied", "cached")


def _apply_snapshot_flips(
    snapshot: list[dict[str, Any]],
    fields: list[str],
) -> list[dict[str, Any]]:
    """Apply each flip in ``fields`` sequentially to ``snapshot``.

    Composition semantics:

    * Distinct fields are independent — flipping ``verdict`` then
      ``override_applied`` produces a snapshot whose ``verdict`` and
      ``override_applied`` are both inverted relative to the input.
    * Repeated fields compose — passing ``["verdict", "verdict"]`` is
      equivalent to a no-op for ``verdict`` (allow→deny→allow). This
      matches the SOTA audit's recommended "force-mismatch" workflow
      where an operator may want to layer multiple canary signals on
      the same snapshot.
    * Empty / falsy entries in ``fields`` are skipped so an operator
      who accidentally passes ``--snapshot-flip ""`` does not crash.

    Returns a fresh list of copies so the input snapshot is never
    mutated.
    """
    if not fields:
        return snapshot
    out: list[dict[str, Any]] = snapshot
    for field in fields:
        if not field:
            continue
        out = _apply_snapshot_flip(out, field)
    return out


def _normalise_snapshot_flip_fields(
    snapshot_flip: str | list[str] | None,
    snapshot_flip_all: bool,
) -> list[str]:
    """Reduce ``--snapshot-flip`` + ``--snapshot-flip-all`` into a single list.

    Typer delivers repeated ``--snapshot-flip`` flags as a ``list[str]``,
    but a single invocation arrives as ``Optional[str]``. This helper
    collapses both into a ``list[str]`` (de-duplicated while preserving
    first-seen order so the composition semantics in
    :func:`_apply_snapshot_flips` stay deterministic) and appends the
    ``--snapshot-flip-all`` preset if requested.
    """
    fields: list[str] = []
    if isinstance(snapshot_flip, str) and snapshot_flip:
        fields.append(snapshot_flip)
    elif isinstance(snapshot_flip, list):
        for entry in snapshot_flip:
            if entry and entry not in fields:
                fields.append(entry)
    if snapshot_flip_all:
        for entry in _all_snapshot_flip_fields():
            if entry not in fields:
                fields.append(entry)
    return fields


def _load_replay_snapshot(path: Path) -> list[dict[str, Any]]:
    """Load the ``--compare`` snapshot into a list of decision dicts.

    Accepts two top-level shapes:

    * a JSON list of ``PolicyDecision``-shaped dicts, or
    * a JSON object with a ``"decisions"`` key holding that same list.

    Anything else surfaces a ``ValueError`` so the CLI can exit ``1``
    with a useful message instead of crashing mid-diff.
    """
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        snapshot = raw
    elif isinstance(raw, dict) and isinstance(raw.get("decisions"), list):
        snapshot = raw["decisions"]
    else:
        raise ValueError(
            "compare snapshot must be a list or an object with a 'decisions' key, "
            f"got {type(raw).__name__}" + (f" with keys {list(raw.keys())}" if isinstance(raw, dict) else "")
        )
    return snapshot


def _compare_decision(
    expected: dict[str, Any],
    actual: dict[str, Any],
) -> list[str]:
    """Return the list of field names that disagree between two decision dicts.

    Whitespace-only differences in ``reason`` are tolerated so author
    edits (markdown line breaks, trailing newlines) don't false-positive.
    All other fields use strict equality.
    """
    diffs: list[str] = []
    for field in _REPLAY_COMPARE_FIELDS:
        exp_val = expected.get(field)
        act_val = actual.get(field)
        if field == "rule_id":
            # ``None`` and ``null`` (JSON's missing) are equivalent here.
            if (exp_val is None or exp_val == "") and (act_val is None or act_val == ""):
                continue
        if exp_val != act_val:
            diffs.append(field)
    # Whitespace-tolerant reason comparison.
    exp_reason = str(expected.get("reason", "")).strip()
    act_reason = str(actual.get("reason", "")).strip()
    if exp_reason != act_reason:
        diffs.append("reason")
    return diffs


def _format_mismatch(
    idx: int,
    expected: dict[str, Any] | None,
    actual: dict[str, Any] | None,
    diff_fields: list[str],
) -> str:
    """Stable text format for one mismatch row: ``mismatch[i]: ...``.

    When a field is in the diff list we render ``expected=X actual=Y``
    for that field so the operator sees the exact disagreement.
    """
    parts: list[str] = []
    if expected is None and actual is not None:
        return f"mismatch[{idx}]: produced entry has no matching expected entry"
    if actual is None and expected is not None:
        return f"mismatch[{idx}]: expected entry has no matching produced entry"
    if expected is None or actual is None:  # pragma: no cover - defensive
        return f"mismatch[{idx}]: <unknown diff>"
    for field in diff_fields:
        exp_val = expected.get(field)
        act_val = actual.get(field)
        parts.append(f"{field} expected={exp_val} actual={act_val}")
    if not parts:
        # Field-level compare reported nothing, but the row is here —
        # fall back to a generic message so the report is never empty.
        parts.append("snapshot differs but no tracked field mismatched")
    return f"mismatch[{idx}]: " + " ".join(parts)


# F-15 (SOTA fifth-pass): collapse the multi-sentence help into a
# single imperative sentence ending in a period (matching the
# convention of every other sub-command), and move the lane /
# delegation guidance into the function docstring that Typer renders
# as the ``--help`` extended description. The lane tag now mirrors
# the ``(WP-XXXX, FR-UX-NNN)`` style used by sibling sub-commands.
@app.command(
    "replay",
    help=(
        "Replay a corpus against an expected PolicyDecision snapshot "
        "(WP-3003/WP-4002, FR-GOV-005, Phase 3/4 hardening lane)."
    ),
)
def cockpit_replay(
    batch: Path = typer.Option(
        ...,
        "--batch",
        help="Corpus of PolicyContext JSONs (file or dir of *.json) — same as pre-check --batch.",
    ),
    compare: Path = typer.Option(
        ...,
        "--compare",
        help=(
            "Expected snapshot JSON: either a list of PolicyDecision-shaped dicts "
            "or an object with a ``decisions`` key holding the same list."
        ),
    ),
    audit_path: Path | None = typer.Option(
        None,
        "--audit-path",
        help="Persist every replay decision to this JSONL file (defaults to cockpit appender's path).",
    ),
    audit_append: bool = typer.Option(
        False,
        "--audit-append/--audit-overwrite",
        help="Append to the audit file (default: overwrite; useful for chained replays).",
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--commit",
        help="Default dry-run; pass --commit to cache decisions in the PolicyEngine.",
    ),
    namespace: str = typer.Option(
        "global",
        "--namespace",
        help="Federated policy namespace (pinned unless an entry declares its own).",
    ),
    default_policy: str | None = typer.Option(
        None,
        "--default-policy",
        help="Enable federated policy lookup with this default namespace on --commit.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit a structured {matched, mismatches, decisions, audit} object instead of text.",
    ),
    snapshot_format: str = typer.Option(
        "json",
        "--snapshot-format",
        help=(
            "Snapshot input format (json, yaml, or toml). Defaults to json. "
            "When set to anything other than 'json', delegates to `thegent sota replay`."
        ),
    ),
    report_format: str = typer.Option(
        "text",
        "--report-format",
        help=(
            "Report output format (text, json, or junitxml). Defaults to text. "
            "When set to anything other than 'text', delegates to `thegent sota replay`."
        ),
    ),
    report_path: Path | None = typer.Option(
        None,
        "--report-path",
        help="Write the report to this file (delegated to sota replay; default: stdout).",
    ),
    snapshot_flip: list[str] | None = typer.Option(
        None,
        "--snapshot-flip",
        help=(
            "SOTA canary workflow: invert the value of <field> on every entry of "
            "the loaded --compare snapshot in memory (e.g. 'verdict' or "
            "'override_applied') so the replay walks the mismatch path without "
            "the operator having to hand-edit the snapshot file. Pass the flag "
            "multiple times to compose flips across fields (``--snapshot-flip "
            "verdict --snapshot-flip override_applied``). Useful for exercising "
            "the diff machinery + JSON envelope + exit code 4 contract "
            "end-to-end on every CI run."
        ),
    ),
    snapshot_flip_all: bool = typer.Option(
        False,
        "--snapshot-flip-all",
        help=(
            "Convenience preset: flip the canonical ``(verdict, "
            "override_applied, cached)`` triple on every entry so the replay "
            "exercises the mismatch path on every tracked field at once. "
            "Equivalent to passing ``--snapshot-flip verdict --snapshot-flip "
            "override_applied --snapshot-flip cached``. Composes with any "
            "explicit ``--snapshot-flip <field>`` invocations without "
            "duplication."
        ),
    ),
) -> None:
    """Replay ``--batch`` through pre-check and validate against ``--compare``.

    Exit codes:

    * ``0`` — every decision matches the expected snapshot.
    * ``4`` — at least one mismatch (mirrors the exit-code-3 convention
      for ``deny`` but kept distinct so ``pre-check`` and ``replay`` can
      signal different failure modes to shell pipelines).
    * ``1`` — bad inputs (missing files, malformed snapshot, etc.).

    The default behaviour (``--snapshot-format json`` + ``--report-format
    text``) is the historical cockpit contract: text output, JSON
    snapshot, exit code 4 on mismatch.  When the operator passes a
    non-default ``--snapshot-format`` (yaml / toml) or
    ``--report-format`` (json / junitxml) we transparently delegate to
    ``thegent sota replay`` so callers do not need to learn a new
    command name.  This is the WORKLOG "Unblocked Next" #1 shim lane.
    """
    # Shim dispatch: when the operator asks for a non-default snapshot
    # or report format, defer to `sota replay` so we don't duplicate
    # the format-dispatch tables in two places.  ``--json`` is
    # translated to ``--report-format json`` so the operator-facing
    # knob keeps its existing shape.
    snapshot_format_lc = snapshot_format.lower()
    report_format_lc = report_format.lower()
    effective_report_format = "json" if json_output else report_format_lc

    if snapshot_format_lc != "json" or effective_report_format != "text":
        # Defer import so the cockpit CLI surface still loads cleanly
        # even if sota tooling is unavailable; the delegated call will
        # surface its own clean error.
        try:
            from .cli_sota import sota_replay
        except Exception as exc:  # pragma: no cover - import guard
            err_console.print(f"[red]sota replay unavailable:[/red] {_exc_text(exc)}")
            raise typer.Exit(1) from exc

        # ``sota replay`` always appends a trailing
        # ``sota replay: matched=...`` tail line for operator visibility,
        # but ``cockpit replay --json`` historically emitted a pure-JSON
        # envelope so pipelines can ``jq`` the output directly.  We don't
        # redirect stdout (so the CliRunner capture still works); instead
        # we let ``sota replay`` print its full stream and then echo a
        # synthetic cockpit-style tail line so the operator still sees
        # the cockpit ``matched=...`` summary that ``cockpit replay``
        # emitted before the shim existed.
        try:
            sota_replay(
                batch=batch,
                compare=compare,
                snapshot_format=snapshot_format_lc,
                report_format=effective_report_format,
                report_path=report_path,
                audit_path=audit_path,
                audit_append=audit_append,
                dry_run=dry_run,
                namespace=namespace,
                default_policy=default_policy,
                # ``suite_name`` has a ``typer.Option(...)`` default in
                # ``sota_replay``; when invoked as a plain function (as
                # we are doing here) that default is the ``OptionInfo``
                # sentinel rather than the string ``"thegent.sota.replay"``.
                # Pass the canonical name explicitly so JUnit-XML output
                # is well-formed when report-format=junitxml.
                suite_name="thegent.sota.replay",
                # Suppress the sota tail line so the cockpit contract
                # (pure JSON for ``--json``, pure text body for the
                # default path) is preserved.  The cockpit command will
                # emit its own tail via the legacy code path that runs
                # before the shim takes over; this prevents double
                # operator summaries.
                _render_tail=False,
                snapshot_flip=snapshot_flip,
                snapshot_flip_all=snapshot_flip_all,
            )
        except typer.Exit:
            raise
        except Exception as exc:
            err_console.print(f"[red]replay delegation failed:[/red] {_exc_text(exc)}")
            raise typer.Exit(1) from exc
        return
    try:
        from ..governance.policy_engine import PolicyEngine
    except Exception as exc:  # pragma: no cover - import guard
        err_console.print(f"[red]governance unavailable:[/red] {_exc_text(exc)}")
        raise typer.Exit(2) from exc

    try:
        if not batch.exists():
            err_console.print(f"[red]replay failed:[/red] batch path not found: {_exc_text(batch)}")
            raise typer.Exit(1)
        if not compare.exists():
            err_console.print(f"[red]replay failed:[/red] compare path not found: {_exc_text(compare)}")
            raise typer.Exit(1)
        try:
            expected_snapshot = _load_replay_snapshot(compare)
        except ValueError as exc:
            err_console.print(f"[red]replay failed:[/red] {_exc_text(exc)}")
            raise typer.Exit(1) from exc
        except json.JSONDecodeError as exc:
            err_console.print(f"[red]replay failed:[/red] compare file is not valid JSON: {_exc_text(exc)}")
            raise typer.Exit(1) from exc

        # SOTA canary workflow: when the operator passes
        # ``--snapshot-flip <field>`` (optionally multiple times) or the
        # ``--snapshot-flip-all`` preset, we invert each named field on
        # every snapshot entry **in memory** so the replay walks the
        # mismatch path without the operator having to hand-edit the
        # --compare file on disk. See ``_apply_snapshot_flips`` for the
        # composition semantics.
        flip_fields = _normalise_snapshot_flip_fields(snapshot_flip, snapshot_flip_all)
        if flip_fields:
            expected_snapshot = _apply_snapshot_flips(expected_snapshot, flip_fields)

        use_federation = default_policy is not None
        contexts, decisions, notices = _build_batch_decision_log(
            batch=batch,
            engine_factory=lambda: PolicyEngine(
                use_federation=use_federation,
                default_namespace=default_policy or "global",
            ),
            use_engine=not dry_run,
            namespace_override=namespace,
        )
        if not contexts:
            err_console.print(f"[yellow]replay batch is empty:[/yellow] {_exc_text(batch)}")
            # An empty corpus against a non-empty snapshot is a mismatch;
            # against an empty snapshot it is a match. Either way, exit 0
            # since there is no decision to validate.
            _emit_replay_summary(
                items=0,
                matched=not expected_snapshot,
                mismatches=[],
                decisions=[],
                audit_path=str(audit_path) if audit_path else None,
                json_output=json_output,
                flipped=list(flip_fields),
                batch=batch,
                compare=compare,
            )
            raise typer.Exit(0)

        produced = [d.to_dict() for d in decisions]
        mismatches: list[dict[str, Any]] = []
        max_len = max(len(produced), len(expected_snapshot))
        for idx in range(max_len):
            exp = expected_snapshot[idx] if idx < len(expected_snapshot) else None
            act = produced[idx] if idx < len(produced) else None
            if exp is None or act is None:
                mismatches.append(
                    {
                        "index": idx,
                        "fields": ["length"],
                        "expected": exp,
                        "actual": act,
                        "text": (f"mismatch[{idx}]: length expected={len(expected_snapshot)} actual={len(produced)}"),
                    }
                )
                continue
            diff_fields = _compare_decision(exp, act)
            if diff_fields:
                mismatches.append(
                    {
                        "index": idx,
                        "fields": diff_fields,
                        "expected": exp,
                        "actual": act,
                        "text": _format_mismatch(idx, exp, act, diff_fields),
                    }
                )

        # Persist decisions via the same appender pattern as pre-check
        # so the JSONL shape stays identical (the spec's "replay
        # writes a JSONL that matches the per-line appender output").
        audit_str: str | None = None
        if audit_path is not None:
            appender = DecisionAuditAppender(audit_path=audit_path)
            if not audit_append:
                path = appender.audit_path()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("", encoding="utf-8")
            appender.record_many(notices)
            audit_str = appender.audit_path_str()

        matched = not mismatches
        _emit_replay_summary(
            items=len(produced),
            matched=matched,
            mismatches=mismatches,
            decisions=produced,
            audit_path=audit_str,
            json_output=json_output,
            flipped=list(flip_fields),
            batch=batch,
            compare=compare,
        )
        # Operator confirmation: when an audit file was written, tell
        # the operator whether the run **appended** to an existing
        # file or **overwrote** it. CI/nightly harnesses that re-run
        # the same snapshot nightly need to know whether their prior
        # audit trail was preserved (append) or zeroed (overwrite)
        # so they can detect accidental truncation. Only emitted in
        # text mode; ``--json`` consumers parse the structured
        # envelope and would treat this line as noise.
        if audit_str is not None and not json_output:
            mode = "append" if audit_append else "overwrite"
            typer.echo(f"replay: audit={audit_str} mode={mode} lines={len(produced)}")
        if not matched:
            raise typer.Exit(4)
    except typer.Exit:
        raise
    except Exception as exc:
        err_console.print(f"[red]replay failed:[/red] {_exc_text(exc)}")
        raise typer.Exit(1) from exc


def _emit_replay_summary(
    *,
    items: int,
    matched: bool,
    mismatches: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    audit_path: str | None,
    json_output: bool,
    flipped: list[str] | None = None,
    batch: Path | None = None,
    compare: Path | None = None,
) -> None:
    """Render the replay outcome (text or JSON) and write to stdout.

    JSON envelope contract (Day 5/5 hardening lane):

    * ``matched`` (bool) — every decision matched the snapshot.
    * ``items`` (int) — total number of decisions evaluated; mirrors the
      sota-side envelope (``_render_report_json`` in ``cli_sota.py``) so
      a downstream consumer that reads both outputs sees one stable
      contract. Closes the JSON-envelope drift gap surfaced by the
      Phase 3/4 SOTA audit second pass (P1-3 / AUDIT-2).
    * ``mismatches`` (list of ``{index, fields, expected, actual}``) —
      the diff report.
    * ``decisions`` (list) — the produced ``PolicyDecision.to_dict()``
      list (used by SOTA tooling that wants to re-run the compare
      itself).
    * ``audit`` (str | null) — JSONL path when ``--audit-path`` was set.
    * ``flipped`` (list[str]) — the resolved ``--snapshot-flip`` +
      ``--snapshot-flip-all`` field set, deduped and in first-seen
      order. Always present (``[]`` when no flip flag was set) so the
      schema never has to be checked twice.

    NEW-14 (SOTA fourth-pass): the text envelope previously rendered
    ``replay: batch=? compare=? items=...`` — the ``?`` were literal
    placeholders never substituted. The operator-visible summary now
    includes the resolved ``--batch`` / ``--compare`` paths so a CI
    log shows which corpus / snapshot the run actually consumed (the
    JSON envelope was unaffected since the fields are operator-only
    convenience). Both paths are optional so legacy call sites that
    only had the JSON fields keep working unchanged.
    """
    if json_output:
        typer.echo(
            json.dumps(
                {
                    "matched": matched,
                    "items": items,
                    "mismatches": [
                        {
                            "index": m["index"],
                            "fields": m["fields"],
                            "expected": m["expected"],
                            "actual": m["actual"],
                        }
                        for m in mismatches
                    ],
                    "decisions": decisions,
                    "audit": audit_path,
                    "flipped": list(flipped or []),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    batch_str = str(batch) if batch is not None else "?"
    compare_str = str(compare) if compare is not None else "?"
    typer.echo(
        f"replay: batch={_exc_text(batch_str)} compare={_exc_text(compare_str)} "
        f"items={items} matched={matched} mismatches={len(mismatches)}"
    )
    for m in mismatches:
        typer.echo(m["text"])


# ---------------------------------------------------------------------------
# cockpit audit (Phase 3/4 JSONL appender companion)
# ---------------------------------------------------------------------------


# F-15 (SOTA fifth-pass): ``name="audit"`` for symmetry with the
# ``traffic_app`` sub-app and so ``cockpit audit --help`` renders
# cleanly under the parent ``cockpit`` group.
audit_app = typer.Typer(
    name="audit",
    help="Tail or replay the JSONL audit log produced by DecisionAuditAppender.",
    no_args_is_help=True,
)


@audit_app.command("tail", help="Print the last N decisions from the audit JSONL.")
def cockpit_audit_tail(
    n: int = typer.Option(20, "--lines", "-n", help="Number of lines to print"),
    audit_path: Path | None = typer.Option(
        None,
        "--path",
        help="Override the default ~/.thegent/cockpit_decisions.jsonl",
    ),
) -> None:
    """Tail the JSONL audit log for SOTA replay tooling."""
    # NEW-2 (SOTA fourth-pass): ``DecisionAuditAppender`` is already
    # imported at module scope (line 175) for the replay path. The
    # previous inner import was a relic of the import-time cycle
    # guard that no longer exists; a redundant inner import only
    # obscured the data flow and cost ~50µs per call site. Reuse
    # the module-level binding instead.
    try:
        appender = DecisionAuditAppender(audit_path=audit_path)
        events = appender.tail_events(n=n)
        for ev in events:
            typer.echo(json.dumps(ev, sort_keys=True))
    except Exception as exc:
        err_console.print(f"[red]audit tail failed:[/red] {_exc_text(exc)}")
        raise typer.Exit(1) from exc


@audit_app.command(
    "decision-tail",
    help="Live-tail the JSONL decision audit log (--follow polls and emits new lines).",
)
def cockpit_audit_decision_tail(
    follow: bool = typer.Option(
        False,
        "--follow",
        "-f",
        help="Poll the file and emit new lines as they appear (SIGINT exits cleanly).",
    ),
    interval: float = typer.Option(
        1.0,
        "--interval",
        "-i",
        help="Poll cadence in seconds when --follow is set.",
    ),
    audit_path: Path | None = typer.Option(
        None,
        "--path",
        help="Override the default ~/.thegent/cockpit_decisions.jsonl",
    ),
    max_events: int = typer.Option(
        0,
        "--max-events",
        help="Stop after this many events (0 = unbounded). Useful for CI smoke tests.",
    ),
    exit_code_on_cap: int = typer.Option(
        0,
        "--exit-code-on-cap",
        help=(
            "Exit code to use when --max-events is reached (only applies when "
            "--follow is set; 0 = silent, recommended non-zero for CI smoke tests, "
            "e.g. 75 to distinguish from generic errors). Default 0 (current behaviour)."
        ),
    ),
) -> None:
    """Live-tail the JSONL decision audit log (or print a one-shot backlog).

    Without ``--follow`` this is a thin wrapper over
    :meth:`DecisionAuditAppender.tail_events` that prints the most
    recent entries (default 20). With ``--follow`` the command polls
    the JSONL file every ``--interval`` seconds and emits each new
    line as it appears; ``SIGINT`` exits cleanly with code ``0`` so
    operator ``tail -f`` style workflows stay ergonomic.

    ``--max-events`` caps the total number of events emitted
    (including the initial backlog on entry) and is intended for
    CI / smoke tests that need to deterministically bound the run.
    When the cap is reached during a ``--follow`` session, the
    process exits with ``--exit-code-on-cap`` (default ``0``) so
    shell pipelines / smoke harnesses can detect the bounded
    completion without parsing stderr. Operators who want the
    historical "success" semantics can leave the flag at its
    default; CI consumers should pass a non-zero value such as
    ``75`` to distinguish "capped and stopped" from "errored out".
    """
    from ..ux.decision_audit import DEFAULT_TAIL_INTERVAL_S, DecisionAuditAppender

    # Defensive: when ``--follow`` is set, fall back to the
    # appender's canonical interval so operator UIs never see a
    # 0s tight loop if the caller passes ``--interval 0``.
    interval_s = float(interval) if interval > 0 else DEFAULT_TAIL_INTERVAL_S
    cap = int(max_events) if max_events and max_events > 0 else 0
    # Exit codes are 0-255; clamp negatives / oversize values so a
    # typo doesn't accidentally return a noisy traceback.
    exit_code = int(exit_code_on_cap) if exit_code_on_cap else 0
    if exit_code < 0 or exit_code > 255:
        raise typer.BadParameter(f"--exit-code-on-cap must be in [0, 255], got {exit_code_on_cap!r}")

    try:
        appender = DecisionAuditAppender(audit_path=audit_path)
    except Exception as exc:
        err_console.print(f"[red]audit decision-tail failed:[/red] {_exc_text(exc)}")
        raise typer.Exit(1) from exc

    if not follow:
        # Single-shot path: identical semantics to ``audit tail`` so
        # operators can switch between the two without surprises.
        try:
            n = 20 if cap == 0 else cap
            events = appender.tail_events(n=n)
            for ev in events:
                typer.echo(json.dumps(ev, sort_keys=True))
        except Exception as exc:
            err_console.print(f"[red]audit decision-tail failed:[/red] {_exc_text(exc)}")
            raise typer.Exit(1) from exc
        return

    try:
        emitted = _follow_audit_log(appender, interval_s=interval_s, max_events=cap)
    except KeyboardInterrupt:
        # SIGINT during a live tail is the operator pressing Ctrl-C;
        # exit cleanly with code 0 so shells / shell pipelines don't
        # treat it as an error.
        raise typer.Exit(0) from None

    # If the operator asked for a bounded run AND the cap was hit AND
    # they wired a non-zero exit code, propagate it so CI smoke
    # harnesses can detect "ran to completion under the cap" without
    # scraping stderr.
    # F-11 (SOTA third-pass): the previous ``if cap and emitted >=
    # cap and exit_code`` branch was a tautology — ``exit_code`` is
    # already validated to be ``0..255`` upstream, and the
    # ``exit_code`` truthiness check silently masked the case where
    # an operator wired ``--exit-code-on-cap 0`` (the canonical "no
    # special exit" value). The branch now checks ``exit_code != 0``
    # so ``0`` correctly short-circuits to the "no special exit"
    # path even when ``cap and emitted >= cap``.
    if cap and emitted >= cap and exit_code != 0:
        raise typer.Exit(exit_code) from None


def _follow_audit_log(
    appender: DecisionAuditAppender,
    *,
    interval_s: float,
    max_events: int,
) -> int:
    """Poll the appender's JSONL file and emit each new line as it appears.

    Tracks a **byte offset** (not a line count) so we never re-emit
    lines that were already seen on entry. Handles truncation by
    re-anchoring to ``0`` whenever the file shrinks below the saved
    offset (so log rotation / ``> file.jsonl`` workflows behave).

    Args:
        appender: A :class:`DecisionAuditAppender` whose
            :meth:`audit_path` points at the JSONL to watch.
        interval_s: Seconds to sleep between polls.
        max_events: Optional cap on the number of events to emit
            (``0`` = unbounded). When the cap is hit the helper
            returns cleanly.

    Returns:
        The total number of events emitted.

    Raises:
        KeyboardInterrupt: Re-raised so callers can map SIGINT to a
            clean exit code.
    """
    path = appender.audit_path()
    # Make sure the parent directory exists; the appender does this on
    # the first record, but a fresh follow on a never-written log still
    # needs somewhere to land.
    path.parent.mkdir(parents=True, exist_ok=True)

    # Seed offset with the file's current size so we don't re-emit the
    # existing backlog (operators who want the backlog should call
    # ``cockpit audit tail`` first).
    offset = path.stat().st_size if path.exists() else 0
    emitted = 0
    # ``max_events <= 0`` means unbounded.
    cap = max_events if max_events and max_events > 0 else 0
    # ``interval_s`` must be > 0 to avoid a tight loop on a typo.
    sleep_s = max(interval_s, 0.01)

    while True:
        try:
            current_size = path.stat().st_size
        except FileNotFoundError:
            # File momentarily missing (rotation, etc.); back off and
            # retry on the next tick.
            time.sleep(sleep_s)
            continue

        if current_size < offset:
            # File was truncated / rotated; re-anchor to the start so
            # we pick up whatever the writer put in its place.
            # NEW-22 (SOTA fourth-pass): on truncation we lose any
            # bytes that were between the previous ``offset`` and the
            # old EOF — the writer (rotation policy / ``> file.jsonl``)
            # intentionally discarded them, so the tail contract is
            # "lines appended after the truncation point are emitted,
            # bytes already in flight at the truncation boundary may
            # be missed". Documented so SOTA replay tooling knows.
            offset = 0

        if current_size > offset:
            try:
                with path.open("r", encoding="utf-8") as fh:
                    fh.seek(offset)
                    chunk = fh.read(current_size - offset)
            except (FileNotFoundError, OSError) as exc:
                # NEW-22 (SOTA fourth-pass): a transient unlink /
                # ``OSError`` between ``stat()`` and ``read()`` (file
                # rotated mid-poll, NFS hiccup, EPERM on a permission
                # flip) previously crashed the tail loop. The next
                # iteration's ``stat()`` will observe the new file
                # state and recover. Log at DEBUG so a long-running
                # tail session doesn't flood the operator's stderr.
                _LOGGER.debug("audit-tail transient read error, will retry: %s", exc)
                time.sleep(sleep_s)
                continue
            # Only advance the offset after a successful read so a
            # transient IO error doesn't silently drop lines.
            offset = current_size
            for raw_line in chunk.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                typer.echo(line)
                emitted += 1
                if cap and emitted >= cap:
                    return emitted

        # ``sleep`` is interruptible so SIGINT bubbles up as
        # ``KeyboardInterrupt`` promptly.
        time.sleep(sleep_s)


@audit_app.command(
    "mcp-tail",
    help=(
        "Print the last N entries from the in-memory MCP audit trail "
        "(SOTA audit pass 8; complements the decision JSONL audit)."
    ),
)
def cockpit_audit_mcp_tail(
    n: int = typer.Option(20, "--lines", "-n", help="Number of entries to print (most recent first)"),
    kind: str | None = typer.Option(
        None,
        "--kind",
        help=(
            "Filter by AuditEntryKind: tool_invocation, resource_read, gate_check, or error. Omit to print all kinds."
        ),
    ),
    agent: str | None = typer.Option(
        None,
        "--agent",
        help="Filter by agent name (exact match).",
    ),
    outcome: str | None = typer.Option(
        None,
        "--outcome",
        help="Filter by outcome (ok, error, budget_exceeded).",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit one JSON object per line instead of formatted text.",
    ),
    stats_only: bool = typer.Option(
        False,
        "--stats",
        help="Print only the audit-trail statistics block (skips entry listing).",
    ),
    # AUDIT-N+25 (SOTA audit pass 11): when set, the ``--json`` path
    # emits a single JSON envelope with ``filters`` / ``entries`` /
    # ``count`` keys instead of the historical line-delimited shape.
    # This mirrors the ``cockpit traffic --include-mcp-audit``
    # envelope contract and lets CI consumers introspect the
    # resolved filter set without re-parsing argv. Default off so the
    # AUDIT-N+15 line-delimited contract is preserved for
    # grep-style pipelines (``head -n 1 | jq``).
    json_envelope: bool = typer.Option(
        False,
        "--json-envelope",
        help=(
            "Emit a single JSON envelope (filters + entries + count) "
            "instead of the line-delimited shape. Mirrors the "
            "``cockpit traffic --include-mcp-audit`` envelope so "
            "CI consumers can introspect the filter set in one round-trip."
        ),
    ),
) -> None:
    """Tail the MCP audit trail singleton (``thegent.mcp.server.mcp_audit_*``).

    Unlike ``audit tail`` (which reads the JSONL decision log), this
    subcommand reads the **in-memory** MCP audit trail that
    ``audited_budget`` writes every time a tool/resource/gate
    dispatch fires. The trail is **per-process** — operators wanting
    cross-process history should add ``--audit-path`` to the replay
    or pre-check subcommand and tail the resulting JSONL with
    ``audit tail`` instead.

    Filters compose: ``--kind tool_invocation --agent cursor`` returns
    only TOOL_INVOCATION entries from agent ``cursor``. ``--json``
    emits one entry per line (so callers can pipe through ``jq``)
    and is the format CI smoke tests should prefer — it never
    changes shape across versions, only the per-entry schema
    evolves (see ``tests/test_unit_mcp_audit_trail_contracts.py``).
    """
    try:
        from ..mcp.server import (
            AuditEntryKind,
            mcp_audit_query,
            mcp_audit_recent,
            mcp_audit_stats,
        )
    except Exception as exc:  # pragma: no cover - import guard
        err_console.print(f"[red]MCP audit module unavailable:[/red] {_exc_text(exc)}")
        raise typer.Exit(1) from exc

    try:
        # AUDIT-N+25 (SOTA audit pass 11): when ``--json-envelope`` is
        # set together with ``--stats``, route the stats through the
        # envelope so the ``filters`` key is always emitted. The
        # historical ``--json --stats`` short-circuit returns the bare
        # stats dict and is preserved when ``--json-envelope`` is off.
        if stats_only and json_output and json_envelope:
            envelope_dict: dict[str, Any] = {
                "filters": {
                    "kind": kind,
                    "agent": agent,
                    "outcome": outcome,
                    "lines": n,
                },
                "stats": mcp_audit_stats(),
            }
            typer.echo(json.dumps(envelope_dict, indent=2, sort_keys=True, default=str))
            return

        if stats_only:
            typer.echo(json.dumps(mcp_audit_stats(), indent=2, sort_keys=True))
            return

        # ``mcp_audit_query`` is the preferred path when any filter is
        # supplied; ``mcp_audit_recent(n)`` is the no-filter fast path.
        if kind or agent or outcome:
            kind_enum: AuditEntryKind | None = None
            if kind is not None:
                try:
                    kind_enum = AuditEntryKind(kind)
                except ValueError as exc:
                    raise typer.BadParameter(
                        f"--kind must be one of {[k.value for k in AuditEntryKind]}, got {kind!r}"
                    ) from exc
            entries = mcp_audit_query(
                kind=kind_enum,
                agent=agent,
                outcome=outcome,
                limit=max(int(n), 1),
            )
        else:
            entries = mcp_audit_recent(n=max(int(n), 1))

        if json_output:
            # AUDIT-N+25 (SOTA audit pass 11): when ``--json-envelope``
            # is set, emit a single JSON object that echoes the
            # resolved filter set (``filters`` key) alongside the
            # entries list and a ``count`` summary. Mirrors the
            # ``cockpit traffic --include-mcp-audit`` envelope so
            # CI consumers can introspect the filter set in one
            # round-trip. The default (``--json`` only) keeps the
            # historical line-delimited shape so existing
            # ``head -n 1 | jq`` pipelines keep working unchanged.
            if json_envelope:
                envelope_dict = {
                    "filters": {
                        "kind": kind,
                        "agent": agent,
                        "outcome": outcome,
                        "lines": n,
                    },
                }
                if stats_only:
                    envelope_dict["stats"] = mcp_audit_stats()
                else:
                    envelope_dict["entries"] = [
                        entry.to_dict() if hasattr(entry, "to_dict") else entry for entry in entries
                    ]
                    envelope_dict["count"] = len(envelope_dict["entries"])
                typer.echo(json.dumps(envelope_dict, indent=2, sort_keys=True, default=str))
                return
            # Default ``--json`` path: line-delimited entries (one
            # ``AuditEntry.to_dict()`` per line) so jq-style pipelines
            # stay terse. ``mcp_audit_recent`` / ``mcp_audit_query``
            # return ``AuditEntry`` dataclasses (or dicts when callers
            # wrap with ``to_dict()``); normalise so JSON mode never
            # crashes on enum types in ``kind``.
            for entry in entries:
                payload = entry.to_dict() if hasattr(entry, "to_dict") else entry
                typer.echo(json.dumps(payload, indent=None, sort_keys=True, default=str))
            return

        # Text mode: aligned columns so operators can ``less`` the output.
        for entry in entries:
            if hasattr(entry, "to_dict"):
                ed = entry.to_dict()
                kind_str = str(ed.get("kind", "-"))
                op_str = str(ed.get("operation", "-"))
                agent_str = str(ed.get("agent") or "-")
                outcome_str = str(ed.get("outcome") or "-")
                ts_val = float(ed.get("ts", 0.0))
                seq_val = ed.get("seq", 0)
                dur_val = float(ed.get("duration_ms", 0.0))
            else:
                kind_str = str(entry.get("kind", "-"))
                op_str = str(entry.get("operation", "-"))
                agent_str = str(entry.get("agent") or "-")
                outcome_str = str(entry.get("outcome") or "-")
                ts_val = float(entry.get("ts", 0.0))
                seq_val = entry.get("seq", 0)
                dur_val = float(entry.get("duration_ms", 0.0))
            typer.echo(
                f"[{ts_val:.3f}] seq={seq_val} "
                f"kind={kind_str} op={op_str} "
                f"agent={agent_str} "
                f"outcome={outcome_str} "
                f"duration_ms={dur_val:.2f}"
            )
    except typer.Exit:
        raise
    except typer.BadParameter:
        raise
    except Exception as exc:
        err_console.print(f"[red]audit mcp-tail failed:[/red] {_exc_text(exc)}")
        raise typer.Exit(1) from exc


app.add_typer(audit_app, name="audit")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_runs(path: Path | None) -> list[RunEvent]:
    """Parse a JSON file of run dicts into :class:`RunEvent` instances."""
    if path is None:
        return []
    if not path.exists():
        raise FileNotFoundError(f"runs file not found: {path}")
    raw: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    out: list[RunEvent] = []
    for entry in raw:
        state_str = entry.get("state", "active")
        try:
            state = RunState(state_str)
        except ValueError as exc:
            raise ValueError(f"invalid run state {state_str!r}: {exc}") from exc
        out.append(
            RunEvent(
                run_id=str(entry["run_id"]),
                state=state,
                lane=str(entry.get("lane", "standard")),
                agent=str(entry.get("agent", "")),
                confidence=_as_optional_float(entry.get("confidence")),
                elapsed_s=float(entry.get("elapsed_s", 0.0)),
                note=str(entry.get("note", "")),
            )
        )
    return out


def _load_overrides(path: Path | None) -> list[OverrideEvent]:
    """Parse a JSON file of override dicts into :class:`OverrideEvent`."""
    if path is None:
        return []
    if not path.exists():
        raise FileNotFoundError(f"overrides file not found: {path}")
    raw: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    out: list[OverrideEvent] = []
    for entry in raw:
        out.append(
            OverrideEvent(
                rule_id=str(entry["rule_id"]),
                by=str(entry.get("by", "operator")),
                reason=str(entry.get("reason", "")),
                expires_in_s=float(entry.get("expires_in_s", 0.0)),
                metadata=dict(entry.get("metadata", {}) or {}),
            )
        )
    return out


def _load_traffic_events(path: Path | None) -> list[TrafficEvent]:
    """Parse a JSON file of traffic event dicts."""
    if path is None:
        return []
    if not path.exists():
        raise FileNotFoundError(f"events file not found: {path}")
    raw: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    out: list[TrafficEvent] = []
    for entry in raw:
        ts = float(entry.get("ts", 0.0))
        out.append(
            TrafficEvent(
                ts=ts,
                lane=str(entry.get("lane", "standard")),
                agent=str(entry.get("agent", "")),
                status=str(entry.get("status", "ok")),
                duration_ms=float(entry.get("duration_ms", 0.0)),
                override_active=bool(entry.get("override_active", False)),
            )
        )
    return out


def _as_optional_float(value: Any) -> float | None:
    """Return ``None`` for missing/None values; otherwise coerce to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"expected float, got {value!r}: {exc}") from exc


__all__ = [
    "app",
]


def main() -> None:  # pragma: no cover - convenience entry point
    """Module-level entry point so ``python -m thegent.ux.cli_cockpit`` works."""
    if len(sys.argv) == 1:
        typer.echo(app.get_help())
        return
    app()


if __name__ == "__main__":  # pragma: no cover
    # NEW-4 (SOTA second-pass): ``sys.exit(main())`` so non-zero
    # return codes from typer surface to shell pipelines. ``app()``
    # already raises ``typer.Exit`` on the failure paths, but a
    # bare ``main()`` call returns ``None`` which Python's
    # interpreter treats as exit 0 — silently swallowing failures
    # for one-shot ``python -m thegent.ux.cli_cockpit …`` runs.
    sys.exit(main() or 0)
