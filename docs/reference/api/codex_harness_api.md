# codex_harness API Reference

> **Source**: `src/thegent/agent/codex_harness.py`

Wire codex/cc/droid harness as agent_executor for Crew.

---

## CCHarness

CC (Claude Code) harness for agent execution.

### Methods

#### CCHarness.**init**

```python
__init__(self: Any)
```

Initialize CC harness.

---

#### CCHarness.execute

```python
execute(self: Any, task: dict[(str, Any)])
```

Execute a task.

**Parameters**:

- `task`: Task dictionary

**Returns**: Execution result

---

---

## CodexHarness

Codex harness for agent execution.

### Methods

#### CodexHarness.**init**

```python
__init__(self: Any)
```

Initialize codex harness.

---

#### CodexHarness.execute

```python
execute(self: Any, agent_id: str, task: dict[(str, Any)])
```

Execute a task with an agent.

**Parameters**:

- `agent_id`: Agent identifier
- `task`: Task dictionary

**Returns**: Execution result

---

#### CodexHarness.register_agent

```python
register_agent(self: Any, agent_id: str, agent_executor: Any)
```

Register an agent executor.

**Parameters**:

- `agent_id`: Agent identifier
- `agent_executor`: Agent executor instance

---

---

## DroidHarness

Droid harness for agent execution.

### Methods

#### DroidHarness.**init**

```python
__init__(self: Any)
```

Initialize droid harness.

---

#### DroidHarness.execute

```python
execute(self: Any, task: dict[(str, Any)])
```

Execute a task.

**Parameters**:

- `task`: Task dictionary

**Returns**: Execution result

---

---

## HarnessAdapter

Adapter to wire harnesses as agent_executor for Crew.

### Methods

#### HarnessAdapter.**init**

```python
__init__(self: Any)
```

Initialize harness adapter.

---

#### HarnessAdapter.get_executor

```python
get_executor(self: Any, harness_type: str)
```

Get executor for a harness type.

**Parameters**:

- `harness_type`: Type of harness (codex, cc, droid)

**Returns**: Executor instance

---

#### HarnessAdapter.wire_to_crew

```python
wire_to_crew(self: Any, crew: Any, harness_type: str)
```

Wire harness to crew as agent_executor.

**Parameters**:

- `crew`: Crew instance
- `harness_type`: Type of harness to use

---

---

## execute

```python
execute(self: Any, task: dict[(str, Any)])
```

Execute a task.

**Parameters**:

- `task`: Task dictionary

**Returns**: Execution result

---

## get_executor

```python
get_executor(self: Any, harness_type: str)
```

Get executor for a harness type.

**Parameters**:

- `harness_type`: Type of harness (codex, cc, droid)

**Returns**: Executor instance

---

## register_agent

```python
register_agent(self: Any, agent_id: str, agent_executor: Any)
```

Register an agent executor.

**Parameters**:

- `agent_id`: Agent identifier
- `agent_executor`: Agent executor instance

---

## wire_to_crew

```python
wire_to_crew(self: Any, crew: Any, harness_type: str)
```

Wire harness to crew as agent_executor.

**Parameters**:

- `crew`: Crew instance
- `harness_type`: Type of harness to use

---
