# federated_policy API Reference

> **Source**: `src/thegent/governance/federated_policy.py`

FederatedPolicyEngine: scope-aware policy registry for governance.

Traces to: FR-GOV-001 (policy federation), FR-GOV-002 (scope precedence)

---

## FederatedPolicyEngine

Registry and evaluator for scoped governance policy rules (FR-GOV-001).

Supports multi-tenant federation via namespace hierarchy.

### Methods

#### FederatedPolicyEngine.**init**

```python
__init__(self: Any, default_namespace: str)
```

---

#### FederatedPolicyEngine.evaluate

```python
evaluate(self: Any, namespace: str, context: dict[(str, Any)])
```

Evaluate matching rules for a namespace, sorted by priority.

---

#### FederatedPolicyEngine.load_from_file

```python
load_from_file(self: Any, path: Path, namespace: str)
```

Load rules from a JSON file.

---

#### FederatedPolicyEngine.merge

```python
merge(self: Any, other: FederatedPolicyEngine)
```

Combine two engines.

---

#### FederatedPolicyEngine.register

```python
register(self: Any, rule: PolicyRule)
```

Add _rule_ to the registry, replacing any existing rule with the same id.

---

#### FederatedPolicyEngine.resolve_policies

```python
resolve_policies(self: Any, namespace: str)
```

Resolve all rules for a namespace, following hierarchy (specific -&gt; parent -&gt; global).

---

---

## PolicyRule

A single governance rule with scope and evaluation metadata (FR-GOV-001).

### Methods

#### PolicyRule.create

```python
create(cls: Any, rule_id: str, scope: PolicyScope, condition: str, action: str, priority: int, namespace: str)
```

Named constructor matching the canonical field order in the task spec.

---

---

## PolicyScope

Hierarchy level of a policy rule. Higher numeric value = higher authority.

**Inherits from**: `Enum`

---

## create

```python
create(cls: Any, rule_id: str, scope: PolicyScope, condition: str, action: str, priority: int, namespace: str)
```

Named constructor matching the canonical field order in the task spec.

---

## evaluate

```python
evaluate(self: Any, namespace: str, context: dict[(str, Any)])
```

Evaluate matching rules for a namespace, sorted by priority.

---

## load_from_file

```python
load_from_file(self: Any, path: Path, namespace: str)
```

Load rules from a JSON file.

---

## merge

```python
merge(self: Any, other: FederatedPolicyEngine)
```

Combine two engines.

---

## register

```python
register(self: Any, rule: PolicyRule)
```

Add _rule_ to the registry, replacing any existing rule with the same id.

---

## resolve_policies

```python
resolve_policies(self: Any, namespace: str)
```

Resolve all rules for a namespace, following hierarchy (specific -&gt; parent -&gt; global).

---
