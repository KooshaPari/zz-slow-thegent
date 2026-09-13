"""Result aggregator — merge sub-agent :class:`InterAgentMessage` outputs.

:class:`ResultAggregator` accumulates :class:`InterAgentMessage` instances
(or any duck-typed object exposing ``message_type``, ``id``, ``payload``)
and produces a summary dict with:

- ``total``         — total number of added messages
- ``by_type``       — mapping of ``message_type → count``
- ``by_node``       — mapping of ``node_id`` → last message for that node
- ``results``       — list of ``message_type == "result"`` messages
- ``errors``        — list of ``message_type == "error"`` messages
- ``passed``        — ``True`` when no errors are present, else ``False``

Hardening (AUDIT-N+33)
----------------------
- :meth:`add` accepts an optional ``node_id=`` kwarg.  When supplied, the
  message is also recorded under ``by_node`` keyed by ``node_id`` so the
  orchestration executor can attribute outcomes back to plan nodes.
- :meth:`aggregate` always returns a fresh dict — never a live alias of
  internal state.
- :meth:`clear` resets every aggregation dimension in one call.
- :meth:`summary` returns a deterministic human-readable single-line
  report (used by :class:`thegent.orchestration.cli` and
  :class:`thegent.agents.plangent.PlangentExecutor`).

# @trace WL-083
# @trace AUDIT-N+33
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from thegent.orchestration.inter_agent_protocol import InterAgentMessage


class ResultAggregator:
    """Merge sub-agent :class:`InterAgentMessage` outputs into a summary.

    Use :meth:`add` to record messages, then call :meth:`aggregate` (or
    :meth:`summary`) to read the merged view.  The aggregator is **not**
    thread-safe; it is intended for single-async-task use inside the
    orchestration layer.
    """

    _RESULT_TYPE = "result"
    _ERROR_TYPE = "error"

    def __init__(self) -> None:
        self._messages: list[InterAgentMessage] = []
        self._by_type: dict[str, int] = {}
        self._by_node: dict[str, InterAgentMessage] = {}
        self._results: list[InterAgentMessage] = []
        self._errors: list[InterAgentMessage] = []
        self._passed: bool = True

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(
        self,
        message: InterAgentMessage | Any,
        *,
        node_id: str | None = None,
    ) -> None:
        """Record *message* in every aggregation bucket.

        Parameters
        ----------
        message
            An :class:`InterAgentMessage` (or duck-typed object exposing
            ``message_type``, ``id``, ``payload``).
        node_id
            Optional plan-node attribution.  When supplied, the message is
            also stored under ``by_node[node_id]``.  Subsequent additions
            for the same ``node_id`` overwrite the previous entry (the
            later outcome wins, matching executor semantics).
        """
        # Validate shape — the executor uses _AggregatorMessage which
        # duck-types the InterAgentMessage surface we need.
        if not hasattr(message, "message_type"):
            raise TypeError("message must expose a 'message_type' attribute")
        msg_type = message.message_type
        if not isinstance(msg_type, str):
            raise TypeError(f"message.message_type must be str, got {type(msg_type).__name__}")

        self._messages.append(message)
        self._by_type[msg_type] = self._by_type.get(msg_type, 0) + 1

        if msg_type == self._RESULT_TYPE:
            self._results.append(message)
        elif msg_type == self._ERROR_TYPE:
            self._errors.append(message)
            self._passed = False

        if node_id is not None:
            if not isinstance(node_id, str) or not node_id:
                raise ValueError("node_id must be a non-empty string")
            self._by_node[node_id] = message

    def clear(self) -> None:
        """Reset every aggregation bucket."""
        self._messages.clear()
        self._by_type.clear()
        self._by_node.clear()
        self._results.clear()
        self._errors.clear()
        self._passed = True

    # ------------------------------------------------------------------
    # Read-only aggregation
    # ------------------------------------------------------------------

    def aggregate(self) -> dict[str, Any]:
        """Return a fresh summary dict (no shared references).

        Keys: ``total``, ``by_type``, ``by_node``, ``results``, ``errors``,
        ``passed``.
        """
        return {
            "total": len(self._messages),
            "by_type": dict(self._by_type),
            "by_node": dict(self._by_node),
            "results": list(self._results),
            "errors": list(self._errors),
            "passed": self._passed,
        }

    def summary(self) -> str:
        """Return a one-line human-readable summary string."""
        total = len(self._messages)
        verdict = "FAILED" if self._errors else "PASSED"
        by_type = ", ".join(f"{k}={v}" for k, v in sorted(self._by_type.items())) or "none"
        return (
            f"ResultAggregator summary: total={total} verdict={verdict} "
            f"by_type={{{by_type}}} errors={len(self._errors)} "
            f"results={len(self._results)}"
        )

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    @property
    def total(self) -> int:
        """Total number of added messages."""
        return len(self._messages)

    @property
    def passed(self) -> bool:
        """Whether every added message so far was non-``error``."""
        return self._passed

    @property
    def messages(self) -> tuple[InterAgentMessage, ...]:
        """Read-only view of all added messages in insertion order."""
        return tuple(self._messages)


def aggregate_results(
    messages: Iterable[InterAgentMessage | Any],
    *,
    node_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Convenience helper: aggregate an iterable of messages in one call.

    When ``node_ids`` is supplied, it must have the same length as
    ``messages`` and each entry is paired with the corresponding message
    for ``by_node`` attribution.
    """
    aggregator = ResultAggregator()
    if node_ids is None:
        for msg in messages:
            aggregator.add(msg)
    else:
        for msg, nid in zip(messages, node_ids, strict=False):
            aggregator.add(msg, node_id=nid)
    return aggregator.aggregate()


__all__ = ["ResultAggregator", "aggregate_results"]


# Defensive: silence an "unused import" warning if Mapping is only used
# indirectly elsewhere in the package.
_ = Mapping
