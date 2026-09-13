"""Governance modules: cost, policy, sandbox, economic routing (G-GP, WP-5003).

All re-exports are lazy to avoid pulling heavy transitive dependencies
(orjson, httpx, …) at package-import time.  This keeps pytest collection
working even when not every runtime dependency is installed.
"""

from __future__ import annotations

import importlib
from typing import Any

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    # Cost governance
    "CostAggregator": ("thegent.cost.aggregator", "CostAggregator"),
    "CostEstimator": ("thegent.cost.aggregator", "CostEstimator"),
    # Compliance
    "ComplianceReporter": ("thegent.governance.compliance_reports", "ComplianceReporter"),
    # Federated policy
    "FederatedPolicyEngine": ("thegent.governance.federated_policy", "FederatedPolicyEngine"),
    "PolicyRule": ("thegent.governance.federated_policy", "PolicyRule"),
    "PolicyScope": ("thegent.governance.federated_policy", "PolicyScope"),
    # Input guardrails
    "GuardrailResult": ("thegent.governance.input_guardrails", "GuardrailResult"),
    "InputGuardrails": ("thegent.governance.input_guardrails", "InputGuardrails"),
    # Phase 2.1: Provider Scoring System (WP-5003)
    "AggregatedMetrics": ("thegent.governance.metrics", "AggregatedMetrics"),
    "MetricsCollector": ("thegent.governance.metrics", "MetricsCollector"),
    "ProviderMetricsSnapshot": ("thegent.governance.metrics", "ProviderMetricsSnapshot"),
    "get_metrics_collector": ("thegent.governance.metrics", "get_metrics_collector"),
    "initialize_metrics_collector": ("thegent.governance.metrics", "initialize_metrics_collector"),
    # Override events
    "OverrideActivatedEvent": ("thegent.governance.override_events", "OverrideActivatedEvent"),
    "OverrideEventEmitter": ("thegent.governance.override_events", "OverrideEventEmitter"),
    "OverrideExpiredEvent": ("thegent.governance.override_events", "OverrideExpiredEvent"),
    "OverrideExpiryMonitor": ("thegent.governance.override_events", "OverrideExpiryMonitor"),
    # Providers
    "ProviderConfig": ("thegent.governance.providers", "ProviderConfig"),
    "ProviderRegistry": ("thegent.governance.providers", "ProviderRegistry"),
    "ProviderType": ("thegent.governance.providers", "ProviderType"),
    # Scoring
    "DefaultProviderScorer": ("thegent.governance.scoring", "DefaultProviderScorer"),
    "ProviderMetrics": ("thegent.governance.scoring", "ProviderMetrics"),
    "ProviderScore": ("thegent.governance.scoring", "ProviderScore"),
    "ProviderScorer": ("thegent.governance.scoring", "ProviderScorer"),
    # Vetter
    "RuffVetterCheck": ("thegent.governance.vetter", "RuffVetterCheck"),
    "TestPassVetterCheck": ("thegent.governance.vetter", "TestPassVetterCheck"),
    "VetterCheck": ("thegent.governance.vetter", "VetterCheck"),
    "VetterCheckResult": ("thegent.governance.vetter", "VetterCheckResult"),
    "VetterOutcome": ("thegent.governance.vetter", "VetterOutcome"),
    "VetterPolicy": ("thegent.governance.vetter", "VetterPolicy"),
    "VetterResult": ("thegent.governance.vetter", "VetterResult"),
    "VetterSeverity": ("thegent.governance.vetter", "VetterSeverity"),
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_IMPORTS:
        module_path, attr = _LAZY_IMPORTS[name]
        mod = importlib.import_module(module_path)
        val = getattr(mod, attr)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return list(_LAZY_IMPORTS.keys())


__all__ = [
    # Phase 2.1: Provider Scoring System (WP-5003)
    "AggregatedMetrics",
    # Cost governance
    "CostAggregator",
    "CostEstimator",
    "DefaultProviderScorer",
    # Input guardrails
    "GuardrailResult",
    "InputGuardrails",
    "MetricsCollector",
    "ProviderConfig",
    "ProviderMetrics",
    "ProviderMetricsSnapshot",
    "ProviderRegistry",
    "ProviderScore",
    "ProviderScorer",
    "ProviderType",
    "get_metrics_collector",
    "initialize_metrics_collector",
    # Compliance
    "ComplianceReporter",
    # Federated policy
    "FederatedPolicyEngine",
    "PolicyRule",
    "PolicyScope",
    # Override events
    "OverrideActivatedEvent",
    "OverrideEventEmitter",
    "OverrideExpiredEvent",
    "OverrideExpiryMonitor",
    # Vetter
    "RuffVetterCheck",
    "TestPassVetterCheck",
    "VetterCheck",
    "VetterCheckResult",
    "VetterOutcome",
    "VetterPolicy",
    "VetterResult",
    "VetterSeverity",
]
