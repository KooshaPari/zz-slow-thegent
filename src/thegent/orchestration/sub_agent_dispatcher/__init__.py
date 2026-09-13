"""Sub-agent dispatcher — plan-node → ``InterAgentMessage`` → ``MessageBus``.

The :class:`SubAgentDispatcher` is the canonical entry point for routing
:class:`PlanNode` work to the correct agent queue.  It publishes an
:class:`InterAgentMessage` of ``message_type="task_request"`` carrying the
node's task, id, and (optional) ``agent_hint`` routing metadata, and
returns the assigned message id so the caller can correlate later
:class:`InterAgentMessage` results.

Hardening (AUDIT-N+33)
----------------------
- Constructor validates ``bus`` is a :class:`MessageBus` and ``plan`` (when
  supplied) is an :class:`OrchestrationPlan`.  Older kwargs (``registry``,
  ``runner``, ``policy_engine``) are tolerated for backwards compatibility
  but do not influence dispatch behaviour — the dispatcher is now
  *message-bus-only*.
- :meth:`dispatch` auto-subscribes the recipient on the bus before
  publishing, so callers do not have to pre-register agents.
- :meth:`dispatch_all` performs a deterministic topological sort so that
  parents are always dispatched before their children.  Cycles raise
  :class:`ValueError` (no silent deadlock).
- :meth:`collect_results` auto-subscribes the agent on demand and forwards
  to :meth:`MessageBus.drain`.
- :attr:`sender_id` is stable per dispatcher instance (UUID4) so that
  downstream agents can identify the originator.

# @trace WL-082
# @trace AUDIT-N+33
"""

from __future__ import annotations

import threading
import uuid
from collections.abc import Iterable
from typing import Any

from thegent.agents.plangent import PlanNode
from thegent.orchestration.inter_agent_protocol import (
    InterAgentMessage,
    MessageBus,
)
from thegent.orchestration.plan import (
    AGENT_HINT,
    OrchestrationPlan,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DISPATCHER_SENDER_PREFIX = "dispatcher"


# ---------------------------------------------------------------------------
# DispatchResult — carried back from a runner to the executor.
# ---------------------------------------------------------------------------

import contextlib

from thegent.orchestration.sub_agent_dispatcher.dispatch_result import DispatchResult

# ---------------------------------------------------------------------------
# SubAgentDispatcher — canonical (bus + plan) implementation
# ---------------------------------------------------------------------------


class SubAgentDispatcher:
    """Publishes :class:`PlanNode` work to a :class:`MessageBus`.

    Parameters
    ----------
    bus
        The :class:`MessageBus` used to deliver :class:`InterAgentMessage`
        instances to subscribed agents.
    plan
        Optional :class:`OrchestrationPlan` the dispatcher is bound to.
        When set, ``self.plan`` exposes it; ``dispatch_all(plan)`` is the
        canonical bulk path.
    sender_id
        Override the auto-generated sender id (default: a deterministic
        UUID4 string prefixed ``"dispatcher-"``).
    registry / runner / policy_engine / config
        Legacy kwargs kept for backwards compatibility with the
        pre-WL-082 stub.  They are tolerated but not consulted by the
        current dispatch path.
    """

    def __init__(
        self,
        bus: MessageBus | None = None,
        plan: OrchestrationPlan | None = None,
        *,
        sender_id: str | None = None,
        registry: Any = None,
        runner: Any = None,
        policy_engine: Any = None,
        config: Any = None,
        capability_index: Any = None,
        event_queue: Any = None,
        budget_tracker: Any = None,
        **_: Any,
    ) -> None:
        if bus is not None and not isinstance(bus, MessageBus):
            raise TypeError(f"bus must be MessageBus, got {type(bus).__name__}")
        if plan is not None and not isinstance(plan, OrchestrationPlan):
            raise TypeError(
                f"plan must be OrchestrationPlan, got {type(plan).__name__}"
            )
        # Backwards-compat: the legacy stub accepted `registry` /
        # `runner` / `policy_engine` / `config` and stored them as
        # attributes.  We keep the attributes so old callers can still
        # introspect them but the canonical dispatch path no longer
        # consults them.
        self.bus = bus if bus is not None else MessageBus()
        self.plan = plan
        self.registry = registry
        self.runner = runner
        self.policy_engine = policy_engine
        self.config = config
        self.capability_index = capability_index
        self.event_queue = event_queue
        self.budget_tracker = budget_tracker
        # Re-entrant lock so concurrent dispatchers do not see a torn
        # STARTED / COMPLETED event pair (FR-ORC-070).
        self._dispatch_lock: threading.RLock = threading.RLock()
        self.sender_id = (
            sender_id
            if isinstance(sender_id, str) and sender_id
            else f"{_DISPATCHER_SENDER_PREFIX}-{uuid.uuid4()}"
        )

    # ------------------------------------------------------------------
    # Single-node dispatch
    # ------------------------------------------------------------------

    def dispatch(self, node: Any) -> str:
        """Publish a ``task_request`` message for ``node`` and return its id.

        The recipient id is derived from the node's ``agent_hint``
        metadata when present, otherwise it falls back to ``node.id`` so
        the dispatch always lands on a queue the bus can deliver to.

        The bus is auto-subscribed for the recipient (idempotent) before
        publishing, so callers do not have to pre-register agents.

        AUDIT-N+37: accepts either a :class:`PlanNode` (canonical) or a
        :class:`~thegent.orchestration.protocol.SubAgentRequest`
        (dormant WL-085 contract).  When ``self.event_queue`` is bound,
        a :class:`~thegent.orchestration.protocol.SubAgentEvent` with
        ``event_type=STARTED`` is published before the bus message and
        ``event_type=COMPLETED`` is published after (FR-ORC-067).
        ``self.budget_tracker.check(...)`` is consulted before the
        message is published; ``BudgetExceededError`` still emits the
        STARTED event so consumers see the dispatch was attempted, but
        no COMPLETED event (FR-ORC-068).
        """
        # AUDIT-N+37: dormant WL-085 contract accepts SubAgentRequest.
        # Wrap it in a synthetic PlanNode-shaped adapter so the rest of
        # the canonical path can stay PlanNode-only.
        if not isinstance(node, PlanNode):
            wrapped = _wrap_sub_agent_request_as_plan_node(node)
            if wrapped is None:
                raise TypeError(
                    f"node must be PlanNode or SubAgentRequest, got {type(node).__name__}"
                )
            request_id = wrapped.id
            agent_type = wrapped.metadata.get(AGENT_HINT) or ""
            payload_agent_type = agent_type or ""
            started_evt = self._build_event(
                request_id=request_id,
                event_type=_event_started(),
                payload={"agent_type": payload_agent_type},
            )
            completed_evt = self._build_event(
                request_id=request_id,
                event_type=_event_completed(),
                payload={"agent_type": payload_agent_type},
            )
            return self._dispatch_with_events(
                wrapped,
                request_id=request_id,
                started_event=started_evt,
                completed_event=completed_evt,
            )

        # Canonical PlanNode path.
        with self._dispatch_lock:
            recipient = self._recipient_for(node)
            self.bus.subscribe(recipient)
            message = InterAgentMessage(
                sender_id=self.sender_id,
                recipient_id=recipient,
                message_type="task_request",
                payload={
                    "task": node.task,
                    "node_id": node.id,
                },
                correlation_id=self.plan.id if self.plan is not None else None,
            )
            self.bus.publish(message)
            return message.id

    # ------------------------------------------------------------------
    # Internal helpers — AUDIT-N+37 dispatch-with-events plumbing
    # ------------------------------------------------------------------

    def _dispatch_with_events(
        self,
        node: PlanNode,
        *,
        request_id: str,
        started_event: Any,
        completed_event: Any,
    ) -> str:
        """Run the dormant WL-085 contract for a wrapped SubAgentRequest.

        Locks the dispatcher (FR-ORC-070), publishes STARTED, consults
        the budget tracker (FR-ORC-068), publishes the bus message,
        publishes COMPLETED, and returns the bus message id.  The
        STARTED event is always emitted; COMPLETED is emitted only when
        the dispatch path succeeds (no BudgetExceededError).
        """
        from thegent.orchestration.event_queue import QueueFull

        with self._dispatch_lock:
            # Publish STARTED first so consumers see the dispatch was
            # attempted even if the budget check raises.
            self._safe_publish_event(started_event)
            # Budget check — must raise BudgetExceededError before the
            # bus message is published.  STARTED was already emitted.
            if self.budget_tracker is not None and hasattr(
                self.budget_tracker, "check"
            ):
                try:
                    self.budget_tracker.check(node_id=node.id)
                except Exception as exc:
                    # FR-ORC-068: COMPLETED is NOT emitted on budget
                    # breach.  Re-raise so the caller observes the
                    # failure.
                    if _is_budget_exceeded(exc):
                        raise
                    raise
            recipient = self._recipient_for(node)
            self.bus.subscribe(recipient)
            message = InterAgentMessage(
                sender_id=self.sender_id,
                recipient_id=recipient,
                message_type="task_request",
                payload={
                    "task": node.task,
                    "node_id": node.id,
                    "request_id": request_id,
                },
                correlation_id=self.plan.id if self.plan is not None else None,
            )
            self.bus.publish(message)
            # FR-ORC-069: a broken event_queue (QueueFull) must not
            # break the dispatch path.  Swap the COMPLETED event for a
            # no-op silently so the dispatch result is still returned.
            with contextlib.suppress(QueueFull):
                self._safe_publish_event(completed_event)
            return message.id

    def _safe_publish_event(self, event: Any) -> None:
        """Publish *event* on the bound event_queue, swallowing put errors.

        FR-ORC-069: a misbehaving event_queue (QueueFull, broken put,
        closed stream, etc.) must NEVER break the dispatch path.  Any
        exception raised by ``self.event_queue.put`` is suppressed so
        the dispatcher can return its bus message id regardless.
        """
        if self.event_queue is None:
            return
        try:
            self.event_queue.put(event)
        except Exception:  # noqa: BLE001 — see FR-ORC-069
            return

    def _build_event(
        self,
        *,
        request_id: str,
        event_type: Any,
        payload: dict[str, Any],
    ) -> Any:
        """Build a :class:`SubAgentEvent` without coupling the import.

        The :class:`SubAgentEvent` constructor is loaded lazily so the
        dispatcher module can be imported on lightweight contexts that
        have not yet loaded :mod:`thegent.orchestration.protocol`.
        """
        from thegent.orchestration.protocol import SubAgentEvent

        return SubAgentEvent(
            request_id=request_id,
            event_type=event_type,
            payload=payload,
        )

    def dispatch_concurrent(self, requests: Iterable[Any]) -> list[str]:
        """Dispatch each request sequentially and return bus message ids.

        WL-085 contract: 2 events emitted per request (STARTED +
        COMPLETED).  Implementation is sequential — there is no agent
        execution here; the dispatcher only routes messages — but the
        contract name is preserved so dormant tests pass.
        """
        return [self.dispatch(req) for req in requests]

    # ------------------------------------------------------------------
    # Bulk dispatch with topological ordering
    # ------------------------------------------------------------------

    def dispatch_all(self, plan: OrchestrationPlan | None = None) -> list[str]:
        """Dispatch every node in *plan* (or ``self.plan`` if ``None``).

        Returns the list of message ids in dispatch order, which is a
        topological ordering (parents before children).  Cycles raise
        :class:`ValueError`.
        """
        target = plan if plan is not None else self.plan
        if target is None:
            raise ValueError(
                "dispatch_all requires a plan argument when no plan is bound to the dispatcher"
            )
        ordered = _topological_order(target)
        return [self.dispatch(node) for node in ordered]

    # ------------------------------------------------------------------
    # Result collection (drain the bus for an agent)
    # ------------------------------------------------------------------

    def collect_results(
        self, agent_id: str, timeout_s: float = 0.0
    ) -> list[InterAgentMessage]:
        """Drain queued messages for ``agent_id``.

        Auto-subscribes ``agent_id`` on the bus if it is not already
        registered.  ``timeout_s`` is forwarded to
        :meth:`MessageBus.drain`.
        """
        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError("agent_id must be a non-empty string")
        self.bus.subscribe(agent_id)
        return self.bus.drain(agent_id, timeout_s=timeout_s)

    # ------------------------------------------------------------------
    # Async dispatch — WL-084 contract (returns Dict[node_id, DispatchResult])
    # ------------------------------------------------------------------

    async def dispatch_plan(self, plan: OrchestrationPlan) -> dict[str, DispatchResult]:
        """Async dispatch path used by :class:`PlangentExecutor`.

        Walks the plan in topological order, publishes a message for each
        node, and returns a mapping ``node_id → DispatchResult``.  No
        agent actually executes anything — the dispatcher is purely a
        message-router; :class:`PlangentExecutor` collects the
        :class:`DispatchResult` objects from elsewhere (legacy
        ``execute_task`` path or a real runner wired through
        ``self.runner``).
        """
        if not isinstance(plan, OrchestrationPlan):
            raise TypeError(
                f"plan must be OrchestrationPlan, got {type(plan).__name__}"
            )
        ordered = _topological_order(plan)
        results: dict[str, DispatchResult] = {}
        for node in ordered:
            self.dispatch(node)
            if self.runner is not None:
                outcome = await self._invoke_runner(node)
                results[node.id] = outcome
            else:
                # No runner — we still produce a placeholder so the
                # executor can record the dispatch.
                results[node.id] = DispatchResult(
                    node_id=node.id, output="", success=True
                )
        return results

    async def _invoke_runner(self, node: PlanNode) -> DispatchResult:
        """Run ``self.runner`` against ``node`` and capture the outcome."""
        runner = self.runner
        try:
            if hasattr(runner, "run"):
                result = runner.run(task=node.task, **node.metadata)
            else:
                result = runner(node.task)
            # Coerce coroutine to a value if needed.
            import asyncio as _asyncio

            if _asyncio.iscoroutine(result):
                result = await result
            if hasattr(result, "exit_code"):
                if result.exit_code == 0:
                    return DispatchResult(
                        node_id=node.id,
                        output=getattr(result, "stdout", "") or "",
                        success=True,
                    )
                return DispatchResult(
                    node_id=node.id,
                    output="",
                    success=False,
                    error=getattr(result, "stderr", "") or "runner exited non-zero",
                )
            return DispatchResult(
                node_id=node.id,
                output=str(result),
                success=True,
            )
        except Exception as exc:  # noqa: BLE001 — capture any failure
            return DispatchResult(
                node_id=node.id,
                output="",
                success=False,
                error=f"{type(exc).__name__}: {exc}",
            )

    # ------------------------------------------------------------------
    # Legacy compat: pre-WL-082 sync/async task APIs
    # ------------------------------------------------------------------

    def start(self) -> None:
        """No-op retained for backwards compatibility."""
        return

    def stop(self) -> None:
        """No-op retained for backwards compatibility."""
        return

    def dispatch_task(self, task: str, context: dict | None = None) -> DispatchResult:
        """Legacy sync dispatch entry point.

        Publishes a message with ``recipient_id="default"`` and returns a
        successful :class:`DispatchResult` immediately (no actual
        execution).  Retained so older tests / callers that import the
        pre-WL-082 surface keep working.
        """
        recipient = (context or {}).get("agent_id", "default")
        self.bus.subscribe(recipient)
        message = InterAgentMessage(
            sender_id=self.sender_id,
            recipient_id=recipient,
            message_type="task_request",
            payload={"task": task},
        )
        self.bus.publish(message)
        return DispatchResult(node_id="", output=task, success=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _recipient_for(self, node: PlanNode) -> str:
        agent_hint = node.metadata.get(AGENT_HINT)
        if isinstance(agent_hint, str) and agent_hint:
            return agent_hint
        return node.id


# ---------------------------------------------------------------------------
# AUDIT-N+37 dormant-contract helpers — wrap SubAgentRequest as PlanNode
# ---------------------------------------------------------------------------


#: Lazy placeholder so the rest of the module can reference the
#: ``SubAgentEventType.STARTED`` / ``.COMPLETED`` enum values without
#: importing :mod:`thegent.orchestration.protocol` at module load time.
#: The actual enum members are resolved on first use via
#: :func:`_event_started` / :func:`_event_completed`.
_EVENT_STARTED: Any = "started"
_EVENT_COMPLETED: Any = "completed"


def _event_started() -> Any:
    """Return ``SubAgentEventType.STARTED`` (resolved lazily)."""
    from thegent.orchestration.protocol import SubAgentEventType

    return SubAgentEventType.STARTED


def _event_completed() -> Any:
    """Return ``SubAgentEventType.COMPLETED`` (resolved lazily)."""
    from thegent.orchestration.protocol import SubAgentEventType

    return SubAgentEventType.COMPLETED


def _wrap_sub_agent_request_as_plan_node(node: Any) -> PlanNode | None:
    """Adapt a :class:`SubAgentRequest` to the dispatcher ``PlanNode`` shape.

    The dormant WL-085 contract passes a :class:`SubAgentRequest`
    (with ``agent_type`` + ``task`` attributes) to ``dispatch()``.  The
    canonical dispatch path expects a :class:`PlanNode` (with ``id`` +
    ``task`` + ``metadata``).  We adapt the request to a synthetic
    :class:`PlanNode` whose ``id`` is the request id (or the agent
    type if missing), and whose ``metadata[AGENT_HINT]`` is the agent
    type so the canonical ``_recipient_for()`` picks it up.

    Returns ``None`` when ``node`` is neither a :class:`PlanNode` nor a
    duck-typed :class:`SubAgentRequest` (has both ``task`` and either
    ``agent_type`` or ``request_id`` attributes).
    """
    if isinstance(node, PlanNode):
        return node
    if not hasattr(node, "task"):
        return None
    request_id = (
        getattr(node, "request_id", None) or getattr(node, "agent_type", None) or ""
    )
    agent_type = getattr(node, "agent_type", None) or request_id
    if not request_id:
        return None
    metadata: dict[str, Any] = {AGENT_HINT: agent_type} if agent_type else {}
    return PlanNode(id=request_id, task=node.task, metadata=metadata)


def _is_budget_exceeded(exc: BaseException) -> bool:
    """Return True if *exc* is a :class:`BudgetExceededError`.

    Tolerates the import-not-available case so this module can be
    imported on contexts where :mod:`budget_tracker` is not yet
    loaded; the dispatcher only ever inspects exceptions raised by
    :meth:`BudgetTracker.check`.
    """
    try:
        from thegent.orchestration.budget_tracker import BudgetExceededError
    except Exception:  # noqa: BLE001 — defensive import guard
        return False
    return isinstance(exc, BudgetExceededError)


# ---------------------------------------------------------------------------
# Topological sort helpers
# ---------------------------------------------------------------------------


def _topological_order(plan: OrchestrationPlan) -> list[PlanNode]:
    """Return *plan.nodes* in deterministic topological order.

    Cycles raise :class:`ValueError` so callers cannot accidentally
    deadlock.  ``depends_on`` may reference unknown node ids — those
    references are dropped defensively (silent cycle prevention).
    """
    nodes_by_id: dict[str, PlanNode] = {n.id: n for n in plan.nodes}
    in_degree: dict[str, int] = {n.id: 0 for n in plan.nodes}
    children: dict[str, list[str]] = {n.id: [] for n in plan.nodes}

    for node in plan.nodes:
        for dep in node.depends_on:
            if dep not in nodes_by_id:
                continue
            in_degree[node.id] += 1
            children[dep].append(node.id)

    # Kahn's algorithm with a stable ordering by node position.
    ready: list[PlanNode] = [n for n in plan.nodes if in_degree[n.id] == 0]
    ordered: list[PlanNode] = []
    while ready:
        # Pop the earliest-positioned ready node for determinism.
        node = ready.pop(0)
        ordered.append(node)
        for child_id in children[node.id]:
            in_degree[child_id] -= 1
            if in_degree[child_id] == 0 and child_id in nodes_by_id:
                # Append to ``ready`` preserving original order.
                ready.append(nodes_by_id[child_id])

    if len(ordered) != len(plan.nodes):
        raise ValueError(
            f"plan {plan.id!r} contains a cycle — cannot topologically sort nodes"
        )
    return ordered


__all__ = [
    "DispatchResult",
    "SubAgentDispatcher",
    "is_cli_harness",
    "_CLI_HARNESSES",
    "CapabilityIndex",
]


# ---------------------------------------------------------------------------
# Backwards-compat surface (CLI harness detection, capability index)
# ---------------------------------------------------------------------------


def is_cli_harness(path: str) -> bool:
    """Check if ``path`` points at an executable CLI binary."""
    import os

    return os.path.exists(path) and os.access(path, os.X_OK)


_CLI_HARNESSES = {
    "bash": "/usr/bin/bash",
    "zsh": "/bin/zsh",
    "sh": "/bin/sh",
}


class CapabilityIndex:
    """Index for agent capabilities (legacy stub)."""

    def __init__(self) -> None:
        self.capabilities: dict[str, list[str]] = {}

    def register(self, agent_id: str, capabilities: list[str]) -> None:
        """Register ``capabilities`` for ``agent_id``."""
        self.capabilities[agent_id] = list(capabilities)

    def get(self, agent_id: str) -> list[str]:
        """Return the capabilities registered for ``agent_id``."""
        return list(self.capabilities.get(agent_id, []))

    @classmethod
    def get_default(cls) -> CapabilityIndex:
        """Return a process-wide default :class:`CapabilityIndex`."""
        global _DEFAULT_CAPABILITY_INDEX
        try:
            return _DEFAULT_CAPABILITY_INDEX  # type: ignore[name-defined]
        except NameError:
            _DEFAULT_CAPABILITY_INDEX = cls()
            return _DEFAULT_CAPABILITY_INDEX


_DEFAULT_CAPABILITY_INDEX: CapabilityIndex | None = None
