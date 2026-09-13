"""Orchestration recovery playbooks (WP-2004, FR-008).

Hardening (AUDIT-N+40 — SOTA pass-24)
--------------------------------------
This module is the dormant-core hardening target for SOTA pass-24.  The
contract surface is asserted by
``tests/test_unit_audit_n40_playbooks_hardening.py`` (15 invariants,
``FR-ORC-PB-001..015``) and exercised by the dormant corridor
``tests/orchestration/test_strategies_playbooks.py``.

Public surface (must stay stable):

* :class:`Playbook` — named step container with ``execute()``.
* :func:`get_playbook_for_failure` — keyword classifier → ordered
  ``list[str]`` of playbook step names.
* :func:`execute_playbook_step` — dispatcher that fans out
  ``escalate`` / ``dlq_enqueue`` to ``EscalationQueue`` /
  ``DLQManager`` and returns a pending envelope for manual steps.

# @trace AUDIT-N+40
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Canonical ladders — mirrored from the dormant corridor so the
# classifier is hermetic and never reaches into the test corpus.
_TIMEOUT_STEPS: list[str] = ["retry_with_backoff", "increase_timeout", "escalate"]
_RATE_LIMIT_STEPS: list[str] = ["wait_and_retry", "reduce_concurrency", "escalate"]
_AUTH_FAILURE_STEPS: list[str] = ["refresh_credentials", "escalate"]
_NETWORK_PARTITION_STEPS: list[str] = ["retry", "failover_provider", "escalate"]
_MALFORMED_RESPONSE_STEPS: list[str] = ["log_drift", "fallback_parser", "escalate"]
_STATE_CORRUPTION_STEPS: list[str] = ["rollback_checkpoint", "escalate"]
_BUDGET_EXCEEDED_STEPS: list[str] = ["pause_non_critical", "escalate"]
_CIRCUIT_OPEN_STEPS: list[str] = ["wait_recovery_window", "half_open_trial", "escalate"]
_POLICY_DENY_STEPS: list[str] = ["request_override", "escalate"]
_CONTRACT_DRIFT_STEPS: list[str] = ["emit_drift_event", "fallback_contract", "escalate"]
_RETRY_EXHAUSTED_STEPS: list[str] = ["dlq_enqueue", "escalate"]
_CHECKPOINT_FAILED_STEPS: list[str] = ["retry_checkpoint", "rollback", "escalate"]
_ROLLBACK_TRIGGERED_STEPS: list[str] = ["verify_rollback", "resume_or_escalate"]
_UNKNOWN_STEPS: list[str] = ["log", "escalate"]


# Ordered (first-match-wins) keyword → ladder rules.
# Longer / more-specific phrases checked before shorter ones.
_CLASSIFIER_RULES: tuple[tuple[tuple[str, ...], list[str]], ...] = (
    (("timed out", "timeout"), _TIMEOUT_STEPS),
    (("rate limit", "429"), _RATE_LIMIT_STEPS),
    (("authentication",), _AUTH_FAILURE_STEPS),
    (("network",), _NETWORK_PARTITION_STEPS),
    (("malformed", "invalid json"), _MALFORMED_RESPONSE_STEPS),
    (("state corruption",), _STATE_CORRUPTION_STEPS),
    (("budget exceeded",), _BUDGET_EXCEEDED_STEPS),
    (("circuit",), _CIRCUIT_OPEN_STEPS),
    (("policy denied", "policy deny"), _POLICY_DENY_STEPS),
    (("contract drift", "schema drift", "schema mismatch"), _CONTRACT_DRIFT_STEPS),
    (("retry exhausted",), _RETRY_EXHAUSTED_STEPS),
    (("checkpoint failed",), _CHECKPOINT_FAILED_STEPS),
    (("rollback triggered",), _ROLLBACK_TRIGGERED_STEPS),
)


@dataclass
class Playbook:
    """Named playbook container (``FR-ORC-PB-015`` public type contract).

    Carries ``name`` / ``steps`` and exposes ``execute()`` returning a
    status dict so callers can treat Playbook as a first-class type
    even when the classifier returns step-name lists.
    """

    name: str
    steps: list[dict[str, Any]] = field(default_factory=list)

    def execute(self) -> dict[str, Any]:
        """Execute the playbook (no-op success envelope)."""
        return {"status": "ok", "steps_executed": len(self.steps)}


def get_playbook_for_failure(failure_type: str) -> list[str]:
    """Classify a free-text failure into an ordered playbook step ladder.

    ``FR-ORC-PB-001`` .. ``FR-ORC-PB-010``: keyword matching over the
    fourteen canonical failure categories; unknown / empty messages
    fall through to ``["log", "escalate"]``.  Matching is
    case-insensitive and first-match-wins.
    """
    text = (failure_type or "").lower()
    for keywords, steps in _CLASSIFIER_RULES:
        if any(keyword in text for keyword in keywords):
            return list(steps)
    return list(_UNKNOWN_STEPS)


def execute_playbook_step(
    session_dir: Path | str,
    step: str,
    run_id: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Dispatch a single playbook step.

    ``FR-ORC-PB-011``: four-parameter signature
    ``(session_dir, step, run_id, context=None)``.

    ``FR-ORC-PB-012`` / ``FR-ORC-PB-013``: ``escalate`` constructs
    ``EscalationQueue(session_dir)`` and calls ``add`` with
    ``agent`` / ``reason`` from context (defaults ``""`` /
    ``"playbook_escalation"``).

    ``FR-ORC-PB-014``: ``dlq_enqueue`` constructs ``DLQManager`` +
    ``RunMeta`` with safe defaults (``agent=""``, ``prompt=""``,
    ``cwd="."``, ``owner="system"``) and enqueues.

    ``FR-ORC-PB-015``: all other steps return a pending envelope
    whose message contains ``"requires manual execution"`` and never
    touch EscalationQueue / DLQManager.
    """
    # Lazy imports so unit tests can patch ``thegent.execution.*``.
    if step == "escalate":
        from thegent.execution import EscalationQueue

        ctx = context or {}
        queue = EscalationQueue(session_dir)
        queue.add(
            run_id=run_id,
            agent=str(ctx.get("agent", "")),
            reason=str(ctx.get("reason", "playbook_escalation")),
        )
        return {"step": "escalate", "status": "escalated"}

    if step == "dlq_enqueue":
        from thegent.execution import DLQManager, RunMeta

        ctx = context or {}
        dlq = DLQManager(session_dir)
        meta = RunMeta(
            run_id=run_id,
            agent=str(ctx.get("agent", "")),
            prompt=str(ctx.get("prompt", "")),
            cwd=str(ctx.get("cwd", ".")),
            owner=str(ctx.get("owner", "system")),
        )
        dlq.enqueue(meta, error=str(ctx.get("error", "")))
        return {"step": "dlq_enqueue", "status": "enqueued"}

    return {
        "step": step,
        "status": "pending",
        "message": f"step {step!r} requires manual execution",
    }


__all__ = [
    "Playbook",
    "execute_playbook_step",
    "get_playbook_for_failure",
]
