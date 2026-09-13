# hitl API Reference

> **Source**: `src/thegent/governance/hitl.py`

Human-in-the-loop (HITL) coordination and approval workflows (WP-3001, WP-3008).

---

## HITLManager

Manages human-in-the-loop signals and approvals.

### Methods

#### HITLManager.**init**

```python
__init__(self: Any)
```

---

#### HITLManager.approve

```python
approve(self: Any, request_id: str)
```

Record an approval for a request.

---

#### HITLManager.is_approved

```python
is_approved(self: Any, request_id: str)
```

Check if a request has been approved.

---

#### HITLManager.request_approval

```python
request_approval(self: Any, request_id: str, action: str, context: dict[(str, Any)])
```

Issue an approval request and return its ID.

---

---

## approve

```python
approve(self: Any, request_id: str)
```

Record an approval for a request.

---

## is_approved

```python
is_approved(self: Any, request_id: str)
```

Check if a request has been approved.

---

## request_approval

```python
request_approval(self: Any, request_id: str, action: str, context: dict[(str, Any)])
```

Issue an approval request and return its ID.

---
