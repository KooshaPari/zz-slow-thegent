# Phase 1: Agent Identity System - Quick Reference

**TL;DR:** Global agent registry with unique IDs and hierarchical relationships

---

## One-Minute Overview

```
Every agent gets a unique ID:  {project}:{uuid}:L{1-3}:{role}
Example:                       thegent:abc123:L2:builder

Registry location:             ~/.claude/civilization/registry.json

Hierarchy:                      L1 (Lead) → L2 (Workers) → L3 (Executors)

Discovery:                      registry.get_agents_by_project("thegent")
```

---

## Quick Start

### Import

```python
from agent_identity_system import (
    GlobalAgentRegistry,
    AgentIdentityFactory,
    AgentLevel,
    AgentRole,
)
```

### Initialize

```python
registry = GlobalAgentRegistry()
factory = AgentIdentityFactory(registry)
```

### Create Agents

```python
# L1: Strategic leader
l1 = factory.create_l1_agent("thegent", AgentRole.COORDINATOR)

# L2: Named worker with parent
l2 = factory.create_l2_agent("thegent", AgentRole.BUILDER, l1.agent_id)

# L3: Executor with parent
l3 = factory.create_l3_agent("thegent", l2.agent_id)
```

---

## Common Operations

| Operation           | Code                                                    | Returns                 |
| ------------------- | ------------------------------------------------------- | ----------------------- |
| Get agent           | `registry.get_agent(agent_id)`                          | `AgentIdentity \| None` |
| Find all in project | `registry.get_agents_by_project("thegent")`             | `List[AgentIdentity]`   |
| Find all L1 leaders | `registry.get_agents_by_level(AgentLevel.L1_STRATEGIC)` | `List[AgentIdentity]`   |
| Find by role        | `registry.get_agents_by_role(AgentRole.BUILDER)`        | `List[AgentIdentity]`   |
| Get hierarchy       | `registry.get_hierarchy(l1_agent_id)`                   | `Dict[str, Any]`        |
| Heartbeat ping      | `registry.update_heartbeat(agent_id)`                   | `bool`                  |
| Find stale          | `registry.get_stale_agents(ttl_seconds=300)`            | `List[AgentIdentity]`   |
| Statistics          | `registry.get_stats()`                                  | `Dict[str, int]`        |

---

## Agent Roles

| Role          | Use Case                                   |
| ------------- | ------------------------------------------ |
| `COORDINATOR` | Orchestration, scheduling, decision-making |
| `RESEARCHER`  | Investigation, analysis, discovery         |
| `BUILDER`     | Implementation, construction, execution    |
| `INTEGRATOR`  | Integration, coordination, testing         |
| `MONITOR`     | Observation, health checks, metrics        |
| `GENERIC`     | Default for L3 executors                   |

---

## Agent Levels

| Level  | Example      | Capabilities                          |
| ------ | ------------ | ------------------------------------- |
| **L1** | Coordinator  | Orchestration, monitoring, escalation |
| **L2** | Named Worker | Component execution, sub-delegation   |
| **L3** | Executor     | Task execution, reporting             |

---

## Agent ID Format

```
{project}:{uuid}:L{level}:{role}

Parts:
- project: "thegent", "kush", etc.
- uuid: 8-character random hex
- level: L1, L2, or L3
- role: coordinator, builder, researcher, etc.

Examples:
- thegent:abc123:L1:coordinator
- kush:def456:L2:builder
- thegent:ghi789:L3:generic
```

---

## Accessing Agent Properties

```python
agent = registry.get_agent(agent_id)

# Identity
agent.project  # "thegent"
agent.uuid  # "abc123"
agent.level  # AgentLevel.L1_STRATEGIC
agent.role  # AgentRole.COORDINATOR
agent.agent_id  # Full ID string

# Relationships
agent.parent_agent_id  # Parent L1/L2 ID (or None)
agent.child_agent_ids  # List of child IDs
agent.peer_agent_ids  # Peer agents at same level

# Status
agent.is_active  # True/False
agent.status_message  # "healthy", etc.
agent.last_heartbeat  # Unix timestamp

# Metadata
agent.capabilities  # ["orchestration", "monitoring"]
agent.scope_tags  # {"tier": "strategic"}
```

---

## Registry Statistics

```python
stats = registry.get_stats()

# Structure
{
    "total_agents": 10,
    "active_agents": 9,
    "stale_agents": 1,
    "by_level": {"L1": 2, "L2": 5, "L3": 3},
    "by_role": {"coordinator": 2, "builder": 3, ...},
    "by_project": {"thegent": 6, "kush": 4}
}
```

---

## Hierarchy Retrieval

```python
# Get full hierarchy from L1
hierarchy = registry.get_hierarchy(l1_agent_id, levels=3)

# Structure
{
    "agent_id": "thegent:abc123:L1:coordinator",
    "identity": {...full AgentIdentity dict...},
    "children": [
        {
            "agent_id": "thegent:def456:L2:builder",
            "identity": {...},
            "children": [
                {
                    "agent_id": "thegent:ghi789:L3:generic",
                    "identity": {...},
                    "children": []
                }
            ]
        }
    ]
}
```

---

## Filtering Examples

```python
# All agents in a project
thegent_agents = registry.get_agents_by_project("thegent")

# All strategic leaders
leaders = registry.get_agents_by_level(AgentLevel.L1_STRATEGIC)

# All researchers
researchers = registry.get_agents_by_role(AgentRole.RESEARCHER)

# All active agents
active = registry.get_active_agents()

# Stale agents (no heartbeat for 5+ min)
stale = registry.get_stale_agents(ttl_seconds=300)
```

---

## Heartbeat Management

```python
# Update agent as alive
registry.update_heartbeat(agent_id)  # Sets last_heartbeat to now

# Check if stale (hasn't updated in 5 minutes)
stale = registry.get_stale_agents(ttl_seconds=300)

# Check individual agent
agent = registry.get_agent(agent_id)
time_since_heartbeat = time.time() - agent.last_heartbeat
```

---

## Serialization

```python
# Convert to dictionary
agent_dict = agent.to_dict()

# Save to JSON
json_str = json.dumps(agent_dict)

# Load from dictionary
new_agent = AgentIdentity.from_dict(agent_dict)

# Full roundtrip
agent1 = factory.create_l1_agent("test")
data = agent1.to_dict()
agent2 = AgentIdentity.from_dict(data)
assert agent1.agent_id == agent2.agent_id  # ✅ True
```

---

## Testing

```python
# Run tests
python3 -m unittest scripts.test_agent_identity_system -v

# Expected output
Ran 17 tests in 0.187s
OK ✅

# Test categories
- AgentIdentity: 4 tests
- GlobalAgentRegistry: 10 tests
- AgentIdentityFactory: 4 tests
```

---

## Files

| File                                                              | Purpose                                |
| ----------------------------------------------------------------- | -------------------------------------- |
| `scripts/agent_identity_system.py`                                | Core implementation (427 LOC)          |
| `scripts/test_agent_identity_system.py`                           | Test suite (361 LOC, 17 tests)         |
| `~/.claude/civilization/registry.json`                            | Global registry (created on first use) |
| `docs/reference/PHASE_1_AGENT_IDENTITY_IMPLEMENTATION.md`         | Full documentation                     |
| `docs/guides/INTEGRATING_AGENT_IDENTITY_WITH_SWARM_CONTROLLER.md` | Integration guide                      |

---

## Common Errors & Fixes

| Error                        | Cause                 | Fix                                               |
| ---------------------------- | --------------------- | ------------------------------------------------- |
| `FileNotFoundError`          | Registry path missing | Check `~/.claude/civilization/` exists            |
| `agent_id` is `None`         | Agent not registered  | Call `factory.create_*_agent()` first             |
| `get_agent()` returns `None` | Wrong agent ID        | Check ID format: `{project}:{uuid}:L{1-3}:{role}` |
| Stale agents not cleaned     | Cleanup not called    | Add `registry.unregister_agent()` in cleanup loop |

---

## Integration Checklist

- [ ] Import agent identity system
- [ ] Create registry instance
- [ ] Create factory instance
- [ ] Register L1 agent on startup
- [ ] Auto-register L2/L3 agents as discovered
- [ ] Update heartbeats during monitoring
- [ ] Cleanup stale agents periodically
- [ ] Query registry for stats/reports

---

## Performance Notes

- **Registry load:** ~1ms per operation
- **Memory:** ~1 KB per agent
- **Disk I/O:** Sync on every write (can optimize with batching)
- **Scale limit:** ~1000 agents (file-based). Switch to DB for larger.

---

## Next Steps

1. Integrate with SwarmController (see integration guide)
2. Implement Phase 2: Service Discovery
3. Add MCP transport for real-time updates
4. Build cross-project communication

---

**Last Updated:** 2026-02-19
**Version:** 1.0
**Status:** Production Ready ✅
