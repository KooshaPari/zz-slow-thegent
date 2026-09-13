# loop_controller API Reference

> **Source**: `src/thegent/agents/loop_controller.py`

Lifecycle Loop Controller with Checker Agent oversight.

---

## LifecycleController

Handles agent execution loops (Ralph Wiggum loops) with Checker Agent oversight.

### Methods

#### LifecycleController.**init**

```python
__init__(self: Any, settings: ThegentSettings, worker_agent_name: str, checker_agent_name: str, mode: LoopMode, max_iterations: int, worker_model: Any, task_id: Any, verification_callback: Any)
```

---

#### LifecycleController.run_loop

```python
run_loop(self: Any, initial_prompt: str, todo_spec: str, on_worker_output: Any, on_progress: Any)
```

Execute the Lifecycle loop.

---

---

## LoopMode

Lifecycle loop modes.

**Inherits from**: `StrEnum`

---

## LoopState

Current state of a Lifecycle loop.

**Inherits from**: `BaseModel`

---

## run_loop

```python
run_loop(self: Any, initial_prompt: str, todo_spec: str, on_worker_output: Any, on_progress: Any)
```

Execute the Lifecycle loop.

---
