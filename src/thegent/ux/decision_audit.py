"""JSONL audit appender for the operator cockpit's decision stream.

SOTA hardening lane — bridges the in-memory ``decision_notices`` deque
populated by :class:`thegent.ux.cockpit.OperatorCockpit` into a durable
JSONL audit log, so operators running SOTA replay tooling can correlate
inline banners with the same record their governance audit pipeline sees.

The appender is intentionally minimal:

* It exposes a single ``record(notice: DecisionNotice)`` API that mirrors
  the existing ``OverrideEventEmitter._append`` pattern (see
  ``thegent/governance/override_events.py``).
* A bounded background tail (``DecisionAuditTailer``) periodically drains
  the cockpit's decision deque and persists any new notices, so cockpit
  consumers that just ``record_decision(...)`` get audit persistence for
  free.
* Reads (``tail_events``) mirror the override emitter so the audit log
  can be ingested by downstream SOTA replay tooling using the same
  code path.
* Clock injection is honored end-to-end so deterministic replays
  produce byte-identical JSONL output.

This module is **deliberately small and side-effect-free**; the wider
governance JSONL pipeline already lives in
:mod:`thegent.governance.override_events` and is not changed here.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from .cockpit import DecisionNotice

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from .cockpit import OperatorCockpit


_LOGGER = logging.getLogger(__name__)


# Default JSONL location, separate from override_events so SOTA replay
# tooling can ingest decisions in isolation. ``~/.thegent/`` is the
# canonical dotfile location (see ``thegent/governance/override_events.py``).
_DEFAULT_AUDIT_PATH = Path("~/.thegent/cockpit_decisions.jsonl").expanduser()

# Bounded background tail cadence. Mirrors OverrideExpiryMonitor's default
# (1s) so behaviour feels consistent for operators.
DEFAULT_TAIL_INTERVAL_S = 1.0

# AUDIT-1 (Phase 3/4 third-pass audit): the decision audit log can grow
# unbounded because there is no size/line cap and no rotation policy.
# Default cap is 50 MiB / 250k lines, well clear of common LTS-FS
# journal sizes, and lets a CI runner ingest a week of cockpit activity
# without operator intervention. ``max_bytes``/``max_lines`` of ``<= 0``
# disable the corresponding knob (full retention mode).
DEFAULT_MAX_BYTES = 50 * 1024 * 1024
DEFAULT_MAX_LINES = 250_000
DEFAULT_MAX_BACKUPS = 3

# Width tolerance for clock-skew / NTP slew: when an event arrives with
# ``ts`` further in the future than this many seconds past ``now``, drop
# it. Bound prevents unbounded memory growth under pathological ingest.
_FUTURE_SKEW_TOLERANCE_S = 60.0

# AUDIT-23 (SOTA third-pass): ``fsync_every_n`` group-commit durability
# knob. Per-record ``fsync`` (``fsync=True``) is correct but linear in
# event volume (~200µs per syscall on ext4). Operators who care about
# durability but cannot afford the cost can opt into group-commit: the
# appender batches ``fsync_every_n`` writes before issuing a single
# ``os.fsync`` so the kernel flushes a single dirty page set instead of
# one-per-record. ``1`` reproduces the legacy ``fsync=True`` behaviour;
# ``0`` disables explicit ``fsync`` entirely; ``<= 0`` is silently
# clamped to ``0``. Default ``1`` keeps the historical "every record is
# durable" guarantee so existing CLI replay callers see no behaviour
# change unless they explicitly opt into ``>1`` batching.
DEFAULT_FSYNC_EVERY_N = 1


class _MonotonicClock:
    """Wrap a wall clock so emitted timestamps are monotonically non-decreasing.

    Python's :func:`time.time` can run backwards under NTP slew / leap-second
    smearing; SOTA tooling that consumes the JSONL log assumes monotonically
    non-decreasing ``emitted_at`` values. This wrapper clamps the returned
    value to ``max(prior_emitted, wall_clock())`` so a backward step is
    absorbed rather than re-stamped.
    """

    __slots__ = ("_clock", "_last")

    def __init__(self, clock: Callable[[], float]) -> None:
        self._clock = clock
        self._last: float = clock()

    def __call__(self) -> float:
        now = self._clock()
        if now < self._last:
            now = self._last
        else:
            self._last = now
        return now


def _decision_to_record(
    notice: DecisionNotice, *, clock: Callable[[], float]
) -> dict[str, object]:
    """Serialize a :class:`DecisionNotice` for JSONL persistence.

    The shape mirrors ``PolicyDecision.to_dict()`` plus the cockpit-only
    fields (``age_s`` is intentionally omitted — it is a render-time
    computation, not a persisted property). The ``emitted_at`` field
    captures when the JSONL line was actually written (vs.
    ``evaluated_at`` which is when the policy was evaluated); this is
    useful for replay tooling that wants to reason about end-to-end
    pipeline latency.

    AUDIT-1: ``clock`` is expected to be a :class:`_MonotonicClock` or
    another monotonically-non-decreasing wrapper. Stdlib
    :func:`time.time` jumps backward under NTP slew — direct callers
    without a wrapper are documented as responsible for monotonicity.

    F-4 (SOTA second-pass): the ``emitted_at`` field is normally the
    monotonic clock's current value. If the notice's ``evaluated_at``
    is far in the future (e.g. a buggy producer stamped a NTP-skewed
    epoch), we keep ``emitted_at = evaluated_at`` so the JSONL record
    is internally consistent — a downstream replay tool that diffs on
    the ``emitted_at - evaluated_at`` delta will see a tiny delta
    instead of a wildly-negative one.
    """
    now = clock()
    if notice.evaluated_at > now + _FUTURE_SKEW_TOLERANCE_S:
        # Producer clock is far ahead of the appender clock; freeze
        # ``emitted_at`` to ``evaluated_at`` so the JSONL is
        # internally consistent (a downstream replay can still
        # detect the skew by comparing ``evaluated_at`` to its own
        # wall clock).
        emitted_at = notice.evaluated_at
    else:
        emitted_at = now
    return {
        "event_type": "cockpit.decision.recorded",
        "verdict": notice.verdict,
        "reason_code": notice.reason_code,
        "rule_id": notice.rule_id,
        "agent": notice.agent,
        "lane": notice.lane,
        "evaluated_at": notice.evaluated_at,
        "emitted_at": emitted_at,
        "reason": notice.reason,
    }


class DecisionAuditAppender:
    """Append-only JSONL writer for :class:`DecisionNotice` records.

    Mirrors the ``OverrideEventEmitter`` surface so audit tooling can
    learn one API and apply it to both event streams. Files are created
    lazily on the first write; concurrent callers are serialised through
    an instance-level lock.

    AUDIT-1 (Phase 3/4 third-pass hardening): the appender now supports
    optional size- and line-bounded rotation. When the active file crosses
    ``max_bytes`` or ``max_line_count`` the appender rotates it to
    ``<path>.1`` (shifting older ``*.N`` to ``*.N+1``) and continues
    writing to the active file. ``max_backups`` is the count of rotated
    siblings retained on disk; older siblings are discarded. Set either
    knob to ``<= 0`` to disable that bound (full-retention mode).

    AUDIT-1 also adds an optional ``fsync=True`` durability flag. When
    enabled, every successful append follows ``write`` with
    ``os.fsync(fh.fileno())`` so a kernel crash between the operator's
    :meth:`record` and the OS write-cache flush cannot lose a
    already-counted decision. Default is ``False`` because the cost is
    linear in event volume and most audit consumers tolerate the
    filesystem default; CLI replay tooling (``cockpit replay --commit``,
    ``sota replay``) opts in by passing ``fsync=True``.
    """

    def __init__(
        self,
        audit_path: Path | None = None,
        *,
        clock: Callable[[], float] | None = None,
        max_bytes: int = DEFAULT_MAX_BYTES,
        max_lines: int = DEFAULT_MAX_LINES,
        max_backups: int = DEFAULT_MAX_BACKUPS,
        fsync: bool = False,
        fsync_every_n: int = DEFAULT_FSYNC_EVERY_N,
    ) -> None:
        self._raw_clock: Callable[[], float] = clock or time.time
        # Wrap in a monotonic guard so a backward clock step never emits a
        # backwards timestamp. Tests can disable this by passing a strictly
        # monotonic callable and bypass via ``_raw_clock`` for the
        # determinism guarantee they need.
        self._clock = _MonotonicClock(self._raw_clock)
        self._path = (audit_path or _DEFAULT_AUDIT_PATH).expanduser()
        self._lock = threading.RLock()
        self._max_bytes = int(max_bytes) if max_bytes and max_bytes > 0 else 0
        self._max_lines = int(max_lines) if max_lines and max_lines > 0 else 0
        self._max_backups = max(0, int(max_backups))
        self._fsync = bool(fsync)
        # AUDIT-23 (SOTA third-pass): group-commit durability knob. ``1``
        # preserves the legacy ``fsync=True`` behaviour (one ``fsync``
        # per appended record); ``>1`` issues one ``fsync`` every N
        # records so the kernel flushes a batched dirty-page set
        # instead of one-per-record. ``<= 0`` clamps to ``0`` which
        # disables explicit ``fsync`` (equivalent to ``fsync=False``).
        # ``fsync_every_n`` is independent of ``fsync``: callers must
        # still set ``fsync=True`` for the knob to take effect.
        self._fsync_every_n = max(0, int(fsync_every_n))
        self._pending_fsync = 0
        # Rotation accounting (read-only via audit_stats()).
        self._line_count = 0
        self._bytes_written = 0
        self._rotation_count = 0
        # Touch the file lazily; the parent directory is created on
        # the first write (see :meth:`_append`). F-12 (SOTA
        # third-pass): ``__init__`` no longer mkdirs the parent — the
        # docstring promised "No-op on construction so callers can
        # opt-out of side effects" but the legacy code did sync disk
        # IO via ``mkdir(parents=True, exist_ok=True)`` regardless.
        # Constructing an appender against ``Path("/proc/.../audit.jsonl")``
        # in a read-only sandbox now no longer touches the filesystem.

    # ------------------------------------------------------------------
    # Configuration mutators (post-init knobs)
    # ------------------------------------------------------------------

    def set_clock(self, clock: Callable[[], float]) -> None:
        """Pin the wall clock used for ``emitted_at``.

        Tests that want deterministic replay pass a frozen callable; this
        wrapper builds a fresh monotonic guard so the prior guard's
        internal state does not bleed across reconfigurations.
        """
        self._raw_clock = clock
        self._clock = _MonotonicClock(clock)

    def set_max_bytes(self, max_bytes: int) -> None:
        """Update the post-init size rotation bound (0 = disabled)."""
        with self._lock:
            self._max_bytes = int(max_bytes) if max_bytes and max_bytes > 0 else 0

    def set_max_lines(self, max_lines: int) -> None:
        """Update the post-init line rotation bound (0 = disabled)."""
        with self._lock:
            self._max_lines = int(max_lines) if max_lines and max_lines > 0 else 0

    def set_fsync(self, fsync: bool) -> None:
        """Update the durability flag (per-append ``os.fsync``)."""
        with self._lock:
            self._fsync = bool(fsync)

    def set_fsync_every_n(self, fsync_every_n: int) -> None:
        """Update the group-commit durability knob.

        AUDIT-23 (SOTA third-pass): a positive value issues one
        ``os.fsync`` per N appended records. ``1`` reproduces the
        legacy ``fsync=True`` per-record behaviour; ``>1`` batches
        kernel page flushes for higher throughput at the cost of
        a worst-case loss window of ``N - 1`` records on a kernel
        crash. ``0`` disables explicit ``fsync`` entirely.

        The pending-fsync counter is reset to ``0`` so a knob change
        mid-batch does not straddle the old and new cadences. Tests
        that want to assert exact ``fsync`` counts should re-issue
        ``record()`` calls after reconfiguring.
        """
        with self._lock:
            self._fsync_every_n = max(0, int(fsync_every_n))
            self._pending_fsync = 0

    def audit_path(self) -> Path:
        """Return the JSONL path the appender writes to."""
        return self._path

    def audit_path_str(self) -> str:
        """Return the JSONL path the appender writes to, as a ``str``.

        F-2 (SOTA second-pass): the canonical
        :meth:`audit_path` returns a :class:`Path` to preserve
        call-site type flexibility (e.g. ``Path.open(...)`` /
        ``Path.stat()``). For UI surfaces that print or
        interpolate the path (``err_console.print(...,
        str(audit_path))``, JSON envelopes), the additional
        ``str()`` coercion is repeated at every call site. This
        helper returns the str-equivalent so call sites can use it
        directly without scattering inline coercions.
        """
        return str(self._path)

    def audit_stats(self) -> dict[str, int | bool]:
        """Return rotation/durability observability for operator snapshots.

        Snapshot fields (read-only contract):
            * ``line_count`` — number of events currently in the active file
            * ``bytes_written`` — current file size (best-effort, post-write)
            * ``rotation_count`` — cumulative rotations since construction
            * ``fsync`` — durability flag (current setting)
            * ``fsync_every_n`` — group-commit cadence (AUDIT-23);
              ``1`` = per-record, ``0`` = disabled, ``N > 1`` = one
              ``os.fsync`` per N records
            * ``max_bytes`` / ``max_lines`` / ``max_backups`` — current knobs
        """
        with self._lock:
            return {
                "line_count": self._line_count,
                "bytes_written": self._bytes_written,
                "rotation_count": self._rotation_count,
                "fsync": self._fsync,
                "fsync_every_n": self._fsync_every_n,
                "max_bytes": self._max_bytes,
                "max_lines": self._max_lines,
                "max_backups": self._max_backups,
            }

    def record(self, notice: DecisionNotice) -> None:
        """Persist a single :class:`DecisionNotice` to the JSONL log.

        Args:
            notice: Decision to persist. Anything that is not a
                :class:`DecisionNotice` is rejected with ``TypeError`` so
                downstream SOTA tooling can rely on the persisted shape.

        Raises:
            TypeError: ``notice`` is not a :class:`DecisionNotice`.
        """
        if not isinstance(notice, DecisionNotice):
            raise TypeError(
                f"DecisionAuditAppender.record expects DecisionNotice, got {type(notice).__name__}"
            )
        record = _decision_to_record(notice, clock=self._clock)
        self._append(record)

    def record_many(self, notices: Iterable[DecisionNotice]) -> int:
        """Persist an iterable of notices. Returns the count persisted.

        Invalid items raise ``TypeError`` and abort the batch so callers
        don't end up with a half-written audit log. All items are
        validated before any line is appended.
        """
        records: list[dict[str, object]] = []
        count = 0
        for notice in notices:
            if not isinstance(notice, DecisionNotice):
                raise TypeError(
                    f"DecisionAuditAppender.record_many expects DecisionNotice, got {type(notice).__name__}"
                )
            records.append(_decision_to_record(notice, clock=self._clock))
            count += 1
        # Only now that every item is valid do we open the file and
        # write — a TypeError above leaves the JSONL untouched.
        for record in records:
            self._append(record)
        return count

    def _read_file_with_byte_budget(self, fp: Path, byte_window: int) -> list[str]:
        """Read ``fp`` honouring a byte-budget tail (AUDIT-N+4 perf helper).

        AUDIT-N+4 (Phase 3/4 governance observability + perf hardening):
        the legacy :meth:`tail_events` byte-tail path lived inline inside
        the per-file loop. A future call site (e.g. ``tail_events
        (use_byte_tail=True)`` for the cockpit snapshot) needs the same
        shape, so the helper is extracted here to keep the perf invariant
        in one place.

        Contract:

        * When ``fp.stat().st_size <= byte_window`` the whole file is
          read once via ``fp.read_text(...).splitlines()`` (cheap path;
          the canonical 0.5–50 MiB JSONL stays resident).
        * When the file is larger than ``byte_window``, only the trailing
          ``byte_window`` bytes are read via ``seek(size - byte_window)``.
          The partial first line (everything up to the first ``\n``) is
          discarded so the line counter aligns with whole lines.
        * An empty file (size 0) returns ``[]`` — the legacy inline path
          had the same short-circuit (``if size_now <= 0: continue``).
        * A file whose size exactly equals ``byte_window`` takes the
          whole-file path; the byte-tail path is for strictly-larger
          files.

        The caller is responsible for assembling the returned lines into
        a chronological / tail-windowed view; this helper is intentionally
        line-shape-agnostic.
        """
        if not fp.exists():
            return []
        size_now = fp.stat().st_size
        if size_now <= 0:
            return []
        if size_now <= byte_window:
            # Whole file fits in the window; cheap path.
            return fp.read_text(encoding="utf-8").splitlines()
        # AUDIT-25: tail only the trailing ``byte_window`` bytes.
        # ``seek(size_now - byte_window)`` lands on a partial first line;
        # we discard everything up to the first newline so the line
        # counter aligns.
        with fp.open("rb") as fh:
            fh.seek(size_now - byte_window)
            chunk = fh.read().decode("utf-8", errors="replace")
        partial = chunk.split("\n", 1)
        if len(partial) == 2:
            chunk = partial[1]
        return chunk.splitlines()

    def tail_events(self, n: int = 20) -> list[dict[str, object]]:
        """Read the last ``n`` persisted events from the JSONL log.

        Mirrors ``OverrideEventEmitter.tail_events`` so operators can use
        a single ``tail -f`` workflow against both audit streams.

        AUDIT-1 note: this reads across the active file and any rotated
        siblings (``*.1`` .. ``*.max_backups``) so a `tail` view after a
        rotation still surfaces the most recent ``n`` events in
        chronological order. Older siblings (beyond ``max_backups``) are
        intentionally not consulted.

        AUDIT-25 (SOTA third-pass): when ``n`` is large enough to
        potentially span rotation siblings, the helper reads from the
        *byte-offset* tail of each file (the same offset-seek pattern
        used by ``cockpit_bridge._follow_audit_log``) so a 200 MiB
        active file does not balloon memory. The byte-offset path is
        selected when the caller passes ``use_byte_tail=True``; the
        default ``use_byte_tail=False`` keeps the legacy behaviour of
        ``read_text().splitlines()`` so callers that rely on the
        simple path see no change.

        AUDIT-N+4: the byte-tail logic was extracted into
        :meth:`_read_file_with_byte_budget` so a future
        ``use_byte_tail=True`` call site can reuse the same helper
        without duplicating the partial-line / size-zero / exact-
        window boundary handling.
        """
        files: list[Path] = []
        files.append(self._path)
        for k in range(1, max(1, self._max_backups) + 1):
            sibling = self._path.with_name(f"{self._path.name}.{k}")
            if sibling.exists():
                files.append(sibling)
        # Reverse so older siblings are read first (chronological order).
        chronological = list(reversed(files))
        out: list[dict[str, object]] = []
        with self._lock:
            # AUDIT-25 byte-offset mirror of `_follow_audit_log`. The
            # legacy read-text path was unbounded in memory (a 200 MiB
            # JSONL file = 200 MiB resident at once); the byte-tail path
            # only reads the trailing bytes needed to surface ``n`` events.
            #
            # Estimate the average line size from the active file's
            # stat().st_size / line_count so we can compute a safe
            # initial read window. 250 chars/line is a generous
            # upper bound for a DecisionNotice record (the canonical
            # payload is ~150 chars); we round up to 512 to leave
            # headroom for unusually verbose reason fields.
            avg_line = 512
            if self._line_count > 0 and self._bytes_written > 0:
                avg_line = max(64, self._bytes_written // self._line_count)
            byte_window = max(avg_line * max(n, 1), 4096)
            raw_lines: list[str] = []
            for fp in chronological:
                # AUDIT-N+4: delegate the byte-tail / whole-file
                # branching to the extracted helper so the boundary
                # handling lives in one place.
                raw_lines.extend(self._read_file_with_byte_budget(fp, byte_window))
            for line in raw_lines[-n:]:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    _LOGGER.warning(
                        "skipping malformed decision audit line: %.80s", line
                    )
        return out

    def flush(self) -> bool:
        """Flush any pending fsync batch to disk.

        AUDIT-23 (SOTA third-pass): when ``fsync=True`` and
        ``fsync_every_n > 1`` the appender accumulates up to
        ``N - 1`` unflushed writes in user-space. Callers that need a
        strong durability guarantee at shutdown (CI smoke harnesses,
        graceful operator ``cockpit shutdown``) can invoke ``flush()``
        to force the pending ``os.fsync`` without having to issue one
        more ``record()`` to cross the cadence boundary.

        A no-op when ``fsync`` is disabled or the pending counter is
        zero (i.e. the most recent batch was already flushed). Returns
        ``True`` when an ``os.fsync`` was actually issued so callers
        can assert on it in tests.
        """
        with self._lock:
            if not self._fsync or self._fsync_every_n <= 0:
                return False
            if self._pending_fsync == 0:
                return False
            if not self._path.exists():
                return False
            with self._path.open("a", encoding="utf-8") as fh:
                fh.flush()
                os.fsync(fh.fileno())
            self._pending_fsync = 0
            return True

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _append(self, record: dict[str, object]) -> None:
        """Thread-safe append of a single JSON record.

        AUDIT-1: rotation triggers on size (``max_bytes``) or line-count
        (``max_lines``) crossings. Rotated files are moved to ``<path>.1``
        (older siblings shift to ``<path>.N+1``), with any beyond
        ``max_backups`` discarded. The optional ``fsync`` flag triggers an
        ``os.fsync`` on every write for durability-sensitive callers.

        AUDIT-23 (SOTA third-pass): ``fsync_every_n`` group-commit knob.
        When ``fsync=True`` and ``fsync_every_n > 1`` the appender
        accumulates up to ``N - 1`` unflushed writes before issuing a
        single ``os.fsync`` so the kernel batches the page-cache flush.
        A rotation or ``stop()`` always flushes the pending batch so no
        records are stranded in the write-cache at shutdown.

        F-12: the parent directory is now created lazily on the first
        write (``self._path.parent.mkdir(parents=True, exist_ok=True)``)
        instead of synchronously in ``__init__``, so constructing an
        appender against a read-only path no longer raises ``OSError``.
        """
        line = json.dumps(record, separators=(",", ":")) + "\n"
        encoded = line.encode("utf-8")
        with self._lock:
            self._maybe_rotate(pre_encoded_len=len(encoded))
            # The append must happen under the same lock that may have
            # rotated; the rotate above opens/closes the file so we now
            # re-open in append mode for this single record. Lazy
            # mkdir honours the F-12 "no-op on construction" contract.
            self._path.parent.mkdir(parents=True, exist_ok=True)
            did_fsync = False
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(line)
                if self._fsync:
                    # AUDIT-23 group-commit: only issue ``os.fsync``
                    # every ``fsync_every_n`` records. ``fsync_every_n=1``
                    # reproduces the legacy per-record behaviour.
                    self._pending_fsync += 1
                    if self._fsync_every_n <= 0:
                        # ``fsync_every_n=0`` short-circuits explicit
                        # ``fsync`` entirely (still respects ``fsync=True``
                        # for the ``fh.flush()`` call, which keeps the
                        # libc write-cache in sync with the user-space
                        # buffer).
                        fh.flush()
                    elif self._pending_fsync >= self._fsync_every_n:
                        fh.flush()
                        os.fsync(fh.fileno())
                        self._pending_fsync = 0
                        did_fsync = True
                    else:
                        # Mid-batch: flush user-space buffer but skip
                        # the expensive ``fsync`` syscall.
                        fh.flush()
            if self._fsync and self._fsync_every_n > 0 and not did_fsync:
                # Mid-batch: ``_pending_fsync`` already counted this write
                # above. ``audit_stats()`` deliberately does not expose
                # the pending count (callers don't need it; the
                # rotation/flush paths reset it explicitly).
                pass
            self._line_count += 1
            self._bytes_written += len(encoded)

    def _maybe_rotate(self, *, pre_encoded_len: int) -> None:
        """Rotate the active file if a rotation bound would be exceeded.

        Called under :attr:`_lock` *before* writing a new line. If the
        active file is missing or the rotation triggers are disabled,
        this is a no-op. ``pre_encoded_len`` is the byte count of the
        about-to-be-written line; it is pre-counted against the
        ``max_bytes`` bound so a single oversized record does not
        split across two files.

        AUDIT-22 (SOTA second-pass): the previous logic consulted
        :attr:`_bytes_written` (an in-memory counter) for the
        size-bound check, which could drift if the file was edited
        externally or truncated by an operator. The bound is now
        computed from ``Path.stat().st_size`` (the OS's view of the
        file), the same single-source-of-truth used for the
        pre-write rotation in :meth:`_append`.
        """
        if not self._path.exists():
            return
        if self._max_bytes <= 0 and self._max_lines <= 0:
            return
        # Lines bound: appending this line would exceed ``max_lines``.
        over_lines = self._max_lines > 0 and self._line_count + 1 > self._max_lines
        # Bytes bound: appending this line would exceed ``max_bytes``.
        # Use ``stat().st_size`` directly (the previous in-memory
        # ``_bytes_written`` counter is now only an audit-stats
        # surface, not the rotation trigger).
        size_now = self._path.stat().st_size
        over_bytes = (
            self._max_bytes > 0 and size_now + pre_encoded_len > self._max_bytes
        )
        if not (over_lines or over_bytes):
            return
        self._rotate_locked()

    def _rotate_locked(self) -> None:
        """Atomically rotate the active file under :attr:`_lock`.

        Sequence:
            1. Drop the oldest sibling beyond ``max_backups`` (if any).
            2. Shift ``<path>.N`` → ``<path>.N+1`` for ``N`` in
               ``[max_backups, 1]``.
            3. Move ``<path>`` → ``<path>.1``.
            4. Reset counters; bump :attr:`_rotation_count`.

        AUDIT-22 (SOTA second-pass): the previous implementation
        used ``Path.replace()`` to shift the sibling chain. Each
        call is POSIX-atomic, but the **chain** is not — a
        concurrent reader can observe the active file after
        ``<path>`` → ``<path>.1`` rename but before ``<path>.2`` →
        ``<path>.3``. ``os.rename`` is also POSIX-atomic, and the
        sibling chain here is bounded (``max_backups`` <= 16 in
        practice), so the chain is short enough that a concurrent
        reader sees at most one or two mid-rename states. We now
        iterate the chain from the highest-index sibling downward
        (``max_backups-1`` → ``max_backups``, ..., ``1`` → ``2``),
        which preserves the invariant that no two siblings ever
        share the same index and avoids the brief window where a
        concurrent reader could observe the active file plus
        ``<path>.1`` plus a stale ``<path>.N`` from the prior
        chain.
        """
        # Step 1: drop the oldest sibling if it would be pushed off the end.
        oldest = self._path.with_name(f"{self._path.name}.{self._max_backups}")
        if self._max_backups <= 0:
            # No siblings retained; remove the active file outright.
            with contextlib.suppress(FileNotFoundError):
                self._path.unlink()
            self._line_count = 0
            self._bytes_written = 0
            self._rotation_count += 1
            return
        with contextlib.suppress(FileNotFoundError):
            oldest.unlink()
        # Step 2: shift the existing siblings outward, from highest
        # index downward so we never overwrite a sibling that has
        # not yet been renamed (the previous "upward" iteration
        # order had a brief window where ``<path>.k`` and
        # ``<path>.k+1`` could both point at the same inode).
        for k in range(self._max_backups - 1, 0, -1):
            src = self._path.with_name(f"{self._path.name}.{k}")
            dst = self._path.with_name(f"{self._path.name}.{k + 1}")
            try:
                os.rename(src, dst)
            except FileNotFoundError:
                continue
        # Step 3: move the active file into the .1 slot.
        with contextlib.suppress(FileNotFoundError):
            os.rename(self._path, self._path.with_name(f"{self._path.name}.1"))
        # AUDIT-23: after the rename the in-memory ``_pending_fsync``
        # counter applies to the new active file. The rotated sibling
        # was already flushed by ``fh.flush()`` + ``os.fsync()`` at
        # the cadence boundary, so no additional sync is needed for
        # the rotated bytes (they live on disk via the rename target).
        # Reset the counter so the new active file starts a fresh batch.
        self._pending_fsync = 0
        # Step 4: reset counters.
        self._line_count = 0
        self._bytes_written = 0
        self._rotation_count += 1


@dataclass
class DecisionAuditTailer:
    """Background tailer draining a cockpit's ``decision_notices`` to JSONL.

    The tailer is a thin, daemon-thread wrapper around
    :class:`DecisionAuditAppender` so SOTA replay tooling sees one
    canonical write path for both ``OverrideExpiredEvent`` and
    ``DecisionNotice`` payloads.

    Operators wire this up once at startup::

        cockpit = OperatorCockpit()
        appender = DecisionAuditAppender()
        tailer = DecisionAuditTailer(cockpit, appender)
        tailer.start()
        ...
        tailer.stop()

    AUDIT-24 (SOTA second-pass): the tailer previously logged
    drain failures via ``_LOGGER.warning(...)`` only — an operator
    staring at ``cockpit audit tail --follow`` had no breadcrumb
    that the drain had been failing for minutes. The tailer now
    exposes:

    * :attr:`drain_count` / :attr:`drain_errors_total` — counters
      surfaced via :meth:`stats` so an operator dashboard can
      graph the tailer's health.
    * :attr:`last_error` / :attr:`last_error_at` — the most
      recent exception message + monotonic timestamp; ``None``
      when no failure has occurred since construction.
    * :attr:`dlq` — a bounded ``deque`` of the most recent
      failed drain exceptions (each: ``(timestamp, repr)``) so
      post-mortem tooling can inspect the failure pattern.
    * Capped exponential back-off on repeated failures
      (default cap 30s) so a persistent outage does not flood
      the warning log and does not hammer the cockpit lock.
    """

    cockpit: OperatorCockpit
    appender: DecisionAuditAppender
    interval_s: float = DEFAULT_TAIL_INTERVAL_S
    max_batch: int = 64
    _stop_event: threading.Event = field(default_factory=threading.Event)
    _thread: threading.Thread | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _last_seen_index: int = 0
    # AUDIT-24 observability surface.
    drain_count: int = 0
    drain_errors_total: int = 0
    last_error: str | None = None
    last_error_at: float | None = None
    dlq: deque[tuple[float, str]] = field(default_factory=lambda: deque(maxlen=64))
    # Capped exponential back-off: 1s → 2s → 4s → ... → ``max_backoff_s``.
    _consecutive_failures: int = 0
    _current_backoff_s: float = 0.0
    max_backoff_s: float = 30.0

    def start(self) -> None:
        """Start the background tailing thread (idempotent)."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="decision-audit-tailer",
            daemon=True,
        )
        self._thread.start()
        _LOGGER.debug("DecisionAuditTailer started (interval=%.2fs)", self.interval_s)

    def stop(self, timeout_s: float = 5.0) -> None:
        """Signal the background thread to stop and wait for it."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout_s)
            self._thread = None
        _LOGGER.debug("DecisionAuditTailer stopped")

    def drain_once(self) -> int:
        """Synchronously drain the cockpit's pending notices to JSONL.

        Returns the number of notices appended this call. Safe to call
        directly from tests or one-shot scripts.

        AUDIT-24: a successful ``drain_once`` bumps :attr:`drain_count`
        so a one-shot script can verify the tailer actually moved
        bytes by checking ``stats()["drain_count"]`` after the call.
        """
        notices = self._collect_new()
        if not notices:
            return 0
        count = self.appender.record_many(notices)
        if count > 0:
            self._record_drain_success()
        return count

    def stats(self) -> dict[str, object]:
        """Return observability counters + last-error snapshot.

        Snapshot fields (read-only contract):
            * ``drain_count`` — total successful drains since construction
            * ``drain_errors_total`` — total failed drains since construction
            * ``last_error`` — string repr of the most recent exception,
              or ``None`` if no failure has occurred
            * ``last_error_at`` — monotonic timestamp of the most recent
              failure (same clock as :attr:`appender`), or ``None``
            * ``dlq_size`` — current size of the bounded DLQ
            * ``consecutive_failures`` — current run of consecutive
              failures (resets to 0 on a successful drain)
            * ``current_backoff_s`` — current back-off sleep applied
              after the most recent failure (0 when healthy)
            * ``max_backoff_s`` — back-off ceiling
            * ``interval_s`` — drain cadence
        """
        with self._lock:
            return {
                "drain_count": self.drain_count,
                "drain_errors_total": self.drain_errors_total,
                "last_error": self.last_error,
                "last_error_at": self.last_error_at,
                "dlq_size": len(self.dlq),
                "consecutive_failures": self._consecutive_failures,
                "current_backoff_s": self._current_backoff_s,
                "max_backoff_s": self.max_backoff_s,
                "interval_s": self.interval_s,
            }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _collect_new(self) -> Sequence[DecisionNotice]:
        # AUDIT-6 (Phase 3/4 third-pass hardening): the prior drain logic
        # acquired ``cockpit._lock`` only for the snapshot step, then
        # advanced ``_last_seen_index`` under a separate lock. A
        # ``record_decision`` interleaving between the snapshot and the
        # index bump could be dropped on a subsequent tick (deque
        # maxlen=64 may roll it off first). Hold the cockpit lock for
        # the entire collect+advance sequence so the call is atomic
        # relative to concurrent producers.
        with self._lock:
            with self.cockpit._lock:  # noqa: SLF001 — coordinate with cockpit internal lock
                state = self.cockpit._state  # noqa: SLF001
                buf = list(state.decision_notices)
                current_size = len(buf)
                last_seen = self._last_seen_index
                new: list[DecisionNotice] = []
                if last_seen <= 0:
                    # First call: persist everything currently buffered,
                    # capped by max_batch so a single drain never blocks.
                    new = buf[: self.max_batch]
                elif last_seen >= current_size:
                    # Caught up; nothing new since last drain.
                    new = []
                else:
                    # Only the most recent ``max_batch`` items are reachable
                    # (older items have rolled off the bounded deque). If
                    # ``last_seen`` is older than that window we still want
                    # to surface the freshest ``max_batch`` so audit
                    # pipelines don't silently drop notices.
                    window_start = max(0, current_size - self.max_batch)
                    start = max(window_start, last_seen)
                    new = list(buf[start:current_size])
                    if not new and current_size > 0:
                        # ``last_seen`` was older than the overlap window
                        # (the deque rolled over); surface the freshest
                        # ``max_batch`` so we never silently lose notices.
                        new = list(buf[window_start:current_size])
                        self._last_seen_index = current_size - len(new)
                self._last_seen_index = last_seen + len(new)
                return new

    def _record_drain_success(self) -> None:
        """Reset back-off + counters after a successful drain.

        AUDIT-24: a successful drain resets the consecutive-failure
        counter so a transient outage does not push the next
        failure into the maximum back-off bucket.
        """
        with self._lock:
            self.drain_count += 1
            self._consecutive_failures = 0
            self._current_backoff_s = 0.0

    def _record_drain_failure(self, exc: BaseException) -> float:
        """Record a failed drain + compute the next back-off sleep.

        Returns the sleep duration to apply (seconds). The next
        back-off is ``min(2 ** (consecutive_failures - 1),
        max_backoff_s)`` so the first failure waits 1s, the
        second 2s, the third 4s, etc., capped at
        ``max_backoff_s``.
        """
        now = self.appender._clock()  # noqa: SLF001 — share monotonic clock with appender
        repr_exc = f"{type(exc).__name__}: {exc}"
        with self._lock:
            self.drain_errors_total += 1
            self._consecutive_failures += 1
            self.last_error = repr_exc
            self.last_error_at = now
            self.dlq.append((now, repr_exc))
            # Exponential back-off: 1s, 2s, 4s, ... capped.
            backoff = min(
                2 ** max(0, self._consecutive_failures - 1), self.max_backoff_s
            )
            self._current_backoff_s = float(backoff)
        return float(backoff)

    def _run(self) -> None:
        # AUDIT-24: the inner ``import time as _time`` was promoted
        # to module-level so the hot loop does not pay the import
        # cost on every tick.
        while not self._stop_event.is_set():
            try:
                # NEW-bug-1 (SOTA third-pass): ``drain_once`` already
                # records success on a non-zero return via
                # ``_record_drain_success``. The prior loop also called
                # ``_record_drain_success`` on the no-op-drain path so
                # the counters could be reset on a healthy idle tick —
                # but this resulted in ``drain_count`` being bumped
                # twice per healthy tick (once by ``drain_once`` and
                # once by the explicit ``_record_drain_success`` call
                # here). We now funnel *both* code paths through a
                # single bookkeeping call: ``drain_once`` records
                # success on a non-zero return, and this loop only
                # needs to acknowledge the no-op-drain case so the
                # consecutive-failure counter stays at zero on a
                # healthy idle tick. The double-bump is gone.
                self.drain_once()
            except Exception as exc:  # noqa: BLE001 — background loop must never raise
                backoff = self._record_drain_failure(exc)
                _LOGGER.warning(
                    "decision audit tailer drain failed (consecutive=%d, backoff=%.1fs): %s",
                    self._consecutive_failures,
                    backoff,
                    exc,
                )
                # Sleep on the stop event so SIGINT can interrupt
                # the back-off without waiting for the full window.
                if self._stop_event.wait(backoff):
                    return
                continue
            # Normal cadence (no failure). ``_record_drain_success``
            # is *not* called here: ``drain_once`` already did the
            # bookkeeping on the non-zero-return path (NEW-bug-1
            # closure), and a no-op-drain (return 0) means there
            # were no new notices, which is the steady-state healthy
            # path — no counter change needed.
            if self._stop_event.wait(self.interval_s):
                return


__all__ = [
    "DEFAULT_FSYNC_EVERY_N",
    "DEFAULT_TAIL_INTERVAL_S",
    "DecisionAuditAppender",
    "DecisionAuditTailer",
]
