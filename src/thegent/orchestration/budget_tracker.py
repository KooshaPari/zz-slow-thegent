"""Per-node token budget tracking and enforcement.

This module provides :class:`BudgetTracker`, a small registry that records
token usage against the per-node ``budget_tokens`` metadata declared on an
:class:`thegent.orchestration.plan.OrchestrationPlan` and raises
:class:`BudgetExceededError` the first time cumulative usage crosses the
declared budget.

The tracker is *strictly per-node* (no per-agent or per-plan aggregation)
because that mirrors the way :class:`OrchestrationPlan` declares its limits
and keeps error attribution simple.  Cumulative usage across repeated
:meth:`track` / :meth:`track_result_stdout` calls is the integer returned by
:meth:`get_usage` for that node.

Hardening (AUDIT-N+33)
----------------------
- :class:`BudgetExceededError` is a regular :class:`Exception` subclass that
  stores ``node_id``, ``budget`` and ``actual`` as attributes and embeds all
  three in its message (no silent message loss).
- :class:`BudgetTracker` constructor validates the plan argument is an
  :class:`OrchestrationPlan` instance.
- :meth:`track` rejects non-int usage amounts and surfaces type errors as
  :class:`TypeError` so callers cannot silently record float budgets.
- :meth:`parse_tokens_from_result` is a :func:`staticmethod` (per the WL-086
  contract) and tolerates malformed JSON / non-usage lines silently — the
  caller is responsible for raising on token-parsing failures.
- :attr:`all_usage` returns a defensive copy so external mutation cannot
  poison the tracker's internal state.

# @trace WL-086
# @trace AUDIT-N+33
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from thegent.orchestration.plan import (
    BUDGET_TOKENS,
    OrchestrationPlan,
)


class BudgetExceededError(Exception):
    """Raised when cumulative usage for a node exceeds ``budget_tokens``.

    Attributes
    ----------
    node_id : str
        The :class:`PlanNode` ID that exceeded the budget.
    budget : int
        The declared ``budget_tokens`` value.
    actual : int
        The cumulative token count that triggered the breach.
    """

    def __init__(self, *, node_id: str, budget: int, actual: int) -> None:
        self.node_id = node_id
        self.budget = budget
        self.actual = actual
        over = max(actual - budget, 0)
        super().__init__(
            f"Budget exceeded for node {node_id!r}: used {actual} tokens, budget was {budget} (over by {over})"
        )


class BudgetTracker:
    """Per-node token budget tracker over an :class:`OrchestrationPlan`.

    The tracker keeps a private ``_usage`` mapping from node-id → cumulative
    token count.  Nodes whose ``metadata[BUDGET_TOKENS]`` is ``None`` are
    tracked but never enforced (the budget is "infinite" for those nodes,
    which is the safe default for plans that opt out of budgeting).

    The tracker is not thread-safe.  Concurrent access across threads must
    be serialised by the caller; the dominant in-process async path is
    single-thread by definition so no internal locking is required.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, plan: OrchestrationPlan) -> None:
        if not isinstance(plan, OrchestrationPlan):
            raise TypeError(f"plan must be OrchestrationPlan, got {type(plan).__name__}")
        self._plan = plan
        self._usage: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Public read-only API
    # ------------------------------------------------------------------

    @property
    def plan(self) -> OrchestrationPlan:
        """The :class:`OrchestrationPlan` this tracker is bound to."""
        return self._plan

    @property
    def all_usage(self) -> dict[str, int]:
        """Return a defensive copy of every tracked node's usage."""
        return dict(self._usage)

    def get_usage(self, node_id: str) -> int:
        """Return cumulative tracked tokens for ``node_id``.

        Raises :class:`KeyError` when ``node_id`` is not in the underlying
        plan.
        """
        self._require_known_node(node_id)
        return self._usage.get(node_id, 0)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def track(self, node_id: str, tokens: int) -> int:
        """Record ``tokens`` usage against ``node_id`` and enforce budget.

        Returns the new cumulative total.  Raises
        :class:`BudgetExceededError` when the new total exceeds the node's
        declared ``budget_tokens`` (or equals it when the budget is set to
        a non-positive value).  Nodes whose ``budget_tokens`` metadata is
        missing are tracked without enforcement.
        """
        if not isinstance(tokens, int) or isinstance(tokens, bool):
            raise TypeError(f"tokens must be int, got {type(tokens).__name__}")
        if tokens < 0:
            raise ValueError("tokens must be non-negative")
        self._require_known_node(node_id)

        current = self._usage.get(node_id, 0)
        new_total = current + tokens
        budget = self._budget_for(node_id)
        if budget is not None and new_total > budget:
            # Persist the overflow so callers that catch the error still
            # see the true usage in subsequent reads.
            self._usage[node_id] = new_total
            raise BudgetExceededError(node_id=node_id, budget=budget, actual=new_total)
        self._usage[node_id] = new_total
        return new_total

    def reset_usage(self, node_id: str) -> None:
        """Zero out the accumulated usage for ``node_id``.

        Raises :class:`KeyError` when ``node_id`` is not in the plan.
        """
        self._require_known_node(node_id)
        self._usage.pop(node_id, None)

    def track_result_stdout(self, node_id: str, stdout: str) -> int:
        """Parse tokens from a worker ``stdout`` blob and ``track`` them.

        Returns the new cumulative total (or raises
        :class:`BudgetExceededError` if the parse crosses the budget).
        """
        tokens = self.parse_tokens_from_result(stdout)
        return self.track(node_id, tokens)

    # ------------------------------------------------------------------
    # Parsing helper (static — no instance state required)
    # ------------------------------------------------------------------

    @staticmethod
    def parse_tokens_from_result(stdout: str) -> int:
        """Sum token usage across all JSON-parseable lines in ``stdout``.

        Accepts the OpenAI-style ``{"usage": {"prompt_tokens": N,
        "completion_tokens": M}}`` shape (returns ``N + M``) and falls back
        to ``{"usage": {"total_tokens": N}}`` when the prompt/completion
        split is absent.  Lines that are not valid JSON, do not contain a
        ``usage`` key, or carry a non-dict ``usage`` value are silently
        skipped.
        """
        if not isinstance(stdout, str):
            raise TypeError(f"stdout must be str, got {type(stdout).__name__}")
        if not stdout:
            return 0
        total = 0
        for raw in stdout.splitlines():
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except (ValueError, TypeError):
                continue
            if not isinstance(obj, Mapping):
                continue
            usage = obj.get("usage")
            if not isinstance(usage, Mapping):
                continue
            total += _tokens_from_usage(usage)
        return total

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_known_node(self, node_id: str) -> None:
        if not isinstance(node_id, str) or not node_id:
            raise TypeError(f"node_id must be a non-empty string, got {node_id!r}")
        for node in self._plan.nodes:
            if node.id == node_id:
                return
        raise KeyError(f"node_id {node_id!r} is not in plan")

    def _budget_for(self, node_id: str) -> int | None:
        for node in self._plan.nodes:
            if node.id == node_id:
                value = node.metadata.get(BUDGET_TOKENS)
                if value is None:
                    return None
                if isinstance(value, bool) or not isinstance(value, int):
                    raise TypeError(f"budget_tokens for node {node_id!r} must be int, got {type(value).__name__}")
                if value < 0:
                    raise ValueError(f"budget_tokens for node {node_id!r} must be non-negative")
                return value
        # _require_known_node guards this branch; explicit raise keeps
        # mypy happy in case callers bypass the public API.
        raise KeyError(f"node_id {node_id!r} is not in plan")


def _tokens_from_usage(usage: Mapping[str, Any]) -> int:
    """Extract a token count from a single ``usage`` mapping."""
    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    if (
        isinstance(prompt, int)
        and not isinstance(prompt, bool)
        and isinstance(completion, int)
        and not isinstance(completion, bool)
    ):
        return prompt + completion
    total = usage.get("total_tokens")
    if isinstance(total, int) and not isinstance(total, bool):
        return total
    return 0


__all__ = ["BudgetTracker", "BudgetExceededError"]
