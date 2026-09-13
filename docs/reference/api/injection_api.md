# injection API Reference

> **Source**: `src/thegent/mesh/injection.py`

Shell and context injection for the agent mesh.

---

## ContextInjection

Dynamic context injection (SCLI-P9.4–P9.5).

### Methods

#### ContextInjection.**init**

```python
__init__(self: Any, project_root: Path, mesh_root: Path)
```

---

#### ContextInjection.create_tool_symlinks

```python
create_tool_symlinks(self: Any, agent_id: str)
```

Create tool-specific symlinks to AGENT.md (SCLI-P9.5).

---

#### ContextInjection.update_agent_md

```python
update_agent_md(self: Any, mesh_state: dict)
```

Render AGENT.md from template with current mesh state (SCLI-P9.4).

---

---

## ShellInjection

Tmux-based shell injection (SCLI-P9.1–P9.3).

### Methods

#### ShellInjection.**init**

```python
__init__(self: Any, agent_id: str)
```

---

#### ShellInjection.find_session

```python
find_session(self: Any)
```

Detect if agent tmux session exists (SCLI-P9.1).

---

#### ShellInjection.is_ready

```python
is_ready(self: Any, prompt_pattern: str)
```

Detect if agent shell is ready for input (SCLI-P9.3).

---

#### ShellInjection.send_command

```python
send_command(self: Any, command: str, wait: float)
```

Inject command into tmux session (SCLI-P9.2).

---

---

## create_tool_symlinks

```python
create_tool_symlinks(self: Any, agent_id: str)
```

Create tool-specific symlinks to AGENT.md (SCLI-P9.5).

---

## find_session

```python
find_session(self: Any)
```

Detect if agent tmux session exists (SCLI-P9.1).

---

## is_ready

```python
is_ready(self: Any, prompt_pattern: str)
```

Detect if agent shell is ready for input (SCLI-P9.3).

---

## send_command

```python
send_command(self: Any, command: str, wait: float)
```

Inject command into tmux session (SCLI-P9.2).

---

## update_agent_md

```python
update_agent_md(self: Any, mesh_state: dict)
```

Render AGENT.md from template with current mesh state (SCLI-P9.4).

---
