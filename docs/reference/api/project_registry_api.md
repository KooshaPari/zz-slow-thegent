# project_registry API Reference

> **Source**: `src/thegent/registry/project_registry.py`

SQLite-backed project registry for hierarchical versioning.

Tracks projects and episodes (atomic units of agent work) in a local
SQLite database with WAL mode for concurrent-safe atomic writes.

WBS: wp-71001-registry-db
FR Traceability: FR-VER-001 (project registry and episode tracking)

---

## EpisodeRecord

An episode: one atomic unit of agent work.

**Inherits from**: `BaseModel`

---

## EpisodeStatus

Lifecycle status for an agent episode.

**Inherits from**: `StrEnum`

---

## ProjectRecord

A registered project in the hierarchy.

**Inherits from**: `BaseModel`

---

## ProjectRegistry

SQLite-backed registry for projects and episodes.

Uses WAL journal mode for safe concurrent reads/writes.

### Methods

#### ProjectRegistry.**init**

```python
__init__(self: Any, db_path: Any)
```

---

#### ProjectRegistry.create_episode

```python
create_episode(self: Any, project_id: str, agent_id: str, metadata: Any)
```

Create a new running episode for the given project.

---

#### ProjectRegistry.get_episodes_for_project

```python
get_episodes_for_project(self: Any, project_id: str)
```

Return all episodes for a given project, ordered by start time.

---

#### ProjectRegistry.get_project

```python
get_project(self: Any, project_id: str)
```

Retrieve a project by ID, or None if not found.

---

#### ProjectRegistry.list_projects

```python
list_projects(self: Any)
```

Return all registered projects.

---

#### ProjectRegistry.register_project

```python
register_project(self: Any, name: str, path: str, metadata: Any)
```

Register a new project and persist it.

---

#### ProjectRegistry.update_episode

```python
update_episode(self: Any, episode_id: str, status: Any, metadata: Any)
```

Update an episode's status and/or metadata.

Returns the updated record, or None if the episode does not exist.
For terminal statuses (completed, failed), `ended_at` is set automatically.

---

#### ProjectRegistry.update_project_metadata

```python
update_project_metadata(self: Any, project_id: str, metadata: dict[(str, Any)])
```

Merge _metadata_ into the project's existing metadata.

Returns the updated record, or None if the project does not exist.

---

---

## create_episode

```python
create_episode(self: Any, project_id: str, agent_id: str, metadata: Any)
```

Create a new running episode for the given project.

---

## get_episodes_for_project

```python
get_episodes_for_project(self: Any, project_id: str)
```

Return all episodes for a given project, ordered by start time.

---

## get_project

```python
get_project(self: Any, project_id: str)
```

Retrieve a project by ID, or None if not found.

---

## list_projects

```python
list_projects(self: Any)
```

Return all registered projects.

---

## register_project

```python
register_project(self: Any, name: str, path: str, metadata: Any)
```

Register a new project and persist it.

---

## update_episode

```python
update_episode(self: Any, episode_id: str, status: Any, metadata: Any)
```

Update an episode's status and/or metadata.

Returns the updated record, or None if the episode does not exist.
For terminal statuses (completed, failed), `ended_at` is set automatically.

---

## update_project_metadata

```python
update_project_metadata(self: Any, project_id: str, metadata: dict[(str, Any)])
```

Merge _metadata_ into the project's existing metadata.

Returns the updated record, or None if the project does not exist.

---
