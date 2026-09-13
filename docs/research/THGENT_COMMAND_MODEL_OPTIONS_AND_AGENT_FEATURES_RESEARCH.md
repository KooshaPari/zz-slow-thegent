<DONE>
# Thegent Command Model Options and Agent Features Research

**Purpose**: Comprehensive research and documentation of thegent CLI commands, model options, routing features, and agent capabilities for proper agent usage.

**Date**: 2026-02-17
**Status**: Research Complete, CLAUDE.md command reference integrated
**Priority**: P1

---

## Executive Summary

This document provides comprehensive research on thegent's command structure, model routing options, agent execution modes, background processing, work stream integration, and all features designed for agent usage. This research will be used to update CLAUDE.md, SKILL.md files, CLI documentation, and MCP documentation.

---

## 1. Core Agent Execution Commands

### 1.1 `thegent run` - Foreground Agent Execution

**Purpose**: Run an agent in foreground with full control and real-time output.

**Syntax**:

```bash
thegent run [PROMPT] [AGENT] [OPTIONS]
```

**Key Options**:

- `--model, -M <model>`: Model override or model-first routing (when agent omitted)
- `--provider, -P <provider>`: Provider override for model-first routing
- `--routing, -R <policy>`: Routing policy (`prefer_direct` | `prefer_proxy` | `failover` | `round_robin` | `cheapest` | `cost_quality` | `pareto` | `roi`)
- `--mode, -m <mode>`: Execution mode (`read-only` | `write` | `full`)
- `--timeout, -t <seconds>`: Timeout hint in seconds (tool-call budget injection, default: 90)
- `--cd, -d <path>`: Working directory
- `--live`: Stream output live to terminal
- `--full, -f`: Show full raw output (default: stream-json, parsed)
- `--failover`: On failure, try next route (model-first only)
- `--include-contract`: Print resolved model route contract metadata in output
- `--run-id <id>`: Explicit run ID for registry correlation
- `--lane <lane>`: Execution lane (`standard` | `critical` | `recovery`)
- `--idempotency-token <token>`: Deterministic token to prevent duplicate runs
- `--confidence <0.0-1.0>`: Task confidence score
- `--arbitration <role>`: Arbitration role (`leader` | `follower` | `consensus`)
- `--override <reason>`: Policy override reason code
- `--contract-version <version>`: Contract schema version (default: current)
- `--domain <tag>`: Domain tag for tiered retention (WP-3006)
- `--speculative`: Enable speculative execution mode (WP-5001)
- `--search/--no-search`: Enable web search for codex agents (default: on)
- `--debug`: Enable debug mode (THGENT_DEBUG=1, proxy -debug for model/provider/latency tags)
- `--retry --run-id <id>`: Retry failed run by run-id (looks up prompt from registry)

**Model-First Routing**:

- When `-M/--model` is provided without `agent`, thegent uses model-first routing
- Resolves provider automatically based on model catalog
- Supports `--failover` to try next route on failure
- Supports `--routing` policy selection

**Examples**:

```bash
# Model-first routing
thegent run "Fix bug in auth.py" -M gemini-3-flash

# Provider override
thegent run "Implement feature" -M claude-sonnet-4.5 -P claude

# Routing policy
thegent run "Optimize code" -M gemini-3-flash -R cheapest

# Full mode with contract metadata
thegent run "Review code" --mode full --include-contract

# Retry failed run
thegent run --retry --run-id abc123
```

### 1.2 `thegent bg` - Background Agent Execution

**Purpose**: Start a background run and register a session. Non-blocking execution.

**Syntax**:

```bash
thegent bg [PROMPT] [AGENT] [OPTIONS]
```

**Key Options** (inherits most from `run`):

- All `run` options plus:
- `--owner <tag>`: Session owner tag (default: `<user>:<cwd-name>`)
- `--format <format>`: Output format (`json` | `rich` (default) | `md` (agent-friendly))
- `--continuation, -C <session_id>`: Prior session id(s) to continue from (comma-separated)
- `--continuation-stderr`: Include stderr from prior session(s)

**Session Management**:

- Sessions stored in `~/.cache/thegent/sessions/<owner>/`
- Session files: `<session_id>.json` (metadata), `<session_id>.stdout.log`, `<session_id>.stderr.log`, `<session_id>.rc`
- Use `thegent ps` to list running sessions
- Use `thegent wait <session_id>` to block until session completes
- Use `thegent status <session_id>` to check session status

**Examples**:

```bash
# Background run
thegent bg "Implement feature X" free

# Continue from prior session
thegent bg "Continue implementation" -C abc123

# With owner tag
thegent bg "Task" --owner "project:feature"

# Agent-friendly output format
thegent bg "Research topic" --format md
```

### 1.3 `thegent free` - Free Tier Agent (Copilot gpt-5-mini)

**Purpose**: Base free tier agent using Copilot gpt-5-mini. Alias for `thegent run "<prompt>" free`.

**Syntax**:

```bash
thegent free [PROMPT] [OPTIONS]
```

**Key Options**:

- `--do-next, -n`: Find next work item from plan do-next and run it
- `--repeat, -r <N>`: With --do-next: run up to N work packages in sequence (stop on first failure)
- `--mode, -m <mode>`: Mode (`read-only` | `write` | `full`, default: `write`)
- `--timeout, -t <seconds>`: Timeout (default from THGENT_DEFAULT_TIMEOUT_FREE, else 300)
- `--live/--no-live, -l`: Stream output live (default: on)
- `--bg, -b`: Run in background (async)
- `--diff, -D`: Suppress live stream; show diff/summary at end
- `--cd, -d <path>`: Working directory

**Work Stream Integration**:

- `--do-next` automatically finds next actionable work item from WORK_STREAM.md
- `--repeat` allows running multiple work items sequentially
- Integrates with `thegent plan do-next` and `thegent plan loop`

**Examples**:

```bash
# Simple free agent run
thegent free "Fix bug in auth.py"

# Run next work item
thegent free --do-next

# Run next 5 work items sequentially
thegent free --do-next --repeat 5

# Background execution
thegent free "Long task" --bg
```

### 1.4 Role-Based Commands

**Purpose**: Run tasks with role-based system prompts.

**Commands**:

- `thegent summarize <prompt>`: Summarize content with brevity and key takeaways
- `thegent research <prompt>`: Deep dive research and comprehensive information gathering
- `thegent review <prompt>`: Critical analysis and quality checks for code or documentation
- `thegent explain <prompt>`: Explain code or concepts
- `thegent fix <prompt>`: Fix issues in code
- `thegent code <prompt>`: Generate or modify code

**Options** (all role commands):

- `--cd, -d <path>`: Working directory
- `--mode, -m <mode>`: Mode (`read-only` | `write` | `full`, default: `write`)
- `--timeout, -t <seconds>`: Timeout hint
- `--bg, -b`: Run in background
- `--model, -M <model>`: Model override
- `--live`: Stream output live

**Default Agent**: Uses virtual 'role' agent which defaults to `gemini-3-flash` unless `--agent` or `--model` specified.

**Examples**:

```bash
# Research task
thegent research "Latest VitePress plugins" --bg

# Code review
thegent review "Review auth.py for security issues"

# Code generation
thegent code "Implement user authentication"
```

---

## 2. Model Routing and Provider Options

### 2.1 Available Providers

| Provider      | Type   | Default Model      | Notes                |
| ------------- | ------ | ------------------ | -------------------- |
| `claude`      | Direct | `claude-haiku-4.5` | Anthropic Claude API |
| `gemini`      | Direct | `gemini-3-flash`   | Google Gemini API    |
| `copilot`     | Direct | `gpt-5-mini`       | GitHub Copilot       |
| `codex`       | Direct | `gpt-5.3-codex`    | Codex API            |
| `cursor`      | Proxy  | `gemini-3-flash`   | Cursor API (wisdgod) |
| `antigravity` | Proxy  | `gemini-3-flash`   | Antigravity proxy    |
| `minimax`     | Proxy  | `minimax-m2.5`     | MiniMax API          |
| `glm`         | Proxy  | `glm-5`            | Zhipu GLM API        |
| `nim`         | Proxy  | `step-3.5-flash`   | NVIDIA NIM           |
| `kilo`        | Proxy  | `minimax-m2.5`     | Kilo proxy           |
| `kiro`        | Proxy  | `claude-haiku-4.5` | Kiro proxy           |
| `free`        | Direct | `gpt-5-mini`       | Copilot free tier    |

### 2.2 Model Catalog

**Anthropic Models**:

- `claude-haiku-4.5`: Fast, cost-effective (priority: -1, cost: 0.2, latency: 300ms, accuracy: 0.85)
- `claude-sonnet-4.5`: Balanced (priority: -1, cost: 0.5, latency: 600ms, accuracy: 0.92)
- `claude-sonnet-4.5-1m`: 1M context (priority: -1, cost: 0.6, latency: 900ms, accuracy: 0.90)
- `claude-opus-4.6`: Highest quality (priority: -1, cost: 1.0, latency: 1500ms, accuracy: 0.98)

**Gemini Models**:

- `gemini-3-flash`: Fast, free tier friendly (priority: -1, cost: 0.1, latency: 200ms, accuracy: 0.82)
- `gemini-3-pro`: Higher quality (priority: -1, cost: 0.4, latency: 800ms, accuracy: 0.91)

**Codex Models**:

- `gpt-5.3-codex`: Base Codex model
- `gpt-5.3-codex-spark`: Spark variant
- `gpt-5.3-codex-spark-high`: High quality spark
- `gpt-5.3-codex-spark-xhigh`: Extra high quality spark
- `gpt-5.3-codex-high`: High quality
- `gpt-5.3-codex-xhigh`: Extra high quality

**Other Models**:

- `gpt-5-mini`: OpenAI GPT-5 Mini (via Copilot)
- `minimax-m2.5`: MiniMax M2.5
- `glm-5`: Zhipu GLM-5
- `deepseek-v3.2`: DeepSeek V3.2
- `qwen3.5-plus-02-15`: Qwen 3.5 Plus

### 2.3 Routing Policies

| Policy          | Description                        | Use Case                               |
| --------------- | ---------------------------------- | -------------------------------------- |
| `prefer_direct` | Prefer direct provider connections | Low latency, high reliability          |
| `prefer_proxy`  | Prefer proxy connections           | Cost optimization, rate limit handling |
| `failover`      | Try primary, fallback on failure   | High availability                      |
| `round_robin`   | Distribute across routes           | Load balancing                         |
| `cheapest`      | Select cheapest route              | Cost optimization                      |
| `cost_quality`  | Balance cost and quality           | Optimal value                          |
| `pareto`        | Pareto frontier optimization       | Multi-objective optimization           |
| `roi`           | Return on investment optimization  | Business value                         |

**Default**: `prefer_direct` (configurable via `THGENT_DEFAULT_ROUTING`)

### 2.4 Model-First Routing

**When to Use**: Specify model without provider, let thegent resolve provider automatically.

**Syntax**:

```bash
thegent run "Task" -M <model> [--provider <provider>] [--routing <policy>]
```

**Behavior**:

1. Resolves model from catalog
2. Finds available routes (provider + backend combinations)
3. Applies routing policy
4. Selects best route
5. Executes with selected route

**Examples**:

```bash
# Model-first with auto provider resolution
thegent run "Task" -M gemini-3-flash

# Model-first with provider override
thegent run "Task" -M claude-sonnet-4.5 -P claude

# Model-first with routing policy
thegent run "Task" -M gemini-3-flash -R cheapest

# Model-first with failover
thegent run "Task" -M gemini-3-flash --failover
```

---

## 3. Work Stream and Planning Commands

### 3.1 `thegent plan do-next` - Find Next Work Items

**Purpose**: Find next actionable work items from PLAN_STATUS, FR_TRACKER, docs/plans/, escalation queue.

**Syntax**:

```bash
thegent plan do-next [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Working directory
- `--limit, -l <N>`: Max items to return (default: 5)
- `--format, -f <format>`: Output format (`rich` | `json`)

**Output**: List of actionable work items with IDs, prompts, dependencies, status.

**Examples**:

```bash
# Get next 5 work items
thegent plan do-next

# Get next 10 work items
thegent plan do-next --limit 10

# JSON output for scripting
thegent plan do-next --format json
```

### 3.2 `thegent plan get-next` - Get First Work Item Prompt

**Purpose**: Get first work item prompt for scripting. Returns prompt only (plain text).

**Syntax**:

```bash
thegent plan get-next [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Working directory
- `--format, -f <format>`: Output (`plain` (default, prompt only) | `json`)

**Use Case**: Scripting integration, e.g., `PROMPT=$(thegent plan get-next)`

**Examples**:

```bash
# Get prompt for scripting
PROMPT=$(thegent plan get-next)
thegent free "$PROMPT"

# JSON format
thegent plan get-next --format json
```

### 3.3 `thegent plan loop` - Continuous Work Loop

**Purpose**: Loop: get next item -> run bg -> repeat until no items or --max reached.

**Syntax**:

```bash
thegent plan loop [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Working directory
- `--max, -m <N>`: Max iterations (0=unbounded, default: 0)
- `--sleep, -s <seconds>`: Seconds between iterations (default: 5.0)
- `--agent, -a <agent>`: Agent for bg runs (default: `free`)
- `--dry-run`: Print only, do not run

**Behavior**:

1. Get next work item via `plan do-next`
2. Run item in background with specified agent
3. Sleep for specified interval
4. Repeat until no items or max iterations reached

**Examples**:

```bash
# Continuous loop (unbounded)
thegent plan loop

# Loop with max 10 iterations
thegent plan loop --max 10

# Loop with custom agent and sleep interval
thegent plan loop --agent codex --sleep 10

# Dry run (see what would run)
thegent plan loop --dry-run
```

### 3.4 `thegent plan wait-next` - Block Until Work Ready

**Purpose**: Block until next actionable work exists (DAG ready, do-next, escalation, inbox).

**Syntax**:

```bash
thegent plan wait-next [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Working directory
- `--poll, -p <seconds>`: Poll interval in seconds (default: 2.0)
- `--timeout, -t <seconds>`: Max wait seconds (0=unbounded, default: 0.0)
- `--sources, -s <sources>`: Comma-separated: `dag,do_next,escalation,inbox` (default: all)
- `--format, -f <format>`: Output format (`rich` | `json`)

**Use Case**: Idle waiting instead of busy loops. Blocks until work is available.

**Examples**:

```bash
# Wait for any work
thegent plan wait-next

# Wait with timeout
thegent plan wait-next --timeout 300

# Wait for specific sources
thegent plan wait-next --sources dag,do_next

# Custom poll interval
thegent plan wait-next --poll 5
```

### 3.5 `thegent plan incorporate` - Merge Fragments into Work Stream

**Purpose**: Merge fragments from 02-UNIFIED-WBS into WORK_STREAM.md. Preserves CLAIMED and COMPLETED.

**Syntax**:

```bash
thegent plan incorporate [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Working directory
- `--dry-run`: Show what would be merged without writing

**Behavior**:

- Scans `docs/plans/`, `docs/research/`, `docs/docset/` for fragments
- Extracts work items from fragments
- Merges into WORK_STREAM.md
- Resolves conflicts automatically
- Preserves CLAIMED and COMPLETED sections

**Examples**:

```bash
# Incorporate fragments
thegent plan incorporate

# Dry run
thegent plan incorporate --dry-run
```

### 3.6 `thegent plan claim` / `thegent plan complete` - Work Stream Management

**Purpose**: Claim or complete items in unified work stream.

**Syntax**:

```bash
thegent plan claim <item_id> [agent_id] [OPTIONS]
thegent plan complete <item_id> [agent_id] [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Project directory
- `agent_id`: Agent ID (auto-detected if missing)

**Examples**:

```bash
# Claim work item
thegent plan claim research-library-http

# Complete work item
thegent plan complete research-library-http
```

### 3.7 `thegent plan progress` - Show Recent Runs

**Purpose**: Show recent runs (work-package progress). Alias for `history --limit N`.

**Syntax**:

```bash
thegent plan progress [OPTIONS]
```

**Options**:

- `--limit, -l <N>`: Number of runs to show (default: 10)
- `--format, -f <format>`: Output format (`rich` | `json`)

---

## 4. Background Execution and Session Management

### 4.1 Session Lifecycle

**Session Creation**:

- Created when `thegent bg` is called
- Session ID: UUID v4
- Owner tag: `<user>:<cwd-name>` (or `--owner` specified)
- Session directory: `~/.cache/thegent/sessions/<owner>/`

**Session Files**:

- `<session_id>.json`: Metadata (prompt, agent, model, status, timestamps, etc.)
- `<session_id>.stdout.log`: Standard output
- `<session_id>.stderr.log`: Standard error
- `<session_id>.rc`: Exit code

**Session States**:

- `running`: Active execution
- `exited:<code>`: Completed with exit code
- `killed`: Terminated (timeout, idle detection, manual kill)
- `failed`: Failed with error

### 4.2 `thegent ps` - List Running Sessions

**Purpose**: List active background sessions.

**Syntax**:

```bash
thegent ps [OPTIONS]
```

**Options**:

- `--all`: Show all sessions (including exited)
- `--owner <tag>`: Filter by owner tag
- `--format <format>`: Output format (`rich` | `json` | `md`)
- `--include-contract`: Include route contract metadata

**Output**: Table of sessions with ID, agent, prompt, status, started time, etc.

**Examples**:

```bash
# List running sessions
thegent ps

# List all sessions
thegent ps --all

# Filter by owner
thegent ps --owner "project:feature"
```

### 4.3 `thegent wait` - Wait for Session Completion

**Purpose**: Block until session exits.

**Syntax**:

```bash
thegent wait <session_id> [OPTIONS]
```

**Options**:

- `--timeout <seconds>`: Max wait time (0=unbounded)
- `--poll <seconds>`: Poll interval (default: 1.0)

**Use Case**: Idle waiting instead of busy loops. Blocks until session completes.

**Examples**:

```bash
# Wait for session
thegent wait abc123

# Wait with timeout
thegent wait abc123 --timeout 300
```

### 4.4 `thegent status` - Check Session Status

**Purpose**: Check status of a background session.

**Syntax**:

```bash
thegent status <session_id> [OPTIONS]
```

**Options**:

- `--format <format>`: Output format (`rich` | `json` | `md`)

**Output**: Session status, metadata, output summary.

### 4.5 `thegent kill` - Terminate Session

**Purpose**: Terminate a running session.

**Syntax**:

```bash
thegent kill <session_id> [OPTIONS]
```

**Options**:

- `--force`: Force kill (SIGKILL instead of SIGTERM)

---

## 5. DAG (Directed Acyclic Graph) Commands

### 5.1 `thegent dag list` - List DAG Tasks

**Purpose**: Parse and display DAG session from `.factory/dag-session.md`.

**Syntax**:

```bash
thegent dag list [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Working directory (default: cwd)
- `--format, -f <format>`: Output format (`rich` | `md`)

### 5.2 `thegent dag run` - Execute DAG

**Purpose**: Execute DAG tasks in dependency order.

**Syntax**:

```bash
thegent dag run [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Working directory
- `--agent <agent>`: Agent for tasks (default: `free`)
- `--dry-run`: Show execution plan without running

### 5.3 `thegent dag sync` - Sync DAG State

**Purpose**: Update task status from session exit.

**Syntax**:

```bash
thegent dag sync [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Working directory

### 5.4 `thegent dag update` - Update DAG State

**Purpose**: Update DAG state manually.

**Syntax**:

```bash
thegent dag update [OPTIONS]
```

### 5.5 `thegent dag validate` - Validate DAG

**Purpose**: Validate DAG: cycles, orphans, agent names. Exit 2 on failure.

**Syntax**:

```bash
thegent dag validate [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Working directory (default: cwd)

---

## 6. Configuration and Setup

### 6.1 `thegent config check` - Validate Configuration

**Purpose**: Validate config; fail-fast on misconfig.

**Syntax**:

```bash
thegent config check [OPTIONS]
```

**Options**:

- `--format <format>`: Output format (`rich` | `json`)

### 6.2 `thegent setup` - Initialize Thegent

**Purpose**: Initialize thegent: configure MCP clients and background services.

**Syntax**:

```bash
thegent setup [OPTIONS]
```

**Options**:

- `--force`: Force re-initialization

### 6.3 `thegent doctor` - Health Checks

**Purpose**: Run comprehensive health and preflight checks.

**Syntax**:

```bash
thegent doctor [OPTIONS]
```

**Options**:

- `--fix`: Try to fix common issues automatically

---

## 7. Provider Login and Authentication

### 7.1 `thegent login` / `thegent cliproxy login` - Provider Login

**Purpose**: Run login for provider. Unified flow: open URL + prompt for API key.

**Syntax**:

```bash
thegent login <provider> [OPTIONS]
thegent cliproxy login <provider> [OPTIONS]
```

**Providers**: `claude`, `codex`, `minimax`, `glm`, `nim`, `kilo`, `roo`, `qwen`, `antigravity`, `iflow`, `kiro`. `gemini`/`copilot` route via Codex proxy.

**Options**:

- `--force, -f`: Re-enter key even if already configured

**Examples**:

```bash
# Login to Claude
thegent login claude

# Login to MiniMax
thegent login minimax

# Force re-login
thegent login claude --force
```

---

## 8. Agent Usage Patterns for Claude/Agents

### 8.1 Default Agent Selection

**When to Use `thegent free`**:

- Default for most tasks
- Free tier (Copilot gpt-5-mini)
- Work stream integration (`--do-next`)
- Background execution (`--bg`)

**When to Use `thegent run`**:

- Need specific model/provider
- Need model-first routing
- Need routing policy control
- Need contract metadata
- Foreground execution with live output

**When to Use `thegent bg`**:

- Long-running tasks
- Non-blocking execution
- Session management needed
- Continuation from prior sessions

### 8.2 Work Stream Integration Pattern

**Recommended Pattern**:

```bash
# Option 1: Continuous loop (recommended)
thegent plan loop

# Option 2: Manual iteration
while true; do
  PROMPT=$(thegent plan get-next)
  [ -z "$PROMPT" ] && break
  thegent free "$PROMPT" --bg
  thegent plan wait-next --timeout 60
done

# Option 3: Single work item
thegent free --do-next
```

### 8.3 Idle Waiting Pattern

**Instead of busy loops**:

```bash
# Bad: Busy loop
while true; do
  sleep 5
  # check work
done

# Good: Use wait-next
thegent plan wait-next

# Good: Use wait for session
thegent wait <session_id>
```

### 8.4 Delegation Pattern

**For multi-file or complex tasks**:

```bash
# Delegate to free agent
thegent free "Implement feature X across multiple files" --bg

# Delegate to specific agent
thegent bg "Research topic" codex

# Delegate with model-first routing
thegent run "Complex task" -M claude-sonnet-4.5
```

### 8.5 Background Execution Pattern

**For parallel work**:

```bash
# Start multiple background tasks
thegent bg "Task 1" free &
thegent bg "Task 2" free &
thegent bg "Task 3" free &

# Monitor with ps
thegent ps

# Wait for all to complete
for sid in $(thegent ps --format json | jq -r '.[].id'); do
  thegent wait "$sid"
done
```

---

## 9. Environment Variables

### 9.1 Timeout Configuration

- `THGENT_DEFAULT_TIMEOUT`: Default agent timeout (default: 90s)
- `THGENT_DEFAULT_TIMEOUT_CLAUDE`: Claude agent timeout (default: 300s)
- `THGENT_DEFAULT_TIMEOUT_FREE`: Free agent timeout (default: 300s)

### 9.2 Routing Configuration

- `THGENT_DEFAULT_ROUTING`: Default routing policy (`prefer_direct` | `prefer_proxy`)

### 9.3 Session Configuration

- `THGENT_OWNER_TAG`: Explicit owner tag override
- `THGENT_OWNER_SCOPE`: Owner scope (supports `{user}`, `{uid}`, `{pid}`, `{ppid}`, `{cwd}` placeholders)

### 9.4 Debug Configuration

- `THGENT_DEBUG`: Enable debug mode (1=enabled)

---

## 10. MCP Integration

### 10.1 MCP Server

**Purpose**: Start thegent MCP server for IDE integration.

**Syntax**:

```bash
thegent mcp serve [OPTIONS]
```

**Options**:

- `--port <port>`: HTTP port (default: 8000)
- `--host <host>`: Host (default: localhost)

**Behavior**: Delegates to launchd/Homebrew service when available.

### 10.2 MCP Tools

Thegent exposes MCP tools for:

- Agent execution (`thegent_run`, `thegent_bg`)
- Work stream management (`plan_do_next`, `plan_claim`, `plan_complete`)
- Session management (`ps`, `status`, `wait`)
- DAG operations (`dag_list`, `dag_run`, `dag_sync`)

---

## 11. Key Takeaways for Agent Usage

### 11.1 Command Selection Guide

| Task Type               | Command                             | Notes                                     |
| ----------------------- | ----------------------------------- | ----------------------------------------- |
| Single task, foreground | `thegent run` or `thegent free`     | Use `free` for default, `run` for control |
| Single task, background | `thegent bg` or `thegent free --bg` | Use `bg` for session management           |
| Work stream integration | `thegent free --do-next`            | Automatic work item selection             |
| Continuous work loop    | `thegent plan loop`                 | Recommended for autonomous agents         |
| Idle waiting            | `thegent plan wait-next`            | Instead of busy loops                     |
| Model-specific routing  | `thegent run -M <model>`            | Model-first routing                       |
| Cost optimization       | `thegent run -R cheapest`           | Use cheapest routing policy               |

### 11.2 Best Practices

1. **Use `thegent plan loop`** for continuous autonomous work
2. **Use `thegent plan wait-next`** instead of busy loops
3. **Use `thegent free`** as default agent (free tier, work stream integration)
4. **Use `thegent bg`** for long-running or parallel tasks
5. **Use model-first routing** (`-M`) when model matters more than provider
6. **Use routing policies** (`-R`) for cost/quality optimization
7. **Use `--do-next`** for automatic work stream integration
8. **Use `--repeat`** for sequential work item execution
9. **Use session management** (`ps`, `wait`, `status`) for background tasks
10. **Use `--continuation`** to continue from prior sessions

### 11.3 Anti-Patterns to Avoid

1. **Don't use busy loops**: Use `plan wait-next` or `wait <session_id>`
2. **Don't use bash wrappers**: Use native `--repeat`, `--do-next`, `plan loop`
3. **Don't poll manually**: Use `plan wait-next` with polling
4. **Don't ignore work stream**: Use `plan do-next` and `plan incorporate`
5. **Don't hardcode agents**: Use `free` as default, override when needed

---

## 12. Documentation Updates Needed

### 12.1 CLAUDE.md Updates

**Completed**: "Thegent Command Reference for Agents" section present in `CLAUDE.md`

- Core commands (`run`, `bg`, `free`) documented
- Work stream integration (`plan do-next`, `plan loop`, `plan wait-next`) documented
- Model routing examples documented
- Background execution and idle waiting patterns documented

**Update Section**: "Delegate to Subagents"

- Replace generic `thegent free` references with specific command patterns
- Add `thegent plan loop` as recommended pattern
- Add `thegent plan wait-next` for idle waiting
- Add model routing examples

### 12.2 SKILL.md Updates

**Update**: `skills/sitback-agent/SKILL.md`

- Add thegent command reference
- Add work stream integration examples
- Add background execution examples

**Update**: `skills/agent-orchestra/SKILL.md`

- Add orchestration patterns using thegent
- Add multi-agent coordination examples

### 12.3 CLI Documentation

**Create/Update**: `docs/guides/THGENT_CLI_REFERENCE.md`

- Complete command reference
- All options documented
- Examples for each command
- Use cases and patterns

### 12.4 MCP Documentation

**Update**: MCP tool documentation

- Document all MCP tools
- Add examples for each tool
- Add integration patterns

---

## 13. Research Findings Summary

### 13.1 Command Structure

- **488 commands** total in main.py
- **Core commands**: `run`, `bg`, `free`, role-based (`summarize`, `research`, `review`, etc.)
- **Work stream**: `plan do-next`, `plan loop`, `plan wait-next`, `plan incorporate`
- **Session management**: `ps`, `wait`, `status`, `kill`
- **DAG**: `dag list`, `dag run`, `dag sync`, `dag update`, `dag validate`

### 13.2 Model Routing

- **Model-first routing**: Use `-M` without agent
- **8 routing policies**: `prefer_direct`, `prefer_proxy`, `failover`, `round_robin`, `cheapest`, `cost_quality`, `pareto`, `roi`
- **12+ providers**: Direct (claude, gemini, copilot, codex) and Proxy (cursor, antigravity, minimax, glm, nim, kilo, kiro)
- **20+ models**: Claude 4.5/4.6, Gemini 3.x, Codex 5.3, GPT-5, MiniMax, GLM, etc.

### 13.3 Agent Features

- **Background execution**: Non-blocking with session management
- **Work stream integration**: Automatic work item discovery and execution
- **Continuation**: Continue from prior sessions
- **Session management**: List, wait, status, kill sessions
- **Idle waiting**: Block until work ready (no busy loops)
- **Role-based prompts**: Specialized system prompts for different tasks

### 13.4 Key Gaps in Current Documentation

1. **CLAUDE.md**: Missing comprehensive thegent command reference
2. **SKILL.md**: Missing thegent integration examples
3. **CLI docs**: Incomplete command reference
4. **MCP docs**: Missing tool documentation

---

## 14. Next Steps

1. **Fix Import Errors**: Fix all `Optional` import issues in agents/ directory
2. **Update CLAUDE.md**: Add comprehensive thegent command reference section
3. **Update SKILL.md**: Add thegent integration examples
4. **Create CLI Reference**: Complete command reference documentation
5. **Update MCP Docs**: Document all MCP tools
6. **Test Commands**: Verify all commands work after import fixes

---

## See also

- [CLAUDE.md](../../CLAUDE.md) — Claude-specific instructions (updated with comprehensive thegent command reference)
- [THGENT_CLI_REFERENCE.md](../guides/THGENT_CLI_REFERENCE.md) — Complete CLI reference guide
- [WORK_STREAM.md](../reference/WORK_STREAM.md) — Unified work stream
- [PROCESS_OPTIMIZATION_PLAN.md](../plans/PROCESS_OPTIMIZATION_PLAN.md) — Process optimization
- [SWARM_PROCESS_OPTIMIZATIONS.md](../reference/SWARM_PROCESS_OPTIMIZATIONS.md) — Swarm optimizations
- [SKILL.md](../../skills/sitback-agent/SKILL.md) — Sitback agent skill (updated)
- [SKILL.md](../../skills/agent-orchestra/SKILL.md) — Agent orchestra skill (updated)
