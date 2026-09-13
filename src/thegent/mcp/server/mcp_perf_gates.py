"""MCP performance budget gates — SOTA audit hardening.

Lightweight module that defines named latency budgets for MCP server
operations and enforces them at runtime.  Designed to be imported
cheaply (no heavy dependencies) so gate checks can sit in hot paths
without adding measurable overhead.

Public surface:

* ``MCP_PERF_BUDGETS`` — ``dict[str, float]`` mapping operation names
  to their latency ceiling in milliseconds.
* ``MCPBudgetExceeded`` — exception raised when a budget is violated.
* ``check_mcp_budget(operation, elapsed_ms)`` — check a single
  measurement against the named budget.
* ``mcp_budget_context(operation, budget_ms=None)`` — context manager
  that times the block and auto-checks on exit.

Canonical home: ``thegent.mcp.server.mcp_perf_gates``
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager

# ------------------------------------------------------------------
# Named budgets
# ------------------------------------------------------------------

MCP_PERF_BUDGETS: dict[str, float] = {
    "tool_invoke_ms": 100.0,
    "resource_read_ms": 50.0,
    "gate_check_ms": 20.0,
    "observe_summary_ms": 150.0,
    "health_trend_ms": 200.0,
}


# ------------------------------------------------------------------
# Exception
# ------------------------------------------------------------------


class MCPBudgetExceeded(Exception):
    """Raised when an MCP operation exceeds its latency budget."""

    __slots__ = ("budget_ms", "elapsed_ms", "operation")

    def __init__(self, operation: str, elapsed_ms: float, budget_ms: float) -> None:
        self.operation = operation
        self.elapsed_ms = elapsed_ms
        self.budget_ms = budget_ms
        super().__init__(f"MCP budget exceeded for {operation!r}: {elapsed_ms:.1f}ms > {budget_ms:.1f}ms")


# ------------------------------------------------------------------
# Budget checking
# ------------------------------------------------------------------


def check_mcp_budget(operation: str, elapsed_ms: float) -> None:
    """Check *elapsed_ms* against the named budget for *operation*.

    Raises :class:`MCPBudgetExceeded` when the measurement exceeds
    the budget.  Raises :class:`KeyError` when *operation* is not
    present in :data:`MCP_PERF_BUDGETS`.
    """
    budget_ms = MCP_PERF_BUDGETS[operation]
    if elapsed_ms > budget_ms:
        raise MCPBudgetExceeded(operation, elapsed_ms, budget_ms)


@contextmanager
def mcp_budget_context(
    operation: str,
    budget_ms: float | None = None,
) -> Iterator[None]:
    """Context manager that times the block and checks on exit.

    When *budget_ms* is ``None`` the named budget from
    :data:`MCP_PERF_BUDGETS` is used.  When *budget_ms* is supplied
    it overrides the named budget for this single measurement (useful
    for per-call overrides in tests).

    Raises :class:`MCPBudgetExceeded` on exit if the elapsed time
    exceeds the budget.  Raises :class:`KeyError` when *operation*
    is not in :data:`MCP_PERF_BUDGETS` and *budget_ms* is ``None``.
    """
    t0 = time.monotonic()
    try:
        yield
    finally:
        elapsed_ms = (time.monotonic() - t0) * 1000.0
        if budget_ms is not None:
            if elapsed_ms > budget_ms:
                raise MCPBudgetExceeded(operation, elapsed_ms, budget_ms)
        else:
            check_mcp_budget(operation, elapsed_ms)


__all__ = [
    "MCP_PERF_BUDGETS",
    "MCPBudgetExceeded",
    "check_mcp_budget",
    "mcp_budget_context",
]
