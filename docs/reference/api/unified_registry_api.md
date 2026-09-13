# unified_registry API Reference

> **Source**: `src/thegent/agents/unified_registry.py`

Unified Agent Registry API - Core Models and Service.

Consolidates agent management across the kush ecosystem.
Reference: docs/research/UNIFIED_AGENT_REGISTRY_API.md

---

## Agent

Unified agent model.

**Inherits from**: `BaseModel`

---

## AgentCapability

Agent capabilities.

**Inherits from**: `str, Enum`

---

## AgentRegistryService

Service for managing the unified agent registry.

### Methods

#### AgentRegistryService.**init**

```python
__init__(self: Any, storage_path: Optional[str])
```

---

#### AgentRegistryService.assign_to_project

```python
assign_to_project(self: Any, agent_id: str, assignment: ProjectAssignment)
```

Assign an agent to a project.

---

#### AgentRegistryService.delete_agent

```python
delete_agent(self: Any, agent_id: str)
```

Delete agent.

---

#### AgentRegistryService.discover_best_agent

```python
discover_best_agent(self: Any, task_description: str, required_capabilities: List[AgentCapability], project_id: Optional[str])
```

Discovery logic to find best agent for task.

---

#### AgentRegistryService.get_agent

```python
get_agent(self: Any, agent_id: str)
```

Get agent by ID.

---

#### AgentRegistryService.list_agents

```python
list_agents(self: Any, status: Optional[AgentStatus], project_id: Optional[str], capability: Optional[AgentCapability])
```

List agents with optional filtering.

---

#### AgentRegistryService.register_agent

```python
register_agent(self: Any, agent: Agent)
```

Register a new agent.

---

#### AgentRegistryService.update_agent

```python
update_agent(self: Any, agent_id: str, updates: Dict[(str, Any)])
```

Update agent metadata.

---

#### AgentRegistryService.update_collaboration_rules

```python
update_collaboration_rules(self: Any, agent_id: str, rules: CollaborationRule)
```

Update collaboration rules for an agent.

---

#### AgentRegistryService.update_metrics

```python
update_metrics(self: Any, agent_id: str, metrics_update: Dict[(str, Any)])
```

Update performance metrics for an agent.

---

---

## AgentStatus

Agent status.

**Inherits from**: `str, Enum`

---

## Availability

Agent availability.

**Inherits from**: `BaseModel`

---

## CollaborationRule

Collaboration rules.

**Inherits from**: `BaseModel`

---

## PerformanceMetrics

Performance metrics.

**Inherits from**: `BaseModel`

---

## ProjectAssignment

Project assignment.

**Inherits from**: `BaseModel`

---

## assign_to_project

```python
assign_to_project(self: Any, agent_id: str, assignment: ProjectAssignment)
```

Assign an agent to a project.

---

## delete_agent

```python
delete_agent(self: Any, agent_id: str)
```

Delete agent.

---

## discover_best_agent

```python
discover_best_agent(self: Any, task_description: str, required_capabilities: List[AgentCapability], project_id: Optional[str])
```

Discovery logic to find best agent for task.

---

## get_agent

```python
get_agent(self: Any, agent_id: str)
```

Get agent by ID.

---

## list_agents

```python
list_agents(self: Any, status: Optional[AgentStatus], project_id: Optional[str], capability: Optional[AgentCapability])
```

List agents with optional filtering.

---

## register_agent

```python
register_agent(self: Any, agent: Agent)
```

Register a new agent.

---

## update_agent

```python
update_agent(self: Any, agent_id: str, updates: Dict[(str, Any)])
```

Update agent metadata.

---

## update_collaboration_rules

```python
update_collaboration_rules(self: Any, agent_id: str, rules: CollaborationRule)
```

Update collaboration rules for an agent.

---

## update_metrics

```python
update_metrics(self: Any, agent_id: str, metrics_update: Dict[(str, Any)])
```

Update performance metrics for an agent.

---
