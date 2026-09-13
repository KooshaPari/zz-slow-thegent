# agent_hierarchy API Reference

> **Source**: `src/thegent/governance/agent_hierarchy.py`

WP-16001+: Agent hierarchy management and team coordination.

Manages agent hierarchies, parent-child relationships, and team structures.

---

## AgentHierarchyManager

Manages agent hierarchy, relationships, and teams.

### Methods

#### AgentHierarchyManager.**init**

```python
__init__(self: Any, storage_path: Path)
```

Initialize hierarchy manager.

**Parameters**:

- `storage_path`: Base path for storage (creates hierarchy.json, teams.json, relationships.json)

---

#### AgentHierarchyManager.add_team_member

```python
add_team_member(self: Any, team_id: str, agent_run_id: str)
```

Add member to team.

---

#### AgentHierarchyManager.can_delegate

```python
can_delegate(self: Any, from_agent_id: str, to_agent_id: str, task_context: Any)
```

Check if agent can delegate to another agent.

**Parameters**:

- `from_agent_id`: Source agent run_id
- `to_agent_id`: Target agent run_id
- `task_context`: Optional task context

**Returns**: True if delegation is allowed

---

#### AgentHierarchyManager.check_team_consistency

```python
check_team_consistency(self: Any)
```

Check team consistency (members match team membership, leads exist, etc.).

**Returns**: List of tuples (team_id, error_message) for inconsistent teams

---

#### AgentHierarchyManager.create_relationship

```python
create_relationship(self: Any, parent_id: str, child_id: str, relationship_type: RelationshipType, task_id: Any, delegation_prompt: Any, handoff_context: Any)
```

Create a relationship between agents.

**Parameters**:

- `parent_id`: Parent agent run_id
- `child_id`: Child agent run_id
- `relationship_type`: Type of relationship
- `task_id`: Optional task identifier
- `delegation_prompt`: Optional delegation prompt
- `handoff_context`: Optional handoff context

**Returns**: Created AgentRelationship

---

#### AgentHierarchyManager.create_team

```python
create_team(self: Any, team_id: str, name: str, description: str, team_type: TeamType, coordination_mode: CoordinationMode, lead_id: str, boundaries: Any, communication_channels: Any)
```

Create a new team.

**Parameters**:

- `team_id`: Unique team identifier
- `name`: Team name
- `description`: Team description
- `team_type`: Type of team
- `coordination_mode`: Coordination mode
- `lead_id`: Team lead agent run_id
- `boundaries`: Optional team boundaries
- `communication_channels`: Optional communication channels

**Returns**: Created AgentTeam

---

#### AgentHierarchyManager.detect_circular_relationships

```python
detect_circular_relationships(self: Any, start_id: str)
```

Detect circular relationships in the hierarchy starting from an agent.

**Parameters**:

- `start_id`: Starting agent run_id

**Returns**: List of agent IDs forming a cycle, empty if no cycle found

---

#### AgentHierarchyManager.detect_orphaned_agents

```python
detect_orphaned_agents(self: Any)
```

Detect agents with invalid parent references (orphaned agents).

**Returns**: List of tuples (agent_id, error_message) for orphaned agents

---

#### AgentHierarchyManager.get_agent

```python
get_agent(self: Any, run_id: str)
```

Get agent by run_id.

---

#### AgentHierarchyManager.get_ancestors

```python
get_ancestors(self: Any, agent_id: str)
```

Get all ancestors of an agent (parent chain).

---

#### AgentHierarchyManager.get_children

```python
get_children(self: Any, parent_id: str)
```

Get all direct children of an agent.

---

#### AgentHierarchyManager.get_descendants

```python
get_descendants(self: Any, agent_id: str)
```

Get all descendants of an agent (all children recursively).

---

#### AgentHierarchyManager.get_hierarchy_tree

```python
get_hierarchy_tree(self: Any, root_id: Any)
```

Get hierarchy tree structure.

**Parameters**:

- `root_id`: Optional root agent run_id (defaults to finding root)

**Returns**: Tree structure as nested dictionary

---

#### AgentHierarchyManager.get_team

```python
get_team(self: Any, team_id: str)
```

Get team by team_id.

---

#### AgentHierarchyManager.get_team_members

```python
get_team_members(self: Any, team_id: str)
```

Get all members of a team.

---

#### AgentHierarchyManager.list_all_agents

```python
list_all_agents(self: Any)
```

List all registered agents.

---

#### AgentHierarchyManager.list_all_relationships

```python
list_all_relationships(self: Any)
```

List all relationships.

---

#### AgentHierarchyManager.list_all_teams

```python
list_all_teams(self: Any)
```

List all teams.

---

#### AgentHierarchyManager.register_agent

```python
register_agent(self: Any, agent_id: str, run_id: str, role: AgentRole, parent_id: Any, team_id: Any, validate: bool)
```

Register a new agent in the hierarchy.

**Parameters**:

- `agent_id`: Agent identifier (e.g., "coder", "researcher")
- `run_id`: Unique run identifier
- `role`: Agent role level
- `parent_id`: Optional parent agent run_id
- `team_id`: Optional team identifier
- `validate`: Whether to validate before registering (default: True)

**Returns**: Created AgentNode

---

#### AgentHierarchyManager.remove_team_member

```python
remove_team_member(self: Any, team_id: str, agent_run_id: str)
```

Remove member from team.

---

#### AgentHierarchyManager.update_agent_status

```python
update_agent_status(self: Any, run_id: str, status: str)
```

Update agent status.

---

#### AgentHierarchyManager.update_team_status

```python
update_team_status(self: Any, team_id: str, status: str)
```

Update team status.

---

#### AgentHierarchyManager.validate_agent_id

```python
validate_agent_id(self: Any, agent_id: str)
```

Validate that an agent ID exists and is valid.

**Parameters**:

- `agent_id`: Agent run_id to validate

**Returns**: Tuple of (is_valid, error_message)

---

#### AgentHierarchyManager.validate_before_register

```python
validate_before_register(self: Any, agent_id: str, run_id: str, parent_id: Any, team_id: Any)
```

Validate before registering a new agent.

**Parameters**:

- `agent_id`: Agent identifier
- `run_id`: Unique run identifier
- `parent_id`: Optional parent agent run_id
- `team_id`: Optional team identifier

**Returns**: Tuple of (is_valid, error_message)

---

---

## AgentNode

Represents an agent in the hierarchy.

### Methods

#### AgentNode.from_dict

```python
from_dict(cls: Any, data: dict[(str, Any)])
```

Create from dictionary.

---

#### AgentNode.to_dict

```python
to_dict(self: Any)
```

Convert to dictionary for serialization.

---

---

## AgentRelationship

Parent-child relationship between agents.

### Methods

#### AgentRelationship.from_dict

```python
from_dict(cls: Any, data: dict[(str, Any)])
```

Create from dictionary.

---

#### AgentRelationship.to_dict

```python
to_dict(self: Any)
```

Convert to dictionary for serialization.

---

---

## AgentRole

Agent role levels.

**Inherits from**: `Enum`

---

## AgentTeam

A team of agents working together.

### Methods

#### AgentTeam.from_dict

```python
from_dict(cls: Any, data: dict[(str, Any)])
```

Create from dictionary.

---

#### AgentTeam.to_dict

```python
to_dict(self: Any)
```

Convert to dictionary for serialization.

---

---

## CoordinationMode

Team coordination modes.

**Inherits from**: `Enum`

---

## RelationshipType

Types of agent relationships.

**Inherits from**: `Enum`

---

## TeamType

Types of teams.

**Inherits from**: `Enum`

---

## add_team_member

```python
add_team_member(self: Any, team_id: str, agent_run_id: str)
```

Add member to team.

---

## build_tree

```python
build_tree(node: AgentNode) -> dict[(str, Any)]
```

---

## can_delegate

```python
can_delegate(self: Any, from_agent_id: str, to_agent_id: str, task_context: Any)
```

Check if agent can delegate to another agent.

**Parameters**:

- `from_agent_id`: Source agent run_id
- `to_agent_id`: Target agent run_id
- `task_context`: Optional task context

**Returns**: True if delegation is allowed

---

## check_team_consistency

```python
check_team_consistency(self: Any)
```

Check team consistency (members match team membership, leads exist, etc.).

**Returns**: List of tuples (team_id, error_message) for inconsistent teams

---

## collect_descendants

```python
collect_descendants(node: AgentNode) -> None
```

---

## create_relationship

```python
create_relationship(self: Any, parent_id: str, child_id: str, relationship_type: RelationshipType, task_id: Any, delegation_prompt: Any, handoff_context: Any)
```

Create a relationship between agents.

**Parameters**:

- `parent_id`: Parent agent run_id
- `child_id`: Child agent run_id
- `relationship_type`: Type of relationship
- `task_id`: Optional task identifier
- `delegation_prompt`: Optional delegation prompt
- `handoff_context`: Optional handoff context

**Returns**: Created AgentRelationship

---

## create_team

```python
create_team(self: Any, team_id: str, name: str, description: str, team_type: TeamType, coordination_mode: CoordinationMode, lead_id: str, boundaries: Any, communication_channels: Any)
```

Create a new team.

**Parameters**:

- `team_id`: Unique team identifier
- `name`: Team name
- `description`: Team description
- `team_type`: Type of team
- `coordination_mode`: Coordination mode
- `lead_id`: Team lead agent run_id
- `boundaries`: Optional team boundaries
- `communication_channels`: Optional communication channels

**Returns**: Created AgentTeam

---

## detect_circular_relationships

```python
detect_circular_relationships(self: Any, start_id: str)
```

Detect circular relationships in the hierarchy starting from an agent.

**Parameters**:

- `start_id`: Starting agent run_id

**Returns**: List of agent IDs forming a cycle, empty if no cycle found

---

## detect_orphaned_agents

```python
detect_orphaned_agents(self: Any)
```

Detect agents with invalid parent references (orphaned agents).

**Returns**: List of tuples (agent_id, error_message) for orphaned agents

---

## dfs

```python
dfs(node_id: str) -> bool
```

---

## from_dict

```python
from_dict(cls: Any, data: dict[(str, Any)])
```

Create from dictionary.

---

## get_agent

```python
get_agent(self: Any, run_id: str)
```

Get agent by run_id.

---

## get_ancestors

```python
get_ancestors(self: Any, agent_id: str)
```

Get all ancestors of an agent (parent chain).

---

## get_children

```python
get_children(self: Any, parent_id: str)
```

Get all direct children of an agent.

---

## get_descendants

```python
get_descendants(self: Any, agent_id: str)
```

Get all descendants of an agent (all children recursively).

---

## get_hierarchy_tree

```python
get_hierarchy_tree(self: Any, root_id: Any)
```

Get hierarchy tree structure.

**Parameters**:

- `root_id`: Optional root agent run_id (defaults to finding root)

**Returns**: Tree structure as nested dictionary

---

## get_team

```python
get_team(self: Any, team_id: str)
```

Get team by team_id.

---

## get_team_members

```python
get_team_members(self: Any, team_id: str)
```

Get all members of a team.

---

## list_all_agents

```python
list_all_agents(self: Any)
```

List all registered agents.

---

## list_all_relationships

```python
list_all_relationships(self: Any)
```

List all relationships.

---

## list_all_teams

```python
list_all_teams(self: Any)
```

List all teams.

---

## register_agent

```python
register_agent(self: Any, agent_id: str, run_id: str, role: AgentRole, parent_id: Any, team_id: Any, validate: bool)
```

Register a new agent in the hierarchy.

**Parameters**:

- `agent_id`: Agent identifier (e.g., "coder", "researcher")
- `run_id`: Unique run identifier
- `role`: Agent role level
- `parent_id`: Optional parent agent run_id
- `team_id`: Optional team identifier
- `validate`: Whether to validate before registering (default: True)

**Returns**: Created AgentNode

**Raises**:

- `ValueError`: If validation fails

---

## remove_team_member

```python
remove_team_member(self: Any, team_id: str, agent_run_id: str)
```

Remove member from team.

---

## to_dict

```python
to_dict(self: Any)
```

Convert to dictionary for serialization.

---

## update_agent_status

```python
update_agent_status(self: Any, run_id: str, status: str)
```

Update agent status.

---

## update_team_status

```python
update_team_status(self: Any, team_id: str, status: str)
```

Update team status.

---

## validate_agent_id

```python
validate_agent_id(self: Any, agent_id: str)
```

Validate that an agent ID exists and is valid.

**Parameters**:

- `agent_id`: Agent run_id to validate

**Returns**: Tuple of (is_valid, error_message)

---

## validate_before_register

```python
validate_before_register(self: Any, agent_id: str, run_id: str, parent_id: Any, team_id: Any)
```

Validate before registering a new agent.

**Parameters**:

- `agent_id`: Agent identifier
- `run_id`: Unique run identifier
- `parent_id`: Optional parent agent run_id
- `team_id`: Optional team identifier

**Returns**: Tuple of (is_valid, error_message)

---
