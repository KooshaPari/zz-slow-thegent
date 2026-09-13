<DONE>
# Integration Examples — Kush Ecosystem

> **Status**: 💡 **EXAMPLES** | **Date**: 2026-02-18
> **Purpose**: Practical code examples for integrating projects across the kush ecosystem

---

## Example 1: Agent Orchestration Integration

**Goal**: Use thegent to orchestrate plangent agents

```python
from thegent import AgentOrchestrator
from plangent import RootAgent, SubAgent

# Setup
orchestrator = AgentOrchestrator()
root_agent = RootAgent(config={"sub_agents": ["code-review", "testing"]})

orchestrator.register_agent("plangent-root", root_agent)

# Execute
result = await orchestrator.execute_task(agent_id="plangent-root", task="Review and test the new feature")
```

---

## Example 2: MCP Server Composition

**Goal**: Combine atoms-mcp-prod and morph tools

```python
from fastmcp import FastMCP
from atoms_mcp import AtomsMCPServer
from morph import MorphServer

mcp = FastMCP("unified")

# Register tools
mcp.register_tools(AtomsMCPServer().get_tools())
mcp.register_tools(MorphServer().get_tools())

# Use
status = await mcp.call_tool("workspace_status", path="/workspace")
research = await mcp.call_tool("web_search", query="Python async")
```

---

## Example 3: CLI Tool Pipeline

**Goal**: Chain bloc → trace → usage for analysis

```python
import asyncio
from pathlib import Path


async def analyze_project(path: Path):
    bloc_result = await run_command(["bloc", str(path), "--health"])
    trace_result = await run_command(["trace", "analyze", str(path)])
    usage_result = await run_command(["usage", "status", "--project", str(path)])

    return {"code": bloc_result, "requirements": trace_result, "usage": usage_result}
```

---

## Example 4: Unified Project Management

**Goal**: Integrate trace + atoms-mcp-prod + jobhunter

```python
from trace import RequirementsManager
from atoms_mcp import EntityManager
from jobhunter import TaskManager


class UnifiedPM:
    def __init__(self, project_id: str):
        self.req = RequirementsManager(project_id)
        self.entities = EntityManager(project_id)
        self.tasks = TaskManager(project_id)

    async def create_feature(self, spec: dict):
        req = await self.req.create(spec)
        entity = await self.entities.create({"type": "feature", **spec})
        tasks = await self.tasks.create_from_requirement(req.id)
        return {"req": req, "entity": entity, "tasks": tasks}
```

---

## Example 5: Voice-Triggered Workflow

**Goal**: kimaki voice → thegent → plangent agents

```python
from kimaki import VoiceInterface
from thegent import AgentOrchestrator

voice = VoiceInterface()
orch = AgentOrchestrator()


@voice.command("review code")
async def handle_review():
    result = await orch.execute_task(agent_id="plangent", task="Review workspace code")
    await voice.speak(f"Review complete: {result.summary}")
```

---

## See Also

- [CROSS_PROJECT_INTEGRATION_GUIDE.md](./CROSS_PROJECT_INTEGRATION_GUIDE.md) - Complete integration guide
- [UNIFIED_AGENT_REGISTRY_API.md](./UNIFIED_AGENT_REGISTRY_API.md) - Agent registry API
- [SHARED_MCP_TOOL_LIBRARY.md](./SHARED_MCP_TOOL_LIBRARY.md) - Shared tools

---

**Status**: 💡 **EXAMPLES COMPLETE**
