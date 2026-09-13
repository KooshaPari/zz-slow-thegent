# Database & Storage Specification

## Overview

thegent uses multiple storage mechanisms depending on use case.

## Storage Mechanisms

### 1. File-Based Storage

| Store                | Format    | Use Case            |
| -------------------- | --------- | ------------------- |
| Session logs         | JSONL     | Audit/telemetry     |
| Conversation history | JSONL     | Session persistence |
| Tool cache           | JSON      | Tool definitions    |
| Policy files         | YAML/TOML | Configuration       |

### 2. Database Systems

| Database      | Use               | Files                  |
| ------------- | ----------------- | ---------------------- |
| SQLite        | Local cache       | `cache/`               |
| Redis         | Distributed state | `orchestration/state/` |
| Shared memory | IPC               | `native/state_shm.py`  |

### 3. Core Entities

#### Session

```python
@dataclass
class Session:
    id: str
    agent_id: str
    state: SessionState
    created_at: datetime
    updated_at: datetime
```

#### Task

```python
@dataclass
class Task:
    id: str
    session_id: str
    status: TaskStatus
    result: Any
    error: str | None
```

#### Agent

```python
@dataclass
class Agent:
    id: str
    capabilities: list[str]
    state: AgentState
    last_seen: datetime
```

#### Tool

```python
@dataclass
class Tool:
    name: str
    description: str
    schema: dict
    handler: str  # module.path
```

#### Policy

```python
@dataclass
class Policy:
    id: str
    rules: list[Rule]
    version: str
    enabled: bool
```

## Migration Paths

| From         | To            | Status |
| ------------ | ------------- | ------ |
| JSONL files  | SQLite        | P1     |
| YAML configs | TOML          | P2     |
| In-memory    | Redis cluster | P2     |

## Performance

| Store  | Latency | Throughput |
| ------ | ------- | ---------- |
| SHM    | <1ms    | 100k ops/s |
| Redis  | <5ms    | 10k ops/s  |
| SQLite | <10ms   | 1k ops/s   |
| JSONL  | <50ms   | 100 ops/s  |
