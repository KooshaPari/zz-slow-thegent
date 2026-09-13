# policy_federation API Reference

> **Source**: `src/thegent/phases/policy_federation.py`

Policy federation surface map (FederatedPolicyEngine).

---

## FederatedPolicyEngine

Federated policy engine for multi-tenant coordination.

### Methods

#### FederatedPolicyEngine.**init**

```python
__init__(self: Any, namespace: str)
```

Initialize federated policy engine for a specific namespace.

---

#### FederatedPolicyEngine.evaluate

```python
evaluate(self: Any, tenant_id: str, action: str, context: dict[(str, Any)])
```

Evaluate policy for an action.

---

#### FederatedPolicyEngine.get_federation_status

```python
get_federation_status(self: Any)
```

Get federation status.

---

#### FederatedPolicyEngine.get_policy

```python
get_policy(self: Any, key: str)
```

Get a policy, resolving through namespace hierarchy.

---

#### FederatedPolicyEngine.is_allowed

```python
is_allowed(self: Any, action: str, context: dict[(str, Any)])
```

Evaluate if an action is allowed based on resolved policies.

---

#### FederatedPolicyEngine.register_tenant

```python
register_tenant(self: Any, tenant_id: str, policy: dict[(str, Any)])
```

Register a tenant with its policy.

---

#### FederatedPolicyEngine.resolve_policy

```python
resolve_policy(self: Any, namespace: str, policy_key: str)
```

Resolve policy through namespace hierarchy.

---

#### FederatedPolicyEngine.set_policy

```python
set_policy(self: Any, key: str, value: Any)
```

Set a policy for the current namespace.

---

---

## PolicyConflictResolver

Resolves conflicts between multiple applicable policies.

### Methods

#### PolicyConflictResolver.resolve

```python
resolve(self: Any, policies: list[dict[(str, Any)]], target_namespace: str)
```

Resolve conflicting policies via precedence (most specific wins).

---

---

## evaluate

```python
evaluate(self: Any, tenant_id: str, action: str, context: dict[(str, Any)])
```

Evaluate policy for an action.

---

## get_federation_status

```python
get_federation_status(self: Any)
```

Get federation status.

---

## get_policy

```python
get_policy(self: Any, key: str)
```

Get a policy, resolving through namespace hierarchy.

---

## is_allowed

```python
is_allowed(self: Any, action: str, context: dict[(str, Any)])
```

Evaluate if an action is allowed based on resolved policies.

---

## register_tenant

```python
register_tenant(self: Any, tenant_id: str, policy: dict[(str, Any)])
```

Register a tenant with its policy.

---

## resolve

```python
resolve(self: Any, policies: list[dict[(str, Any)]], target_namespace: str)
```

Resolve conflicting policies via precedence (most specific wins).

---

## resolve_policy

```python
resolve_policy(self: Any, namespace: str, policy_key: str)
```

Resolve policy through namespace hierarchy.

---

## set_policy

```python
set_policy(self: Any, key: str, value: Any)
```

Set a policy for the current namespace.

---

## specificity

```python
specificity(p: dict[(str, Any)]) -> int
```

---
