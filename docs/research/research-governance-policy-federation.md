<DONE>
# Governance Policy Federation Research

> **WORK_STREAM ID:** research-governance-policy-federation
> **Priority:** P1
> **Depends:** WP-3001, research-phase13-policy-federation
> **Status:** ✅ Research Complete

## Summary

This document provides research and implementation guidance for multi-tenant policy federation in thegent governance system. It builds on the `research-phase13-policy-federation` work and focuses on governance-specific aspects.

## Architecture Options

### Option A: Centralized Policy Server

**Approach**: Single authoritative policy server for all tenants

**Pros**:

- Single source of truth
- Easier consistency
- Simplified conflict resolution

**Cons**:

- Single point of failure
- Potential performance bottleneck
- Network dependency

### Option B: Distributed Consensus

**Approach**: Each tenant maintains local policy cache with consensus protocol

**Pros**:

- High availability
- Better performance (local cache)
- No single point of failure

**Cons**:

- Complex consensus logic
- Potential inconsistency windows
- Higher implementation complexity

### Option C: Hybrid Approach (Recommended)

**Approach**: Centralized policy server with distributed caching and local overrides

**Pros**:

- Balance of consistency and performance
- Local overrides for tenant-specific needs
- Graceful degradation if server unavailable

**Cons**:

- More complex than pure centralized
- Cache invalidation logic needed

## Implementation Details

### 3.1 Integration with Existing Components

The policy federation builds on existing components:

```python
from thegent.phases.policy_federation import FederatedPolicyEngine
from thegent.governance.escalation import EscalationQueue
from thegent.execution import PolicyEngine


class GovernancePolicyFederation:
    """Governance-specific policy federation."""

    def __init__(self, federated_engine: FederatedPolicyEngine):
        self.federated_engine = federated_engine
        self.escalation_queue = EscalationQueue()

    def evaluate_governance_policy(self, namespace: str, action: str, context: dict) -> bool:
        """Evaluate governance policy with federation support."""
        # Resolve policy through federation hierarchy
        policy = self.federated_engine.resolve_policy(namespace=namespace, policy_key=f"governance.{action}")

        # Evaluate policy
        if not policy.allow(context):
            # Add to escalation queue if blocked
            self.escalation_queue.add(
                blocked_run=context.get("run_id"), reason=f"Policy denied: {action}", sla_minutes=policy.sla_minutes
            )
            return False

        return True
```

### 3.2 Cache Strategy

```python
from cachetools import TTLCache
from typing import Optional


class PolicyCache:
    """TTL-based policy cache for federation."""

    def __init__(self, ttl_seconds: int = 300):
        self.cache = TTLCache(maxsize=1000, ttl=ttl_seconds)

    def get(self, namespace: str, policy_key: str) -> Optional[dict]:
        """Get cached policy."""
        cache_key = f"{namespace}:{policy_key}"
        return self.cache.get(cache_key)

    def set(self, namespace: str, policy_key: str, policy: dict) -> None:
        """Cache policy."""
        cache_key = f"{namespace}:{policy_key}"
        self.cache[cache_key] = policy

    def invalidate(self, namespace: str, policy_key: Optional[str] = None) -> None:
        """Invalidate cache for namespace or specific policy."""
        if policy_key:
            cache_key = f"{namespace}:{policy_key}"
            self.cache.pop(cache_key, None)
        else:
            # Invalidate all policies for namespace
            keys_to_remove = [k for k in self.cache.keys() if k.startswith(f"{namespace}:")]
            for key in keys_to_remove:
                self.cache.pop(key, None)
```

### 3.3 Conflict Resolution

```python
from thegent.phases.policy_federation import PolicyConflictResolver


class GovernanceConflictResolver(PolicyConflictResolver):
    """Governance-specific conflict resolution."""

    def resolve_governance_conflict(self, policies: list[dict], namespace: str) -> dict:
        """Resolve governance policy conflicts.

        Precedence rules:
        1. Project-level overrides org-level
        2. Environment-level overrides project-level
        3. Explicit deny overrides allow
        4. More restrictive wins (lower cost cap, stricter SLA)
        """
        # Sort by namespace depth (deeper = higher precedence)
        sorted_policies = sorted(policies, key=lambda p: len(p["namespace"].split(".")), reverse=True)

        resolved = {}
        for policy in sorted_policies:
            # Merge with precedence
            for key, value in policy["rules"].items():
                if key not in resolved:
                    resolved[key] = value
                elif self._is_more_restrictive(key, value, resolved[key]):
                    resolved[key] = value

        return resolved

    def _is_more_restrictive(self, key: str, new_value: Any, current_value: Any) -> bool:
        """Check if new value is more restrictive."""
        if key == "cost_cap":
            return new_value < current_value
        elif key == "sla_minutes":
            return new_value < current_value
        elif key == "allow":
            return not new_value  # Deny is more restrictive
        return False
```

## Acceptance Criteria

- [x] Architecture options evaluated (A, B, C)
- [x] Hybrid approach recommended (Option C)
- [x] Integration with `FederatedPolicyEngine` designed
- [x] Cache strategy defined (`PolicyCache` with TTL)
- [x] Conflict resolution logic specified
- [ ] Implementation complete (pending)
- [ ] Integration tests passing (pending)

## References

- [Policy Federation Surface Map](./phase13-policy-federation-surface-map.md)
- [Governance WP Gaps](./GOVERNANCE_WP_GAPS_EXPANDED.md)
- [WORK_STREAM.md](../reference/WORK_STREAM.md)
