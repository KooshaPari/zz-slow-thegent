"""MCP audit trail wiring — SOTA audit pass 7 Lane A.

Wires the on-disk :class:`thegent.mcp.server.mcp_audit_trail.MCPAuditTrail`
into the MCP server dispatch surface so every tool invocation, resource
read, and gate check is recorded into a single shared, bounded, thread-safe
trail that the cockpit's traffic pane can read.

Design constraints:

* **No new dep / no hot-path overhead.** The wiring records one
  ``AuditEntry`` per dispatch. ``record()`` is in-process, appends to a
  bounded list under a lock, and hashes payloads lazily — the bench in
  :mod:`scripts.bench_tool_invoke_ms_budget` already pins the
  ``tool_invoke_ms`` budget at 100ms, so we explicitly keep this cheap.
* **Defensive config.** ``max_entries`` is read from the environment
  variable ``THEGENT_MCP_AUDIT_MAX_ENTRIES`` (default ``5000``). Negative
  or zero values fall back to the default with a ``UserWarning`` so a
  bad operator config does not silently disable audit capture (the
  SOTA audit table flagged ``max_entries not validated`` as a defensive
  gap).
* **Lazy singleton.** The trail is created on first access so importing
  the module does no work. Tests use :func:`reset_audit_trail` to swap
  in a fresh trail.
* **Observability.** :func:`mcp_audit_stats` /
  :func:`mcp_audit_recent` / :func:`mcp_audit_query` are the cockpit
  gauge surface — same shape the existing cockpit snapshot produces.

Public surface:

* :data:`MCP_AUDIT_DEFAULT_MAX_ENTRIES`
* :func:`get_audit_trail`
* :func:`reset_audit_trail`
* :func:`record_tool_call`
* :func:`record_resource_read`
* :func:`record_gate_check`
* :func:`record_error`
* :func:`audit_context`
* :func:`audited_budget`
* :func:`mcp_audit_stats`
* :func:`mcp_audit_recent`
* :func:`mcp_audit_query`

Canonical home: ``thegent.mcp.server.mcp_audit_wiring``
"""

import logging
import os
import threading
import time
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from thegent.mcp.server.mcp_audit_trail import (
    AuditEntry,
    AuditEntryKind,
    MCPAuditTrail,
)

_log = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

MCP_AUDIT_DEFAULT_MAX_ENTRIES: int = 5000
_ENV_MAX_ENTRIES = "THEGENT_MCP_AUDIT_MAX_ENTRIES"


# ------------------------------------------------------------------
# Singleton trail
# ------------------------------------------------------------------

_lock = threading.Lock()
_trail: MCPAuditTrail | None = None


def _resolve_max_entries() -> int:
    """Read the configured ``max_entries`` from env, with a defensive default.

    A negative or zero value falls back to the default and emits a
    ``UserWarning`` so a misconfiguration does not silently disable
    audit capture (the SOTA audit table flagged
    ``max_entries not validated`` as a defensive gap).
    """
    raw = os.environ.get(_ENV_MAX_ENTRIES)
    if raw is None or raw.strip() == "":
        return MCP_AUDIT_DEFAULT_MAX_ENTRIES
    try:
        value = int(raw)
    except ValueError:
        warnings.warn(
            f"{_ENV_MAX_ENTRIES}={raw!r} is not an int; using default {MCP_AUDIT_DEFAULT_MAX_ENTRIES}",
            stacklevel=2,
        )
        return MCP_AUDIT_DEFAULT_MAX_ENTRIES
    if value <= 0:
        warnings.warn(
            f"{_ENV_MAX_ENTRIES}={value} must be positive; using default {MCP_AUDIT_DEFAULT_MAX_ENTRIES}",
            stacklevel=2,
        )
        return MCP_AUDIT_DEFAULT_MAX_ENTRIES
    return value


def get_audit_trail() -> MCPAuditTrail:
    """Return the module-level singleton :class:`MCPAuditTrail`.

    The trail is created on first call. Tests use
    :func:`reset_audit_trail` to swap it.
    """
    global _trail
    if _trail is not None:
        return _trail
    with _lock:
        if _trail is None:
            max_entries = _resolve_max_entries()
            _trail = MCPAuditTrail(max_entries=max_entries)
            _log.debug(
                "mcp audit trail initialised max_entries=%d env=%s",
                max_entries,
                _ENV_MAX_ENTRIES,
            )
        return _trail


def reset_audit_trail(max_entries: int | None = None) -> MCPAuditTrail:
    """Replace the singleton with a fresh trail. Tests only.

    If ``max_entries`` is ``None``, the configured
    ``THEGENT_MCP_AUDIT_MAX_ENTRIES`` is resolved (default
    :data:`MCP_AUDIT_DEFAULT_MAX_ENTRIES`).
    """
    global _trail
    if max_entries is None:
        max_entries = _resolve_max_entries()
    fresh = MCPAuditTrail(max_entries=max_entries)
    with _lock:
        _trail = fresh
    return fresh


# ------------------------------------------------------------------
# Record helpers
# ------------------------------------------------------------------


def record_tool_call(
    operation: str,
    *,
    agent: str = "unknown",
    session_id: str | None = None,
    outcome: str = "ok",
    duration_ms: float | None = None,
    payload: Any = None,
    extra: dict[str, Any] | None = None,
) -> AuditEntry:
    """Record a tool invocation. Cheap; safe in hot paths."""
    return get_audit_trail().record(
        kind=AuditEntryKind.TOOL_INVOCATION,
        operation=operation,
        agent=agent,
        session_id=session_id,
        outcome=outcome,
        duration_ms=duration_ms,
        payload=payload,
        extra=extra,
    )


def record_resource_read(
    operation: str,
    *,
    agent: str = "unknown",
    session_id: str | None = None,
    outcome: str = "ok",
    duration_ms: float | None = None,
    payload: Any = None,
    extra: dict[str, Any] | None = None,
) -> AuditEntry:
    """Record an MCP resource read."""
    return get_audit_trail().record(
        kind=AuditEntryKind.RESOURCE_READ,
        operation=operation,
        agent=agent,
        session_id=session_id,
        outcome=outcome,
        duration_ms=duration_ms,
        payload=payload,
        extra=extra,
    )


def record_gate_check(
    operation: str,
    *,
    agent: str = "unknown",
    session_id: str | None = None,
    outcome: str = "ok",
    duration_ms: float | None = None,
    payload: Any = None,
    extra: dict[str, Any] | None = None,
) -> AuditEntry:
    """Record a policy / contract gate check."""
    return get_audit_trail().record(
        kind=AuditEntryKind.GATE_CHECK,
        operation=operation,
        agent=agent,
        session_id=session_id,
        outcome=outcome,
        duration_ms=duration_ms,
        payload=payload,
        extra=extra,
    )


def record_error(
    operation: str,
    *,
    agent: str = "unknown",
    session_id: str | None = None,
    error_message: str,
    duration_ms: float | None = None,
    extra: dict[str, Any] | None = None,
) -> AuditEntry:
    """Record an MCP-side error (failure path of any dispatch)."""
    return get_audit_trail().record(
        kind=AuditEntryKind.ERROR,
        operation=operation,
        agent=agent,
        session_id=session_id,
        outcome="error",
        duration_ms=duration_ms,
        error_message=error_message,
        extra=extra,
    )


# ------------------------------------------------------------------
# Audit-aware context manager
# ------------------------------------------------------------------


@contextmanager
def audit_context(
    *,
    kind: AuditEntryKind | str,
    operation: str,
    agent: str = "unknown",
    session_id: str | None = None,
    payload: Any = None,
    extra: dict[str, Any] | None = None,
) -> Iterator[dict[str, Any]]:
    """Time the block and record start/finish into the audit trail.

    Records exactly one entry per call:

    * On normal exit: ``outcome="ok"`` with the elapsed ``duration_ms``.
    * On exception: ``outcome="error"`` with ``error_message=str(exc)``.

    The yielded ``state`` dict allows callers to attach extra fields to
    the recorded entry (e.g., ``state["verdict"] = "deny"``).

    ``kind`` may be an :class:`AuditEntryKind` (preferred) or a string
    matching a member value (``"tool_invocation"``,
    ``"resource_read"``, ``"gate_check"``, ``"error"``). Unknown
    strings are coerced to :attr:`AuditEntryKind.TOOL_INVOCATION` with
    a ``UserWarning`` so a typo does not silently misclassify the
    audit entry.
    """
    state: dict[str, Any] = {}
    if isinstance(kind, str):
        try:
            kind_enum = AuditEntryKind(kind)
        except ValueError:
            warnings.warn(
                f"audit_context: unknown kind={kind!r}; coercing to {AuditEntryKind.TOOL_INVOCATION.value}",
                stacklevel=2,
            )
            kind_enum = AuditEntryKind.TOOL_INVOCATION
    elif isinstance(kind, AuditEntryKind):
        kind_enum = kind
    else:
        raise TypeError(f"audit_context: kind must be AuditEntryKind or str, got {type(kind).__name__}")
    t0 = time.monotonic()
    error_message: str | None = None
    try:
        yield state
    except Exception as exc:  # noqa: BLE001 — record the message, re-raise.
        error_message = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        elapsed_ms = (time.monotonic() - t0) * 1000.0
        merged_extra: dict[str, Any] = dict(extra or {})
        merged_extra.update(state)
        # AUDIT-N+22 (SOTA audit pass 8, B3 reconciliation): when a caller
        # explicitly passes ``kind=AuditEntryKind.ERROR`` and the block
        # succeeds, the entry would otherwise record ``kind=error,
        # outcome=ok`` — semantically contradictory and likely to mask
        # audit anomalies downstream. Coerce ``outcome`` to ``"error"``
        # whenever the kind itself signals an error path so the JSONL
        # audit log and the cockpit's ``by_outcome`` breakdown stay
        # self-consistent. An exception inside the block still drives
        # ``outcome="error"`` via the ``error_message`` branch below.
        if error_message is not None or kind_enum == AuditEntryKind.ERROR:
            outcome = "error"
        else:
            outcome = "ok"
        try:
            get_audit_trail().record(
                kind=kind_enum,
                operation=operation,
                agent=agent,
                session_id=session_id,
                outcome=outcome,
                duration_ms=elapsed_ms,
                payload=payload,
                error_message=error_message,
                extra=merged_extra,
            )
        except Exception as exc:  # never let the audit raise in finally
            _log.warning("audit_context.record failed: %s", exc)


# ------------------------------------------------------------------
# Composite: budget + audit
# ------------------------------------------------------------------


@contextmanager
def audited_budget(
    kind: AuditEntryKind | str,
    operation: str,
    *,
    budget_ms: float | None = None,
    agent: str = "unknown",
    session_id: str | None = None,
    payload: Any = None,
    extra: dict[str, Any] | None = None,
) -> Iterator[dict[str, Any]]:
    """Compose :func:`mcp_budget_context` with :func:`audit_context`.

    AUDIT-N+22 (SOTA audit pass 8, A2 helper): collapses the
    ``with mcp_budget_context("..."):`` + ``with audit_context(...):``
    nesting into a single ``with audited_budget(...):`` call so every
    MCP tool/resource dispatch records exactly one audit entry and
    checks the per-call perf budget in lockstep. ``operation`` is
    used as both the perf-budget key and the audit ``operation``
    field, so budget violations and audit timestamps line up.

    ``kind`` follows the same ``AuditEntryKind | str`` contract as
    :func:`audit_context` (unknown strings coerce to ``TOOL_INVOCATION``
    with a ``UserWarning``). ``budget_ms`` overrides the named budget
    for this single measurement (useful for per-call overrides in
    tests); when ``None`` the named budget from ``MCP_PERF_BUDGETS`` is
    applied — same fallback contract as
    :func:`mcp_budget_context`.

    Performance: this helper adds one extra ``time.monotonic()`` read
    (the budget context already times its block) and one extra
    dictionary allocation for the merged ``extra`` payload. Both are
    in the low-microsecond range on dev hardware; the bench in
    :mod:`scripts.bench_tool_invoke_ms_budget` keeps the
    ``tool_invoke_ms`` budget pinned at 100ms so this helper has ~5
    orders of magnitude of headroom.
    """
    # Local import keeps ``mcp_perf_gates`` decoupled from
    # ``mcp_audit_wiring`` at module-load time (otherwise the two
    # would form an import cycle through ``mcp_audit_trail``).
    from thegent.mcp.server.mcp_perf_gates import mcp_budget_context

    with (
        audit_context(
            kind=kind,
            operation=operation,
            agent=agent,
            session_id=session_id,
            payload=payload,
            extra=extra,
        ) as state,
        mcp_budget_context(operation, budget_ms=budget_ms),
    ):
        yield state


# ------------------------------------------------------------------
# Observability gauge
# ------------------------------------------------------------------


def mcp_audit_stats() -> dict[str, Any]:
    """Return the singleton trail's :meth:`MCPAuditTrail.summary`.

    Same shape the cockpit snapshot consumes (already validated by
    AUDIT-N+15 contract tests in
    :mod:`tests.test_unit_mcp_audit_trail_contracts`).
    """
    return get_audit_trail().summary()


def mcp_audit_recent(n: int = 100) -> list[AuditEntry]:
    """Return the most recent ``n`` audit entries (newest last)."""
    return get_audit_trail().recent(n=n)


def mcp_audit_query(
    *,
    kind: AuditEntryKind | None = None,
    operation: str | None = None,
    agent: str | None = None,
    outcome: str | None = None,
    limit: int = 200,
) -> list[AuditEntry]:
    """Filter audit entries by field values."""
    return get_audit_trail().query(
        kind=kind,
        operation=operation,
        agent=agent,
        outcome=outcome,
        limit=limit,
    )


__all__ = [
    "MCP_AUDIT_DEFAULT_MAX_ENTRIES",
    "audited_budget",
    "audit_context",
    "get_audit_trail",
    "mcp_audit_query",
    "mcp_audit_recent",
    "mcp_audit_stats",
    "record_error",
    "record_gate_check",
    "record_resource_read",
    "record_tool_call",
    "reset_audit_trail",
]
