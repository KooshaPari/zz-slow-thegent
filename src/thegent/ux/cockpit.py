"""Operator Cockpit: 4-pane live dashboard for thegent runs.

Implements:

* WP-4001 (Batch 7A) — Operator cockpit with traffic/lane/confidence/overrides
* FR-015, FR-039 — Progressive disclosure for transport / model picks
* FR-UX-007, OBS8, P-060, P-090, P-092 — operator-first UX

The cockpit is a **plain-Python** rendering engine that produces a single
``render()`` string per frame.  It does not depend on ``textual``,
``prompt_toolkit``, or any curses binding so it can be embedded in
non-interactive contexts (logs, ``rich.console.Console.print``,
``rich.live.Live``, CI capture, etc.).

Layout (4 panes):
    ┌───────────────────────┬─────────────────────────┐
    │ 1. Live Runs          │ 2. Lane Distribution    │
    │    (active, queued)   │    (counts per lane)     │
    ├───────────────────────┼─────────────────────────┤
    │ 3. Confidence Spark   │ 4. Active Overrides     │
    │    (P50, P95 trend)   │    (TTL countdowns)     │
    └───────────────────────┴─────────────────────────┘

The cockpit is **stateful**: callers feed it ``tick(events)`` once per
``DAG_TICK_MS`` (default 1000ms) and read out ``render()`` or individual
``snapshot()`` for downstream consumers.

Public surface:
  - ``CockpitPane`` — enum of the four panes
  - ``CockpitConfig`` — dataclass configuring the cockpit
  - ``OperatorCockpit`` — main entry point; ``tick()`` then ``render()``
  - ``render_cockpit(events)`` — convenience wrapper for one-shot rendering

Traces to: FR-015 (progressive disclosure), FR-039 (transport hints),
          FR-UX-007 (operator cockpit), OBS8 (realtime telemetry),
          P-060 (lane routing), P-090 (cockpit latency SLO),
          P-092 (progressive disclosure), WP-4001 (cockpit scaffolding),
          WP-4002 (explanations companion).
"""

from __future__ import annotations

import logging
import re
import threading
import time
import weakref
from collections import Counter, deque
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from thegent.i18n.aria import annotate

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ARIA annotation helpers
# ---------------------------------------------------------------------------


def _annotate_pane_close(
    closing_line: str,
    *,
    label: str,
    role: str = "status",
    aria_live: str = "polite",
) -> str:
    """Return ``closing_line`` with an ARIA annotation trailer appended.

    The trailer rides on the closing ``└─...─┘`` border of a pane so
    the metadata travels with the box without disturbing the row
    layout (the box's right border stays aligned). An empty ``label``
    falls back to the bare closing line so callers can opt out of
    annotation by passing ``label=""``.

    L17 I18n/A11y: the cockpit renderers surface WAI-ARIA-style
    metadata so screen readers and TUI inspection tooling can pick up
    the pane's role + live-region semantics without scraping free-form
    text. ``role="status"`` + ``aria-live="polite"`` is the task-brief
    default for live status panes; ``role="log"`` is used for the
    decision-history pane.
    """
    if not label:
        return closing_line
    return annotate(
        closing_line,
        role=role,
        aria_live=aria_live,
        aria_label=label,
    )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


DEFAULT_DAG_TICK_MS = 1000
MAX_RUNS_PANE_ROWS = 14
MAX_OVERRIDE_PANE_ROWS = 6
# Maximum number of decision notices kept in the bounded deque. Older
# notices roll off silently; full history is reachable via the JSONL
# audit log (``DecisionAuditAppender``).
MAX_DECISION_NOTICES = 64
# Cap on rendered rows in the decision-history pane. Slightly smaller
# than the bounded deque size (64) so the inline pane stays scannable;
# older notices are reachable through the JSONL audit log.
MAX_DECISION_PANE_ROWS = 8
SPARKLINE_CHARS = "▁▂▃▄▅▆▇█"
# How long an OverrideExpiryNotice stays visible in the inline banner
# before fading out. 30s matches the cockpit tick cadence and gives the
# operator enough time to glance up between DAG ticks.
OVERRIDE_BANNER_MAX_AGE_S = 30.0
# Default wall-clock function (overridable per-cockpit for deterministic
# audit replays; see ``OperatorCockpit(clock=...)``).
# NEW-15 (SOTA third-pass): drop the ``staticmethod(time.time)`` wrapper.
# ``staticmethod`` returns a descriptor that is not directly callable;
# the previous declaration would raise ``TypeError: 'staticmethod'
# object is not callable`` if the ``clock or _DEFAULT_CLOCK`` branch
# ever fell through (e.g. when ``OperatorCockpit.__init__`` was called
# without an explicit ``clock=...`` kwarg from a module that monkey-
# patched the class attribute). Using ``time.time`` directly is the
# canonical, well-tested form.
_DEFAULT_CLOCK: Callable[[], float] = time.time


class CockpitPane(StrEnum):
    """The panes of the operator cockpit.

    AUDIT-N+15 added the ``TRAFFIC`` pane so operators see live
    ``TrafficDashboard`` metrics (count, rps, error_rate, p50/p95)
    inline rather than only through the progress bar.

    AUDIT-N+18 added the ``DORMANT_CORE`` pane so the cockpit
    surfaces the AUDIT-N+13 dormant-core trend envelope (escalation
    count, past-SLA count, freshness bucket) alongside the live
    traffic metrics so operators see one unified snapshot of the
    dormant-core reconciliation rather than only through
    ``observe summary``.
    """

    RUNS = "runs"
    LANES = "lanes"
    CONFIDENCE = "confidence"
    OVERRIDES = "overrides"
    TRAFFIC = "traffic"
    DORMANT_CORE = "dormant_core"


class RunState(StrEnum):
    """Lifecycle states of a run."""

    QUEUED = "queued"
    ACTIVE = "active"
    PAUSED = "paused"
    DONE = "done"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Configuration & event model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CockpitConfig:
    """Configuration knobs for the cockpit render."""

    title: str = "thegent operator cockpit"
    tick_ms: int = DEFAULT_DAG_TICK_MS
    show_sparkline: bool = True
    sparkline_width: int = 24
    progress_total: int = 100  # for the progress bar (P-081)
    progress_label: str = "Run progress"
    pane_labels: Mapping[CockpitPane, str] = field(
        default_factory=lambda: {
            CockpitPane.RUNS: "Live Runs",
            CockpitPane.LANES: "Lane Distribution",
            CockpitPane.CONFIDENCE: "Confidence (P50/P95)",
            CockpitPane.OVERRIDES: "Active Overrides",
            CockpitPane.TRAFFIC: "Traffic",
            CockpitPane.DORMANT_CORE: "Dormant Core",
        }
    )


@dataclass(frozen=True)
class RunEvent:
    """Single run state observed by the cockpit (per tick)."""

    run_id: str
    state: RunState
    lane: str = "standard"
    agent: str = ""
    confidence: float | None = None
    elapsed_s: float = 0.0
    note: str = ""


@dataclass(frozen=True)
class OverrideEvent:
    """Single active override observed by the cockpit."""

    rule_id: str
    by: str
    reason: str
    expires_in_s: float
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OverrideExpiryNotice:
    """A single most-recent override-expiry event surfaced to the operator.

    Bridges WP-3003 (``OverrideEventEmitter`` writes the
    ``governance.override.expired`` JSONL line) to the WP-4001 cockpit UX
    surface. Operators can connect an :class:`OverrideExpiryMonitor` (or
    any tail-reader of the JSONL log) and call
    :meth:`OperatorCockpit.record_override_event` to surface recent
    expiry lines inline in the cockpit header.

    Attributes:
        rule_id: Policy rule whose override expired (e.g. ``"no-network"``).
        owner: Principal who applied the override.
        reason: Free-form reason text (``"ttl_elapsed"`` by default).
        expired_at: Unix timestamp of expiry.
        age_s: Seconds since expiry at render time. Updated lazily on
            every render so an old notice naturally fades out.
    """

    rule_id: str
    owner: str
    reason: str
    expired_at: float
    age_s: float = 0.0


@dataclass(frozen=True)
class DecisionNotice:
    """A governance decision surfaced to the operator cockpit (WP-3001 -> WP-4001).

    Bridges :class:`thegent.governance.policy_engine.PolicyDecision` into the
    cockpit UX so verdicts (allow / deny / warn), reason codes, and the
    matched ``rule_id`` are visible inline as the runtime produces them.

    Attributes:
        verdict: One of ``"allow"``, ``"deny"``, ``"warn"`` (matches
            ``thegent.governance.policy_engine.Verdict`` values).
        reason_code: Machine-readable reason code (``ReasonCode`` value).
        rule_id: Matched policy rule (or ``None`` when no rule matched).
        agent: Originating agent name (truncated for display).
        lane: Originating lane (e.g. ``"critical"``).
        evaluated_at: Unix timestamp of decision; used for stale-decay.
        reason: Free-form human-readable reason string.
    """

    verdict: str
    reason_code: str
    rule_id: str | None
    agent: str = ""
    lane: str = "standard"
    evaluated_at: float = 0.0
    reason: str = ""

    def is_deny(self) -> bool:
        """Whether the decision blocked the request."""
        return self.verdict == "deny"

    def is_warn(self) -> bool:
        """Whether the decision emitted a warning (admissible but flagged)."""
        return self.verdict == "warn"


# ---------------------------------------------------------------------------
# Internal state containers
# ---------------------------------------------------------------------------


@dataclass
class _CockpitState:
    """Mutable internal state of the cockpit (single source of truth).

    ``confidence_history`` and ``override_notices`` are bounded ``deque``
    collections to prevent unbounded memory growth across a long-running
    operator session.

    AUDIT-N+15: ``traffic_dashboard`` is the optional :class:`TrafficDashboard`
    attached via :meth:`OperatorCockpit.attach_traffic`. When set, the
    cockpit renders a dedicated traffic pane (count, rps, error_rate,
    p50/p95, recent by-status split).
    """

    last_tick_at: float = 0.0
    runs: dict[str, RunEvent] = field(default_factory=dict)
    overrides: dict[str, OverrideEvent] = field(default_factory=dict)
    confidence_history: deque[float] = field(default_factory=lambda: deque(maxlen=1024))
    override_notices: deque[OverrideExpiryNotice] = field(default_factory=lambda: deque(maxlen=32))
    decision_notices: deque[DecisionNotice] = field(
        default_factory=lambda: deque(maxlen=MAX_DECISION_NOTICES),
    )
    last_progress: tuple[int, int] = (0, 0)  # (done, total)
    traffic_dashboard: Any = None  # TrafficDashboard | None — imported lazily to avoid cycle
    # AUDIT-N+18: dormant-core envelope source. Accepts any callable
    # returning a dict (the AUDIT-N+13 ``_build_observe_trend_payload``
    # output shape) or any object exposing ``.summary()`` like
    # ``TrafficDashboard``. Stored as ``Any`` so the cockpit does not
    # force an import of the dormant-core service module at cockpit
    # import time.
    dormant_source: Any = None
    # AUDIT-N+22 (SOTA audit pass 8, Lane A): MCP audit-trail source.
    # Same shape as ``dormant_source`` — accepts any zero-arg callable
    # returning the audit-stats dict (e.g.
    # ``thegent.mcp.server.mcp_audit_stats``) or any object exposing a
    # ``.summary()`` method. Stored as ``Any`` to keep the cockpit
    # import graph cycle-free.
    audit_source: Any = None


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


def _progress_bar(done: int, total: int, *, width: int = 24) -> str:
    """Return a textual progress bar ``[####------]  42%``.

    Used by the cockpit header (P-081, FR-UX-007) to surface run progress.
    Width and percent are emitted in a single round-trip-safe string.
    """
    if total <= 0:
        return "[" + " " * width + "]   -"
    pct = max(0, min(100, int(100 * done / total)))
    filled = int(width * pct / 100)
    return f"[{'#' * filled}{'-' * (width - filled)}] {pct:3d}%"


def _sparkline(values: Sequence[float], width: int) -> str:
    """Return a unicode sparkline representation.

    Maps a sequence of values to the eight ``SPARKLINE_CHARS`` characters.
    Empty input or all-equal values produce a flat line — never raises.
    """
    if not values:
        return "·" * width
    if width <= 0:
        return ""
    # Coerce to a windowed view
    windowed = list(values[-width:])
    if len(windowed) < width:
        windowed = ([0.0] * (width - len(windowed))) + windowed
    lo, hi = min(windowed), max(windowed)
    if hi - lo < 1e-9:
        return "·" * width
    out = []
    for v in windowed:
        idx = int((v - lo) / (hi - lo) * (len(SPARKLINE_CHARS) - 1))
        out.append(SPARKLINE_CHARS[idx])
    return "".join(out)


def _truncate(text: str, limit: int) -> str:
    """Truncate ``text`` to ``limit`` chars, appending an ellipsis when needed.

    A non-positive ``limit`` returns the empty string.
    """
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    if limit == 1:
        return text[:1]
    return text[: limit - 1] + "…"


def _pad_box_row(row: str, interior: int) -> str:
    """Pad / truncate a box row so the interior width matches ``interior``.

    AUDIT-N+18: the DORMANT_CORE pane renders inside a fixed-width box
    (``box_width`` chars). The body rows must always have exactly
    ``interior = box_width - 2`` characters between the leading and
    trailing ``│`` so the right border aligns. When a producer hands us
    a longer-than-expected token (a runaway ``freshness_bucket``, a
    long ``trend_scope_signature``) the row would otherwise push the
    right border outwards. The renderer truncates the *content* to
    fit, never expands the box — the box stays compact for the common
    case and degrades gracefully under input pressure.
    """
    # Strip the borders if present so the math is straightforward.
    body = row[1:-1] if len(row) >= 2 and row[0] == "│" and row[-1] == "│" else row
    if len(body) > interior:
        body = body[:interior]
    elif len(body) < interior:
        body = body + " " * (interior - len(body))
    return f"│{body}│"


# F-9 + NEW-5 (SOTA third-pass): strip ANSI / Rich control sequences from
# operator-rendered strings so a producer that stows a Rich markup token
# or an ANSI escape in a decision reason / rule_id cannot corrupt the
# operator terminal (or worse, inject escape sequences that re-write the
# surrounding UI). The cockpit renders plain ASCII/Unicode only — any
# control character outside the printable BMP range that lands in a
# reason field is replaced with a placeholder so the pane layout is
# preserved. ``markup=False`` semantics: we never feed this output to
# ``Rich.print(..., markup=True)``.
_ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
_RICH_MARKUP_PATTERN = re.compile(r"\[/?[a-zA-Z0-9_=#,. -]+\]")


def _sanitize_console_text(text: str, *, max_len: int = 256) -> str:
    """Strip ANSI/Rich control sequences and non-printable chars from ``text``.

    F-9 + NEW-5 (SOTA third-pass): a malicious or buggy producer
    can stash ``\\x1b[31m`` (ANSI red) or ``[red]...[/red]`` (Rich
    markup) inside a ``DecisionNotice.reason`` field; without
    sanitisation, the deny banner would render the text as if it
    were a styled UI fragment, potentially wiping the surrounding
    banner or — when consumed by ``err_console.print(...)`` with
    ``markup=True`` — injecting arbitrary markup. We strip both
    classes plus all C0/C1 control characters, then truncate to
    ``max_len`` so a 10 MiB reason field cannot blow the terminal
    width. The placeholder ``_`` is a single ASCII character so the
    pane layout survives.
    """
    if not text:
        return ""
    out = _ANSI_ESCAPE_PATTERN.sub("", text)
    out = _RICH_MARKUP_PATTERN.sub("", out)
    # Drop remaining C0 controls (except space) and C1 controls so
    # bell / backspace / CSI sequences from any source are gone.
    out = "".join(ch if ch.isprintable() or ch == " " else "_" for ch in out)
    if len(out) > max_len:
        out = _truncate(out, max_len)
    return out


def _format_run_row(ev: RunEvent) -> str:
    """Format a single run as a cockpit row."""
    state_glyph = {
        RunState.QUEUED: "·",
        RunState.ACTIVE: "▶",
        RunState.PAUSED: "⏸",
        RunState.DONE: "✓",
        RunState.ERROR: "✗",
    }.get(ev.state, "?")
    conf_str = f"{ev.confidence:.2f}" if ev.confidence is not None else "  - "
    return f"{state_glyph} {ev.run_id:<10}  {ev.lane:<9}  {ev.agent:<10}  c={conf_str}  {ev.elapsed_s:5.1f}s"


def _format_override_row(ev: OverrideEvent) -> str:
    """Format a single override row with TTL countdown."""
    # F-9 + NEW-5 (SOTA third-pass): sanitise ``reason`` so a producer
    # cannot inject ANSI/Rich markup via the override reason field.
    return f"! {_sanitize_console_text(ev.rule_id, max_len=22):<22}  by {_sanitize_console_text(ev.by, max_len=8):<8}  ⏳ {ev.expires_in_s:5.0f}s  {_sanitize_console_text(ev.reason, max_len=32)}"


# ---------------------------------------------------------------------------
# Main cockpit class
# ---------------------------------------------------------------------------


class OperatorCockpit:
    """The 4-pane operator cockpit.

    Usage::

        cockpit = OperatorCockpit(config=CockpitConfig())
        cockpit.tick(runs=[RunEvent(...)], overrides=[OverrideEvent(...)])
        print(cockpit.render())
    """

    def __init__(
        self,
        config: CockpitConfig | None = None,
        *,
        clock: Callable[[], float] | None = None,
        audit_appender: DecisionAuditAppender | None = None,
        auto_tail: bool = False,
        tail_interval_s: float = 1.0,
    ) -> None:
        """Build the operator cockpit.

        Args:
            config: Optional :class:`CockpitConfig`; defaults to a fresh config.
            clock: Injectable wall-clock. Default ``time.time``. Useful for
                deterministic audit replays.
            audit_appender: Optional :class:`DecisionAuditAppender`. When
                provided *and* ``auto_tail`` is ``True``, the cockpit spins
                up a :class:`DecisionAuditTailer` so every
                :meth:`record_decision` call lands in the JSONL audit log
                without manual wiring. Production deployments should pass
                their own appender (so audit-path / cache / clock are
                controlled at boot); tests can pass an appender with a
                tmp_path and ``auto_tail=False`` for synchronous drains.
            auto_tail: Start a background :class:`DecisionAuditTailer`
                against ``audit_appender``. Ignored when no appender is
                supplied. Default ``False`` keeps the cockpit free of
                background threads in tests and short-lived scripts.
            tail_interval_s: Drain cadence for the background tailer.
                Same default as :data:`DEFAULT_TAIL_INTERVAL_S`.

        The cockpit owns the tailer for the lifetime of the instance; it
        is stopped on :meth:`shutdown` (and on garbage collection as a
        safety net so test sessions don't leak threads).
        """
        self.config = config or CockpitConfig()
        self._state = _CockpitState()
        # counters
        self._frame_count = 0
        self._last_render_ms = 0.0
        # State mutators (tick/reset) run concurrently with readers (render/
        # snapshot); serialise with an RLock so render can re-enter safely.
        self._lock = threading.RLock()
        # Clock function used for tick timestamps, banner age, render-time
        # metrics. Injected for deterministic audit replays; defaults to
        # ``time.time``. Monotonicity is the caller's responsibility.
        self._clock: Callable[[], float] = clock or _DEFAULT_CLOCK

        # Optional JSONL audit wiring. The appender is owned by the
        # caller (so multi-cockpit deployments can share one file
        # handle); the tailer is owned by the cockpit so the lifetime
        # matches the cockpit.
        self._audit_appender = audit_appender
        self._audit_tailer: DecisionAuditTailer | None = None
        self._tail_interval_s = float(tail_interval_s)
        if audit_appender is not None and auto_tail:
            self._start_audit_tailer()

        # Track whether ``shutdown`` was explicitly invoked so the
        # finaliser doesn't double-stop the tailer in production.
        self._shutdown_called = False
        weakref.finalize(self, _finalize_cockpit, self)

    # ------------------------------------------------------------- audit wiring

    def _start_audit_tailer(self) -> None:
        """Idempotently start the JSONL audit tailer, if configured.

        A no-op when ``audit_appender`` was not supplied at construction.
        Re-entrant (e.g. after a manual stop) — restarts a fresh thread.
        """
        if self._audit_appender is None:
            return
        from .decision_audit import DecisionAuditTailer  # local import to avoid cycle

        tailer = DecisionAuditTailer(
            cockpit=self,
            appender=self._audit_appender,
            interval_s=self._tail_interval_s,
        )
        tailer.start()
        self._audit_tailer = tailer

    def audit_appender(self) -> DecisionAuditAppender | None:
        """Return the JSONL audit appender the cockpit is wired to (or ``None``)."""
        return self._audit_appender

    def shutdown(self, timeout_s: float = 5.0) -> None:
        """Stop the background audit tailer (idempotent, safe to call twice).

        Production deployments should invoke this on graceful shutdown so
        the daemon :class:`DecisionAuditTailer` thread exits cleanly and
        no notices are lost mid-drain. Tests can lean on the finaliser
        registered in ``__init__``.
        """
        self._shutdown_called = True
        tailer = self._audit_tailer
        if tailer is not None:
            tailer.stop(timeout_s=timeout_s)
            self._audit_tailer = None

    # --------------------------------------------------------------- mutators

    def tick(
        self,
        *,
        runs: Iterable[RunEvent] | None = None,
        overrides: Iterable[OverrideEvent] | None = None,
        progress: tuple[int, int] | None = None,
    ) -> None:
        """Apply one ``DAG_TICK`` worth of events.

        ``runs``: full replacement set of current runs (idempotent per ``run_id``).
        ``overrides``: full replacement set of active overrides (idempotent).
        ``progress``: ``(done, total)`` for the header progress bar.
        """
        # NEW-18 (SOTA third-pass): read the clock under the lock so a
        # clock-injected cockpit that resets its clock between ticks
        # (deterministic audit replay, frozen-clock tests) sees a
        # single timestamp atomically applied. The previous
        # ``now = self._clock(); with self._lock:`` pattern read
        # ``self._clock`` outside the lock window, so a concurrent
        # ``set_clock`` interleaved between the read and the lock
        # acquire could land a timestamp sourced from the old clock
        # into state owned by the new clock. Symptom: deterministic
        # replays occasionally saw a header timestamp one tick
        # behind the pane timestamps; root cause was the un-locked
        # clock read.
        with self._lock:
            now = self._clock()
            self._state.last_tick_at = now
            if runs is not None:
                self._state.runs = {ev.run_id: ev for ev in runs}
            if overrides is not None:
                self._state.overrides = {ev.rule_id: ev for ev in overrides}
            if progress is not None:
                self._state.last_progress = progress
            # Update confidence sparkline history with newest run confidence.
            # The deque is bounded (maxlen=1024) so this cannot grow unbounded.
            for ev in self._state.runs.values():
                if ev.confidence is not None and -1e-6 <= ev.confidence <= 1.0 + 1e-6:
                    self._state.confidence_history.append(ev.confidence)

    def reset(self) -> None:
        """Reset cockpit state (used between sessions / tests)."""
        with self._lock:
            self._state = _CockpitState()
            self._frame_count = 0
            self._last_render_ms = 0.0

    def record_override_event(self, notice: OverrideExpiryNotice) -> None:
        """Push a most-recent override-expiry notice into the cockpit.

        Designed to be called from an :class:`OverrideExpiryMonitor`
        callback (WP-3003) so the operator sees expiry events inline in
        the cockpit header as soon as they fire.

        The notice deque is bounded (``maxlen=32``); the oldest notice is
        silently dropped once full. ``age_s`` is recomputed against the
        current wall clock on every render so the banner naturally
        fades.
        """
        if not isinstance(notice, OverrideExpiryNotice):  # defensive — surface config drift
            raise TypeError(f"record_override_event expects OverrideExpiryNotice, got {type(notice).__name__}")
        with self._lock:
            self._state.override_notices.append(notice)

    def record_decision(self, notice: DecisionNotice) -> None:
        """Push a governance-decision notice into the cockpit (WP-3001 -> WP-4001).

        Surfaces :class:`thegent.governance.policy_engine.PolicyDecision`
        payloads inline so operators can see verdicts / reason codes
        appear as the runtime produces them. ``deny`` verdicts are
        rendered as a focused banner (similar to override expiry); all
        other verdicts accumulate into a bounded ``decision_notices``
        deque and can be read out via :meth:`snapshot` for downstream
        consumers (CI hooks, log shippers).

        The deque is bounded (``maxlen=64``) so a long-lived operator
        session cannot grow unbounded. ``evaluated_at == 0`` is filled
        with the cockpit's clock for ergonomic zero-init.
        """
        if not isinstance(notice, DecisionNotice):
            raise TypeError(f"record_decision expects DecisionNotice, got {type(notice).__name__}")
        with self._lock:
            payload = notice
            if payload.evaluated_at <= 0.0:
                payload = DecisionNotice(
                    verdict=payload.verdict,
                    reason_code=payload.reason_code,
                    rule_id=payload.rule_id,
                    agent=payload.agent,
                    lane=payload.lane,
                    evaluated_at=self._clock(),
                    reason=payload.reason,
                )
            self._state.decision_notices.append(payload)

    # -------------------------------------------------------------- AUDIT-N+15 traffic pane

    def attach_traffic(self, dashboard: Any) -> OperatorCockpit:
        """Attach a :class:`TrafficDashboard` so the cockpit renders a TRAFFIC pane.

        AUDIT-N+15: the operator cockpit gains a dedicated TRAFFIC pane
        (count, rps, error_rate, p50_ms, p95_ms, recent by-status split)
        so operators see live traffic metrics inline rather than only
        through the progress bar. The dashboard is a borrowed reference;
        callers retain ownership and decide when to record events.

        The dashboard reference is stored under the cockpit's lock so
        the renderer can pick it up atomically. Pass ``None`` to detach.

        Returns ``self`` for fluent chaining::

            OperatorCockpit().attach_traffic(my_dashboard).render()
        """
        if dashboard is not None:
            # Local import keeps the cockpit module cycle-free; the
            # kpis.traffic module imports from cockpit if needed.
            from .kpis.traffic import TrafficDashboard

            if not isinstance(dashboard, TrafficDashboard):
                raise TypeError(f"attach_traffic expects TrafficDashboard, got {type(dashboard).__name__}")
        with self._lock:
            self._state.traffic_dashboard = dashboard
        return self

    def traffic_dashboard(self) -> Any:
        """Return the currently attached :class:`TrafficDashboard`, or ``None``.

        Read-only accessor used by ``snapshot()`` and tests.
        """
        with self._lock:
            return self._state.traffic_dashboard

    # -------------------------------------------------------------- AUDIT-N+18 dormant-core pane

    def attach_dormant_core(self, dormant_source: Any) -> OperatorCockpit:
        """Attach a dormant-core envelope source so the cockpit renders a DORMANT_CORE pane.

        AUDIT-N+18: wire the AUDIT-N+13 dormant-core trend envelope
        (``thegent.cli.commands.observability_impl._build_observe_trend_payload``
        output shape) into the cockpit so operators see live escalation
        count, past-SLA count, and freshness bucket inline alongside the
        AUDIT-N+15 traffic pane in a single unified snapshot.

        The source can be either:

        * A zero-argument callable returning the dormant-core trend
          dict (e.g. ``lambda: _build_observe_trend_payload(10)``).
        * Any object exposing a no-arg ``summary()`` method that returns
          a dict in the dormant-core envelope shape.

        The source is borrowed by reference — callers retain ownership
        and decide when the envelope is re-computed. Pass ``None`` to
        detach and disable the pane.

        Returns ``self`` for fluent chaining::

            OperatorCockpit().attach_dormant_core(my_source).render()

        The source reference is stored under the cockpit's lock so the
        renderer can pick it up atomically. No validation is performed
        on the source at attach time; the renderer defends against
        bad / throwing sources by rendering a single neutral line
        instead of crashing the cockpit.
        """
        with self._lock:
            self._state.dormant_source = dormant_source
        return self

    def dormant_core_source(self) -> Any:
        """Return the currently attached dormant-core source, or ``None``.

        Read-only accessor used by ``snapshot()`` and tests.
        """
        with self._lock:
            return self._state.dormant_source

    # -------------------------------------------------------------- AUDIT-N+22 MCP audit-trail pane

    def attach_audit_trail(self, audit_source: Any) -> OperatorCockpit:
        """Attach an MCP audit-trail source so the cockpit renders an MCP_AUDIT_STATS block.

        AUDIT-N+22 (SOTA audit pass 8, Lane A): wire the
        :data:`thegent.mcp.server.mcp_audit_wiring.mcp_audit_stats`
        singleton into the cockpit snapshot so operators see the live
        ``total_entries``, ``by_kind``, ``by_outcome``, ``error_count``,
        and ``p99_duration_ms`` gauges inline alongside the existing
        ``traffic`` and ``dormant_core`` blocks.

        The source can be either:

        * A zero-argument callable returning the audit-stats dict
          (e.g. ``thegent.mcp.server.mcp_audit_stats`` — note it is a
          function, not a method, so this works out of the box).
        * Any object exposing a no-arg ``summary()`` method that
          returns a dict in the audit-stats envelope shape
          (``total_entries``, ``max_entries``, ``by_kind``,
          ``by_outcome``, ``error_count``, ``avg_duration_ms``,
          ``p99_duration_ms``, ``oldest_seq``, ``newest_seq``).

        The source is borrowed by reference — callers retain
        ownership. Pass ``None`` to detach and disable the block.

        Returns ``self`` for fluent chaining::

            from thegent.mcp.server import mcp_audit_stats
            from thegent.ux.cockpit import OperatorCockpit

            cockpit = OperatorCockpit().attach_audit_trail(mcp_audit_stats)
            snapshot = cockpit.snapshot()
            assert "mcp_audit_stats" in snapshot
        """
        with self._lock:
            self._state.audit_source = audit_source
        return self

    def audit_trail_source(self) -> Any:
        """Return the currently attached audit-trail source, or ``None``.

        Read-only accessor used by :meth:`snapshot` and tests.
        """
        with self._lock:
            return self._state.audit_source

    def _invoke_attached(self, attr: str) -> dict[str, Any] | None:
        """Resolve an attached source (callable or ``.summary()``) to a dict.

        AUDIT-N+22 (SOTA audit pass 8, Lane A): generic helper that
        both :meth:`_invoke_dormant_core` and :meth:`_invoke_audit_stats`
        delegate to. Returns ``None`` when the source is unattached,
        raises, or returns a non-dict. The renderer uses this so a
        buggy producer (audit trail or dormant-core) cannot crash
        the cockpit.

        ``attr`` is the ``_CockpitState`` field name holding the
        source (e.g. ``"dormant_source"``, ``"audit_source"``).
        """
        with self._lock:
            source = getattr(self._state, attr, None)
        if source is None:
            return None
        try:
            payload = source() if callable(source) else source.summary()
        except Exception:  # noqa: BLE001 - never crash the cockpit.
            return None
        return payload if isinstance(payload, dict) else None

    def _invoke_dormant_core(self) -> dict[str, Any] | None:
        """Resolve the attached dormant-core source to a dict (or ``None``).

        Thin wrapper over :meth:`_invoke_attached` for the dormant-core
        slot. Kept for backwards compatibility with the AUDIT-N+18
        callers (renderer, ``cockpit_bridge`` consumers) that already
        use the named helper.
        """
        return self._invoke_attached("dormant_source")

    def _invoke_audit_stats(self) -> dict[str, Any] | None:
        """Resolve the attached MCP audit-trail source to a dict (or ``None``).

        AUDIT-N+22 (SOTA audit pass 8, Lane A): the snapshot block
        that surfaces the MCP audit trail alongside the live traffic
        pane. Defensive against missing/raising sources so a buggy
        audit-trail implementation cannot crash the operator cockpit.
        """
        return self._invoke_attached("audit_source")

    # -------------------------------------------------------------- snapshots

    def snapshot(self) -> dict[str, Any]:
        """Return a structured snapshot for downstream consumers (logs, JSON).

        Frontends that want plain text should use :meth:`render` instead.
        The snapshot is a consistent point-in-time copy under the cockpit's
        internal lock to avoid torn reads.
        """
        with self._lock:
            now = self._clock()
            runs = list(self._state.runs.values())
            overrides = list(self._state.overrides.values())
            lanes = Counter(ev.lane for ev in runs)
            return {
                "title": self.config.title,
                "tick_at": self._state.last_tick_at,
                "frame_count": self._frame_count,
                "runs": [
                    {
                        "run_id": r.run_id,
                        "state": r.state.value,
                        "lane": r.lane,
                        "agent": r.agent,
                        "confidence": r.confidence,
                        "elapsed_s": r.elapsed_s,
                        "note": r.note,
                    }
                    for r in runs
                ],
                "lanes": dict(lanes),
                "overrides": [
                    {
                        "rule_id": o.rule_id,
                        "by": o.by,
                        "reason": o.reason,
                        "expires_in_s": o.expires_in_s,
                        "metadata": dict(o.metadata),
                    }
                    for o in overrides
                ],
                "progress": self._state.last_progress,
                "confidence_history": list(self._state.confidence_history),
                "override_notices": [
                    {
                        "rule_id": n.rule_id,
                        "owner": n.owner,
                        "reason": n.reason,
                        "expired_at": n.expired_at,
                        "age_s": max(0.0, now - n.expired_at),
                    }
                    for n in self._state.override_notices
                ],
                "decision_notices": [
                    {
                        "verdict": d.verdict,
                        "reason_code": d.reason_code,
                        "rule_id": d.rule_id,
                        "agent": d.agent,
                        "lane": d.lane,
                        "evaluated_at": d.evaluated_at,
                        "age_s": max(0.0, now - d.evaluated_at) if d.evaluated_at > 0 else 0.0,
                        "reason": d.reason,
                    }
                    for d in self._state.decision_notices
                ],
                "last_render_ms": self._last_render_ms,
                "traffic": (
                    dict(self._state.traffic_dashboard.summary()) if self._state.traffic_dashboard is not None else None
                ),
                # AUDIT-N+18: dormant-core envelope (dict shape from
                # ``thegent.cli.commands.observability_impl._build_observe_trend_payload``)
                # surfaced alongside the live traffic snapshot so
                # downstream consumers (CI hooks, log shippers) see one
                # unified payload. ``None`` when no source is attached
                # so consumers can short-circuit cleanly.
                "dormant_core": self._invoke_dormant_core(),
                # AUDIT-N+22 (SOTA audit pass 8, Lane A): MCP audit-trail
                # singleton stats. Same shape as the live traffic
                # snapshot (``total_entries`` / ``max_entries`` /
                # ``by_kind`` / ``by_outcome`` / ``error_count`` /
                # ``avg_duration_ms`` / ``p99_duration_ms`` /
                # ``oldest_seq`` / ``newest_seq``) so downstream CI hooks
                # and SOTA replay tooling can ingest it without bespoke
                # parsing. ``None`` when no source is attached so the
                # cockpit can run cleanly without the MCP subsystem
                # (e.g. ``cockpit render`` against a synthetic snapshot).
                "mcp_audit_stats": self._invoke_audit_stats(),
            }

    def progress_bar(self) -> str:
        """Return the current progress bar (``P-081``).

        NEW-19 (SOTA fourth-pass): reads ``self._state.last_progress``
        under ``self._lock`` so a concurrent ``tick`` cannot land a
        torn ``(done, total)`` tuple into the operator's progress bar.
        """
        with self._lock:
            done, total = self._state.last_progress
        return _progress_bar(done, total)

    def last_render_ms(self) -> float:
        """How long the most recent ``render()`` call took, in milliseconds.

        NEW-19 (SOTA fourth-pass): reads ``self._last_render_ms`` under
        ``self._lock`` so a concurrent ``render`` call cannot tear the
        float read with the write in the ``finally`` block.
        """
        with self._lock:
            return self._last_render_ms

    # ----------------------------------------------------------------- render

    def render(self) -> str:
        """Render the cockpit into a single string (the current frame).

        The render is plain ASCII/Unicode, with one pane per line, four panes
        laid out as a 2x2 grid.  Returns ``""`` if the cockpit is empty.

        NEW-19 (SOTA fourth-pass): ``render`` and the private ``_render_*_pane``
        methods now run under ``self._lock`` so a concurrent ``tick`` /
        ``record_decision`` cannot land a torn snapshot into the operator's
        terminal. The previous implementation read ``self._state`` without
        the lock and updated ``self._frame_count`` / ``self._last_render_ms``
        outside it; a concurrent ``tick`` could replace ``self._state.runs``
        mid-render and a concurrent render could lose ``_frame_count``
        increments to a read-modify-write race. The frame counter is now
        bumped under the lock, and each pane renderer takes the lock for
        the duration of its read so a ``tick`` interleaved between two
        pane calls still sees consistent per-render state.
        """
        with self._lock:
            t0 = self._clock()
            try:
                text = self._render_grid_locked()
            finally:
                dt = (self._clock() - t0) * 1000.0
                self._last_render_ms = dt
                self._frame_count += 1
        return text

    def _render_grid_locked(self) -> str:
        """Inner renderer — caller must hold ``self._lock``.

        Kept separate from :meth:`render` so the lock contract is explicit
        at the call boundary (NEW-19). All pane renderers are themselves
        lock-aware and may be invoked from tests / debug utilities
        without the outer lock; the production ``render`` path is the
        only one that locks.

        ARIA (L17 I18n/A11y): each pane is invoked with an ``aria_label``
        derived from :attr:`CockpitConfig.pane_labels` so the rendered
        output emits ARIA annotation trailers (e.g. ``[role=status
        aria-live=polite aria-label="Live Runs"]``) on the closing
        border of each pane. The headers/decisions/traffic/dormant_core
        panes also get their own labels so downstream tooling
        (screen readers, TUI inspectors) can identify the region
        without scraping free-form text.
        """
        cfg = self.config
        # Resolve labels defensively; older configs (pre-AUDIT-N+15 / +18 / +22)
        # may not have every key, so the grid reflects only the configured
        # subset. ``pane_labels.get(...)`` returns the default and is
        # never missing.
        runs_label = cfg.pane_labels.get(CockpitPane.RUNS, "Live Runs")
        lanes_label = cfg.pane_labels.get(CockpitPane.LANES, "Lane Distribution")
        confidence_label = cfg.pane_labels.get(CockpitPane.CONFIDENCE, "Confidence (P50/P95)")
        overrides_label = cfg.pane_labels.get(CockpitPane.OVERRIDES, "Active Overrides")
        traffic_label = cfg.pane_labels.get(CockpitPane.TRAFFIC, "Traffic")
        dormant_label = cfg.pane_labels.get(CockpitPane.DORMANT_CORE, "Dormant Core")
        decisions_label = "Decision History"

        # 1. Header — title + progress bar (P-081). The header lands
        #    in a ``region`` so screen readers flag it as a landmark.
        header = self._render_header(aria_label=cfg.title)

        # 2. Optional override-expiry banner (WP-3003 -> WP-4001 bridge).
        #    Surfaces the most recent governance.override.expired events
        #    inline so operators see TTL expirations as they fire rather
        #    than waiting for the next JSONL tail.
        banner = self._render_override_banner()

        # 3. The four panes (ARIA-annotated on the closing border).
        runs_lines = self._render_runs_pane(aria_label=runs_label)
        lanes_lines = self._render_lanes_pane(aria_label=lanes_label)
        conf_lines = self._render_confidence_pane(aria_label=confidence_label)
        ovr_lines = self._render_overrides_pane(aria_label=overrides_label)

        # 4. Compose into 2x2 grid
        body_lines: list[str] = []
        for i in range(max(len(runs_lines), len(lanes_lines))):
            left = runs_lines[i] if i < len(runs_lines) else ""
            right = lanes_lines[i] if i < len(lanes_lines) else ""
            body_lines.append(f"{left:<46}│ {right}")
        for i in range(max(len(conf_lines), len(ovr_lines))):
            left = conf_lines[i] if i < len(conf_lines) else ""
            right = ovr_lines[i] if i < len(ovr_lines) else ""
            body_lines.append(f"{left:<46}│ {right}")
        # 5. Third row: decision-history pane (full-width). Mirrors the
        #    existing override-history UX (different stream): every
        #    recorded ``DecisionNotice`` shows up with verdict glyph +
        #    age so operators can trace governance denies without
        #    tailing the JSONL. Uses ``role="log"`` per ARIA conventions.
        decisions_lines = self._render_decisions_pane(aria_label=decisions_label)
        # 6. AUDIT-N+15: fourth row — traffic pane (full-width). When a
        #    ``TrafficDashboard`` is attached via ``attach_traffic``, this
        #    surfaces live count/rps/error_rate/p50/p95 so operators see
        #    traffic without tailing a separate dashboard. Without a
        #    dashboard attached the pane is omitted entirely so the
        #    layout reflects only attached subsystems.
        traffic_lines = self._render_traffic_pane_lines(aria_label=traffic_label)
        # 7. AUDIT-N+18: fifth row — dormant-core pane (full-width). When a
        #    dormant-core source is attached via ``attach_dormant_core`,
        #    this surfaces live escalation count, past-SLA count,
        #    freshness bucket, and the AUDIT-N+13 ``wl120_dormant_round_trip``
        #    side-channel flag so operators see the dormant-core
        #    reconciliation inline alongside the traffic pane. Without a
        #    source attached the pane is omitted entirely.
        dormant_lines = self._render_dormant_core_pane_lines(aria_label=dormant_label)
        body = (
            "\n".join(body_lines)
            + "\n"
            + "\n".join(decisions_lines)
            + ("\n" + "\n".join(traffic_lines) if traffic_lines else "")
            + ("\n" + "\n".join(dormant_lines) if dormant_lines else "")
        )

        if banner:
            return f"{header}\n{banner}\n{body}"
        return f"{header}\n{body}"

    def _render_override_banner(self) -> str:
        """Render an inline banner for the freshest operationally-relevant event.

        Walks both :attr:`_CockpitState.override_notices` and
        :attr:`_CockpitState.decision_notices` for any event whose age is
        within ``OVERRIDE_BANNER_MAX_AGE_S``, then picks the freshest.
        Returns ``""`` when nothing qualifies so the banner naturally
        fades between DAG ticks.

        NEW-20 (SOTA fourth-pass): ``now`` is sampled inside the same
        critical section that copies the notice pointers, so the age
        deltas are computed against the *same* clock value that was
        visible to the locked snapshot. The previous implementation
        read the state under the lock and then sampled ``self._clock``
        outside it — a clock swap (the exact scenario NEW-18 fixed in
        ``tick``) between the locked read and the unlocked ``now``
        could land a banner whose age was computed against a different
        clock than the timestamp it was compared to.
        """
        with self._lock:
            now = self._clock()
            last_override: OverrideExpiryNotice | None = (
                self._state.override_notices[-1] if self._state.override_notices else None
            )
            last_deny: DecisionNotice | None = None
            for n in reversed(self._state.decision_notices):
                if n.is_deny():
                    last_deny = n
                    break
        candidates: list[tuple[float, str]] = []
        if last_override is not None:
            o_age = max(0.0, now - last_override.expired_at)
            if o_age <= OVERRIDE_BANNER_MAX_AGE_S:
                candidates.append((o_age, "override"))
        if last_deny is not None and last_deny.evaluated_at > 0:
            d_age = max(0.0, now - last_deny.evaluated_at)
            if d_age <= OVERRIDE_BANNER_MAX_AGE_S:
                candidates.append((d_age, "deny"))
        if not candidates:
            return ""
        # Freshest wins.
        candidates.sort(key=lambda item: item[0])
        kind = candidates[0][1]
        if kind == "override":
            return _render_override_banner_text(last_override, now)
        return _render_decision_deny_banner(last_deny, now)  # type: ignore[arg-type]

    def _render_header(self, *, aria_label: str | None = None) -> str:
        """Render the header line (title + progress bar + tick clock).

        NEW-19 (SOTA fourth-pass): reads ``self._state.last_progress``,
        ``self._state.last_tick_at``, and ``self._frame_count`` under
        ``self._lock`` so a concurrent ``tick`` / ``render`` cannot
        tear the values into the operator's title bar.

        NEW-21 (SOTA fourth-pass): the F-13 docstring previously
        claimed this function "uses ``self._clock``" but it actually
        formats the *stored* ``self._state.last_tick_at`` value (which
        is already populated via ``self._clock()`` under the lock by
        :meth:`tick` — see NEW-18). The misleading F-13 comment block
        has been removed; the clock-injection contract is now stated
        once and accurately.

        ARIA (L17 I18n/A11y): when ``aria_label`` is supplied, the
        header line is suffixed with an ARIA annotation trailer so
        screen readers can pick up the cockpit's landmark role.
        Default ``None`` preserves the unannotated output.
        """
        with self._lock:
            cfg = self.config
            done, total = self._state.last_progress
            frame_idx = self._frame_count
            last_tick_at = self._state.last_tick_at
        bar = _progress_bar(done, total)
        ts = time.strftime("%H:%M:%S", time.localtime(last_tick_at))
        header = f"  {cfg.title}   {cfg.progress_label}: {bar}   tick={ts} (#{frame_idx + 1})"
        if aria_label:
            header = annotate(header, role="region", aria_label=aria_label)
        return header

    def _render_runs_pane(self, *, aria_label: str | None = None) -> list[str]:
        """Render the live-runs pane rows.

        NEW-19 (SOTA fourth-pass): copies ``self._state.runs`` under
        ``self._lock`` so a concurrent ``tick`` cannot replace the dict
        mid-iteration and tear a row that the operator sees in their
        terminal.

        ARIA (L17 I18n/A11y): when ``aria_label`` is supplied, the
        closing ``└─...─┘`` border is suffixed with an ARIA
        annotation trailer (e.g.
        ``[role=status aria-live=polite aria-label="Live Runs"]``)
        so screen readers and TUI inspection tooling can pick up
        the pane's role + live-region semantics without scraping
        free-form text. Default ``None`` preserves the original
        unannotated output for callers that have not opted in.
        """
        cfg = self.config
        with self._lock:
            runs = sorted(
                self._state.runs.values(),
                key=lambda ev: (ev.state.value, ev.run_id),
            )
            total_runs = len(self._state.runs)
            pane_label = cfg.pane_labels[CockpitPane.RUNS]
        lines = [f"┌─ {pane_label} ───────────────┐"]
        if not runs:
            lines.append("│  (no active runs)                    │")
            lines.append("│                                      │")
        else:
            for ev in runs[:MAX_RUNS_PANE_ROWS]:
                lines.append(f"│ {_format_run_row(ev):<38} │")
            if total_runs > MAX_RUNS_PANE_ROWS:
                lines.append(f"│  … {total_runs - MAX_RUNS_PANE_ROWS} more            │")
        closing = "└──────────────────────────────────────┘"
        if aria_label is not None:
            closing = _annotate_pane_close(closing, label=aria_label)
        lines.append(closing)
        return lines

    def _render_lanes_pane(self, *, aria_label: str | None = None) -> list[str]:
        """Render the lane-distribution pane rows.

        NEW-19 (SOTA fourth-pass): copies ``self._state.runs`` under
        ``self._lock`` so a concurrent ``tick`` cannot replace the dict
        between ``list(...)`` and ``Counter(...)``.

        ARIA (L17 I18n/A11y): when ``aria_label`` is supplied, the
        closing ``└─...─┘`` border is suffixed with an ARIA annotation
        trailer so screen readers can pick up the pane's role + live
        semantics. Default ``None`` preserves the unannotated output.
        """
        cfg = self.config
        with self._lock:
            runs = list(self._state.runs.values())
            pane_label = cfg.pane_labels[CockpitPane.LANES]
        lines = [f"┌─ {pane_label} ───────────────┐"]
        if not runs:
            lines.append("│  (idle)                              │")
            lines.append("│                                      │")
        else:
            counts = Counter(ev.lane for ev in runs)
            for lane, count in sorted(counts.items()):
                bar = _progress_bar(count, max(counts.values()), width=12)
                lines.append(f"│  {lane:<10} {count:3d}  {bar:<18} │")
        closing = "└──────────────────────────────────────┘"
        if aria_label is not None:
            closing = _annotate_pane_close(closing, label=aria_label)
        lines.append(closing)
        return lines

    def _render_confidence_pane(self, *, aria_label: str | None = None) -> list[str]:
        """Render the confidence (P50/P95) sparkline pane rows.

        NEW-19 (SOTA fourth-pass): copies ``self._state.confidence_history``
        under ``self._lock`` so a concurrent ``tick`` cannot append to
        the bounded deque between the materialise-to-list step and
        the percentile computation.

        ARIA (L17 I18n/A11y): when ``aria_label`` is supplied, the
        closing ``└─...─┘`` border is suffixed with an ARIA annotation
        trailer so screen readers can pick up the pane's role + live
        semantics. Default ``None`` preserves the unannotated output.
        """
        cfg = self.config
        # ``confidence_history`` is a bounded ``deque`` to prevent unbounded
        # memory growth. Materialise once into a plain list so the helpers
        # below can slice/index it without relying on ``collections.deque``
        # slice semantics (which Python 3.14 + abstract ``Sequence[float]``
        # typing can refuse at runtime).
        with self._lock:
            history: list[float] = list(self._state.confidence_history)
            pane_label = cfg.pane_labels[CockpitPane.CONFIDENCE]
        p50 = self._percentile(history, 0.5)
        p95 = self._percentile(history, 0.95)
        lines = [f"┌─ {pane_label} ─┐"]
        lines.append(f"│ P50={p50:.2f}   P95={p95:.2f}   n={len(history):3d}     │")
        if cfg.show_sparkline:
            spark = _sparkline(history, cfg.sparkline_width)
            lines.append(f"│ {spark:<36} │")
        else:
            lines.append("│                                      │")
            lines.append("│                                      │")
        # Pad to same height as lanes pane
        while len(lines) < 4:
            lines.append("│                                      │")
        closing = "└──────────────────────────────────────┘"
        if aria_label is not None:
            closing = _annotate_pane_close(closing, label=aria_label)
        lines.append(closing)
        return lines

    def _render_overrides_pane(self, *, aria_label: str | None = None) -> list[str]:
        """Render the active-overrides pane rows.

        NEW-19 (SOTA fourth-pass): copies ``self._state.overrides``
        under ``self._lock`` so a concurrent ``tick`` cannot replace
        the dict mid-iteration.

        ARIA (L17 I18n/A11y): when ``aria_label`` is supplied, the
        closing ``└─...─┘`` border is suffixed with an ARIA annotation
        trailer so screen readers can pick up the pane's role + live
        semantics. Default ``None`` preserves the unannotated output.
        """
        cfg = self.config
        with self._lock:
            ovrs = sorted(
                self._state.overrides.values(),
                key=lambda ev: ev.expires_in_s,
            )
            total_ovrs = len(self._state.overrides)
            pane_label = cfg.pane_labels[CockpitPane.OVERRIDES]
        lines = [f"┌─ {pane_label} ───────────┐"]
        if not ovrs:
            lines.append("│  (no active overrides)               │")
            lines.append("│                                      │")
        else:
            for ev in ovrs[:MAX_OVERRIDE_PANE_ROWS]:
                lines.append(f"│ {_format_override_row(ev):<38} │")
            if total_ovrs > MAX_OVERRIDE_PANE_ROWS:
                lines.append(f"│  … {total_ovrs - MAX_OVERRIDE_PANE_ROWS} more            │")
        closing = "└──────────────────────────────────────┘"
        if aria_label is not None:
            closing = _annotate_pane_close(closing, label=aria_label)
        lines.append(closing)
        return lines

    def _render_dormant_core_pane(self) -> str:
        """Render the AUDIT-N+18 DORMANT_CORE pane rows as a single string.

        Reads the optionally-attached dormant-core source (via
        :meth:`attach_dormant_core`) and renders a compact 4-line summary::

            ┌─ Dormant Core ───────────────┐
            │ esc=3  past_sla=1  fresh      │
            │ health=good  sig=abc123      │
            │ round_trip=True              │
            └──────────────────────────────┘

        When no source is attached, returns an empty string so callers
        can treat the result as a no-op (the renderer omits the pane
        entirely). When the source is attached but raises or returns
        a non-dict, the pane renders a single neutral line so the
        cockpit still produces usable output.

        The renderer pulls fields by name from the AUDIT-N+13 envelope
        shape (``trend_summary``, ``escalation_breakdown``,
        ``wl120_dormant_round_trip``, ``trend_scope_signature``) so
        the pane stays decoupled from the dormant-core service module
        itself. Missing keys render as ``-`` rather than crashing so
        the pane is tolerant of partial envelopes (the dormant core
        is allowed to return incomplete data when its dependencies
        are degraded).
        """
        lines = self._render_dormant_core_pane_lines()
        return "\n".join(lines)

    def _render_dormant_core_pane_lines(self, *, aria_label: str | None = None) -> list[str]:
        """Render the AUDIT-N+18 DORMANT_CORE pane rows as a list of strings.

        Internal helper used by :meth:`_render_grid_locked` to splice
        the dormant-core pane into the grid layout. Returns ``[]``
        when no source is attached.

        ARIA (L17 I18n/A11y): when ``aria_label`` is supplied, the
        closing ``└─...─┘`` border is suffixed with an ARIA annotation
        trailer so screen readers can pick up the pane's role + live
        semantics. Default ``None`` preserves the unannotated output.
        """
        cfg = self.config
        with self._lock:
            source = self._state.dormant_source
        if source is None:
            return []
        # Resolve the pane label defensively — older configs that pre-date
        # AUDIT-N+18 won't have a DORMANT_CORE entry and we don't want a
        # KeyError to crash the render.
        pane_label = cfg.pane_labels.get(CockpitPane.DORMANT_CORE, "Dormant Core")
        # Box layout (matches the AUDIT-N+15 TRAFFIC pane width):
        #   total width = 35 chars (including corners)
        #   interior   = 33 chars between the two ``│`` borders
        box_width = 35
        interior = box_width - 2
        label = _truncate(str(pane_label), 16)
        # Header: ``┌─ <label> ─...─┐`` with trailing dashes so total == box_width.
        header_prefix = f"┌─ {label} "
        header_dashes = "─" * max(1, box_width - len(header_prefix) - 1)
        header_line = f"{header_prefix}{header_dashes}┐"
        footer_line = "└" + "─" * interior + "┘"
        empty_line = f"│{'':<{interior}}│"
        payload = self._invoke_dormant_core()
        if payload is None:
            err_marker = "  (dormant-core source errored)  "
            pad = max(0, interior - len(err_marker))
            footer = footer_line
            if aria_label is not None:
                footer = _annotate_pane_close(footer, label=aria_label)
            return [
                header_line,
                f"│{err_marker}{'':<{pad}}│",
                empty_line,
                empty_line,
                footer,
            ]
        # AUDIT-N+13 envelope keys (defensive lookup — see the docstring
        # for the canonical names). Nested ``trend_summary`` /
        # ``escalation_breakdown`` dicts are flattened one level deep
        # so a single-line summary is readable on an 80-col console.
        trend_summary = payload.get("trend_summary") if isinstance(payload.get("trend_summary"), dict) else {}
        escalation_breakdown = (
            payload.get("escalation_breakdown") if isinstance(payload.get("escalation_breakdown"), dict) else {}
        )
        backlog = escalation_breakdown.get("backlog_count", escalation_breakdown.get("rows_count", "-"))
        past_sla = escalation_breakdown.get("past_sla_count", "-")
        freshness = trend_summary.get("freshness_bucket", trend_summary.get("trend_snapshot_health", "-"))
        health = trend_summary.get("trend_snapshot_health", "-")
        # Side-channel flag from AUDIT-N+12/13: True iff the dormant-core
        # round-trip produced dict-shaped output for both halves.
        round_trip = payload.get("wl120_dormant_round_trip")
        scope_sig = payload.get("trend_scope_signature", "")
        sig_short = (scope_sig[:8] + "…") if scope_sig and len(scope_sig) > 8 else (scope_sig or "-")
        fresh_txt = _sanitize_console_text(str(freshness), max_len=6)
        health_txt = _sanitize_console_text(str(health), max_len=6)
        sig_txt = _sanitize_console_text(sig_short, max_len=12)
        rt_txt = "True" if round_trip else "False"
        # Body rows (each exactly ``interior`` chars between the borders).
        body_lines = [
            f"│ esc={backlog:<3} sla={past_sla:<3} f={fresh_txt:<6}{'':<14}│",
            f"│ health={health_txt:<6} sig={sig_txt:<12}{'':<7}│",
            f"│ round_trip={rt_txt:<22}{'':<1}│",
        ]
        # Hard-enforce width so the border lines stay aligned even when
        # the source envelope contains unexpectedly long tokens.
        body_lines = [_pad_box_row(row, interior) for row in body_lines]
        footer = footer_line
        if aria_label is not None:
            footer = _annotate_pane_close(footer, label=aria_label)
        return [header_line, *body_lines, footer]

    def _render_traffic_pane(self) -> str:
        """Render the AUDIT-N+15 TRAFFIC pane rows as a single string.

        Reads the optionally-attached :class:`TrafficDashboard` (via
        :meth:`attach_traffic`) and renders a compact 4-line summary::

            ┌─ TRAFFIC ────────────────┐
            │ count=240 rps=4.0 err=2.5%│
            │ p50=120ms  p95=410ms      │
            │ ok=232 err=6 warn=2       │
            └───────────────────────────┘

        When no dashboard is attached, returns an empty string so callers
        can treat the result as a no-op (the renderer omits the pane
        entirely). When the dashboard is attached but has no events yet,
        the pane renders a single neutral line so operators can tell the
        audit pipeline is idle at a glance.

        NEW-22 (SOTA fourth-pass, AUDIT-N+15): copies the dashboard
        reference under ``self._lock`` so a concurrent ``attach_traffic``
        / ``tick`` cannot tear the bound identity. The pane joins all
        rows into a single string for caller convenience; the grid
        renderer uses :meth:`_render_traffic_pane_lines` to consume
        the raw list form.
        """
        lines = self._render_traffic_pane_lines()
        return "\n".join(lines)

    def _render_traffic_pane_lines(self, *, aria_label: str | None = None) -> list[str]:
        """Render the AUDIT-N+15 TRAFFIC pane rows as a list of strings.

        Internal helper used by :meth:`_render_grid_locked` to splice
        the traffic pane into the grid layout. Returns ``[]`` when no
        dashboard is attached.

        ARIA (L17 I18n/A11y): when ``aria_label`` is supplied, the
        closing ``└─...─┘`` border is suffixed with an ARIA annotation
        trailer so screen readers can pick up the pane's role + live
        semantics. Default ``None`` preserves the unannotated output.
        """
        cfg = self.config
        with self._lock:
            dashboard = self._state.traffic_dashboard
        if dashboard is None:
            return []
        # Resolve the pane label defensively — older configs that pre-date
        # AUDIT-N+15 won't have a TRAFFIC entry and we don't want a
        # KeyError to crash the render.
        pane_label = cfg.pane_labels.get(CockpitPane.TRAFFIC, "Traffic")
        lines = [f"┌─ {pane_label} ────────────────┐"]
        try:
            snap = dashboard.summary()
        except Exception:  # noqa: BLE001 - never crash the cockpit.
            closing = "└─────────────────────────────────┘"
            if aria_label is not None:
                closing = _annotate_pane_close(closing, label=aria_label)
            lines.append("│  (traffic dashboard error)       │")
            lines.append("│                                 │")
            lines.append("│                                 │")
            lines.append(closing)
            return lines
        count = int(snap.get("count", 0))
        rps = float(snap.get("rps", 0.0))
        err = float(snap.get("error_rate", 0.0)) * 100.0
        p50 = float(snap.get("p50_ms", 0.0))
        p95 = float(snap.get("p95_ms", 0.0))
        by_status = ", ".join(f"{k}={int(v)}" for k, v in sorted(snap.get("by_status", {}).items()))
        lines.append(f"│ count={count:<5d} rps={rps:<4.2f} err={err:>5.2f}% │")
        lines.append(f"│ p50={p50:<6.0f}ms p95={p95:<6.0f}ms        │")
        if by_status:
            lines.append(f"│ {by_status:<33} │")
        else:
            lines.append("│ (no events yet)                  │")
        closing = "└─────────────────────────────────┘"
        if aria_label is not None:
            closing = _annotate_pane_close(closing, label=aria_label)
        lines.append(closing)
        return lines

    def _render_decisions_pane(self, *, aria_label: str | None = None) -> list[str]:
        """Render the decision-history stream (WP-3001 -> WP-4001 inline view).

        Full-width row sitting under the 2x2 grid. Shows the most recent
        :class:`DecisionNotice` events with verdict glyph, rule_id (12),
        agent (8), lane (8), and age (4s). Mirrors the existing
        override-banner UX so operators learn one pattern. Bounded by
        ``MAX_DECISION_NOTICES`` (deque maxlen, ``cockpit.py:67``) so long sessions
        can't blow up the renderer's memory.

        Empty panes render a single neutral line so the cockpit always
        reserves the row and operators can tell the audit pipeline is
        idle at a glance.

        NEW-20 (SOTA fourth-pass): both the ``decision_notices`` snapshot
        and the ``self._clock()`` sample are now taken under the same
        ``self._lock`` critical section so a clock swap between the two
        reads cannot compute ages against a different clock than the
        one used to write the ``evaluated_at`` timestamp (same family
        as NEW-18 + NEW-20 on ``_render_override_banner``).

        ARIA (L17 I18n/A11y): when ``aria_label`` is supplied, the
        closing ``└─...─┘`` border is suffixed with an ARIA annotation
        trailer using ``role="log"`` (the audit log role) so screen
        readers can pick up the pane's role + semantics. Default
        ``None`` preserves the unannotated output.
        """
        with self._lock:
            now = self._clock()
            decisions: list[DecisionNotice] = list(self._state.decision_notices)
        lines: list[str] = ["┌─ Decision History ──────────────────────────────┐"]
        if not decisions:
            lines.append("│  (no policy decisions recorded yet)            │")
            lines.append("│                                                 │")
        else:
            newest = list(reversed(decisions[-MAX_DECISION_PANE_ROWS:]))
            for d in newest:
                glyph = _decision_glyph(d)
                age = max(0.0, now - d.evaluated_at) if d.evaluated_at > 0 else 0.0
                lines.append(f"│ {glyph} {_format_decision_row(d, age):<47} │")
            total = len(decisions)
            if total > MAX_DECISION_PANE_ROWS:
                lines.append(f"│  … {total - MAX_DECISION_PANE_ROWS} older decisions hidden       │")
        closing = "└─────────────────────────────────────────────────┘"
        if aria_label is not None:
            closing = _annotate_pane_close(closing, label=aria_label, role="log")
        lines.append(closing)
        return lines

    @staticmethod
    def _percentile(values: Sequence[float], pct: float) -> float:
        """Return the ``pct`` percentile of ``values`` (0..1).

        Returns ``0.0`` for empty input.
        """
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = max(0, min(len(sorted_vals) - 1, int(pct * (len(sorted_vals) - 1))))
        return sorted_vals[idx]

    # --------------------------------------------------- context-manager sugar

    def __enter__(self) -> OperatorCockpit:
        return self

    def __exit__(self, *exc: Any) -> None:
        # Best-effort stop of the background tailer (if any) so the
        # daemon thread exits cleanly when used as ``with OperatorCockpit(...)``.
        self.shutdown(timeout_s=0.1)


# ---------------------------------------------------------------------------
# Module-level helpers (lifecycle)
# ---------------------------------------------------------------------------


def _finalize_cockpit(cockpit: OperatorCockpit) -> None:
    """Finaliser that stops the audit tailer at garbage-collection time.

    Registered via :func:`weakref.finalize` so that test suites and
    short-lived scripts that forget to call :meth:`OperatorCockpit.shutdown`
    still exit their daemon threads and don't leave the JSONL file half
    written. Idempotent with explicit ``shutdown()`` because the tailer
    keeps its own state.
    """
    try:
        tailer = cockpit._audit_tailer  # noqa: SLF001 — finaliser contract
    except AttributeError:
        return
    if tailer is not None:
        try:
            tailer.stop(timeout_s=0.5)
        except Exception:  # noqa: BLE001 — finaliser must never raise
            pass
        cockpit._audit_tailer = None  # noqa: SLF001


# ---------------------------------------------------------------------------
# One-shot helper
# ---------------------------------------------------------------------------


def render_cockpit(
    runs: Iterable[RunEvent] | None = None,
    overrides: Iterable[OverrideEvent] | None = None,
    *,
    progress: tuple[int, int] | None = None,
    config: CockpitConfig | None = None,
    clock: Callable[[], float] | None = None,
) -> str:
    """One-shot convenience renderer.

    Equivalent to building an ``OperatorCockpit``, calling ``tick(...)`` once,
    and returning ``render()``. ``clock`` lets callers pin the wall clock for
    deterministic audit replays.
    """
    cockpit = OperatorCockpit(config=config, clock=clock)
    cockpit.tick(runs=runs, overrides=overrides, progress=progress)
    return cockpit.render()


# ---------------------------------------------------------------------------
# Internal banner helpers (extracted so audit replays are byte-identical)
# ---------------------------------------------------------------------------


def _render_override_banner_text(notice: OverrideExpiryNotice, now: float) -> str:
    """Format the override-expiry banner line; deterministic given (notice, now)."""
    age = max(0.0, now - notice.expired_at)
    reason = _sanitize_console_text(notice.reason or "ttl_elapsed", max_len=64)
    glyph = "✓" if age < 1.0 else "!"
    # Fixed-width columns: rule_id (12), owner (8), age (4), reason (32).
    # F-9 + NEW-5 (SOTA third-pass): sanitise every user-supplied token
    # so a producer cannot inject ANSI/Rich markup via ``rule_id``,
    # ``owner``, or ``reason``.
    rule_id = _sanitize_console_text(notice.rule_id, max_len=12)
    owner = _sanitize_console_text(notice.owner, max_len=8)
    return f"  {glyph} override expired: {rule_id:<12}  by {owner:<8}  {age:4.0f}s ago  {_truncate(reason, 32)}"


def _render_decision_deny_banner(notice: DecisionNotice, now: float) -> str:
    """Render a single-line banner highlighting a recent policy deny.

    The rule_id is shown first so it survives Rich's default console
    width truncation on operators' terminals — operators triaging a deny
    always have the offending rule in view, even on 80-col consoles.

    F-9 + NEW-5 (SOTA third-pass): every user-supplied token
    (``rule_id``, ``lane``, ``reason_code``, ``reason``) is routed
    through :func:`_sanitize_console_text` so a producer that stows
    ANSI escapes or Rich markup in any of those fields cannot
    corrupt the banner layout.

    NEW-9 (SOTA third-pass): ``notice.reason`` is also length-capped
    via ``_sanitize_console_text`` (``max_len=64`` for the banner
    path; the pane path uses ``_truncate`` at 32 chars) so a 10 MiB
    reason field cannot blow the operator terminal.
    """
    age = max(0.0, now - notice.evaluated_at)
    age_text = f"{age:.0f}s"
    rule_id = _sanitize_console_text(notice.rule_id, max_len=64)
    lane = _sanitize_console_text(notice.lane, max_len=16) if notice.lane else ""
    head = f"\u2717 policy deny: {rule_id or '?'}"
    if lane:
        head = f"{head}  lane={lane}"
    head = f"{head}  {age_text} ago"
    if notice.reason_code:
        head = f"{head}  ({_sanitize_console_text(notice.reason_code, max_len=24)})"
    if notice.reason:
        head = f"{head}  {_sanitize_console_text(notice.reason, max_len=64)}"
    return head


def _decision_glyph(notice: DecisionNotice) -> str:
    """Glyph used in the decision-history pane for a given verdict.

    Same vocabulary as the deny banner (``\u2717`` = ballot-x) so the
    pane and the banner read identically. ``allow`` gets a check mark;
    ``warn`` gets a bang. ``evaluated_at == 0`` (no clock yet) is
    represented as a dash to avoid displaying nonsense ages.
    """
    if notice.is_deny():
        return "\u2717"
    if notice.is_warn():
        return "!"
    if notice.evaluated_at <= 0:
        return "-"
    return "\u2713"


def _format_decision_row(notice: DecisionNotice, age: float) -> str:
    """Format one row of the decision-history pane.

    Columns (fixed-width):
        rule_id (12) | agent (8) | lane (8) | age (4s) | reason_code
    The reason is omitted to keep the row readable on 80-col consoles;
    operators wanting the full message read the JSONL audit log via
    ``thegent cockpit audit tail``.

    F-9 + NEW-5 (SOTA third-pass): all four columns are routed
    through :func:`_sanitize_console_text` so a producer cannot
    inject ANSI/Rich markup via any of the ``DecisionNotice`` fields.
    """
    age_text = f"{age:.0f}s" if notice.evaluated_at > 0 else "   -"
    rule = _sanitize_console_text(notice.rule_id or "-", max_len=12)
    agent = _sanitize_console_text(notice.agent or "-", max_len=8)
    lane = _sanitize_console_text(notice.lane or "-", max_len=8)
    code = _sanitize_console_text(notice.reason_code or "", max_len=16)
    return f"{rule:<12}  {agent:<8}  {lane:<8}  {age_text:>4}  {code}"


__all__ = [
    "CockpitConfig",
    "CockpitPane",
    "DecisionNotice",
    "OperatorCockpit",
    "OverrideEvent",
    "OverrideExpiryNotice",
    "RunEvent",
    "RunState",
    "render_cockpit",
]
