# team_coordinator API Reference

> **Source**: `src/thegent/governance/team_coordinator.py`

Team coordination and cross-team collaboration.

---

## TeamCoordinator

Coordinates team activities and cross-team collaboration.

### Methods

#### TeamCoordinator.**init**

```python
__init__(self: Any, hierarchy_manager: AgentHierarchyManager)
```

Initialize team coordinator.

**Parameters**:

- `hierarchy_manager`: AgentHierarchyManager instance

---

#### TeamCoordinator.coordinate_team_task

```python
coordinate_team_task(self: Any, team_id: str, task: str, context: Any)
```

Coordinate a task within a team based on coordination mode.

**Parameters**:

- `team_id`: Team identifier
- `task`: Task description
- `context`: Optional context

**Returns**: Coordination result

---

#### TeamCoordinator.delegate_cross_team

```python
delegate_cross_team(self: Any, from_agent_id: str, to_agent_id: str, task: str, context: Any, mediator_id: Any)
```

Delegate task across teams (requires coordination).

**Parameters**:

- `from_agent_id`: Source agent run_id
- `to_agent_id`: Target agent run_id
- `task`: Task description
- `context`: Optional context
- `mediator_id`: Optional mediator agent run_id (defaults to orchestrator)

**Returns**: Created AgentRelationship

---

#### TeamCoordinator.delegate_within_team

```python
delegate_within_team(self: Any, from_agent_id: str, to_agent_id: str, task: str, context: Any)
```

Delegate task within same team.

**Parameters**:

- `from_agent_id`: Source agent run_id
- `to_agent_id`: Target agent run_id
- `task`: Task description
- `context`: Optional context

**Returns**: Created AgentRelationship

---

#### TeamCoordinator.get_team_coordination_status

```python
get_team_coordination_status(self: Any, team_id: str)
```

Get coordination status for a team.

**Parameters**:

- `team_id`: Team identifier

**Returns**: Coordination status dictionary

---

---

## coordinate_team_task

```python
coordinate_team_task(self: Any, team_id: str, task: str, context: Any)
```

Coordinate a task within a team based on coordination mode.

**Parameters**:

- `team_id`: Team identifier
- `task`: Task description
- `context`: Optional context

**Returns**: Coordination result

---

## delegate_cross_team

```python
delegate_cross_team(self: Any, from_agent_id: str, to_agent_id: str, task: str, context: Any, mediator_id: Any)
```

Delegate task across teams (requires coordination).

**Parameters**:

- `from_agent_id`: Source agent run_id
- `to_agent_id`: Target agent run_id
- `task`: Task description
- `context`: Optional context
- `mediator_id`: Optional mediator agent run_id (defaults to orchestrator)

**Returns**: Created AgentRelationship

**Raises**:

- `ValueError`: If agents in same team or not found

---

## delegate_within_team

```python
delegate_within_team(self: Any, from_agent_id: str, to_agent_id: str, task: str, context: Any)
```

Delegate task within same team.

**Parameters**:

- `from_agent_id`: Source agent run_id
- `to_agent_id`: Target agent run_id
- `task`: Task description
- `context`: Optional context

**Returns**: Created AgentRelationship

**Raises**:

- `ValueError`: If agents not in same team

---

## get_team_coordination_status

```python
get_team_coordination_status(self: Any, team_id: str)
```

Get coordination status for a team.

**Parameters**:

- `team_id`: Team identifier

**Returns**: Coordination status dictionary

---
