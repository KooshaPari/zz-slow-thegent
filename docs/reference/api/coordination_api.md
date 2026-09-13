# coordination API Reference

> **Source**: `src/thegent/team/coordination.py`

WP-9003: Teammate Coordination Protocol.

Handles inter-agent communication, idle detection, and task completion hooks.

---

## TeamCoordinator

Coordinates teammates during a multi-agent run.

### Methods

#### TeamCoordinator.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### TeamCoordinator.broadcast_message

```python
broadcast_message(self: Any, team_id: str, sender: str, message: str)
```

WP-9003: Broadcast a message to all teammates in a team.

---

#### TeamCoordinator.call_vote

```python
call_vote(self: Any, team_id: str, caller: str, subject: str, options: list[str])
```

WP-9003: Call a vote among teammates.

---

#### TeamCoordinator.cast_vote

```python
cast_vote(self: Any, team_id: str, vote_id: str, voter: str, option: str)
```

WP-9003: Cast a vote.

---

#### TeamCoordinator.detect_idle

```python
detect_idle(self: Any, stdout: str)
```

WP-9003: Detect if a teammate agent is idle and needs input.

Looks for common patterns like 'waiting for input', 'how can I help?', etc.

---

#### TeamCoordinator.get_vote_result

```python
get_vote_result(self: Any, team_id: str, vote_id: str)
```

WP-9003: Get current results of a vote.

---

#### TeamCoordinator.handle_task_completed

```python
handle_task_completed(self: Any, team_id: str, task_id: str, result: str)
```

WP-9003: Handle a task completion event from a teammate.

---

#### TeamCoordinator.wait_for_task

```python
wait_for_task(self: Any, team_id: str, task_id: str, timeout: int)
```

WP-9003: Wait for a task to be completed by a teammate.

---

---

## broadcast_message

```python
broadcast_message(self: Any, team_id: str, sender: str, message: str)
```

WP-9003: Broadcast a message to all teammates in a team.

---

## call_vote

```python
call_vote(self: Any, team_id: str, caller: str, subject: str, options: list[str])
```

WP-9003: Call a vote among teammates.

---

## cast_vote

```python
cast_vote(self: Any, team_id: str, vote_id: str, voter: str, option: str)
```

WP-9003: Cast a vote.

---

## detect_idle

```python
detect_idle(self: Any, stdout: str)
```

WP-9003: Detect if a teammate agent is idle and needs input.

Looks for common patterns like 'waiting for input', 'how can I help?', etc.

---

## get_vote_result

```python
get_vote_result(self: Any, team_id: str, vote_id: str)
```

WP-9003: Get current results of a vote.

---

## handle_task_completed

```python
handle_task_completed(self: Any, team_id: str, task_id: str, result: str)
```

WP-9003: Handle a task completion event from a teammate.

---

## wait_for_task

```python
wait_for_task(self: Any, team_id: str, task_id: str, timeout: int)
```

WP-9003: Wait for a task to be completed by a teammate.

---
