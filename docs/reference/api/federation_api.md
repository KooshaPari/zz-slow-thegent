# federation API Reference

> **Source**: `src/thegent/governance/federation.py`

WP-13001: Multi-org policy federation.

---

## FederatedPolicyManager

Manages federated policy resolution and health.

### Methods

#### FederatedPolicyManager.**init**

```python
__init__(self: Any, base_dir: Path)
```

---

#### FederatedPolicyManager.apply_jurisdiction_constraints

```python
apply_jurisdiction_constraints(self: Any, policy: dict[(str, Any)], region: str)
```

Apply jurisdiction overlay (EU-AI-ACT, US-SEC).

---

#### FederatedPolicyManager.arbitrate_conflict

```python
arbitrate_conflict(self: Any, policies: list[dict[(str, Any)]])
```

Arbitrate conflicts using 'most restrictive wins'.

---

#### FederatedPolicyManager.get_federation_health

```python
get_federation_health(self: Any)
```

Return federation health status.

---

#### FederatedPolicyManager.join_namespace

```python
join_namespace(self: Any, ns_str: str)
```

Register current node with a federated namespace (WP-13006).

---

#### FederatedPolicyManager.leave_namespace

```python
leave_namespace(self: Any, ns_str: str)
```

Remove registration for a federated namespace.

---

#### FederatedPolicyManager.relay_consent

```python
relay_consent(self: Any, ns1: PolicyNamespace, ns2: PolicyNamespace, run_id: str, approver: str)
```

WP-13003: Relay approval consent between namespaces with provenance signatures.

---

#### FederatedPolicyManager.resolve_policy

```python
resolve_policy(self: Any, ns: PolicyNamespace, policy_id: str)
```

Resolve policy by traversing namespace hierarchy.

---

---

## FederationManager

Manages policy federation across multiple organizations.

### Methods

#### FederationManager.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### FederationManager.get_effective_policy

```python
get_effective_policy(self: Any, policy_id: str)
```

Resolve a policy, considering federated overrides.

---

#### FederationManager.sync_policies

```python
sync_policies(self: Any, peer_id: str)
```

Sync governance policies from a peer organization.

---

---

## PolicyNamespace

Namespace identifier for org/project/env.

### Methods

#### PolicyNamespace.**init**

```python
__init__(self: Any, org: str, project: str, environment: str)
```

---

#### PolicyNamespace.get_hierarchy

```python
get_hierarchy(self: Any)
```

Return resolution order: specific -> org default -> root default.

---

---

## apply_jurisdiction_constraints

```python
apply_jurisdiction_constraints(self: Any, policy: dict[(str, Any)], region: str)
```

Apply jurisdiction overlay (EU-AI-ACT, US-SEC).

---

## arbitrate_conflict

```python
arbitrate_conflict(self: Any, policies: list[dict[(str, Any)]])
```

Arbitrate conflicts using 'most restrictive wins'.

---

## get_effective_policy

```python
get_effective_policy(self: Any, policy_id: str)
```

Resolve a policy, considering federated overrides.

---

## get_federation_health

```python
get_federation_health(self: Any)
```

Return federation health status.

---

## get_hierarchy

```python
get_hierarchy(self: Any)
```

Return resolution order: specific -> org default -> root default.

---

## join_namespace

```python
join_namespace(self: Any, ns_str: str)
```

Register current node with a federated namespace (WP-13006).

---

## leave_namespace

```python
leave_namespace(self: Any, ns_str: str)
```

Remove registration for a federated namespace.

---

## relay_consent

```python
relay_consent(self: Any, ns1: PolicyNamespace, ns2: PolicyNamespace, run_id: str, approver: str)
```

WP-13003: Relay approval consent between namespaces with provenance signatures.

---

## resolve_policy

```python
resolve_policy(self: Any, ns: PolicyNamespace, policy_id: str)
```

Resolve policy by traversing namespace hierarchy.

---

## sync_policies

```python
sync_policies(self: Any, peer_id: str)
```

Sync governance policies from a peer organization.

---
