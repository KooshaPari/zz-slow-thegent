# ACP Adapters Quick Start Guide

**Date**: 2026-02-18
**Purpose**: Quick guide for using ACP adapters with thegent

---

## What is ACP?

**Agent Client Protocol (ACP)** is a standardized protocol for communication between code editors/IDEs and coding agents. It enables interoperability between different agents and editors.

**Benefits**:

- Use thegent agents in ACP-compatible clients (gsh, Zed)
- Spawn external ACP agents from thegent
- Bridge MCP and ACP ecosystems

---

## Quick Start

### 1. Run ACP Server (Expose thegent Agents)

```bash
# Start ACP server (stdio mode)
thegent acp server
```

This exposes thegent agents (claude, codex, copilot, etc.) as ACP-compatible agents.

### 2. Use with gsh

**Step 1**: Install gsh (if not already installed)

```bash
# macOS
brew install gsh

# Or from source
git clone https://github.com/atinylittleshell/gsh
cd gsh && make install
```

**Step 2**: Configure gsh to use thegent

```gsh
# ~/.gsh/repl.gsh
acp Thegent {
    command: "thegent",
    args: ["acp", "server"],
}
```

**Step 3**: Use in gsh REPL

```bash
gsh> @thegent analyze my codebase and suggest improvements
```

### 3. Spawn External ACP Agents

```bash
# Spawn Claude Agent SDK via ACP
thegent acp client "npx -y @zed-industries/claude-agent-acp" \
    --prompt "Review my Python code" \
    --cwd /path/to/project
```

---

## Configuration

### ACP Server Options

Currently, the ACP server runs in stdio mode (JSON-RPC over stdin/stdout). Future versions may support HTTP/WebSocket for remote agents.

### Available Agents

The ACP server exposes these thegent agents:

- `claude` - Claude (via Claude Code CLI)
- `codex` - Codex (via Codex CLI)
- `copilot` - GitHub Copilot
- `gemini` - Google Gemini
- `opencode` - OpenCode CLI

---

## Troubleshooting

### Issue: "Agent 'X' not found"

**Solution**: Ensure the agent is available in your PATH:

```bash
# Check if agent CLI is available
which claude
which codex
```

### Issue: ACP server not responding

**Solution**: Check logs:

```bash
# Run with debug logging
GENT_DEBUG=1 thegent acp server
```

### Issue: gsh can't connect to thegent

**Solution**: Verify ACP configuration in `~/.gsh/repl.gsh`:

```gsh
# Ensure command path is correct
acp Thegent {
    command: "thegent",  # Must be in PATH
    args: ["acp", "server"],
}
```

---

## Advanced Usage

### Programmatic Usage

```python
from thegent.acp.client import ACPClientAdapter
from pathlib import Path

# Create ACP client adapter
adapter = ACPClientAdapter(["npx", "-y", "@zed-industries/claude-agent-acp"], agent_name="claude-acp")

# Run agent
result = adapter.run(
    prompt="Analyze my codebase",
    cwd=Path("/path/to/project"),
    mode="default",
    timeout=3600,
)

print(f"Exit code: {result.exit_code}")
print(f"Output: {result.stdout}")
```

### Custom ACP Agents

You can create custom ACP agents that work with thegent:

1. Implement ACP protocol (JSON-RPC over stdio)
2. Register with thegent via `ACPClientAdapter`
3. Use in agent workflows

---

## Related Documentation

- **Full Design**: `docs/research/ACP_ADAPTERS_DESIGN_2026-02-18.md`
- **Implementation Summary**: `docs/research/ACP_ADAPTERS_IMPLEMENTATION_SUMMARY_2026-02-18.md`
- **gsh Analysis**: `docs/research/GSH_ANALYSIS_2026-02-18.md`
- **ACP Specification**: https://agentclientprotocol.com

---

## Next Steps

1. **Test with gsh**: Configure gsh and test `@thegent` command
2. **Test External Agents**: Try `claude-agent-acp` via `thegent acp client`
3. **Report Issues**: Open GitHub issues for bugs or feature requests
4. **Contribute**: Help improve ACP adapter implementation

---

## Status

**Current Status**: Initial implementation complete, testing pending

**Known Limitations**:

- Session management (multi-turn conversations) not yet implemented
- Streaming responses not yet implemented
- MCP ↔ ACP bridge not yet implemented

**Roadmap**: See `docs/research/ACP_ADAPTERS_DESIGN_2026-02-18.md` for full roadmap.
