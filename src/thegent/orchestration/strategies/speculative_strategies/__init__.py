"""Speculative execution strategies (WP-5001).

Hardening (AUDIT-N+39 — SOTA pass-23)
--------------------------------------
This module is the dormant-core hardening target for SOTA pass-23.  The
contract surface is asserted by ``tests/test_unit_audit_n39_speculative_strategies_hardening.py``
(15 invariants, ``FR-ORC-SS-001..015``) and exercised by the dormant
corridor ``tests/orchestration/test_speculative_strategies.py`` (38 tests
across 5 test classes).

Public surface (must stay stable):

* :class:`SpeculativeStrategy` — 5-value ``enum.Enum`` selector.
* :class:`SpeculativeConfig` — ``@dataclass`` with ``__post_init__``
  validation/normalisation.
* :func:`compute_adaptive_timeout` — adaptive budget helper.
* :func:`select_speculative_providers` — provider fan-out helper.
* :func:`should_terminate_early` — early-termination decision helper.

# @trace AUDIT-N+39
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class SpeculativeStrategy(enum.Enum):
    """Speculative execution strategy selector.

    Members (must match ``FR-ORC-SS-001``):

    * ``RACE_FIRST`` — race a fixed fan-out of providers, take the first
      response that lands.
    * ``RACE_BEST`` — race a fixed fan-out of providers, take the
      highest-quality response.
    * ``ADAPTIVE_TIMEOUT`` — fan-out with an adaptive per-run budget.
    * ``COST_QUALITY_TRADEOFF`` — fan-out limited by a cost budget.
    * ``EARLY_TERMINATION`` — terminate early when a partial result
      crosses the halfway budget.
    """

    RACE_FIRST = "race_first"
    RACE_BEST = "race_best"
    ADAPTIVE_TIMEOUT = "adaptive_timeout"
    COST_QUALITY_TRADEOFF = "cost_quality_tradeoff"
    EARLY_TERMINATION = "early_termination"


# Canonical provider cost table — mirrors the dormant
# ``test_speculative_strategies.py`` cost table so callers can reason
# about cost-quality tradeoffs deterministically.  ``FR-ORC-SS-009``.
_PROVIDER_COST: dict[str, float] = {
    "free": 0.0,
    "claude": 0.001,
}
_DEFAULT_PROVIDER_COST = 0.001
_DEFAULT_PROVIDERS: list[str] = ["free", "claude", "gemini"]
_MAX_SPECULATIVE_FAN_OUT = 3


@dataclass
class SpeculativeConfig:
    """Speculative execution configuration.

    ``FR-ORC-SS-002``: ``providers=None`` is normalised to the canonical
    default ``["free", "claude", "gemini"]``; an explicit empty list is
    preserved (caller opt-out).

    ``FR-ORC-SS-003``: negative ``timeout_ms`` /
    ``historical_latency_p95_ms`` / ``historical_quality_avg`` raise
    ``ValueError`` so a misconfigured config cannot silently disable
    the speculative budget.
    """

    strategy: SpeculativeStrategy = SpeculativeStrategy.RACE_FIRST
    providers: list[str] | None = field(default_factory=list)
    timeout_ms: int = 5000
    historical_latency_p95_ms: float = 0.0
    historical_quality_avg: float = 0.0

    def __post_init__(self) -> None:
        # FR-ORC-SS-002 — normalise None → canonical default; preserve
        # empty list (caller opt-out) and any other explicit list.
        if self.providers is None:
            self.providers = list(_DEFAULT_PROVIDERS)
        else:
            # Defensive copy — never let callers mutate the field through
            # the shared default list.
            self.providers = list(self.providers)

        # FR-ORC-SS-003 — reject negative budget knobs.
        if self.timeout_ms < 0:
            raise ValueError(f"timeout_ms must be >= 0 (got {self.timeout_ms})")
        if self.historical_latency_p95_ms < 0:
            raise ValueError(f"historical_latency_p95_ms must be >= 0 (got {self.historical_latency_p95_ms})")
        if self.historical_quality_avg < 0:
            raise ValueError(f"historical_quality_avg must be >= 0 (got {self.historical_quality_avg})")


def should_terminate_early(
    elapsed_ms: int,
    timeout_ms: int,
    other_results: list[Any],
    strategy: SpeculativeStrategy,
) -> bool:
    """Decide whether a speculative run should terminate early.

    ``FR-ORC-SS-011`` / ``FR-ORC-SS-012``: hard-timeout check uses
    strict ``>`` so ``elapsed_ms == timeout_ms`` is **not** a
    termination trigger.

    ``FR-ORC-SS-013`` / ``FR-ORC-SS-014``: the ``EARLY_TERMINATION``
    strategy returns ``True`` only when ``other_results`` is non-empty
    **and** ``elapsed_ms / timeout_ms > 0.5``; non-early-termination
    strategies never fire early on a result alone.
    """
    # FR-ORC-SS-011 / FR-ORC-SS-012 — hard timeout wins (strict >).
    if elapsed_ms > timeout_ms:
        return True
    # FR-ORC-SS-014 — non-EARLY_TERMINATION strategies never fire early
    # on a result alone; the hard-timeout branch above already returned.
    if strategy is not SpeculativeStrategy.EARLY_TERMINATION:
        return False
    # FR-ORC-SS-013 — EARLY_TERMINATION needs both a partial result AND
    # a >50% consumed budget.  Guard against timeout_ms == 0 to keep the
    # divide-by-zero at bay (treat as "never crossed halfway").
    if not other_results:
        return False
    if timeout_ms <= 0:
        return False
    return (elapsed_ms / timeout_ms) > 0.5


def compute_adaptive_timeout(
    historical_p95_ms: float,
    base_timeout_ms: int = 5000,
    safety_multiplier: float = 1.5,
) -> int:
    """Compute an adaptive per-run timeout.

    ``FR-ORC-SS-004``: returns
    ``max(base_timeout_ms, historical_p95_ms * safety_multiplier)``
    so callers always get a non-negative adaptive budget that respects
    the historical p95 latency when it dominates the base.

    ``FR-ORC-SS-005``: defaults are ``base_timeout_ms=5000`` and
    ``safety_multiplier=1.5``.
    """
    adaptive = historical_p95_ms * safety_multiplier
    return int(max(base_timeout_ms, adaptive))


def select_speculative_providers(
    providers: list[str],
    strategy: SpeculativeStrategy,
    cost_budget: float | None = None,
) -> list[str]:
    """Select the speculative fan-out for ``strategy``.

    ``FR-ORC-SS-006``: for ``RACE_FIRST`` / ``RACE_BEST`` /
    ``ADAPTIVE_TIMEOUT`` / ``EARLY_TERMINATION`` returns at most the
    top-3 providers in input order.

    ``FR-ORC-SS-007`` / ``FR-ORC-SS-008``: for
    ``COST_QUALITY_TRADEOFF`` always includes ``free`` regardless of
    ``cost_budget`` and respects the budget by accumulating
    provider costs in input order, never returning more than 3.

    ``FR-ORC-SS-009``: provider-cost table is
    ``free=0.0``, ``claude=0.001``, unknown default ``0.001``.

    ``FR-ORC-SS-010``: empty input returns ``[]``.
    """
    if not providers:
        return []

    if strategy is SpeculativeStrategy.COST_QUALITY_TRADEOFF:
        return _select_cost_quality(providers, cost_budget)

    # FR-ORC-SS-006 — cap at the three-way race budget.
    return list(providers[:_MAX_SPECULATIVE_FAN_OUT])


def _select_cost_quality(
    providers: list[str],
    cost_budget: float | None,
) -> list[str]:
    """Cost-quality fan-out — always include ``free``, respect ``cost_budget``.

    ``FR-ORC-SS-007`` / ``FR-ORC-SS-008`` / ``FR-ORC-SS-009``.
    """
    chosen: list[str] = []
    spent = 0.0
    budget = cost_budget if cost_budget is not None else float("inf")

    for provider in providers:
        if len(chosen) >= _MAX_SPECULATIVE_FAN_OUT:
            break
        cost = _PROVIDER_COST.get(provider, _DEFAULT_PROVIDER_COST)
        # ``free`` always fits — it is cost 0.0 and we want it regardless.
        if provider == "free":
            if "free" not in chosen:
                chosen.append(provider)
            continue
        # All non-free providers must fit within the remaining budget.
        if spent + cost > budget:
            continue
        chosen.append(provider)
        spent += cost

    return chosen


__all__ = [
    "SpeculativeConfig",
    "SpeculativeStrategy",
    "compute_adaptive_timeout",
    "select_speculative_providers",
    "should_terminate_early",
]
