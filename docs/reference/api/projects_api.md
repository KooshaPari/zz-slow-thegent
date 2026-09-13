# projects API Reference

> **Source**: `src/thegent/discovery/projects.py`

WP-11001: Cross-project discovery and context management.

---

## ContextBridger

WP-11002: Bridges context (files, state) across projects.

### Methods

#### ContextBridger.**init**

```python
__init__(self: Any, registry: ProjectRegistry)
```

---

#### ContextBridger.get_peer_context

```python
get_peer_context(self: Any, project_name: str, file_pattern: str)
```

Find files in a peer project matching a pattern.

---

---

## ProjectRegistry

Manages a registry of local projects using thegent.

### Methods

#### ProjectRegistry.**init**

```python
__init__(self: Any, global_config_dir: Path)
```

---

#### ProjectRegistry.list_projects

```python
list_projects(self: Any)
```

List all registered projects.

---

#### ProjectRegistry.register_project

```python
register_project(self: Any, path: Path, name: str)
```

Register a project path.

---

#### ProjectRegistry.update_activity

```python
update_activity(self: Any, path: Path)
```

Update last active timestamp for a project.

---

---

## get_peer_context

```python
get_peer_context(self: Any, project_name: str, file_pattern: str)
```

Find files in a peer project matching a pattern.

---

## list_projects

```python
list_projects(self: Any)
```

List all registered projects.

---

## register_project

```python
register_project(self: Any, path: Path, name: str)
```

Register a project path.

---

## update_activity

```python
update_activity(self: Any, path: Path)
```

Update last active timestamp for a project.

---
