"""MCP server contract definitions — AUDIT-N+15 gate delta hardening.

Formalises the shape of every MCP server gate response so that
downstream consumers (cockpit panes, governance dashboards, SOTA
audit tests) can validate payloads against a single source of truth
instead of ad-hoc ``assert "key" in payload`` checks scattered across
test files.

Canonical home: ``thegent.mcp.server.mcp_server_contracts``

Design constraints:
- Pure data: no side effects, no I/O.
- Pydantic-free for zero-dependency import in test harnesses.
- Every contract has a ``SCHEMA_VERSION`` so gate tests can detect
  drift between the contract definition and the live payload.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "2026.07-aud15"


# ------------------------------------------------------------------
# Base gate contract
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GateContract:
    """Minimal contract that every MCP gate response must satisfy."""

    required_keys: tuple[str, ...] = ()
    optional_keys: tuple[str, ...] = ()
    meta_keys: tuple[str, ...] = ()

    def validate(self, payload: dict[str, Any]) -> list[str]:
        """Return a list of validation errors (empty = valid)."""
        errors: list[str] = []
        for key in self.required_keys:
            if key not in payload:
                errors.append(f"missing_required: {key}")
        return errors

    def to_dict(self) -> dict[str, Any]:
        """Serialise for test-introspection."""
        return {
            "schema_version": SCHEMA_VERSION,
            "required_keys": list(self.required_keys),
            "optional_keys": list(self.optional_keys),
            "meta_keys": list(self.meta_keys),
        }


# ------------------------------------------------------------------
# Concrete gate contracts
# ------------------------------------------------------------------

OBSERVE_SUMMARY_CONTRACT = GateContract(
    required_keys=(
        "status",
        "payload_type",
        "payload_schema_version",
        "alerts",
        "drift",
        "escalation",
        "trend_summary",
        "generated_query",
    ),
    optional_keys=(
        "scope_key",
        "scope_owner",
        "generated_at_utc",
    ),
    meta_keys=(
        "status",
        "payload_type",
        "payload_schema_version",
        "alerts_count",
        "drift_within_budget",
        "backlog_past_sla_count",
        "top_escalations_requested",
        "drift_structural_budget_pct",
        "drift_semantic_budget_pct",
        "provider",
        "trend_enabled",
        "trend_samples_requested",
    ),
)

CONTRACT_HEALTH_GATE_CONTRACT = GateContract(
    required_keys=(
        "status",
        "policy_profile",
        "decision_reasons",
        "total",
        "healthy_count",
        "unhealthy_count",
        "blocked_count",
    ),
    optional_keys=(
        "top_blocked_count",
        "blocked_sessions_cap",
        "scope_key",
    ),
    meta_keys=(
        "status",
        "policy_profile",
        "decision_reasons",
        "total",
        "healthy_count",
        "unhealthy_count",
        "blocked_count",
        "top_blocked_count",
        "blocked_sessions_cap",
    ),
)

HEALTH_TREND_CONTRACT = GateContract(
    required_keys=(
        "status",
        "payload_type",
        "schema_version",
        "trend_payload_type",
        "generated_at_utc",
        "snapshot_count",
        "snapshot_ids_hash",
    ),
    optional_keys=(
        "scope_key",
        "scope_owner",
        "latest",
        "delta_summary_json",
        "blocked_ratio_delta",
        "blocked_count_delta",
        "compat",
        "snapshot_health_volatility",
        "snapshot_health_volatility_hash",
        "snapshot_freshness_seconds",
        "snapshot_freshness_hash",
        "snapshot_retention_max_lines",
        "snapshot_density_per_hour",
        "snapshot_density_hash",
        "snapshot_issue_churn_count",
        "snapshot_issue_churn_hash",
        "snapshot_window_seconds",
        "snapshot_window_hash",
        "snapshot_interval_seconds_avg",
        "snapshot_interval_hash",
        "latest_status",
        "latest_pass",
        "latest_captured_at_utc",
        "latest_blocked_ratio",
        "latest_blocked_count",
        "latest_issue_types_csv",
        "latest_issue_types_json",
        "latest_issue_types_hash",
        "latest_issue_types_count",
        "compat_mode",
        "compat_aliases",
        "compat_aliases_count",
    ),
    meta_keys=(
        "status",
        "payload_type",
        "schema_version",
        "trend_payload_type",
        "generated_at_utc",
        "scope_key",
        "snapshot_count",
        "snapshot_ids_hash",
        "snapshot_health_volatility",
        "snapshot_health_volatility_hash",
        "latest_issue_types_count",
        "latest_issue_types_csv",
        "latest_issue_types_json",
        "latest_issue_types_hash",
        "compat_mode",
        "compat_aliases_count",
    ),
)


# ------------------------------------------------------------------
# Registry
# ------------------------------------------------------------------

CONTRACTS: dict[str, GateContract] = {
    "observe_summary": OBSERVE_SUMMARY_CONTRACT,
    "contract_health_gate": CONTRACT_HEALTH_GATE_CONTRACT,
    "health_trend": HEALTH_TREND_CONTRACT,
}


def get_contract(name: str) -> GateContract | None:
    """Look up a gate contract by name."""
    return CONTRACTS.get(name)


def validate_payload(name: str, payload: dict[str, Any]) -> list[str]:
    """Validate *payload* against the named contract.

    Returns a list of error strings; empty means valid.
    """
    contract = get_contract(name)
    if contract is None:
        return [f"unknown_contract: {name}"]
    return contract.validate(payload)


def list_contracts() -> dict[str, dict[str, Any]]:
    """Return all registered contracts as serialisable dicts."""
    return {name: c.to_dict() for name, c in CONTRACTS.items()}
