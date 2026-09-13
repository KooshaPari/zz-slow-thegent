# Agents Domain Technical Specification

## Overview

The Agents domain manages AI agent lifecycle, execution, and coordination.

## Components

### Core Agent Types

| Agent Type     | Purpose               | Implementation               |
| -------------- | --------------------- | ---------------------------- |
| `DirectAgent`  | Single-task execution | `agents/direct_agents.py`    |
| `CrewAgent`    | Multi-agent crew      | `agents/crew/*.py`           |
| `UnifiedAgent` | Unified interface     | `agents/unified_registry.py` |
| `LoopAgent`    | Iterative execution   | `agents/loop_controller.py`  |
| `SmolAgent`    | Lightweight agents    | `agents/smolgents/*.py`      |

### Agent Infrastructure

| Component | Purpose          | Path                 |
| --------- | ---------------- | -------------------- |
| Registry  | Agent discovery  | `agents/registry.py` |
| Base      | Common interface | `agents/base.py`     |
| Router    | Agent selection  | `agents/routing.py`  |
| Runner    | Execution        | `agents/*_runner.py` |

## API Reference

### Agent Interface

```python
class Agent(Protocol):
    async def run(self, task: Task) -> Result: ...
    async def validate(self, input: Input) -> bool: ...
    def capabilities(self) -> list[Capability]: ...
```

### Execution Flow

```
Task → Router → Agent Selection → Execution → Result
              ↓
         Registry (capabilities)
```

## Performance

| Metric          | Target |
| --------------- | ------ |
| Agent startup   | <100ms |
| Task dispatch   | <50ms  |
| Parallel agents | 100+   |

## Dependencies

- `routing/` - Agent selection
- `orchestration/` - Task execution
- `mcp/tools/` - Tool exposure
