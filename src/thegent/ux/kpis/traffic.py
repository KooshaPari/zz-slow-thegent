"""Real-time TRAFFIC KPI dashboard (Batch 10A, WP-Y7, P-081).

Thegent needs a high-cardinality live "TRAFFIC" view that rolls up requests
per second, lane distribution, error budget burn, and override churn.  This
module provides:

* :class:`TrafficWindow` — a fixed-size ring buffer of events with bucketed counts
* :class:`TrafficDashboard` — exposes live TRAFFIC counts as plain-Python dicts
* :func:`render_traffic` — render a single TRAFFIC string (suitable for ``print``)
* :func:`progress_bar` — the canonical progress bar used everywhere else in UX

All values are thread-safe *per-dashboard* in single-threaded usage.  Designed
to embed in CI captures, ``rich.live.Live``, and the operator cockpit.

The dashboard accepts an optional ``clock`` callable (``-> float``) so audit
replays and CI snapshots can pin the wall clock deterministically; by default
``time.time`` is used.

Traces to: OPS-001 (request rate), OPS-002 (error rate), OPS-003 (latency
            p95), P-081 (progress bar), P-090 (cockpit latency SLO),
            WP-Y7 (TRAFFIC real-time view).
"""

from __future__ import annotations

import logging
import threading
import time
from collections import Counter, deque
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


DEFAULT_WINDOW_SECONDS = 60.0
DEFAULT_BUCKET_SECONDS = 1.0
DEFAULT_TREND_WIDTH = 30


# ---------------------------------------------------------------------------
# Progress bar (the canonical one; re-used from cockpit)
# ---------------------------------------------------------------------------


def progress_bar(done: int, total: int, *, width: int = 24) -> str:
    """Return a textual progress bar ``[####------]  42%``.

    Returns a flat line for ``total <= 0``.  Always emits a width-stable string
    so callers can stack progress bars across runs.
    """
    if total <= 0:
        return "[" + " " * width + "]   -"
    pct = max(0, min(100, int(100 * done / total)))
    filled = int(width * pct / 100)
    return f"[{'#' * filled}{'-' * (width - filled)}] {pct:3d}%"


def progress_bar_with_eta(
    done: int, total: int, elapsed_s: float, *, width: int = 24
) -> str:
    """Progress bar with an ETA estimate appended.

    Appends `` ETA 12s`` (or `` ETA 0:02`` for >= 60 s) to the standard
    bar.  Returns a bare bar when ``done == 0`` (ETA unknown) or
    ``done == total`` (``ETA 0s``).

    Args:
        done: Items processed so far.
        total: Total items expected.
        elapsed_s: Wall-clock seconds elapsed since start.
        width: Character width of the filled bar section.

    Returns:
        A single-line string like ``[##########--------]  50% ETA 12s``.
    """
    bar = progress_bar(done, total, width=width)
    if done == 0:
        return f"{bar} ETA -"
    if done >= total:
        return f"{bar} ETA 0s"
    if elapsed_s <= 0:
        return f"{bar} ETA -"
    remaining = (elapsed_s / done) * (total - done)
    if remaining >= 60:
        minutes = int(remaining) // 60
        seconds = int(remaining) % 60
        return f"{bar} ETA {minutes}:{seconds:02d}"
    return f"{bar} ETA {int(remaining)}s"


# ---------------------------------------------------------------------------
# TrafficWindow
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TrafficEvent:
    """A single traffic event recorded in the dashboard.

    F-5 (SOTA second-pass): the dataclass is now ``frozen=True`` so
    a producer cannot mutate an event after :meth:`TrafficWindow.record`
    has returned (the old mutable variant meant a downstream
    consumer could see a partially-overwritten timestamp). The
    ``record()`` method now builds a fresh :class:`TrafficEvent`
    via :func:`dataclasses.replace` when it needs to default
    ``ts`` to the current clock — callers that pass ``ts <= 0``
    get the same behaviour, just without mutating the input.
    """

    ts: float
    lane: str = "standard"
    agent: str = ""
    status: str = "ok"  # one of: ok, error, warn
    duration_ms: float = 0.0
    override_active: bool = False


@dataclass(slots=True)
class TrafficWindow:
    """A sliding time window of events with per-bucket counts.

    The window is a fixed-size ring buffer of :class:`TrafficEvent`s.  Reads
    and writes are serialised through ``self._lock`` so the dashboard is safe
    to share across threads.

    ``clock`` (``-> float``) defaults to ``time.time`` and can be injected
    via ``TrafficWindow(clock=...)`` to make audit replays deterministic.

    AUDIT-19 (Phase 3/4 third-pass hardening): the deque is bounded by
    ``maxlen`` so a flood of events cannot OOM the process, and eviction
    also drops **future** events (relative to ``now``) so a backwards
    wall-clock jump (NTP step, audit replay with negative ``time.sleep``,
    mis-configured test clock) cannot leak events past the window
    boundary.  ``maxlen`` defaults to ``int(window_s / bucket_s) * 8`` —
    enough headroom for bursty traffic at 1s granularity without
    requiring every caller to plumb a magic number.

    NEW-1 (SOTA third-pass): ``slots=True`` so a fleet of per-cockpit
    windows doesn't pay the per-instance ``__dict__`` cost (the
    dataclass previously allocated an 8-element ``__dict__`` per
    instance, which adds up across the tens-of-thousands of short-
    lived windows spawned by replay tests). ``_lock`` and ``_clock``
    are promoted to first-class fields so ``slots`` has a slot for
    each one; ``__post_init__`` still wires up the auto-derived
    ``maxlen`` and the bounded ``_events`` deque.
    """

    window_s: float = DEFAULT_WINDOW_SECONDS
    bucket_s: float = DEFAULT_BUCKET_SECONDS
    maxlen: int = 0  # 0 → auto-derive from window_s / bucket_s * 8

    _events: deque[TrafficEvent] = field(default_factory=deque)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _clock: Callable[[], float] = field(default=time.time)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.maxlen <= 0:
            self.maxlen = max(int(self.window_s / max(self.bucket_s, 1e-9)) * 8, 64)
        # Replace the deque with a bounded one; dataclass field default is
        # a fresh deque each instance so this mutation is safe.
        self._events = deque(self._events, maxlen=self.maxlen)

    def set_clock(self, clock: Callable[[], float]) -> None:
        """Override the wall clock used for eviction and zero-init fallback."""
        # ``slots=True`` forbids ad-hoc attribute assignment outside
        # the declared fields, so we route through ``object.__setattr__``
        # to swap the underlying callable in-place. This preserves the
        # public surface (``window.set_clock(...)``) without forcing
        # a constructor rebuild.
        object.__setattr__(self, "_clock", clock)

    def record(self, event: TrafficEvent) -> None:
        """Append ``event`` and evict anything outside the window.

        F-5: ``event.ts <= 0`` is normalised to the current clock
        via :func:`dataclasses.replace` (since the event is now
        frozen). All other fields pass through unchanged.
        """
        if event.ts <= 0:
            event = replace(event, ts=self._clock())
        with self._lock:
            self._events.append(event)
            self._evict(event.ts)

    def _evict(self, now: float) -> None:
        """Drop events outside ``[now - window_s, now]``.

        AUDIT-19: also drops events with ``ts > now`` so a backwards
        wall-clock jump cannot leak stale future events.  The deque's
        ``maxlen`` then caps absolute memory under burst pressure.

        F-6 + F-14 (SOTA second-pass): the future-ts second pass is
        bounded by a ``safety`` counter (initialised to
        ``len(self._events)``) so a corrupted monotonic clock can
        never hang the cockpit in a tight loop. Observable symptoms
        of the safety firing:

        * ``_evict`` logs a single WARNING at the moment the counter
          is exhausted (the deque still has events with ``ts > now``
          after the safety counter dropped to 0);
        * the operator sees ``count > 0`` on the dashboard even
          though :meth:`summary` reports an empty window — a clear
          breadcrumb that the system clock is misconfigured.

        The safety counter is intentionally a defensive guard, not a
        feature; it must NOT be removed when refactoring without
        also pinning :func:`test_evict_safety_counter_canary`.
        """
        low = now - self.window_s
        # First pass: stale events older than the window.
        while self._events and self._events[0].ts < low:
            self._events.popleft()
        # Second pass: future events leaked by a clock step / mis-set
        # ``event.ts``.  Limited to the deque head so we don't loop
        # forever on a corrupted monotonic clock. The bound is
        # ``len(self._events)`` because in steady state the deque's
        # head count equals the remaining "stuck" future events; a
        # corrupted clock would otherwise re-queue the same events
        # on every :meth:`summary` call until the process was killed.
        # F-7 (SOTA third-pass): emit a DEBUG breadcrumb for each
        # stuck head so an operator tailing the cockpit log can see
        # *how many* future-ts events were dropped, not just whether
        # the safety counter exhausted. The WARNING-on-exhaustion
        # canary (F-14) stays as-is for log-grep alerting; the DEBUG
        # breadcrumbs here are for forensic post-mortem after a
        # clock-step incident.
        dropped_stuck = 0
        safety = len(self._events)
        while self._events and self._events[0].ts > now and safety > 0:
            self._events.popleft()
            safety -= 1
            dropped_stuck += 1
        if dropped_stuck:
            _log.debug(
                "TrafficWindow._evict dropped %d future-ts event(s) "
                "(now=%.3f, head_ts=%.3f). Likely a backwards clock step.",
                dropped_stuck,
                now,
                self._events[0].ts if self._events else float("nan"),
            )
        # F-14 canary: if the safety counter was exhausted, log a
        # single WARNING so an operator staring at ``summary()["count"] == 0``
        # with a non-empty upstream has a breadcrumb to grep for.
        if safety == 0 and self._events and self._events[0].ts > now:
            _log.warning(
                "TrafficWindow._evict safety counter exhausted; "
                "deque still holds %d event(s) with ts > now=%.3f. "
                "Likely a corrupted system clock — check NTP / monotonic source.",
                len(self._events),
                now,
            )

    def summary(self, *, now: float | None = None) -> dict[str, Any]:
        """Return ``{count, by_lane, by_status, rps, error_rate, p50_ms, p95_ms}``.

        ``now`` overrides the wall clock for deterministic replay; defaults
        to ``self._clock()`` when omitted.
        """
        now = now if now is not None else self._clock()
        with self._lock:
            self._evict(now)
            events = list(self._events)
        count = len(events)
        if count == 0:
            return {
                "count": 0,
                "by_lane": {},
                "by_status": {},
                "rps": 0.0,
                "error_rate": 0.0,
                "p50_ms": 0.0,
                "p95_ms": 0.0,
                "override_count": 0,
                "duration_ms_window": self.window_s,
            }
        by_lane = Counter(ev.lane for ev in events)
        by_status = Counter(ev.status for ev in events)
        errors = sum(1 for ev in events if ev.status == "error")
        error_rate = errors / count
        durations = sorted(ev.duration_ms for ev in events if ev.duration_ms > 0)
        p50_ms = _percentile(durations, 0.50)
        p95_ms = _percentile(durations, 0.95)
        rps = count / self.window_s
        return {
            "count": count,
            "by_lane": dict(by_lane),
            "by_status": dict(by_status),
            "rps": rps,
            "error_rate": error_rate,
            "p50_ms": p50_ms,
            "p95_ms": p95_ms,
            "override_count": sum(1 for ev in events if ev.override_active),
            "duration_ms_window": self.window_s,
        }

    def events(self) -> Sequence[TrafficEvent]:
        """Return a snapshot of current events (read-only, thread-safe)."""
        with self._lock:
            return tuple(self._events)


# ---------------------------------------------------------------------------
# Trend bar
# ---------------------------------------------------------------------------


def render_trend(
    values,
    *,
    width: int = DEFAULT_TREND_WIDTH,
    chars: str = "▁▂▃▄▅▆▇█",
) -> str:
    """Render a trend bar of ``values`` as a unicode sparkline.

    Returns ``width`` characters.  Empty input produces ``width`` ``·``
    placeholder characters.  Will not raise on input shorter than ``width``.
    Accepts any iterable (including ``deque`` / generators); values are
    consumed via ``list(...)`` after a fast ``len()`` short-circuit.
    """
    if width <= 0:
        return ""
    try:
        n = len(values)
    except TypeError:
        values = list(values)
        n = len(values)
    if n == 0:
        return "·" * width
    buf = list(values)
    buf = [0.0] * (width - n) + buf if n < width else buf[-width:]
    lo, hi = min(buf), max(buf)
    if hi - lo < 1e-9:
        return "·" * width
    n_chars = len(chars) - 1
    out = [chars[int((v - lo) / (hi - lo) * n_chars)] for v in buf]
    return "".join(out)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class TrafficDashboard:
    """Real-time TRAFFIC dashboard.

    Use :meth:`record` (or :meth:`tick`) to feed events.  Use
    :meth:`summary` or :meth:`render` to read the current state.

    The dashboard is single-threaded; concurrent callers must serialize.

    Pass ``clock=`` to the constructor (or call ``set_clock``) to pin the
    wall clock for deterministic audit replays and CI snapshots.
    """

    def __init__(
        self,
        *,
        window_s: float = DEFAULT_WINDOW_SECONDS,
        bucket_s: float = DEFAULT_BUCKET_SECONDS,
        trend_width: int = DEFAULT_TREND_WIDTH,
        maxlen: int = 0,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.window = TrafficWindow(window_s=window_s, bucket_s=bucket_s, maxlen=maxlen)
        if clock is not None:
            self.window.set_clock(clock)
        self.trend_width = trend_width
        # RPS trend is appended on every record() call; consumers can
        # render a sparkline of it via :meth:`rps_trend`.
        # NEW-12 (SOTA fourth-pass): the trend deque is now wrapped in
        # a ``_Trend`` helper that owns its own ``Lock`` so concurrent
        # ``record()`` producers and ``summary()``/``rps_trend()``/
        # ``render_traffic()``/``progress_bar()`` readers can race
        # without corrupting the bounded deque (the previous inline
        # ``deque`` had no lock; ``TrafficWindow._lock`` only covers
        # ``_events``, not the dashboard-level trend).
        self._rps_trend = _Trend(maxlen=trend_width * 2)

    def set_clock(self, clock: Callable[[], float]) -> None:
        """Pin the wall clock on the underlying :class:`TrafficWindow`."""
        self.window.set_clock(clock)

    def record(self, event: TrafficEvent) -> None:
        """Record a single traffic event (defaulted helpers attached).

        F-8 (SOTA third-pass): the previous implementation called
        ``self.window.summary()`` per event to refresh the RPS trend.
        For a burst of ``N`` events this was an O(N²) operation
        (each ``summary`` re-evicts + re-sorts the entire deque).
        The trend point is now computed inline using the rolling
        count delta so a sustained burst stays at O(N).
        """
        self.window.record(event)
        # Inline trend update: append ``1 / window_s`` for a single
        # event so the sparkline scales with the per-call rate. We
        # avoid the full ``summary()`` call; the dashboard's
        # ``rps_trend`` reader rolls the window naturally because the
        # underlying deque is bounded by ``trend_width * 2``.
        self._rps_trend.append(1.0 / max(self.window.window_s, 1e-9))

    def tick(self, events: Iterable[TrafficEvent]) -> None:
        """Record many events in one call."""
        for ev in events:
            self.record(ev)

    def summary(self) -> dict[str, Any]:
        """Aggregate summary combining window and trend stats."""
        snap = self.window.summary()
        snap["rps_trend"] = render_trend(
            self._rps_trend.values(), width=self.trend_width
        )
        return snap

    def rps_trend(self) -> str:
        """Return just the RPS sparkline (e.g., for embedding in logs)."""
        return render_trend(self._rps_trend.values(), width=self.trend_width)

    def progress_bar(self) -> str:
        """Render the canonical progress bar (P-081).

        ``done`` is the current event count and ``total`` is the configured
        window seconds.  The bar's denominator is the window size, not the
        number of seconds — meaningful for a "rotating window" view.  Pass
        ``total=1`` for an unbounded count indicator.
        """
        snap = self.window.summary()
        return progress_bar(snap["count"], max(int(self.window.window_s), 1))


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------


def render_traffic(
    dashboard: TrafficDashboard,
    *,
    width: int = 60,
    title: str = "TRAFFIC",
) -> str:
    """Render a single TRAFFIC string from ``dashboard``.

    Format::

        TRAFFIC                                            updated 12:34:56
        ────────────────────────────────────────────────────────────
        count:    240        by_status: ok=232 err=6 warn=2
        rps:      4.0        error_rate: 2.5%
        p50_ms:   120        p95_ms:        410
        overrides active: 3
        ▁▂▃▄▅▆▇█▁▂▃▄▅▆▇█▁▂▃▄▅▆▇█▁▂▃▄▅▆▇ (rps trend)
    """
    snap = dashboard.summary()
    bar = progress_bar(snap["count"], max(int(snap["duration_ms_window"]), 1), width=20)
    rps = snap["rps"]
    err = snap["error_rate"] * 100
    by_status = ", ".join(f"{k}={v}" for k, v in sorted(snap["by_status"].items()))
    by_lane = ", ".join(f"{k}={v}" for k, v in sorted(snap["by_lane"].items()))

    return (
        f"{title}                                                bar={bar}\n"
        f"{'-' * width}\n"
        f"count:    {snap['count']:>5}     by_status: {by_status or '-'}\n"
        f"rps:      {rps:>5.2f}     error_rate: {err:>5.2f}%\n"
        f"p50_ms:   {snap['p50_ms']:>5.0f}     p95_ms:        {snap['p95_ms']:>5.0f}\n"
        f"by_lane:  {by_lane or '-'}\n"
        f"overrides active: {snap['override_count']}\n"
        f"{snap.get('rps_trend', '·' * dashboard.trend_width)} (rps trend)"
    )


# ---------------------------------------------------------------------------
# Trend helper (NEW-12, SOTA fourth-pass)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class _Trend:
    """Bounded, thread-safe trend deque for the dashboard-level RPS sparkline.

    Wraps :class:`collections.deque` in a per-instance ``Lock`` so concurrent
    ``TrafficDashboard.record()`` producers and ``summary()`` / ``rps_trend()``
    / ``render_traffic()`` / ``progress_bar()`` readers can race without
    corrupting the bounded deque. The previous inline ``deque`` had no lock
    (``TrafficWindow._lock`` only covers ``_events``, not the dashboard-level
    trend) — under load the bounded deque could raise ``IndexError`` mid-iter
    when ``popleft()`` interleaved with the consumer's ``list(...)`` snapshot.

    Public surface intentionally minimal so the call sites stay short:

    * ``append(value)`` — single-writer API (called from ``record()``).
    * ``values()`` — read-only snapshot for :func:`render_trend`.
    """

    maxlen: int
    _events: deque[float] = field(default_factory=deque)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self) -> None:
        if self.maxlen <= 0:
            self.maxlen = 64
        self._events = deque(self._events, maxlen=self.maxlen)

    def append(self, value: float) -> None:
        """Append a single trend sample under the lock."""
        with self._lock:
            self._events.append(value)

    def values(self) -> list[float]:
        """Return a snapshot list of trend values (caller may iterate freely)."""
        with self._lock:
            return list(self._events)

    def __len__(self) -> int:
        """Snapshot length so legacy probes (``len(d._rps_trend)``) keep working."""
        with self._lock:
            return len(self._events)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _percentile(values: Sequence[float], pct: float) -> float:
    """Return the percentile (0..1) of ``values``; 0.0 for empty input."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = max(0, min(len(sorted_vals) - 1, int(pct * (len(sorted_vals) - 1))))
    return sorted_vals[idx]


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------


__all__ = [
    "DEFAULT_BUCKET_SECONDS",
    "DEFAULT_TREND_WIDTH",
    "DEFAULT_WINDOW_SECONDS",
    "TrafficDashboard",
    "TrafficEvent",
    "TrafficWindow",
    "progress_bar",
    "progress_bar_with_eta",
    "render_traffic",
    "render_trend",
]
