<DONE>
# ACP Adapters for thegent: Design & Implementation Plan

**Date**: 2026-02-18
**Status**: Design Phase
**Goal**: Enable thegent agents to communicate via ACP (Agent Client Protocol) for interoperability with ACP-compatible clients (gsh, Zed, etc.)

---

## Executive Summary

Build **bidirectional ACP adapters** for thegent:

1. **ACP Server Adapter**: Expose thegent agents as ACP-compatible agents
2. **ACP Client Adapter**: Allow thegent to spawn/communicate with ACP agents
3. **MCP ↔ ACP Bridge**: Translate between MCP and ACP protocols

This enables:

- **gsh integration**: Use `@thegent` in gsh REPL to invoke thegent agents
- **Zed integration**: Use thegent agents in Zed editor
- **Protocol interoperability**: Bridge MCP and ACP ecosystems

---

## ACP Protocol Overview

### What is ACP?

**Agent Client Protocol (ACP)** standardizes communication between code editors/IDEs and coding agents, similar to how LSP standardized language servers.

**Key Characteristics**:

- **JSON-RPC over stdio** (local agents) or **HTTP/WebSocket** (remote agents)
- **Reuses MCP JSON representations** where possible
- **Markdown** as default format for user-readable text
- **Agent-centric**: Assumes user is in editor, reaching out to agents

### ACP vs MCP

| Aspect             | MCP (Model Context Protocol) | ACP (Agent Client Protocol)            |
| ------------------ | ---------------------------- | -------------------------------------- |
| **Focus**          | Model ↔ Tool communication  | Editor ↔ Agent communication          |
| **Use Case**       | Tools, resources, prompts    | Agent spawns, conversations, edits     |
| **Transport**      | stdio, HTTP, WebSocket       | stdio (local), HTTP/WebSocket (remote) |
| **Message Format** | JSON-RPC                     | JSON-RPC (similar structure)           |
| **Ecosystem**      | Anthropic, MCP servers       | Zed, gsh, Claude Agent SDK             |

**Key Insight**: ACP is **complementary** to MCP, not a replacement. MCP handles tooling; ACP handles agent interactions.

---

## Architecture Design

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    ACP-Compatible Clients                    │
│  (gsh, Zed, etc.)                                            │
└──────────────────────┬───────────────────────────────────────┘
                       │ ACP Protocol
                       │ (JSON-RPC)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ACP Server Adapter (thegent-acp-server)        │
│  • Exposes thegent agents as ACP agents                      │
│  • Translates ACP requests → AgentRunner.run()               │
│  • Translates RunResult → ACP responses                      │
└──────────────────────┬───────────────────────────────────────┘
                       │ AgentRunner Interface
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    thegent Core                              │
│  • AgentRunner implementations                                │
│  • MCP Server (FastMCP)                                      │
│  • Agent Registry                                            │
└──────────────────────┬───────────────────────────────────────┘
                       │ ACP Client Protocol
                       │ (spawn external ACP agents)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ACP Client Adapter (thegent-acp-client)        │
│  • Spawns external ACP agents                               │
│  • Translates AgentRunner.run() → ACP requests              │
│  • Translates ACP responses → RunResult                      │
└──────────────────────┬───────────────────────────────────────┘
                       │ ACP Protocol
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              External ACP Agents                             │
│  (claude-agent-acp, custom ACP agents, etc.)                │
└─────────────────────────────────────────────────────────────┘
```

---

## Component 1: ACP Server Adapter

### Purpose

Expose thegent agents as **ACP-compatible agents**, allowing ACP clients (gsh, Zed) to invoke thegent agents.

### Implementation

**File**: `src/thegent/acp/server.py`

```python
"""ACP server adapter for thegent agents."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from thegent.agents.registry import get_runner
from thegent.agents.base import AgentRunner, RunResult


class ACPServerAdapter:
    """Exposes thegent agents via ACP protocol."""

    def __init__(self):
        self.agents: dict[str, AgentRunner] = {}
        self._load_agents()

    def _load_agents(self):
        """Load available thegent agents."""
        # Load from agents/ registry
        # Map agent names to AgentRunner instances
        pass

    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle ACP JSON-RPC request."""
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            return await self._handle_initialize(params)
        elif method == "agent/spawn":
            return await self._handle_spawn(params)
        elif method == "agent/message":
            return await self._handle_message(params)
        elif method == "agent/stop":
            return await self._handle_stop(params)
        else:
            return {"error": {"code": -32601, "message": "Method not found"}}

    async def _handle_spawn(self, params: dict[str, Any]) -> dict[str, Any]:
        """Spawn a thegent agent via ACP."""
        agent_name = params.get("agent")
        prompt = params.get("prompt", "")
        cwd = params.get("cwd")

        runner = get_runner(agent_name, default_model="")
        if not runner:
            return {"error": {"code": -32602, "message": f"Agent '{agent_name}' not found"}}

        # Run agent
        result = runner.run(
            prompt=prompt,
            cwd=Path(cwd) if cwd else None,
            mode="default",
            timeout=3600,
            use_stream=True,
        )

        # Convert RunResult to ACP response
        return {
            "result": {
                "agent_id": f"thegent-{agent_name}",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
            }
        }

    async def run_stdio(self):
        """Run ACP server over stdio (for local agents)."""
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break

            request = json.loads(line.strip())
            response = await self.handle_request(request)
            print(json.dumps(response), flush=True)


async def main():
    """Entry point for ACP server."""
    adapter = ACPServerAdapter()
    await adapter.run_stdio()


if __name__ == "__main__":
    asyncio.run(main())
```

### CLI Entry Point

**File**: `src/thegent/acp/__main__.py`

```python
"""CLI entry point for ACP server."""

import asyncio
from thegent.acp.server import main

if __name__ == "__main__":
    asyncio.run(main())
```

**Usage**:

```bash
# Run as ACP agent (stdio)
thegent-acp-server

# Or via gsh:
# ~/.gsh/repl.gsh
acp Thegent {
    command: "thegent-acp-server",
}
```

---

## Component 2: ACP Client Adapter

### Purpose

Allow thegent to **spawn and communicate with external ACP agents** (e.g., `claude-agent-acp`).

### Implementation

**File**: `src/thegent/acp/client.py`

```python
"""ACP client adapter for spawning external ACP agents."""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any

from thegent.agents.base import AgentRunner, RunResult


class ACPClientAdapter(AgentRunner):
    """AgentRunner implementation that spawns ACP agents."""

    def __init__(self, acp_command: list[str], agent_name: str = "acp-agent"):
        self.acp_command = acp_command
        self.agent_name = agent_name
        self.process: subprocess.Popen | None = None

    def run(
        self,
        prompt: str,
        cwd: Path | None,
        mode: str,
        timeout: int,
        *,
        use_stream: bool = True,
        live_output: bool = False,
        on_stdout: Callable[[str], None] | None = None,
        on_stderr: Callable[[str], None] | None = None,
    ) -> RunResult:
        """Run ACP agent via subprocess."""
        # Spawn ACP agent process
        self.process = subprocess.Popen(
            self.acp_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(cwd) if cwd else None,
        )

        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "capabilities": {},
            },
        }
        self.process.stdin.write(json.dumps(init_request) + "\n")
        self.process.stdin.flush()

        # Send spawn request
        spawn_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "agent/spawn",
            "params": {
                "prompt": prompt,
                "cwd": str(cwd) if cwd else None,
            },
        }
        self.process.stdin.write(json.dumps(spawn_request) + "\n")
        self.process.stdin.flush()

        # Read responses
        stdout_lines = []
        stderr_lines = []

        try:
            # Read stdout (ACP responses)
            for line in self.process.stdout:
                response = json.loads(line.strip())
                if "result" in response:
                    result = response["result"]
                    if "stdout" in result:
                        stdout_lines.append(result["stdout"])
                    if "stderr" in result:
                        stderr_lines.append(result["stderr"])

            # Wait for process
            exit_code = self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            exit_code = 1

        return RunResult(
            exit_code=exit_code,
            stdout="\n".join(stdout_lines),
            stderr="\n".join(stderr_lines),
            timed_out=(exit_code == 1 and self.process.poll() is None),
        )
```

### Integration with Agent Registry

**File**: `src/thegent/agents/registry.py` (additions)

```python
from thegent.acp.client import ACPClientAdapter


def get_acp_runner(acp_config: dict[str, Any]) -> ACPClientAdapter:
    """Create ACP client adapter from config."""
    command = acp_config.get("command", [])
    agent_name = acp_config.get("agent_name", "acp-agent")
    return ACPClientAdapter(command, agent_name)
```

---

## Component 3: MCP ↔ ACP Bridge

### Purpose

Translate between MCP and ACP protocols, enabling:

- ACP clients to use MCP tools
- MCP servers to expose ACP agents

### Implementation

**File**: `src/thegent/acp/mcp_bridge.py`

```python
"""Bridge between MCP and ACP protocols."""

from typing import Any

from thegent.mcp_server import mcp_app  # FastMCP app


class MCPACPBridge:
    """Translates MCP tools/resources to ACP agent capabilities."""

    def __init__(self, mcp_app):
        self.mcp_app = mcp_app

    def mcp_tool_to_acp_capability(self, tool_name: str) -> dict[str, Any]:
        """Convert MCP tool to ACP agent capability."""
        # Query MCP server for tool definition
        # Return ACP-compatible capability description
        pass

    def acp_request_to_mcp_call(self, acp_request: dict[str, Any]) -> dict[str, Any]:
        """Convert ACP request to MCP tool call."""
        # Extract tool name and params from ACP request
        # Call MCP tool
        # Convert MCP response to ACP format
        pass
```

---

## Integration Points

### 1. gsh Integration

**File**: `docs/guides/GSH_INTEGRATION.md`

```gsh
# ~/.gsh/repl.gsh

# Configure thegent as ACP agent
acp Thegent {
    command: "thegent-acp-server",
    args: [],
}

# Use in gsh REPL:
# gsh> @thegent analyze my codebase and suggest improvements
```

### 2. Zed Integration

**File**: `docs/guides/ZED_INTEGRATION.md`

```yaml
# ~/.config/zed/settings.json
{
  "external_agents":
    { "thegent": { "command": "thegent-acp-server", "args": [] } },
}
```

### 3. thegent CLI Integration

**File**: `src/thegent/cli.py` (additions)

```python
@app.command("acp")
def acp_cmd(
    server: bool = typer.Option(False, "--server", help="Run ACP server"),
    client: str = typer.Option(None, "--client", help="Connect to ACP agent"),
):
    """ACP protocol integration."""
    if server:
        from thegent.acp.server import main

        asyncio.run(main())
    elif client:
        # Spawn ACP client
        pass
```

---

## Implementation Plan

### Phase 1: ACP Server Adapter (Week 1)

**Goal**: Expose thegent agents as ACP-compatible agents.

**Tasks**:

1. ✅ Research ACP protocol specification
2. ⏳ Implement `ACPServerAdapter` class
3. ⏳ Map `AgentRunner.run()` to ACP `agent/spawn` method
4. ⏳ Convert `RunResult` to ACP response format
5. ⏳ Add stdio transport (JSON-RPC over stdin/stdout)
6. ⏳ Add CLI entry point (`thegent-acp-server`)
7. ⏳ Test with gsh (`@thegent` command)

**Deliverables**:

- `src/thegent/acp/server.py`
- `src/thegent/acp/__main__.py`
- `docs/guides/GSH_INTEGRATION.md`
- Basic tests

### Phase 2: ACP Client Adapter (Week 2)

**Goal**: Allow thegent to spawn external ACP agents.

**Tasks**:

1. ⏳ Implement `ACPClientAdapter` class (extends `AgentRunner`)
2. ⏳ Spawn ACP agent subprocess
3. ⏳ Send ACP JSON-RPC requests
4. ⏳ Parse ACP responses
5. ⏳ Convert to `RunResult`
6. ⏳ Integrate with agent registry
7. ⏳ Test with `claude-agent-acp`

**Deliverables**:

- `src/thegent/acp/client.py`
- Integration with `agents/registry.py`
- Tests for external ACP agents

### Phase 3: MCP ↔ ACP Bridge (Week 3)

**Goal**: Translate between MCP and ACP protocols.

**Tasks**:

1. ⏳ Implement `MCPACPBridge` class
2. ⏳ Map MCP tools to ACP capabilities
3. ⏳ Convert ACP requests to MCP tool calls
4. ⏳ Convert MCP responses to ACP format
5. ⏳ Test bidirectional translation

**Deliverables**:

- `src/thegent/acp/mcp_bridge.py`
- Integration tests
- Documentation

### Phase 4: Production Polish (Week 4)

**Goal**: Production-ready ACP adapters.

**Tasks**:

1. ⏳ Error handling and retries
2. ⏳ Logging and telemetry
3. ⏳ Performance optimization
4. ⏳ Documentation (guides, API reference)
5. ⏳ CI/CD integration
6. ⏳ Release preparation

**Deliverables**:

- Complete test suite
- Production documentation
- Release artifacts

---

## Testing Strategy

### Unit Tests

```python
# tests/test_acp_server.py
def test_acp_server_spawn():
    adapter = ACPServerAdapter()
    request = {"method": "agent/spawn", "params": {"agent": "claude", "prompt": "Hello"}}
    response = await adapter.handle_request(request)
    assert "result" in response
```

### Integration Tests

```python
# tests/integration/test_gsh_integration.py
def test_gsh_thegent_integration():
    # Spawn thegent-acp-server
    # Send ACP request via subprocess
    # Verify response
    pass
```

### End-to-End Tests

```bash
# Test with gsh
gsh> @thegent analyze my codebase
# Verify thegent agent runs and returns results
```

---

## Open Questions

### 1. **Protocol Compatibility**

**Question**: How compatible are ACP and MCP JSON-RPC formats?

**Research Needed**:

- Compare ACP `agent/spawn` vs MCP `tools/call`
- Map ACP message types to MCP equivalents
- Identify gaps/incompatibilities

**Action**: Review ACP spec and MCP spec side-by-side.

### 2. **Streaming Support**

**Question**: How to handle streaming responses in ACP?

**Current**: `AgentRunner.run()` supports `use_stream=True`, but ACP may have different streaming model.

**Action**: Research ACP streaming protocol.

### 3. **Agent Lifecycle**

**Question**: How to manage long-running agent sessions in ACP?

**Current**: `AgentRunner.run()` is request-response. ACP may support persistent sessions.

**Action**: Review ACP session management.

### 4. **Error Handling**

**Question**: How to map thegent errors to ACP error codes?

**Action**: Define error mapping table.

---

## Success Metrics

### Phase 1 (ACP Server)

- ✅ `thegent-acp-server` runs without errors
- ✅ gsh can invoke `@thegent` command
- ✅ Basic agent spawn works (claude, codex, etc.)

### Phase 2 (ACP Client)

- ✅ thegent can spawn `claude-agent-acp`
- ✅ External ACP agents return `RunResult`
- ✅ Integration with agent registry works

### Phase 3 (Bridge)

- ✅ MCP tools accessible via ACP
- ✅ ACP agents can use MCP tools
- ✅ Bidirectional translation works

### Phase 4 (Production)

- ✅ Test coverage >80%
- ✅ Documentation complete
- ✅ CI/CD passes
- ✅ Performance acceptable (<100ms overhead)

---

## References

- **ACP Specification**: https://agentclientprotocol.com
- **ACP Reference Implementation**: https://github.com/zed-industries/claude-agent-acp
- **MCP Specification**: https://modelcontextprotocol.io
- **gsh ACP Integration**: See `docs/research/GSH_ANALYSIS_2026-02-18.md`

---

## Related Documents

- `docs/research/GSH_ANALYSIS_2026-02-18.md` - gsh analysis and comparison
- `docs/research/TERMINAL_COMPARISON_DEEP_2026-02-18.md` - Terminal comparison
- `src/thegent/mcp_server.py` - Existing MCP server implementation
- `src/thegent/agents/base.py` - AgentRunner interface
