# git_enhance API Reference

> **Source**: `src/thegent/hooks/git_enhance.py`

Enhance git subcommand: TTL caching, lock detection, agent passthrough.

---

## GitEnhance

Enhanced git subcommand with caching and lock detection.

### Methods

#### GitEnhance.**init**

```python
__init__(self: Any, ttl_seconds: int)
```

Initialize git enhance.

**Parameters**:

- `ttl_seconds`: TTL for cache in seconds

---

#### GitEnhance.detect_lock

```python
detect_lock(self: Any, repo_path: str)
```

Detect if repository is locked.

**Parameters**:

- `repo_path`: Repository path

**Returns**: True if locked

---

#### GitEnhance.git_status

```python
git_status(self: Any, repo_path: str, use_cache: bool)
```

Get git status with caching.

**Parameters**:

- `repo_path`: Repository path
- `use_cache`: Use cache if available

**Returns**: Git status dictionary

---

#### GitEnhance.passthrough_to_agent

```python
passthrough_to_agent(self: Any, command: str, args: list[str])
```

Passthrough git command to agent.

**Parameters**:

- `command`: Git command
- `args`: Command arguments

**Returns**: Execution result

---

---

## detect_lock

```python
detect_lock(self: Any, repo_path: str)
```

Detect if repository is locked.

**Parameters**:

- `repo_path`: Repository path

**Returns**: True if locked

---

## git_status

```python
git_status(self: Any, repo_path: str, use_cache: bool)
```

Get git status with caching.

**Parameters**:

- `repo_path`: Repository path
- `use_cache`: Use cache if available

**Returns**: Git status dictionary

---

## passthrough_to_agent

```python
passthrough_to_agent(self: Any, command: str, args: list[str])
```

Passthrough git command to agent.

**Parameters**:

- `command`: Git command
- `args`: Command arguments

**Returns**: Execution result

---
