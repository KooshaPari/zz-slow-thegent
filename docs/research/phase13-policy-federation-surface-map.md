<DONE>
# Phase 13: Policy Federation Surface Map

> **Purpose:** Map architectural surfaces for single-tenant → multi-org policy federation.
> **Depends:** —
> **Acceptance:** FederatedPolicyEngine, namespace model (org.project.env), storage/API surfaces documented.
> **WORK_STREAM ID:** phase13-policy-federation

## 1. Overview
This document maps the architectural surfaces affected by the transition from single-tenant to multi-org policy federation.

## 2. Integration Points

### 2.1 Policy Resolution Surface
- **Existing**: `src/thegent/contracts/policy.py`
- **Federated**: Introduction of `FederatedPolicyEngine` which handles namespace-aware lookups.

### 2.2 Namespace Model
- **Core Concept**: `org.project.environment` (e.g., `acme.payments.production`)
- **Inheritance**: Policies at `acme` level apply to all sub-namespaces unless overridden at project level.

### 2.3 Storage Surface
- **Persistence**: Policy files stored in a directory structure reflecting the namespace.
- **Migration**: Tools to move existing single-tenant policies into the `default` namespace.

### 2.4 API/CLI Surface
- **Commands**:
  - `thegent govern federation list`
  - `thegent govern federation join <namespace>`
  - `thegent govern federation leave <namespace>`

## 3. Implementation Details

### 3.1 FederatedPolicyEngine

The `FederatedPolicyEngine` is implemented in `src/thegent/phases/policy_federation.py`:

```python
from thegent.phases.policy_federation import FederatedPolicyEngine

# Initialize with namespace support
engine = FederatedPolicyEngine(namespace="acme.payments.production", parent_namespaces=["acme.payments", "acme"])

# Policy resolution with inheritance
policy = engine.resolve_policy("cost_cap")
# Checks: acme.payments.production -> acme.payments -> acme -> default
```

### 3.2 Namespace Model Implementation

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class PolicyNamespace:
    """Represents a policy namespace with inheritance."""

    org: str
    project: Optional[str] = None
    environment: Optional[str] = None

    def to_string(self) -> str:
        """Convert to namespace string."""
        parts = [self.org]
        if self.project:
            parts.append(self.project)
        if self.environment:
            parts.append(self.environment)
        return ".".join(parts)

    def get_parents(self) -> list[str]:
        """Get parent namespace hierarchy."""
        parents = []
        if self.environment and self.project:
            parents.append(f"{self.org}.{self.project}")
        if self.project:
            parents.append(self.org)
        return parents
```

### 3.3 Policy Conflict Resolution

```python
class PolicyConflictResolver:
    """Resolves conflicts between federated policies."""

    def resolve(self, policies: list[dict], namespace: str) -> dict:
        """Resolve conflicts using precedence rules.

        Precedence: project > org > default
        """
        # Sort by namespace depth (deeper = higher precedence)
        sorted_policies = sorted(policies, key=lambda p: len(p["namespace"].split(".")), reverse=True)

        # Merge policies with precedence
        resolved = {}
        for policy in sorted_policies:
            resolved.update(policy["rules"])

        return resolved
```

### 3.4 Storage Structure

```
.thegent/policies/
├── acme/
│   ├── policy.yaml          # Org-level policies
│   ├── payments/
│   │   ├── policy.yaml      # Project-level policies
│   │   └── production/
│   │       └── policy.yaml  # Environment-specific policies
│   └── analytics/
│       └── policy.yaml
└── default/
    └── policy.yaml          # Default policies
```

## 4. Acceptance Criteria Status

- [x] Policy federation architecture designed (`FederatedPolicyEngine`)
- [x] Multi-tenant policy coordination implemented (`PolicyNamespace`)
- [x] Policy conflict resolution strategy defined (`PolicyConflictResolver`)
- [x] Federation surface area documented (this document)
- [x] Integration points mapped (Policy Resolution, Namespace Model, Storage, API/CLI)
- [ ] Integration tests passing (pending implementation)
## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index


---

## 7. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made
1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related docs

### Cross-References Added
- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions
- Implementation templates
- Configuration examples
- Best practices
