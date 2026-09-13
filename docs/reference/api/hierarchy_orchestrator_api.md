# hierarchy_orchestrator API Reference

> **Source**: `src/thegent/agents/hierarchy_orchestrator.py`

Hierarchy orchestrator extending the plangent runner pattern.

Supports delegating to sub-agents with different personas,
manages context passing between hierarchy levels, and uses
structlog for structured logging.

# @trace FR-AGT-025

---

## HierarchyOrchestrator

Orchestrate work across sub-agents using the plangent DAG pattern.

The orchestrator maintains a registry of sub-agent personas and
delegates plan nodes to the appropriate sub-agent based on
metadata tags. Context is passed down through the hierarchy
via a shared context dict that accumulates results.

### Methods

#### HierarchyOrchestrator.**init**

```python
__init__(self: Any, planner: Any, executor: Any)
```

---

#### HierarchyOrchestrator.decompose

```python
decompose(self: Any, goal: str, max_depth: int)
```

Decompose a goal into a plan DAG.

**Parameters**:

- `goal`: Natural-language goal.
- `max_depth`: Maximum decomposition depth.

**Returns**: A Plan with pending nodes.

---

#### HierarchyOrchestrator.execute

```python
execute(self: Any, plan: Plan, runner: Any)
```

Execute a plan, delegating nodes to sub-agents.

**Parameters**:

- `plan`: The Plan to execute.
- `runner`: Callable (PlanNode) -&gt; str invoked for each node.

**Returns**: The mutated plan with updated statuses.

---

#### HierarchyOrchestrator.get_agent

```python
get_agent(self: Any, name: str)
```

Retrieve a registered sub-agent by name.

**Parameters**:

- `name`: Sub-agent name.

**Returns**: The SubAgentConfig.

---

#### HierarchyOrchestrator.get_context

```python
get_context(self: Any)
```

Return the current shared context dict.

---

#### HierarchyOrchestrator.list_agents

```python
list_agents(self: Any)
```

Return all registered sub-agent configs.

---

#### HierarchyOrchestrator.register_agent

```python
register_agent(self: Any, config: SubAgentConfig)
```

Register a sub-agent persona.

**Parameters**:

- `config`: Sub-agent configuration.

---

#### HierarchyOrchestrator.set_context

```python
set_context(self: Any, key: str, value: Any)
```

Set a context value to be passed down the hierarchy.

**Parameters**:

- `key`: Context key.
- `value`: Context value.

---

---

## SubAgentConfig

Configuration for a sub-agent persona.

---

## decompose

```python
decompose(self: Any, goal: str, max_depth: int)
```

Decompose a goal into a plan DAG.

**Parameters**:

- `goal`: Natural-language goal.
- `max_depth`: Maximum decomposition depth.

**Returns**: A Plan with pending nodes.

---

## execute

```python
execute(self: Any, plan: Plan, runner: Any)
```

Execute a plan, delegating nodes to sub-agents.

**Parameters**:

- `plan`: The Plan to execute.
- `runner`: Callable (PlanNode) -&gt; str invoked for each node.

**Returns**: The mutated plan with updated statuses.

---

## get_agent

```python
get_agent(self: Any, name: str)
```

Retrieve a registered sub-agent by name.

**Parameters**:

- `name`: Sub-agent name.

**Returns**: The SubAgentConfig.

**Raises**:

- `KeyError`: If the agent is not registered.

---

## get_context

```python
get_context(self: Any)
```

Return the current shared context dict.

---

## list_agents

```python
list_agents(self: Any)
```

Return all registered sub-agent configs.

---

## register_agent

```python
register_agent(self: Any, config: SubAgentConfig)
```

Register a sub-agent persona.

**Parameters**:

- `config`: Sub-agent configuration.

**Raises**:

- `ValueError`: If an agent with the same name is already registered.

---

## set_context

```python
set_context(self: Any, key: str, value: Any)
```

Set a context value to be passed down the hierarchy.

**Parameters**:

- `key`: Context key.
- `value`: Context value.

---
