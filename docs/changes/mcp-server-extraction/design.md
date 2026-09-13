---
title: MCP Server Tool Extraction — Design
date: 2026-02-21
status: implemented
owner: agent-f (B90-W2-F1)
tags: [wl-126, b90, monolith-split, mcp]
---

# Design: MCP Server Tool Extraction

## New Module Layout

```
src/thegent/mcp/
├── server.py              # Registrar + lifespan + middleware (3,939 lines)
│                          # Loads tool groups via _load_server_tools_*_module()
├── server_catalog_tools.py # Catalog tool group (direct import)
├── server_dispatch_helpers.py
├── server_elicitation_cache_helpers.py
├── server_elicitation_response_helpers.py
├── server_meta_helpers.py
├── server_module_loader.py
├── server_policy_quality_helpers.py
├── server_result_helpers.py
├── server_runtime_helpers.py
└── server/                # Tool group implementations (extracted)
    ├── auth.py
    ├── lifecycle.py
    ├── resources_catalog.py
    ├── resources_contracts.py
    ├── resources_sessions.py
    ├── resources_system.py
    ├── resources_workflow.py
    ├── resources_workstream.py
    ├── session_tools.py
    ├── tools_batch4.py
    ├── tools_catalog.py
    ├── tools_contract_observe.py
    ├── tools_coordination.py
    ├── tools_escalation.py
    ├── tools_governance.py
    ├── tools_handoff_queue.py
    ├── tools_locking_planning.py
    ├── tools_lsp.py
    ├── tools_planning.py
    ├── tools_prompt_and_handoff.py
    ├── tools_queue_mutations.py
    ├── tools_queue.py
    ├── tools_research.py
    ├── tools_runtime.py
    ├── tools_sessions.py
    ├── tools_skills.py
    ├── tools_terminal.py
    ├── tools_workstream_governance.py
    ├── tools_workstream_lsp.py
    └── workflow_prompts.py
```

## Tool Groups Extracted

| Module                             | Domain                      | Load pattern                                   |
| ---------------------------------- | --------------------------- | ---------------------------------------------- |
| `server/tools_sessions.py`         | Session lifecycle tools     | `_load_server_tools_sessions_module()`         |
| `server/tools_queue.py`            | Queue read tools            | `_load_server_tools_queue_module()`            |
| `server/tools_terminal.py`         | Terminal/PTY tools          | `_load_server_tools_terminal_module()`         |
| `server/tools_escalation.py`       | Escalation/alert tools      | `_load_server_tools_escalation_module()`       |
| `server/tools_governance.py`       | Governance rule tools       | `_load_server_tools_governance_module()`       |
| `server/tools_research.py`         | Research/search tools       | `_load_server_tools_research_module()`         |
| `server/tools_planning.py`         | Planning/workstream tools   | `_load_server_tools_planning_module()`         |
| `server/tools_contract_observe.py` | Contract observation tools  | `_load_server_tools_contract_observe_module()` |
| `server/tools_locking_planning.py` | Locking + planning combined | `_load_server_tools_locking_planning_module()` |
| `server/tools_skills.py`           | Skill catalog tools         | `_load_server_tools_skills_module()`           |
| `server/tools_coordination.py`     | Multi-agent coordination    | `_load_server_tools_coordination_module()`     |
| `server/tools_runtime.py`          | Runtime diagnostics tools   | `_load_server_tools_runtime_module()`          |
| `server/tools_batch4.py`           | Batch-4 additional tools    | `_load_server_tools_batch4_module()`           |
| `server_catalog_tools.py`          | Model catalog tools         | direct import (not lazy-loaded)                |

## Loading Pattern

`server.py` uses a consistent lazy-loading pattern for each tool group:

```python
def _load_server_tools_<group>_module() -> Any:
    module_path = Path(__file__).with_suffix("") / "tools_<group>.py"
    spec = importlib.util.spec_from_file_location(
        "thegent.mcp._server_tools_<group>", module_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load tools_<group>.py from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module

_server_tools_<group> = _load_server_tools_<group>_module()
```

This pattern:

- Fails loudly at startup if a tool group module is missing (no silent degradation).
- Allows each tool group to be modified independently without touching `server.py`.
- Preserves the FastMCP tool registration protocol in each extracted module.

## Re-Export Strategy

`server.py` does not re-export tool group symbols. Tool groups are loaded as
opaque modules; their `register_tools(mcp)` or equivalent entry point is called
during lifespan initialization.

## What Remains in server.py

- FastMCP app instantiation and lifespan
- Middleware registration (logging, rate-limiting, error-handling, timing, caching)
- Auth and lifecycle module loading
- Resource group module loading
- Tool group lazy loading (the `_load_server_tools_*_module()` functions)
- Top-level route/prompt registration
