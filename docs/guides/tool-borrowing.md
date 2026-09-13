# Tool Borrowing Guide

Allow other projects to use thegent MCP tools without copying code.

## Overview

thegent exposes dozens of MCP tools covering session management, planning, research, DAG execution, and more. The tool borrowing mechanism lets any other project consume these tools by:

1. Generating an `mcp.json` entry that points Claude Code at the running thegent MCP server.
2. Generating a `CLAUDE.md` snippet that tells Claude which tools are available.

No code is copied. The borrowing project connects to the thegent server at `http://127.0.0.1:3847/mcp` (default) over the standard MCP HTTP+SSE transport.

## Prerequisites

- thegent installed and running: `thegent serve` (or the MCP server process is managed by your dev stack).
- The borrowing project has Claude Code configured (i.e., it has a `.claude/` directory or `mcp.json`).

## Quick Start

### Borrow all tools

```bash
# In the root of the other project
thegent tools borrow --output-dir .
```

This writes `./mcp.json` (or updates it if it already exists) with a `thegent` server entry.

### Borrow specific tools

```bash
thegent tools borrow thegent_run,thegent_ps,thegent_ddg_search --output-dir /path/to/other-project
```

### Also generate a CLAUDE.md snippet

```bash
thegent tools borrow thegent_run,thegent_ps --output-dir . --claude-md
```

The snippet is printed to stdout. Append it to your project's `CLAUDE.md`:

```bash
thegent tools snippet thegent_run,thegent_ps >> CLAUDE.md
```

### Check server reachability first

```bash
thegent tools borrow thegent_run --check
```

### Point at a non-default server

```bash
thegent tools borrow --host 10.0.0.1 --port 4000
```

## CLI Reference

### `thegent tools list`

List all borrowable tools with category, read-only flag, and description.

```
thegent tools list
thegent tools list --category research
thegent tools list --json
```

### `thegent tools borrow [TOOL_NAMES] [OPTIONS]`

Write or update `mcp.json` in the target directory.

| Option               | Default     | Description                       |
| -------------------- | ----------- | --------------------------------- |
| `TOOL_NAMES`         | (all)       | Comma-separated tool names        |
| `--output-dir`, `-o` | `.`         | Target directory                  |
| `--host`             | `127.0.0.1` | thegent MCP server host           |
| `--port`             | `3847`      | thegent MCP server port           |
| `--no-merge`         | False       | Overwrite instead of merging      |
| `--claude-md`        | False       | Print CLAUDE.md snippet to stdout |
| `--check`            | False       | Verify server reachability first  |

### `thegent tools show NAME`

Show details for a single tool.

```
thegent tools show thegent_run
thegent tools show thegent_ddg_search --json
```

### `thegent tools snippet [TOOL_NAMES]`

Print a CLAUDE.md section for the given tools (or all tools).

```
thegent tools snippet thegent_run,thegent_ps,thegent_ddg_search
```

## Python API

Use the `ToolBorrower` class directly for programmatic access.

```python
from pathlib import Path
from thegent.tools.borrow import BorrowConfig, ToolBorrower

# Create borrower pointing at a custom server
config = BorrowConfig(host="10.0.0.1", port=4000)
borrower = ToolBorrower(config=config)

# List all available tools
for manifest in borrower.list_available_tools():
    print(manifest.name, "-", manifest.description)

# Get tools by category
by_cat = borrower.list_available_tools_by_category()
for tool in by_cat.get("research", []):
    print(tool.name)

# Write mcp.json
written = borrower.generate_mcp_json(
    tool_names=["thegent_run", "thegent_ps"],
    output_path=Path("/path/to/other-project"),
    merge=True,
)
print(f"Written to {written}")

# Get CLAUDE.md content
snippet = borrower.generate_claude_md_snippet(["thegent_run", "thegent_ddg_search"])
print(snippet)

# Check server is up
if borrower.validate_server_reachable():
    print("Server ready")
```

## Available Tool Categories

| Category     | Label                     | Example Tools                                    |
| ------------ | ------------------------- | ------------------------------------------------ |
| `session`    | Session Management        | `thegent_run`, `thegent_ps`, `thegent_stop`      |
| `planning`   | Planning and Work Streams | `thegent_do_next`, `thegent_plan_progress`       |
| `dag`        | DAG Task Management       | `thegent_dag_list`, `thegent_dag_status`         |
| `research`   | Web Research              | `thegent_ddg_search`, `thegent_scrape_url`       |
| `discovery`  | Agent and Model Discovery | `thegent_list_agents`, `thegent_list_models`     |
| `queue`      | Task Queue                | `thegent_queue_add`, `thegent_queue_claim`       |
| `escalation` | Escalations               | `thegent_escalate_add`, `thegent_escalate_list`  |
| `history`    | History and Continuity    | `thegent_history`, `thegent_continuity_snapshot` |
| `execution`  | Agent Execution           | `thegent_free`, `thegent_retry`                  |

## Generated mcp.json Format

```json
{
  "mcpServers": {
    "thegent": {
      "type": "http",
      "url": "http://127.0.0.1:3847/mcp",
      "metadata": {
        "description": "thegent MCP server — agent orchestration and governance platform",
        "borrowed_tools": ["thegent_run", "thegent_ps"],
        "tool_count": 2,
        "categories": ["session"]
      }
    }
  }
}
```

The `mcpServers.thegent` entry is merged with any existing `mcp.json` entries by default.

## Architecture Decision

This mechanism uses a **live proxy** approach rather than code copying:

- The borrowing project's Claude connects to the running thegent MCP server.
- No thegent source code is replicated.
- Tool implementations stay in thegent and receive updates automatically.
- The connection is point-to-point HTTP; no authentication is required for local use (configurable via `THGENT_MCP_AUTH_MODE`).

This is intentionally thin (no SDK coupling, no stub generation). See `ADR.md` for the decision record.
