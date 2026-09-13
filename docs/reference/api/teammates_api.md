# teammates API Reference

> **Source**: `src/thegent/governance/teammates.py`

WP-16001/16002: Thegent Teammates orchestration and delegation protocol.

---

## DelegationRequest

Record of a delegated task to a teammate.

---

## TeammateManager

Manages discovery and delegation for the teammate swarm.

### Methods

#### TeammateManager.**init**

```python
__init__(self: Any, storage_path: Path, hierarchy_manager: Any)
```

Initialize teammate manager.

**Parameters**:

- `storage_path`: Path for storing delegations (JSON file)
- `hierarchy_manager`: Optional AgentHierarchyManager for hierarchy support

---

#### TeammateManager.create_team

```python
create_team(self: Any, team_id: str, name: str, description: str, team_type: TeamType, coordination_mode: CoordinationMode, lead_id: str)
```

Create a new team.

**Parameters**:

- `team_id`: Team identifier
- `name`: Team name
- `description`: Team description
- `team_type`: Type of team
- `coordination_mode`: Coordination mode
- `lead_id`: Team lead agent run_id

**Returns**: Created AgentTeam

---

#### TeammateManager.delegate

```python
delegate(self: Any, teammate_id: str, parent_run_id: str, prompt: str, team_id: Any, relationship_type: RelationshipType)
```

WP-16002: Delegate a task to a teammate with hierarchy support.

**Parameters**:

- `teammate_id`: Teammate agent identifier
- `parent_run_id`: Parent agent run_id
- `prompt`: Task prompt
- `team_id`: Optional team identifier
- `relationship_type`: Type of relationship

**Returns**: DelegationRequest

---

#### TeammateManager.get_delegations

```python
get_delegations(self: Any, parent_run_id: Any)
```

List all delegations, optionally filtered by parent run.

---

#### TeammateManager.list_personas

```python
list_personas(self: Any)
```

WP-16001: Discover teammates from agent markdown files.

---

#### TeammateManager.update_status

```python
update_status(self: Any, req_id: str, status: str, summary: Any)
```

Update the status of a delegation.

---

---

## TeammatePersona

Specialized agent persona for the teammate swarm.

---

## create_team

```python
create_team(self: Any, team_id: str, name: str, description: str, team_type: TeamType, coordination_mode: CoordinationMode, lead_id: str)
```

Create a new team.

**Parameters**:

- `team_id`: Team identifier
- `name`: Team name
- `description`: Team description
- `team_type`: Type of team
- `coordination_mode`: Coordination mode
- `lead_id`: Team lead agent run_id

**Returns**: Created AgentTeam

---

## delegate

```python
delegate(self: Any, teammate_id: str, parent_run_id: str, prompt: str, team_id: Any, relationship_type: RelationshipType)
```

WP-16002: Delegate a task to a teammate with hierarchy support.

**Parameters**:

- `teammate_id`: Teammate agent identifier
- `parent_run_id`: Parent agent run_id
- `prompt`: Task prompt
- `team_id`: Optional team identifier
- `relationship_type`: Type of relationship

**Returns**: DelegationRequest

---

## get_delegations

```python
get_delegations(self: Any, parent_run_id: Any)
```

List all delegations, optionally filtered by parent run.

---

## list_personas

```python
list_personas(self: Any)
```

WP-16001: Discover teammates from agent markdown files.

---

## update_status

```python
update_status(self: Any, req_id: str, status: str, summary: Any)
```

Update the status of a delegation.

---
