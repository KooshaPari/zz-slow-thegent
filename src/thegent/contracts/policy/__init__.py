"""thegent.contracts.policy — fallback policy dataclass + evaluator.

The canonical ``FallbackPolicy`` is a dataclass (not an ``Enum`` — the
stub-era module exposed an enum-based ``FallbackPolicy(NONE|ALLOW|…)``
which was structurally wrong for the field set the state machine
needed). The pinned field set, ordered to match ``make_fallback_policy``
in :mod:`tests.conftest_factories`:

* ``allow_plain_fallback: bool`` (default ``True``)
* ``min_confidence_threshold: float`` (default ``0.4``)
* ``max_fallback_rate: float`` (default ``0.3``)
* ``strict_providers: list[str]`` (default ``[]``)
* ``max_latency_ms: float`` (default ``300_000``) — used by the
  :class:`~thegent.agents.state_machine.FallbackStateMachine` for
  SLO timeout enforcement (WP-X6).

The evaluator signature is pinned by
``tests/test_unit_contracts_policy.py`` and
``tests/test_integration_normalization_pipeline.py``:

    evaluate_fallback(
        provider: str,
        confidence: float,
        *,
        is_fallback: bool,
        policy: FallbackPolicy,
        stats: dict | None = None,
    ) -> list[str]

Returns an empty list when the action is acceptable, otherwise a list
of human-readable violation strings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "FallbackPolicy",
    "evaluate_fallback",
    "get_contracts_fallback_policy",
]


@dataclass
class FallbackPolicy:
    """Fallback policy dataclass.

    All defaults match the historical "permissive" baseline so a newly-
    constructed ``FallbackPolicy()`` accepts every well-formed CSM.
    Production deployments override the threshold fields to tighten
    budgets; see ``thegent config`` for the canonical config knob set.
    """

    allow_plain_fallback: bool = True
    min_confidence_threshold: float = 0.4
    max_fallback_rate: float = 0.3
    strict_providers: list[str] = field(default_factory=list)
    max_latency_ms: float = 300_000.0


def evaluate_fallback(
    provider: str,
    confidence: float,
    *,
    is_fallback: bool = False,
    policy: FallbackPolicy,
    stats: dict[str, Any] | None = None,
) -> list[str]:
    """Evaluate a fallback attempt against ``policy``.

    Args:
        provider: Provider name being evaluated.
        confidence: Adapter-reported confidence for the normalised
            payload (in ``[0.0, 1.0]``).
        is_fallback: ``True`` when the adapter fell back to plain-text
            extraction (source_contract == "fallback-plain").
        policy: The active :class:`FallbackPolicy` instance.
        stats: Optional telemetry stats; when present, must contain a
            ``fallback_rate`` float in ``[0.0, 1.0]``.

    Returns:
        A list of violation strings. An empty list means the action
        is acceptable and the orchestrator may proceed.
    """
    violations: list[str] = []

    # 1. Plain-text fallback gate.
    if is_fallback and not policy.allow_plain_fallback:
        violations.append(f"Plain text fallback is disabled by policy (provider={provider})")

    # 2. Strict-provider gate.
    if is_fallback and provider in policy.strict_providers:
        violations.append(f"Provider '{provider}' is on the strict list and may not fall back")

    # 3. Confidence threshold.
    if confidence < policy.min_confidence_threshold:
        violations.append(f"Confidence {confidence:.2f} is below threshold {policy.min_confidence_threshold:.2f}")

    # 4. Global fallback-rate budget (only when telemetry stats available).
    if stats is not None:
        rate = float(stats.get("fallback_rate", 0.0) or 0.0)
        if rate > policy.max_fallback_rate:
            violations.append(f"Global fallback rate {rate:.2f} exceeds budget {policy.max_fallback_rate:.2f}")

    return violations


def get_contracts_fallback_policy() -> FallbackPolicy:
    """Return the default contracts fallback policy.

    Retained as a module-level factory so legacy callers that import
    ``get_contracts_fallback_policy`` continue to resolve to a
    sensible default.
    """
    return FallbackPolicy()
