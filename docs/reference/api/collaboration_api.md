# collaboration API Reference

> **Source**: `src/thegent/orchestration/collaboration.py`

WP-6008: Collaborative task resolution.

---

## CollaborativeSession

A session where multiple agents collaborate on a task.

### Methods

#### CollaborativeSession.**init**

```python
__init__(self: Any, settings: ThegentSettings, task_id: str)
```

---

#### CollaborativeSession.broadcast_state

```python
broadcast_state(self: Any, state: dict[(str, Any)])
```

Broadcast state updates to all participants.

---

#### CollaborativeSession.recruit_participants

```python
recruit_participants(self: Any, needed_capabilities: list[str])
```

Recruit external agents based on capabilities (including P2P).

---

---

## broadcast_state

```python
broadcast_state(self: Any, state: dict[(str, Any)])
```

Broadcast state updates to all participants.

---

## recruit_participants

```python
recruit_participants(self: Any, needed_capabilities: list[str])
```

Recruit external agents based on capabilities (including P2P).

---
