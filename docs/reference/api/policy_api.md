# policy API Reference

> **Source**: `src/thegent/governance/policy.py`

Core policy management and evaluation (WP-3001, WP-3002).

---

## LearningSession

Represents an autonomous learning session bounded by policy.

### Methods

#### LearningSession.**init**

```python
__init__(self: Any, policy_manager: PolicyManager)
```

---

#### LearningSession.is_valid

```python
is_valid(self: Any)
```

Verify session is still valid against current policy.

---

#### LearningSession.start

```python
start(self: Any)
```

Start the learning session.

---

---

## PolicyManager

Manages system-wide policies and their evaluation.

### Methods

#### PolicyManager.**init**

```python
__init__(self: Any, initial_policies: Any)
```

---

#### PolicyManager.get_policy

```python
get_policy(self: Any, key: str)
```

Get a policy value.

---

#### PolicyManager.update

```python
update(self: Any, new_policies: dict[(str, Any)])
```

Update policies.

---

---

## get_policy

```python
get_policy(self: Any, key: str)
```

Get a policy value.

---

## is_valid

```python
is_valid(self: Any)
```

Verify session is still valid against current policy.

---

## start

```python
start(self: Any)
```

Start the learning session.

---

## update

```python
update(self: Any, new_policies: dict[(str, Any)])
```

Update policies.

---
