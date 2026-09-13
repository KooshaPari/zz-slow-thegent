# Agent Hierarchy & Harness Integration Reference

> **Quick reference for agent hierarchy implementation and harness integrations**
> **Status**: Implemented
> **Last Updated**: 2026-02-20

---

## Overview

Thegent has a multi-layered agent hierarchy system with support for multiple AI harnesses integrated via various runners.

---

## Agent Hierarchy Modules

### 1. Execution Hierarchy (`src/thegent/agents/hierarchy.py`)

**Purpose**: Live-execution hierarchy manager for running agent tasks

| Component               | Description                                                                                  |
| ----------------------- | -------------------------------------------------------------------------------------------- |
| `AgentHierarchyManager` | Main orchestrator for capability-based routing                                               |
| `AgentNode`             | Represents a node in the hierarchy tree                                                      |
| `AgentCapability`       | Enum: CODE, RESEARCH, REVIEW, TEST, DEPLOY, PLAN, SECURITY, DATA, DOCUMENTATION, ORCHESTRATE |
| `AgentState`            | Enum: IDLE, RUNNING, COMPLETED, FAILED, CANCELLED                                            |
| `RoutingStrategy`       | CAPABILITY_MATCH, ROUND_ROBIN, LEAST_LOADED                                                  |

### 2. SmolGents Integration (`src/thegent/agents/smolgents/`)

| Component   | Description                                       |
| ----------- | ------------------------------------------------- |
| `SmolAgent` | Base agent class wrapping SmolAgents framework    |
| `AgentTree` | Parent/child relationship tracking for SmolAgents |
| `tools.py`  | Tool definitions for SmolAgents                   |

**Integration Points**:

- `AgentTree` can be attached to `AgentHierarchyManager` via `smolagent` field
- Supports `MultiStepAgent`, `CodeAgent`, `ToolCallingAgent` from SmolAgents

### 3. Governance Hierarchy (`src/thegent/governance/agent_hierarchy.py`)

**Purpose**: Persistence-backed role-based hierarchy

| Component               | Description                      |
| ----------------------- | -------------------------------- |
| `AgentHierarchyManager` | JSON file-based persistence      |
| Role-based              | EXECUTIVE, TEAM_LEAD, SPECIALIST |
| Team Management         | Delegation policy enforcement    |

---

## Harness Integrations

### Available Harness Runners

| Harness             | Location           | Description                                       |
| ------------------- | ------------------ | ------------------------------------------------- |
| **Codex**           | `codex_proxy.py`   | Runs via CLIProxyAPIPlus with multi-agent support |
| **Claude Code**     | `direct_agents.py` | Direct CLI invocation                             |
| **Droid (Factory)** | `droid.py`         | Factory droid exec runner                         |
| **Cursor**          | `direct_agents.py` | Direct CLI invocation                             |
| **Copilot**         | `direct_agents.py` | Direct CLI invocation                             |
| **Gemini CLI**      | `direct_agents.py` | Direct CLI invocation                             |
| **OpenCode**        | `direct_agents.py` | Direct CLI invocation                             |
| **Crew**            | `crew/harness.py`  | Crew executor with DAG resolution                 |

### Agent CLI Mapping

```python
_AGENT_CLI = {
    "cursor-agent": ("cursor-agent", False, "--print"),
    "claude": ("claude", True, "--output-format stream-json"),
    "copilot": ("copilot", False, "--stream on"),
    "codex": ("codex", True, "--json"),
    "gemini": ("gemini", False, "--output-format stream-json"),
    "opencode": ("opencode", False, ""),
}
```

### Harness Wrapper

`_wrap_with_harness()` in `direct_agents.py` provides unified harness integration:

- Phase 2/3: Uses `thegent-hooks` Rust harness
- Fallback: Legacy `heliosShield` harness

---

## Key Files

| Path                                        | Purpose                                |
| ------------------------------------------- | -------------------------------------- |
| `src/thegent/agents/hierarchy.py`           | AgentHierarchyManager (live execution) |
| `src/thegent/agents/smolgents/base.py`      | SmolAgent base class                   |
| `src/thegent/agents/smolgents/hierarchy.py` | AgentTree for SmolGents                |
| `src/thegent/governance/agent_hierarchy.py` | Governance hierarchy                   |
| `src/thegent/agents/codex_proxy.py`         | Codex via CLIProxy                     |
| `src/thegent/agents/droid.py`               | Factory Droid runner                   |
| `src/thegent/agents/direct_agents.py`       | Direct CLI agents                      |
| `src/thegent/agents/crew/harness.py`        | Crew harness bridge                    |

---

## Related Documentation

- [HARNESS_PARITY_MATRIX.md](./HARNESS_PARITY_MATRIX.md) - Feature comparison
- [AGENT_HIERARCHY_QUICK_REFERENCE.md](../research/AGENT_HIERARCHY_QUICK_REFERENCE.md) - Roles & patterns
- [AGENT_HIERARCHY_MVP_REPORT.md](../research/AGENT_HIERARCHY_MVP_REPORT.md) - Implementation details
- [SMOLGENTS_MVP_AND_LANGGRAPH_CC_VISION.md](../research/SMOLGENTS_MVP_AND_LANGGRAPH_CC_VISION.md) - SmolGents vision
