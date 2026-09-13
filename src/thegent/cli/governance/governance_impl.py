"""Governance, escalation, and HITL implementation — AUDIT-N+10.

AUDIT-N+10 canonical home for the nine governance / escalation /
HITL / data-protection symbols that previously lived scattered
across:

  * :mod:`thegent.cli.governance.governance` (8 functions)
  * :mod:`thegent.cli.services.run_post_surface_helpers` (1 function)
  * undefined (1 function: ``get_data_protection_status_impl``)

This module also pins ``escalate_add_impl`` re-exported from
:mod:`thegent.cli.commands.observability_impl` so AUDIT-N+5/9
contract closures keep their canonical home.

The legacy import surface
``from thegent.cli.commands.impl import <symbol>`` continues to
work via a re-export block in :mod:`thegent.cli.commands.impl`,
mirroring the AUDIT-N+9 observability pattern.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from thegent.config import ThegentSettings

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _session_dir() -> Path:
    """Resolve the session directory from settings (Path form)."""
    settings = ThegentSettings()
    return Path(settings.session_dir).expanduser().resolve()


# ---------------------------------------------------------------------------
# Escalation queue — WP-3008 (governance.py:155-200 surface)
# ---------------------------------------------------------------------------


def escalate_add_impl(
    run_id: str,
    reason: str,
    sla_minutes: int = 30,
    owner: str | None = None,
    agent: str | None = None,
    lane: str = "standard",
    priority: int = 0,
) -> None:
    """WP-3008: Add a blocked run to the escalation queue.

    Args:
        run_id: Run identifier (canonical primary key).
        reason: Human-readable reason for escalation.
        sla_minutes: SLA window before escalation is past-SLA.
        owner: Owner / responsible party (optional).
        agent: Agent that emitted the escalation (optional).
        lane: Logical lane / classification (default ``"standard"``).
        priority: Integer priority (default ``0``).
    """
    from thegent.execution import EscalationQueue

    queue = EscalationQueue(_session_dir())
    queue.add(
        run_id=run_id,
        reason=reason,
        sla_minutes=sla_minutes,
        owner=owner,
        agent=agent,
        lane=lane,
        priority=priority,
    )


def escalate_approve_impl(run_id: str) -> bool:
    """WP-3008: Approve an escalation, marking it approved in the queue (G-GP-05)."""
    from thegent.execution import EscalationQueue

    queue = EscalationQueue(_session_dir())
    return queue.resolve(run_id=run_id, resolution="approved")


def escalate_list_impl(
    past_sla_only: bool = False, limit: int = 50
) -> list[dict[str, Any]]:
    """WP-3008: List escalation queue items (blocked runs with SLA)."""
    from thegent.execution import EscalationQueue

    queue = EscalationQueue(_session_dir())
    return queue.list_pending(past_sla_only=past_sla_only, limit=limit)


def escalate_resolve_impl(run_id: str, resolution: str = "resolved") -> bool:
    """WP-3008: Mark an escalation item as resolved."""
    from thegent.execution import EscalationQueue

    queue = EscalationQueue(_session_dir())
    return queue.resolve(run_id=run_id, resolution=resolution)


# ---------------------------------------------------------------------------
# HITL approval — WL-019-B (governance.py:203-224 surface)
# ---------------------------------------------------------------------------


def govern_approve_impl(run_id: str, reason: str | None = None) -> dict[str, Any]:
    """WL-019-B: Approve a HITL-blocked run, writing 'approved' to governance_events.jsonl."""
    from thegent.governance.hitl import HITLApprovalWorkflow

    workflow = HITLApprovalWorkflow(_session_dir())
    return workflow.approve(run_id=run_id, reason=reason)


def govern_reject_impl(run_id: str, reason: str | None = None) -> dict[str, Any]:
    """WL-019-B: Reject a HITL-blocked run, writing 'rejected' to governance_events.jsonl."""
    from thegent.governance.hitl import HITLApprovalWorkflow

    workflow = HITLApprovalWorkflow(_session_dir())
    return workflow.reject(run_id=run_id, reason=reason)


def govern_list_pending_impl() -> list[dict[str, Any]]:
    """WL-019-B: List all pending HITL approval events from governance_events.jsonl."""
    from thegent.governance.hitl import HITLApprovalWorkflow

    workflow = HITLApprovalWorkflow(_session_dir())
    return workflow.list_pending()


# ---------------------------------------------------------------------------
# Remote harness — WL-110 (services/run_post_surface_helpers.py:638 surface)
# ---------------------------------------------------------------------------


def harness_register_host_impl(
    *,
    host_id: str,
    harness: str,
    command_prefix: str = "",
    custom_actions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Register a new host device with custom command mappings.

    Args:
        host_id: Unique host identifier.
        harness: Harness type (``cursor``, ``codex``, ``claude``, ``ante``, ``droid``).
        command_prefix: Command prefix (e.g., ``"ssh user@host"``).
        custom_actions: Optional dict of action-name → command-string mappings.

    Returns:
        Dict with ``success``, ``host_id``, ``harness``, ``command_prefix`` keys.
    """
    from thegent.agents.unified_session_index import HarnessTUIMapper, HarnessType

    try:
        harness_type = HarnessType(harness.lower())
    except ValueError:
        return {
            "success": False,
            "error": f"Unknown harness: {harness}",
        }

    mapper = HarnessTUIMapper()
    mapper.register_host(
        host_id=host_id,
        harness=harness_type,
        command_prefix=command_prefix,
        custom_actions=custom_actions,
    )
    return {
        "success": True,
        "host_id": host_id,
        "harness": harness,
        "command_prefix": command_prefix,
    }


# ---------------------------------------------------------------------------
# Data protection status — WP-3010 (previously UNDEFINED)
# ---------------------------------------------------------------------------


def get_data_protection_status_impl() -> dict[str, Any]:
    """WP-3010 / data-protection: Inspect session directory + retention config.

    Inspects the current ``ThegentSettings`` and reports on:

      * ``session_dir``: the resolved session directory path.
      * ``session_dir_exists``: whether the directory exists on disk.
      * ``permissions_restricted``: whether the directory is mode ``0o700``
        (the canonical "operator-only" permission set).
      * ``masking_enabled``: whether PII masking on logs/telemetry is on
        (defaults to True if the settings key is absent).
      * ``retention_days_sessions`` / ``retention_days_registry`` /
        ``retention_days_health``: per-domain retention windows (days).
      * ``retention_policy_days``: the *minimum* retention window across
        the three domains — the effective data-retention floor.

    Returns:
        Dict containing the keys documented above. All values are JSON-serializable.
    """
    settings = ThegentSettings()

    session_dir = Path(settings.session_dir).expanduser().resolve()
    session_dir_exists = session_dir.exists()

    permissions_restricted = bool(
        session_dir_exists and (session_dir.stat().st_mode & 0o777) == 0o700
    )

    # Default masking to True: PII redaction is the safer default.
    masking_enabled = bool(getattr(settings, "masking_enabled", True))

    retention_days_sessions = int(getattr(settings, "retention_days_sessions", 30))
    retention_days_registry = int(getattr(settings, "retention_days_registry", 90))
    retention_days_health = int(getattr(settings, "retention_days_health", 365))

    # The effective data-retention floor is the smallest of the three windows.
    retention_policy_days = min(
        retention_days_sessions,
        retention_days_registry,
        retention_days_health,
    )

    return {
        "session_dir": str(session_dir),
        "session_dir_exists": session_dir_exists,
        "permissions_restricted": permissions_restricted,
        "masking_enabled": masking_enabled,
        "retention_days_sessions": retention_days_sessions,
        "retention_days_registry": retention_days_registry,
        "retention_days_health": retention_days_health,
        "retention_policy_days": retention_policy_days,
    }


# ---------------------------------------------------------------------------
# Policy drift sweep — WP-3005 (services/observability.py:45 surface, AUDIT-N+10
# signature-aligned). The canonical 5-kwarg signature is preserved; the
# call-site in ``governance_escalation_hitl_cmds.sweep_cmd`` is updated to
# match.
# ---------------------------------------------------------------------------


def sweep_impl(
    *,
    drift_window: int,
    structural_budget: float,
    semantic_budget: float,
    include_audit: bool,
    update_calibration_fn: Any,
) -> dict[str, Any]:
    """WP-3005: Policy drift sweep service.

    Runs drift detection, budget check, past-SLA escalation scan,
    and optionally registry audit. Returns a dict that always has
    the ``pass`` key (True iff all checks are clean).

    Args:
        drift_window: Window size for drift detection (events).
        structural_budget: Structural-drift budget percentage (e.g. ``5.0``).
        semantic_budget: Semantic-drift budget percentage (e.g. ``10.0``).
        include_audit: Whether to invoke the registry auditor.
        update_calibration_fn: Callable returning the calibration dict.

    Returns:
        Dict with keys: ``drift_issues``, ``drift_budget``, ``past_sla_count``,
        ``past_sla_items``, ``calibration``, ``audit``, ``pass``.
    """
    from thegent.contracts.telemetry import ContractTelemetry
    from thegent.execution import Auditor, EscalationQueue, RunRegistry

    settings = ThegentSettings()
    session_dir = Path(settings.session_dir).expanduser().resolve()

    ct = ContractTelemetry(session_dir)
    drift_issues = ct.detect_drift(window_size=drift_window)
    budget = ct.get_drift_budget_status(
        structural_budget_pct=structural_budget,
        semantic_budget_pct=semantic_budget,
    )
    if not budget["within_budget"]:
        drift_issues.append(
            f"Drift budget exceeded: structural {budget['structural_rate_pct']}% "
            f"(budget {budget['structural_budget_pct']}%), semantic {budget['semantic_rate_pct']}% "
            f"(budget {budget['semantic_budget_pct']}%)"
        )

    queue = EscalationQueue(session_dir)
    past_sla_items = queue.list_pending(past_sla_only=True, limit=100)

    if past_sla_items and bool(getattr(settings, "escalation_sla_breach_alert", False)):
        import logging

        _sweep_log = logging.getLogger(__name__)
        _sweep_log.warning(
            "Escalation SLA breach: %d item(s) past SLA. Run: thegent govern escalate list --past-sla",
            len(past_sla_items),
        )

    audit_result: dict[str, Any] | None = None
    if include_audit:
        registry = RunRegistry(session_dir)
        auditor = Auditor(registry.registry_path)
        audit_result = auditor.verify_registry()

    has_issues = bool(drift_issues) or bool(past_sla_items)
    if (
        include_audit
        and audit_result
        and audit_result.get("status") not in ("passed", "empty")
    ):
        has_issues = True

    cal_results = update_calibration_fn()
    return {
        "drift_issues": drift_issues,
        "drift_budget": budget,
        "past_sla_count": len(past_sla_items),
        "past_sla_items": past_sla_items,
        "calibration": cal_results,
        "audit": audit_result,
        "pass": not has_issues,
    }


# ---------------------------------------------------------------------------
# AUDIT-N+5/9 contract: ``escalate_add_impl`` canonical home is
# :mod:`thegent.cli.commands.observability_impl`. Re-export here so the
# governance surface is complete (callers importing from
# ``thegent.cli.governance.governance_impl`` get the same function object).
# ---------------------------------------------------------------------------

from thegent.cli.commands.observability_impl import (
    escalate_add_impl,  # noqa: E402, F401
)

__all__ = [
    "escalate_add_impl",
    "escalate_approve_impl",
    "escalate_list_impl",
    "escalate_resolve_impl",
    "govern_approve_impl",
    "govern_reject_impl",
    "govern_list_pending_impl",
    "harness_register_host_impl",
    "get_data_protection_status_impl",
    "sweep_impl",
]
