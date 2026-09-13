# executor API Reference

> **Source**: `src/thegent/crew/executor.py`

Task and Crew executors for orchestration.

---

## AgentAssigner

Base class for agent assignment strategies.

### Methods

#### AgentAssigner.assign

```python
assign(self: Any, tasks: list[Task], agents: list[CrewAgent])
```

Assign tasks to agents.

**Parameters**:

- `tasks`: List of tasks
- `agents`: List of available agents

**Returns**: Map of task_id -> agent_id

---

---

## CrewExecutor

Orchestrates agent-task execution in crews.

Manages:

- Task-to-agent assignment
- Multi-agent coordination
- Result consolidation
- Execution orchestration

### Methods

#### CrewExecutor.**init**

```python
__init__(self: Any, crew: Crew, task_executor: Any, agent_assigner: Any)
```

Initialize CrewExecutor.

**Parameters**:

- `crew`: Crew to execute
- `task_executor`: Optional TaskExecutor (creates default if None)
- `agent_assigner`: Optional AgentAssigner (creates based on execution_mode if None)

---

#### CrewExecutor.assign_tasks_to_agents

```python
assign_tasks_to_agents(self: Any)
```

Assign tasks to agents based on execution mode.

---

#### CrewExecutor.execute

```python
execute(self: Any)
```

Execute crew tasks.

**Returns**: Map of task_id -> ExecutionResult

---

---

## ExecutionResult

Result of task execution.

---

## HierarchicalAssigner

Assign tasks hierarchically (managers/leads get priority tasks).

**Inherits from**: `AgentAssigner`

**Method Resolution Order**: `HierarchicalAssigner -> AgentAssigner`

### Methods

#### HierarchicalAssigner.assign

```python
assign(self: Any, tasks: list[Task], agents: list[CrewAgent])
```

Assign priority tasks to managers/leads, rest to workers.

---

---

## RoundRobinAssigner

Round-robin task assignment.

**Inherits from**: `AgentAssigner`

**Method Resolution Order**: `RoundRobinAssigner -> AgentAssigner`

### Methods

#### RoundRobinAssigner.assign

```python
assign(self: Any, tasks: list[Task], agents: list[CrewAgent])
```

Assign tasks round-robin.

---

---

## SkillBasedAssigner

Assign tasks based on agent skills/role.

**Inherits from**: `AgentAssigner`

**Method Resolution Order**: `SkillBasedAssigner -> AgentAssigner`

### Methods

#### SkillBasedAssigner.assign

```python
assign(self: Any, tasks: list[Task], agents: list[CrewAgent])
```

Assign tasks to agents based on role/capability matching.

---

---

## TaskExecutor

Executes tasks with dependency resolution.

Handles:

- Topological sorting of tasks
- Dependency resolution
- Task execution via agent_executor callback
- Result aggregation

### Methods

#### TaskExecutor.**init**

```python
__init__(self: Any, max_retries: int, timeout_seconds: int, agent_executor: Any)
```

Initialize TaskExecutor.

**Parameters**:

- `max_retries`: Maximum retries per task
- `timeout_seconds`: Timeout for task execution
- `agent_executor`: Callback function (agent_id, prompt, context) -> ExecutionResult

---

#### TaskExecutor.execute_all

```python
execute_all(self: Any, tasks: list[Task], task_assignments: dict[(str, str)])
```

Execute all tasks respecting dependencies.

**Parameters**:

- `tasks`: List of tasks to execute
- `task_assignments`: Map of task_id -> agent_id

**Returns**: Map of task_id -> ExecutionResult

---

#### TaskExecutor.execute_task

```python
execute_task(self: Any, task: Task, agent_id: str, context: Any)
```

Execute a single task.

**Parameters**:

- `task`: Task to execute
- `agent_id`: Agent ID to execute task
- `context`: Optional context from dependencies

**Returns**: ExecutionResult

---

#### TaskExecutor.get_task_input

```python
get_task_input(self: Any, task: Task, completed_tasks: dict[(str, ExecutionResult)])
```

Get input for task based on dependency results.

**Parameters**:

- `task`: Task to get input for
- `completed_tasks`: Map of task_id -> ExecutionResult

**Returns**: Context dictionary with dependency results

---

#### TaskExecutor.resolve_dependencies

```python
resolve_dependencies(self: Any, tasks: list[Task])
```

Resolve task dependencies using topological sort.

Returns tasks in execution order (dependencies first).

---

---

## assign

```python
assign(self: Any, tasks: list[Task], agents: list[CrewAgent])
```

Assign priority tasks to managers/leads, rest to workers.

---

## assign_tasks_to_agents

```python
assign_tasks_to_agents(self: Any)
```

Assign tasks to agents based on execution mode.

---

## execute

```python
execute(self: Any)
```

Execute crew tasks.

**Returns**: Map of task_id -> ExecutionResult

---

## execute_all

```python
execute_all(self: Any, tasks: list[Task], task_assignments: dict[(str, str)])
```

Execute all tasks respecting dependencies.

**Parameters**:

- `tasks`: List of tasks to execute
- `task_assignments`: Map of task_id -> agent_id

**Returns**: Map of task_id -> ExecutionResult

---

## execute_task

```python
execute_task(self: Any, task: Task, agent_id: str, context: Any)
```

Execute a single task.

**Parameters**:

- `task`: Task to execute
- `agent_id`: Agent ID to execute task
- `context`: Optional context from dependencies

**Returns**: ExecutionResult

---

## get_task_input

```python
get_task_input(self: Any, task: Task, completed_tasks: dict[(str, ExecutionResult)])
```

Get input for task based on dependency results.

**Parameters**:

- `task`: Task to get input for
- `completed_tasks`: Map of task_id -> ExecutionResult

**Returns**: Context dictionary with dependency results

---

## resolve_dependencies

```python
resolve_dependencies(self: Any, tasks: list[Task])
```

Resolve task dependencies using topological sort.

Returns tasks in execution order (dependencies first).

---
