# crew_executor API Reference

> **Source**: `src/thegent/agent/crew_executor.py`

Crew executor for agent execution.

---

## CrewExecutor

Execute crew tasks.

### Methods

#### CrewExecutor.**init**

```python
__init__(self: Any, crew: Any)
```

Initialize crew executor.

**Parameters**:

- `crew`: Crew instance

---

#### CrewExecutor.execute

```python
execute(self: Any, task: dict[(str, Any)])
```

Execute a task.

**Parameters**:

- `task`: Task dictionary

**Returns**: Execution result

---

#### CrewExecutor.execute_async

```python
execute_async(self: Any, task: dict[(str, Any)])
```

Execute task asynchronously.

**Parameters**:

- `task`: Task dictionary

**Returns**: Async result

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

## execute_async

```python
execute_async(self: Any, task: dict[(str, Any)])
```

Execute task asynchronously.

**Parameters**:

- `task`: Task dictionary

**Returns**: Async result

---
