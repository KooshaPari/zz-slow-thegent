"""Orchestration plan.

The :class:`OrchestrationPlan` extends :class:`thegent.agents.plangent.Plan`
with budget / agent-hint metadata per node, the canonical metadata key
constants used across the orchestration layer, and a small set of
filtering helpers (``total_budget_used``, ``get_sandbox_nodes``,
``get_hitl_nodes``, ``get_nodes_by_agent``, ``get_nodes_by_model``).

Hardening (AUDIT-N+33)
----------------------
- :class:`OrchestrationPlan` accepts ``goal`` (required non-empty ``str``),
  optional ``nodes`` list, and ``metadata`` dict (defensive copy on
  assignment, defensive copy on read via ``_safe_metadata``).
- ``add_task(...)`` validates every kwarg, stores only the *set* metadata
  fields (no absent-key pollution), and returns the freshly-created
  :class:`PlanNode`.
- ``from_goal(...)`` is a deterministic constructor; two calls with the
  same goal produce two distinct plan IDs (UUIDs).
- ``total_budget_used()`` aggregates ``budget_tokens`` / ``budget_time_s``
  defensively, ignoring nodes whose metadata keys are missing or
  non-numeric (no ``TypeError``).
- ``get_sandbox_nodes`` / ``get_hitl_nodes`` / ``get_nodes_by_agent`` /
  ``get_nodes_by_model`` return list copies — callers cannot mutate the
  underlying node list.

# @trace WL-081
# @trace AUDIT-N+33
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from thegent.agents.plangent import Plan, PlanNode

# ---------------------------------------------------------------------------
# Metadata key constants (canonical names)
# ---------------------------------------------------------------------------

AGENT_HINT = "agent_hint"
BUDGET_TIME_S = "budget_time_s"
BUDGET_TOKENS = "budget_tokens"
MODEL_HINT = "model_hint"
OUTPUT_SCHEMA = "output_schema"
PARENT_RUN_ID = "parent_run_id"
REQUIRE_HITL = "require_hitl"
SANDBOX = "sandbox"

# Default budget values (kept for backward compatibility with the legacy
# stub module that exported them).
_DEFAULT_BUDGET_TIME_S: float = 300.0
_DEFAULT_BUDGET_TOKENS: int = 100_000


class OrchestrationPlan(Plan):
    """A :class:`Plan` enriched with per-node budget + agent-hint metadata.

    ``OrchestrationPlan`` is the canonical container used by the
    orchestration dispatch / execution layer (``SubAgentDispatcher``,
    ``PlangentExecutor``).  It inherits ``id``, ``goal``, ``nodes``,
    ``created_at`` and ``metadata`` from :class:`Plan` and adds a
    convenience factory (``add_task``) plus a small set of filtering
    helpers.

    Examples
    --------
    >>> plan = OrchestrationPlan(goal="research the topic")
    >>> node = plan.add_task("gather sources", agent_hint="researcher",
    ...                       budget_tokens=4096, budget_time_s=60.0)
    >>> plan.total_budget_used()
    {'budget_tokens': 4096, 'budget_time_s': 60.0}
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        *,
        goal: str,
        nodes: list[PlanNode] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        # Defensive validation: goal must be a non-empty string. This is
        # the strongest invariant the rest of the orchestration layer
        # relies on, so we reject empty / non-string values up-front.
        if not isinstance(goal, str):
            raise TypeError(f"goal must be a string, got {type(goal).__name__}")
        if not goal or not goal.strip():
            raise ValueError("goal must be a non-empty string")
        if nodes is not None and not isinstance(nodes, list):
            raise TypeError(f"nodes must be a list or None, got {type(nodes).__name__}")
        if metadata is not None and not isinstance(metadata, dict):
            raise TypeError(
                f"metadata must be a dict or None, got {type(metadata).__name__}"
            )
        # Note: Plan dataclass declares `goal: str = ""`. The override is
        # safe because Plan's __init__ assigns every field directly.
        super().__init__(goal=goal.strip())
        if nodes:
            self.nodes = list(nodes)
        if metadata:
            self.metadata = dict(metadata)

    # ------------------------------------------------------------------
    # Factory: from_goal (deterministic per-instance id)
    # ------------------------------------------------------------------

    @classmethod
    def from_goal(
        cls,
        goal: str,
        *,
        agent_hint: str | None = None,
        model_hint: str | None = None,
        budget_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> OrchestrationPlan:
        """Build an :class:`OrchestrationPlan` from a single goal string.

        The returned plan carries no nodes (callers are expected to
        :meth:`add_task` immediately).  Any of ``agent_hint``,
        ``model_hint`` or ``budget_tokens`` provided here are stored on
        ``plan.metadata`` under the canonical keys.
        """
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("goal must be a non-empty string")
        meta: dict[str, Any] = dict(metadata) if metadata else {}
        if agent_hint is not None:
            meta[AGENT_HINT] = agent_hint
        else:
            meta.setdefault(AGENT_HINT, None)
        if model_hint is not None:
            meta[MODEL_HINT] = model_hint
        if budget_tokens is not None:
            meta[BUDGET_TOKENS] = budget_tokens
        return cls(goal=goal.strip(), metadata=meta)

    # ------------------------------------------------------------------
    # Factory: add_task
    # ------------------------------------------------------------------

    def add_task(
        self,
        task: str,
        *,
        agent_hint: str | None = None,
        model_hint: str | None = None,
        budget_tokens: int | None = None,
        budget_time_s: float | None = None,
        sandbox: bool | None = None,
        require_hitl: bool | None = None,
        output_schema: dict[str, Any] | None = None,
        parent_run_id: str | None = None,
        depends_on: Iterable[str] | None = None,
    ) -> PlanNode:
        """Create and append a :class:`PlanNode` carrying optional metadata.

        Returns the freshly-created node.  Only the metadata fields that
        were explicitly provided are stored (defaults *do not* leak into
        the per-node ``metadata`` dict).  ``depends_on`` is forwarded to
        :class:`PlanNode` unchanged.
        """
        if not isinstance(task, str) or not task.strip():
            raise ValueError("task must be a non-empty string")

        node_metadata: dict[str, Any] = {}
        if agent_hint is not None:
            node_metadata[AGENT_HINT] = agent_hint
        if model_hint is not None:
            node_metadata[MODEL_HINT] = model_hint
        if budget_tokens is not None:
            if not isinstance(budget_tokens, int) or isinstance(budget_tokens, bool):
                raise TypeError(
                    f"budget_tokens must be int, got {type(budget_tokens).__name__}"
                )
            if budget_tokens < 0:
                raise ValueError("budget_tokens must be non-negative")
            node_metadata[BUDGET_TOKENS] = budget_tokens
        if budget_time_s is not None:
            if not isinstance(budget_time_s, (int, float)) or isinstance(
                budget_time_s, bool
            ):
                raise TypeError(
                    f"budget_time_s must be a number, got {type(budget_time_s).__name__}"
                )
            node_metadata[BUDGET_TIME_S] = float(budget_time_s)
        if sandbox is not None:
            node_metadata[SANDBOX] = bool(sandbox)
        if require_hitl is not None:
            node_metadata[REQUIRE_HITL] = bool(require_hitl)
        if output_schema is not None:
            if not isinstance(output_schema, dict):
                raise TypeError(
                    f"output_schema must be a dict, got {type(output_schema).__name__}"
                )
            node_metadata[OUTPUT_SCHEMA] = dict(output_schema)
        if parent_run_id is not None:
            node_metadata[PARENT_RUN_ID] = parent_run_id

        node = PlanNode(
            task=task.strip(),
            depends_on=list(depends_on) if depends_on else [],
            metadata=node_metadata,
        )
        self.nodes.append(node)
        return node

    # ------------------------------------------------------------------
    # Aggregation helpers
    # ------------------------------------------------------------------

    def total_budget_used(self) -> dict[str, float]:
        """Sum ``budget_tokens`` and ``budget_time_s`` across every node.

        Nodes without the corresponding metadata key are skipped.  Nodes
        whose metadata key is set to a non-numeric value are silently
        ignored for that field (defensive against malformed plans from
        upstream writers).
        """
        total_tokens = 0
        total_time_s = 0.0
        for node in self.nodes:
            tokens = node.metadata.get(BUDGET_TOKENS)
            if isinstance(tokens, int) and not isinstance(tokens, bool):
                total_tokens += tokens
            time_s = node.metadata.get(BUDGET_TIME_S)
            if isinstance(time_s, (int, float)) and not isinstance(time_s, bool):
                total_time_s += float(time_s)
        return {"budget_tokens": total_tokens, "budget_time_s": total_time_s}

    # ------------------------------------------------------------------
    # Filtering helpers (return list copies — never internal list)
    # ------------------------------------------------------------------

    def get_sandbox_nodes(self) -> list[PlanNode]:
        """Return nodes whose ``sandbox`` metadata is ``True``."""
        return [n for n in self.nodes if n.metadata.get(SANDBOX) is True]

    def get_hitl_nodes(self) -> list[PlanNode]:
        """Return nodes whose ``require_hitl`` metadata is ``True``."""
        return [n for n in self.nodes if n.metadata.get(REQUIRE_HITL) is True]

    def get_nodes_by_agent(self, agent_hint: str) -> list[PlanNode]:
        """Return nodes whose ``agent_hint`` matches ``agent_hint``."""
        return [n for n in self.nodes if n.metadata.get(AGENT_HINT) == agent_hint]

    def get_nodes_by_model(self, model_hint: str) -> list[PlanNode]:
        """Return nodes whose ``model_hint`` matches ``model_hint``."""
        return [n for n in self.nodes if n.metadata.get(MODEL_HINT) == model_hint]


__all__ = [
    "AGENT_HINT",
    "BUDGET_TIME_S",
    "BUDGET_TOKENS",
    "MODEL_HINT",
    "OrchestrationPlan",
    "OUTPUT_SCHEMA",
    "PARENT_RUN_ID",
    "REQUIRE_HITL",
    "SANDBOX",
]
