"""Unified worker daemon — orchestration event consumer + post-run hook.

The :class:`UnifiedWorkerDaemon` is the long-running consumer that
drains a :class:`~thegent.orchestration.event_queue.SubAgentEventQueue`
and, on each :class:`~thegent.orchestration.protocol.SubAgentEvent` with
``event_type=COMPLETED``, dispatches the
:class:`~thegent.governance.post_agent_run_hook.post_agent_run` governance
hook so downstream observability / compliance tooling sees the
lifecycle closure.

Hardening (AUDIT-N+37)
======================

| FR | Invariant |
|---|-----------|
| FR-ORC-073 | ``UnifiedWorkerDaemon(event_queue=)`` stores the queue; falls back to the global singleton when none is supplied. |
| FR-ORC-074 | ``_consume_events()`` exits cleanly on ``CancelledError``; COMPLETED events trigger ``_dispatch_post_agent_run_hook(run_id=, extra_context=)``. |
| FR-ORC-075 | ``_dispatch_post_agent_run_hook`` is a module-level symbol so test harnesses can patch it. |

The class is intentionally minimal — there is no global state, no
background thread, and no I/O outside the bound queue.  ``start()`` is
a no-op kept for legacy callers; ``stop()`` flips the daemon's
running flag but does not cancel any consumer task (the caller owns
the asyncio.Task lifecycle).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _dispatch_post_agent_run_hook(*, run_id: str, extra_context: dict[str, Any] | None = None) -> None:
    """Forward a COMPLETED event to the governance post-run hook.

    FR-ORC-075: this function lives at module scope so test harnesses
    can patch ``thegent.orchestration.unified_worker._dispatch_post_agent_run_hook``
    and observe the COMPLETED-event → hook dispatch path without
    exercising the real governance pipeline.

    The hook signature is ``post_agent_run(*, run_id, output_context,
    run_metadata, audit_log)``; the dormant event payload only carries
    ``{"agent_type": ...}`` so we forward it under ``output_context``
    (the most semantically appropriate of the four kwargs) and pass
    empty defaults for the rest.  Any failure inside the hook is
    logged and swallowed — a misbehaving post-run observer must never
    break the consumer loop.
    """
    try:
        from thegent.governance.post_agent_run_hook import post_agent_run
    except Exception as exc:  # noqa: BLE001 — defensive import guard
        logger.debug("post_agent_run_hook unavailable: %s", exc)
        return
    context = dict(extra_context or {})
    try:
        post_agent_run(
            run_id=run_id,
            output_context=context.get("output_context", context),
            run_metadata=context.get("run_metadata", {}),
            audit_log=context.get("audit_log", []),
        )
    except Exception as exc:  # noqa: BLE001 — see above
        logger.warning(
            "post_agent_run_hook raised for run_id=%r: %s",
            run_id,
            exc,
        )


class UnifiedWorkerDaemon:
    """Long-running consumer for :class:`SubAgentEventQueue`.

    Parameters
    ----------
    event_queue
        Optional :class:`SubAgentEventQueue` to drain.  When omitted
        the daemon binds to the process-wide singleton returned by
        :func:`thegent.orchestration.event_queue.get_global_event_queue`.

    Notes
    -----
    The daemon does NOT own an event loop — callers create an
    ``asyncio.Task`` around :meth:`_consume_events` and own its
    lifecycle.  ``stop()`` flips a flag the consumer can check between
    events; ``CancelledError`` is the canonical shutdown signal.
    """

    def __init__(self, event_queue: Any = None) -> None:
        # Lazy import to keep this module importable in lightweight
        # contexts (MCP server dynamic-loader that the dormant test
        # warns about).
        if event_queue is None:
            from thegent.orchestration.event_queue import get_global_event_queue

            event_queue = get_global_event_queue()
        self._event_queue: Any = event_queue
        self._running: bool = False

    # ------------------------------------------------------------------
    # Lifecycle (legacy)
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Mark the daemon as running (no background task is spawned)."""
        self._running = True

    def stop(self) -> None:
        """Mark the daemon as stopped (caller must cancel any task)."""
        self._running = False

    def is_running(self) -> bool:
        """Return True when :meth:`start` was called and :meth:`stop` was not."""
        return self._running

    # ------------------------------------------------------------------
    # Async consumer
    # ------------------------------------------------------------------

    async def _consume_events(self) -> None:
        """Drain the bound event_queue and dispatch COMPLETED events.

        Loops on ``event_queue.get()`` until the enclosing asyncio.Task
        is cancelled, at which point the ``CancelledError`` is
        re-raised so callers observe a clean shutdown.  Every
        ``COMPLETED`` event triggers
        :func:`_dispatch_post_agent_run_hook` with the event's
        ``request_id`` and the ``output_context`` derived from the
        event payload (FR-ORC-074).
        """
        while True:
            try:
                event = await self._event_queue.get()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 — defensive
                logger.warning(
                    "UnifiedWorkerDaemon._consume_events: get() raised %s — continuing",
                    exc,
                )
                continue
            self._handle_event(event)

    def _handle_event(self, event: Any) -> None:
        """Dispatch *event* to the right governance hook based on type.

        COMPLETED events trigger the post-agent-run hook.  Every other
        event type (STARTED / PROGRESS / FAILED / LOG / unknown) is
        a no-op for now — the cockpit and audit pipeline consume the
        event directly via the queue, so the daemon only fans out
        governance-relevant closures.
        """
        event_type = getattr(event, "event_type", None)
        # Resolve the enum value lazily to keep the daemon importable
        # without dragging in ``thegent.orchestration.protocol``.
        try:
            from thegent.orchestration.protocol import SubAgentEventType

            completed_value = SubAgentEventType.COMPLETED
        except Exception:  # noqa: BLE001 — defensive
            completed_value = "completed"
        if event_type == completed_value:
            run_id = getattr(event, "request_id", "") or ""
            payload = getattr(event, "payload", {}) or {}
            _dispatch_post_agent_run_hook(
                run_id=run_id,
                extra_context={"output_context": payload},
            )


__all__ = [
    "UnifiedWorker",
    "UnifiedWorkerDaemon",
    "_dispatch_post_agent_run_hook",
]


class UnifiedWorker:
    """Unified worker for orchestration (legacy stub)."""

    def __init__(self) -> None:
        self._workers: dict = {}

    def register(self, name: str, worker: object) -> None:
        self._workers[name] = worker

    def execute(self, task: dict) -> dict:
        return {"status": "success"}
