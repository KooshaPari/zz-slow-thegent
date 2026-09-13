# Thegent CLI Reference Guide

**Purpose**: Complete reference guide for thegent CLI commands, options, and usage patterns.

**Date**: 2026-02-17
**Status**: Complete
**Audience**: Agents, Developers, Users

---

## Table of Contents

1. [Core Agent Execution Commands](#core-agent-execution-commands)
2. [Work Stream Integration](#work-stream-integration)
3. [Background Execution & Session Management](#background-execution--session-management)
4. [Model Routing & Provider Options](#model-routing--provider-options)
5. [DAG Commands](#dag-commands)
6. [Planning Commands](#planning-commands)
7. [Configuration & Setup](#configuration--setup)
8. [Phench Runtime Control Plane](#phench-runtime-control-plane)
9. [Provider Authentication](#provider-authentication)
10. [MCP Integration](#mcp-integration)
11. [Command Examples](#command-examples)

---

## Core Agent Execution Commands

### `thegent run` - Foreground Agent Execution

Run an agent in foreground with full control and real-time output.

**Syntax**:

```bash
thegent run [PROMPT] [AGENT] [OPTIONS]
```

**Arguments**:

- `PROMPT`: Task prompt (required unless using `--retry --run-id`)
- `AGENT`: Provider name (optional when `-M/--model` given)

**Options**:

| Option                 | Short | Description                                                                                                                            | Default           |
| ---------------------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| `--model`              | `-M`  | Model override or model-first routing                                                                                                  | None              |
| `--provider`           | `-P`  | Provider override for model-first routing                                                                                              | None              |
| `--routing`            | `-R`  | Routing policy (`prefer_direct` \| `prefer_proxy` \| `failover` \| `round_robin` \| `cheapest` \| `cost_quality` \| `pareto` \| `roi`) | `prefer_direct`   |
| `--mode`               | `-m`  | Execution mode (`read-only` \| `write` \| `full`)                                                                                      | `write`           |
| `--timeout`            | `-t`  | Timeout hint in seconds (tool-call budget injection)                                                                                   | 90                |
| `--cd`                 | `-d`  | Working directory                                                                                                                      | Current directory |
| `--live`               |       | Stream output live to terminal                                                                                                         | False             |
| `--full`               | `-f`  | Show full raw output (default: stream-json, parsed)                                                                                    | False             |
| `--failover`           |       | On failure, try next route (model-first only)                                                                                          | False             |
| `--include-contract`   |       | Print resolved model route contract metadata                                                                                           | False             |
| `--run-id`             |       | Explicit run ID for registry correlation                                                                                               | Auto-generated    |
| `--lane`               |       | Execution lane (`standard` \| `critical` \| `recovery`)                                                                                | `standard`        |
| `--idempotency-token`  |       | Deterministic token to prevent duplicate runs                                                                                          | None              |
| `--confidence`         |       | Task confidence score (0.0-1.0)                                                                                                        | None              |
| `--arbitration`        |       | Arbitration role (`leader` \| `follower` \| `consensus`)                                                                               | None              |
| `--override`           |       | Policy override reason code                                                                                                            | None              |
| `--contract-version`   |       | Contract schema version (default: current)                                                                                             | None              |
| `--domain`             |       | Domain tag for tiered retention (WP-3006)                                                                                              | None              |
| `--speculative`        |       | Enable speculative execution mode (WP-5001)                                                                                            | False             |
| `--search/--no-search` |       | Enable web search for codex agents                                                                                                     | `--search`        |
| `--debug`              |       | Enable debug mode (THGENT_DEBUG=1)                                                                                                     | False             |
| `--retry`              |       | Retry failed run by --run-id                                                                                                           | False             |

**Examples**:

```bash
# Basic usage
thegent run "Fix bug in auth.py" free

# Model-first routing
thegent run "Implement feature" -M gemini-3-flash

# With routing policy
thegent run "Optimize code" -M gemini-3-flash -R cheapest

# Full mode with contract metadata
thegent run "Review code" --mode full --include-contract

# Retry failed run
thegent run --retry --run-id abc123
```

### `thegent bg` - Background Agent Execution

Start a background run and register a session. Non-blocking execution.

**Syntax**:

```bash
thegent bg [PROMPT] [AGENT] [OPTIONS]
```

**Additional Options** (inherits all `run` options plus):

| Option                  | Short | Description                                            | Default |
| ----------------------- | ----- | ------------------------------------------------------ | ------- |
| `--owner`               |       | Session owner tag (default: `<user>:<cwd-name>`)       | Auto    |
| `--format`              |       | Output format (`json` \| `rich` \| `md`)               | `rich`  |
| `--continuation`        | `-C`  | Prior session id(s) to continue from (comma-separated) | None    |
| `--continuation-stderr` |       | Include stderr from prior session(s)                   | False   |

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

### `thegent free` - Free Tier Agent (Recommended Default)

Base free tier agent using Copilot gpt-5-mini. Alias for `thegent run "<prompt>" free`.

**Syntax**:

```bash
thegent free [PROMPT] [OPTIONS]
```

**Key Options**:

| Option             | Short | Description                                                  | Default           |
| ------------------ | ----- | ------------------------------------------------------------ | ----------------- |
| `--do-next`        | `-n`  | Find next work item from plan do-next and run it             | False             |
| `--repeat`         | `-r`  | With --do-next: run up to N work packages sequentially       | 1                 |
| `--mode`           | `-m`  | Mode (`read-only` \| `write` \| `full`)                      | `write`           |
| `--timeout`        | `-t`  | Timeout (default from THGENT_DEFAULT_TIMEOUT_FREE, else 300) | 300               |
| `--live/--no-live` | `-l`  | Stream output live                                           | `--live`          |
| `--bg`             | `-b`  | Run in background (async)                                    | False             |
| `--diff`           | `-D`  | Suppress live stream; show diff/summary at end               | False             |
| `--cd`             | `-d`  | Working directory                                            | Current directory |

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

### Role-Based Commands

Run tasks with role-based system prompts.

**Commands**:

- `thegent summarize <prompt>`: Summarize content with brevity and key takeaways
- `thegent research <prompt>`: Deep dive research and comprehensive information gathering
- `thegent review <prompt>`: Critical analysis and quality checks for code or documentation
- `thegent explain <prompt>`: Explain code or concepts
- `thegent fix <prompt>`: Fix issues in code
- `thegent code <prompt>`: Generate or modify code

**Common Options** (all role commands):

- `--cd, -d <path>`: Working directory
- `--mode, -m <mode>`: Mode (`read-only` \| `write` \| `full`, default: `write`)
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

### `thegent review` Exit Codes (CI-Friendly)

`thegent review` is designed for automation gates:

| Exit Code      | Meaning                                                |
| -------------- | ------------------------------------------------------ |
| `0`            | Review completed and found no issues                   |
| `1`            | Review completed and found one or more issues          |
| `2`            | Review output contract invalid (schema/JSON violation) |
| other non-zero | Underlying runner failure propagated as-is             |

**CI Example**:

```bash
thegent review "Review src/ for correctness" --format json
```

- parse JSON output for issue details
- fail pipeline on any non-zero code
- structured review JSON must include `summary`, `overall_rating`, and `issues` (legacy `rating` alias is rejected)

### `--image` Capability Matrix Note (WL-114)

Image input guards use the model capability matrix in
`src/thegent/agents/cliproxy_data/model_indices.json`.

- `--image` is allowed only on image-capable agent paths
- if `--model` is provided, that model must advertise `vision: true` (or `modalities.vision: true`)
- non-vision models fail fast with a non-zero error
- duplicate `--image` inputs are normalized to a unique ordered set before dispatch

### Wave 11 Contract Hardening Notes (WL-107/108/109/110/114)

- `WL-107` (`thegent review`): `overall_rating` must be an integer `0..100`; boolean values are rejected as schema violations.
- `WL-108` (context usage payload): invalid ratio values (for example `NaN`/bool/non-numeric) are ignored in favor of computed `used/max`, and negative usage is rejected from payload emission.
- `WL-109` (MCP LSP symbol lookup): symbol matches are normalized to strict objects (`name`, `kind`, `file_path`, `line`, `character`); malformed entries fail loudly.
- `WL-110` (`thegent resume`): latest-session auto-selection now tolerates mixed naive/offset ISO timestamps by normalizing to UTC before ordering.
- `WL-114` (`--image`): non-string image inputs are rejected early with a clear contract error.

### Wave 12 Contract Hardening Notes (WL-107/108/109/110/114)

- `WL-107` (`thegent review`): `issues[].line` now rejects boolean values explicitly to preserve the integer-only line contract.
- `WL-108` (context usage payload): payload emission now rejects invalid states where `used > max`.
- `WL-109` (MCP LSP symbol lookup): symbol `file_path` values are normalized with whitespace trimming before contract validation/output.
- `WL-110` (`thegent resume`): latest-session and resume contract strings (`session_id`, `run_id`) are normalized via trimming before selection/registration.
- `WL-114` (`--image` forwarding args): codex `--image` argument builder now rejects empty or non-string path values.

### Wave 13 Contract Hardening Notes (WL-107/108/109/110/114)

- `WL-107` (`thegent review`): validated string fields are now normalized with trimming (`summary`, `issues[].file`, `issues[].message`, `issues[].suggestion`) before returning contract output.
- `WL-108` (context usage payload): externally supplied ratio values are now accepted only when consistent with `used/max`; inconsistent ratios are ignored in favor of computed usage.
- `WL-109` (MCP LSP symbol lookup): fractional float coordinates for symbol match positions now fail loudly instead of being silently truncated.
- `WL-110` (`thegent session list`): state/registry contract strings are now normalized via trimming for listed `session_id`/`run_id` values.
- `WL-114` (`--image` forwarding args): codex `--image` argument emission now trims path values to keep forwarded args canonical.

---

## Work Stream Integration

### `thegent plan do-next` - Find Next Work Items

Find next actionable work items from WORK_STREAM.md, PLAN_STATUS, FR_TRACKER, docs/plans/, escalation queue.

**Syntax**:

```bash
thegent plan do-next [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Working directory
- `--limit, -l <N>`: Max items to return (default: 5)
- `--format, -f <format>`: Output format (`rich` \| `json`)

**Output**: List of actionable work items with IDs, prompts, dependencies, status.

**Examples**:

```bash
# Get next 5 work items (default)
thegent plan do-next

# Get next 10 work items
thegent plan do-next --limit 10

# JSON output for scripting
thegent plan do-next --format json
```

### `thegent plan get-next` - Get First Work Item Prompt

Get first work item prompt for scripting. Returns prompt only (plain text).

**Syntax**:

```bash
thegent plan get-next [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Working directory
- `--format, -f <format>`: Output (`plain` (default, prompt only) \| `json`)

**Use Case**: Scripting integration, e.g., `PROMPT=$(thegent plan get-next)`

**Examples**:

```bash
# Get prompt for scripting
PROMPT=$(thegent plan get-next)
thegent free "$PROMPT"

# JSON format
thegent plan get-next --format json
```

### `thegent plan loop` - Continuous Work Loop (RECOMMENDED)

Loop: get next item -> run bg -> repeat until no items or --max reached.

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
# Continuous loop (unbounded, recommended)
thegent plan loop

# Loop with max 10 iterations
thegent plan loop --max 10

# Loop with custom agent and sleep interval
thegent plan loop --agent codex --sleep 10

# Dry run (see what would run)
thegent plan loop --dry-run
```

### `thegent plan wait-next` - Block Until Work Ready

Block until next actionable work exists (DAG ready, do-next, escalation, inbox).

**Syntax**:

```bash
thegent plan wait-next [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Working directory
- `--poll, -p <seconds>`: Poll interval in seconds (default: 2.0)
- `--timeout, -t <seconds>`: Max wait seconds (0=unbounded, default: 0.0)
- `--sources, -s <sources>`: Comma-separated: `dag,do_next,escalation,inbox` (default: all)
- `--format, -f <format>`: Output format (`rich` \| `json`)

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

### `thegent plan incorporate` - Merge Fragments into Work Stream

Merge fragments from 02-UNIFIED-WBS.md, docs/plans/, docs/research/, docs/docset/ into WORK_STREAM.md.

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

### `thegent plan claim` / `thegent plan complete` - Work Stream Management

Claim or complete items in unified work stream.

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

### `thegent plan progress` - Show Recent Runs

Show recent runs (work-package progress). Alias for `history --limit N`.

**Syntax**:

```bash
thegent plan progress [OPTIONS]
```

**Options**:

- `--limit, -l <N>`: Number of runs to show (default: 10)
- `--format, -f <format>`: Output format (`rich` \| `json`)

---

## Background Execution & Session Management

### `thegent ps` - List Running Sessions

List active background sessions.

**Syntax**:

```bash
thegent ps [OPTIONS]
```

**Options**:

- `--all`: Show all sessions (including exited)
- `--owner <tag>`: Filter by owner tag
- `--format <format>`: Output format (`rich` \| `json` \| `md`)
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

# JSON output
thegent ps --format json
```

### `thegent wait` - Wait for Session Completion

Block until session exits.

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

### `thegent status` - Check Session Status

Check status of a background session.

**Syntax**:

```bash
thegent status <session_id> [OPTIONS]
```

**Options**:

- `--format <format>`: Output format (`rich` \| `json` \| `md`)

**Output**: Session status, metadata, output summary.

### `thegent kill` - Terminate Session

Terminate a running session.

**Syntax**:

```bash
thegent kill <session_id> [OPTIONS]
```

**Options**:

- `--force`: Force kill (SIGKILL instead of SIGTERM)

---

## Model Routing & Provider Options

### Available Providers

| Provider      | Type   | Default Model      | Notes                                   |
| ------------- | ------ | ------------------ | --------------------------------------- |
| `free`        | Direct | `gpt-5-mini`       | Copilot free tier (recommended default) |
| `claude`      | Direct | `claude-haiku-4.5` | Anthropic Claude API                    |
| `gemini`      | Direct | `gemini-3-flash`   | Google Gemini API                       |
| `copilot`     | Direct | `gpt-5-mini`       | GitHub Copilot                          |
| `codex`       | Direct | `gpt-5.3-codex`    | Codex API                               |
| `cursor`      | Proxy  | `gemini-3-flash`   | Cursor API (wisdgod)                    |
| `antigravity` | Proxy  | `gemini-3-flash`   | Antigravity proxy                       |
| `minimax`     | Proxy  | `minimax-m2.5`     | MiniMax API                             |
| `glm`         | Proxy  | `glm-5`            | Zhipu GLM API                           |
| `nim`         | Proxy  | `step-3.5-flash`   | NVIDIA NIM                              |
| `kilo`        | Proxy  | `minimax-m2.5`     | Kilo proxy                              |
| `kiro`        | Proxy  | `claude-haiku-4.5` | Kiro proxy                              |

### Model Catalog

**Anthropic Models**:

- `claude-haiku-4.5`: Fast, cost-effective (cost: 0.2, latency: 300ms, accuracy: 0.85)
- `claude-sonnet-4.5`: Balanced (cost: 0.5, latency: 600ms, accuracy: 0.92)
- `claude-sonnet-4.5-1m`: 1M context (cost: 0.6, latency: 900ms, accuracy: 0.90)
- `claude-opus-4.6`: Highest quality (cost: 1.0, latency: 1500ms, accuracy: 0.98)

**Gemini Models**:

- `gemini-3-flash`: Fast, free tier friendly (cost: 0.1, latency: 200ms, accuracy: 0.82)
- `gemini-3-pro`: Higher quality (cost: 0.4, latency: 800ms, accuracy: 0.91)

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

### Routing Policies

| Policy          | Description                        | Use Case                                |
| --------------- | ---------------------------------- | --------------------------------------- |
| `prefer_direct` | Prefer direct provider connections | Low latency, high reliability (default) |
| `prefer_proxy`  | Prefer proxy connections           | Cost optimization, rate limit handling  |
| `failover`      | Try primary, fallback on failure   | High availability                       |
| `round_robin`   | Distribute across routes           | Load balancing                          |
| `cheapest`      | Select cheapest route              | Cost optimization                       |
| `cost_quality`  | Balance cost and quality           | Optimal value                           |
| `pareto`        | Pareto frontier optimization       | Multi-objective optimization            |
| `roi`           | Return on investment optimization  | Business value                          |

**Default**: `prefer_direct` (configurable via `THGENT_DEFAULT_ROUTING`)

### Model-First Routing

**When to Use**: Specify model without provider, let thegent resolve provider automatically.

**Syntax**:

```bash
thegent run "Task" -M <model> [--provider <provider>] [--routing <policy>]
```

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

## DAG Commands

### `thegent dag list` - List DAG Tasks

Parse and display DAG session from `.factory/dag-session.md`.

**Syntax**:

```bash
thegent dag list [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Working directory (default: cwd)
- `--format, -f <format>`: Output format (`rich` \| `md`)

### `thegent dag run` - Execute DAG

Execute DAG tasks in dependency order.

**Syntax**:

```bash
thegent dag run [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Working directory
- `--agent <agent>`: Agent for tasks (default: `free`)
- `--dry-run`: Show execution plan without running

### `thegent dag sync` - Sync DAG State

Update task status from session exit.

**Syntax**:

```bash
thegent dag sync [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Working directory

### `thegent dag update` - Update DAG State

Update DAG state manually.

**Syntax**:

```bash
thegent dag update [OPTIONS]
```

### `thegent dag validate` - Validate DAG

Validate DAG: cycles, orphans, agent names. Exit 2 on failure.

**Syntax**:

```bash
thegent dag validate [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Working directory (default: cwd)

---

## Planning Commands

### `thegent plan analyze` - Planning Simulation Overlays

Run planning simulation overlays (XD1–XD3): PERT, resources, continuity risk.

**Syntax**:

```bash
thegent plan analyze [OPTIONS]
```

**Options**:

- `--cd, -d <path>`: Working directory
- `--pert`: Run PERT overlay on DAG tasks
- `--resources`: Simulate resource contention
- `--continuity`: Score continuity risk for handoff
- `--format, -f <format>`: Output format (`json` \| `rich`)

---

## Configuration & Setup

### `thegent config check` - Validate Configuration

Validate config; fail-fast on misconfig.

**Syntax**:

```bash
thegent config check [OPTIONS]
```

**Options**:

- `--format <format>`: Output format (`rich` \| `json`)

### `thegent setup` - Initialize Thegent

Initialize thegent: configure MCP clients and background services.

**Syntax**:

```bash
thegent setup [OPTIONS]
```

**Options**:

- `--force`: Force re-initialization

### `thegent doctor` - Health Checks

Run comprehensive health and preflight checks.

**Syntax**:

```bash
thegent doctor [OPTIONS]
```

**Options**:

- `--fix`: Try to fix common issues automatically

---

## Phench Runtime Control Plane

`phench` manages deterministic execution across local repositories using
`~/CodeProjects/Phenotype/projects/<target>/repos` (or `THGENT_PHENOTYPE_ROOT` override).

### `thegent phench target bootstrap` - Seed a target from sibling repos

Create a target lock and optionally lock it in one step.

**Syntax**:

```bash
thegent phench target bootstrap <target> --source-root <dir> --ref <ref> --include <glob> --exclude <glob>
```

**Notes**:

- Omit `--source-root` to default to the sibling `repos/` root.
- `--ref` sets the initial selection for each discovered repo.
- Use `--no-auto-lock` if you need to adjust entries before locking.

## Module manifest schema

Manifest path:

- `~/CodeProjects/Phenotype/projects/modules/<module-name>/manifest.json`

```json
{
  "schema_version": 1,
  "repo_ids": ["thegent-api", "thegent-control-plane"],
  "repo_patterns": ["*mcp*"],
  "repo_ref_overrides": { "thegent-api": "main" },
  "repo_runner_overrides": { "thegent-api": "task" },
  "repo_command_overrides": { "thegent-api": "hello" },
  "repo_env_profile_overrides": { "thegent-api": "ci" }
}
```

Notes:

- `schema_version` defaults to `1` when omitted in existing manifests.
- `repo_ids` and `repo_patterns` are optional; at least one must be present.
- `repo_patterns` expands against repos in the selected target lock.
- Only repos in the selected target are runnable. Unknown repo keys in override maps fail fast.
- `repo_env_profile_overrides` accepts per-repo profile names and overrides `--env-profile`.

### `thegent phench modules audit` - Find shared modules across sibling repos

Scan repository checkouts and surface modules that appear across multiple repos.

**Syntax**:

```bash
thegent phench modules audit [OPTIONS]
```

**Options**:

- `--source-root <dir>`: Root containing repo checkouts (defaults to `THGENT_PHENOTYPE_REPOS_ROOT`).
- `--include-repo <glob>`: Limit to repositories matching a glob pattern (repeatable).
- `--exclude-repo <glob>`: Exclude repositories matching a glob pattern (repeatable).
- `--skip-repo <repo-id>`: Explicit repository IDs to skip (repeatable).
- `--min-repo-count <n>`: Minimum repo ownership count for shared module reporting (default `2`).
- `--include-module <name>`: Restrict scan to specific module names (repeatable).
- `--exclude-module <name>`: Exclude module names from scan (repeatable).
- `--include-repo-modules-root/--no-include-repo-modules-root`: Include or ignore `<repo>/modules/<module>/manifest.json` as ownership signal.

**Notes**:

- Modules are discovered from:
  - `src/<module>/__init__.py` package markers.
  - `<repo>/modules/<module>/manifest.json` when enabled.
- Default exclusions include: `4sgm`, `trace`, `parpour`, `civ`.

```bash
thegent phench modules audit --source-root ../repos --min-repo-count 2
thegent phench modules audit --include-module thegent-app --exclude-module legacy
```

### `thegent phench modules sync` - Sync module manifests into `projects/modules`

Collect repo-local module manifests and mirror them into
`~/CodeProjects/Phenotype/projects/modules/<module>/manifest.json`.

**Syntax**:

```bash
thegent phench modules sync [OPTIONS]
```

**Options**:

- `--source-root <dir>`: Root containing repos to scan.
- `--destination-root <dir>`: Destination module root for sync output.
- `--include-repo <glob>` / `--exclude-repo <glob>`: Repository include/exclude filter.
- `--include-module <name>` / `--exclude-module <name>`: Restrict which modules are copied.
- `--overwrite`: Replace existing manifests.
- `--dry-run` / `-n`: Preview copy plan only.

```bash
thegent phench modules sync --dry-run --source-root ../repos --include-module thegent-app
thegent phench modules sync --source-root ../repos --destination-root ../projects/modules --overwrite
```

### `thegent phench projects run` - Orchestrate target runs

Execute a command against selected repo(s) in a target.

**Syntax**:

```bash
thegent phench projects run --target <target> --runner <runner> --command <command>
```

**Options**:

- `--repo-id`: Single repo target.
- `--repo-ref <repo-id>@<ref>`: Explicit per-repo branch/tag/SHA mapping (repeatable).
- `--ref` / `--branch`: Shared ref for selected repo or all repos.
- `--include-repo <glob>` / `--exclude-repo <glob>`: Limit repo scope by glob before selection.
- `--module <module-name>`: Resolve module manifest from
  `~/CodeProjects/Phenotype/projects/modules/<module-name>/manifest.json` and run that repo subset.
- `--all-repos`: Execute across all repos in the target.
- `--mode serial|parallel`: Multi-repo execution mode.
- `--env-profile <name>`: Apply profile globally, then per-repo overrides from manifest.
- `--snapshot-id <id>`: Run using a previously captured snapshot state from `phench snapshot create`.
- `--timeline-limit N`: Refs shown during interactive selection.
- `--no-prepare`: Skip automatic `lock` and `materialize` before run.

**Module override precedence** (highest to lowest):

- CLI `--repo-ref` overrides manifest `repo_ref_overrides` for matching repos.
- CLI `--runner` / `--command` overrides both manifest runner/command overrides.
- `repo_runner_overrides`, `repo_command_overrides`, `repo_env_profile_overrides` from manifest
  apply to matching repos unless overridden by CLI arguments.

**Examples**:

```bash
# Run per-repo refs from feature branches in one command
thegent phench projects run \
  --target thegent-app \
  --runner task \
  --command hello \
  --repo-ref thegent-api@feature-gui \
  --repo-ref thegent-control-plane@feat/scheduler

# Run by module manifest subset with module-level env profile override
thegent phench projects run \
  --target thegent-app \
  --module thegent-mcp \
  --runner task \
  --command hello \
  --env-profile default \
  --no-interactive

# Run from a snapshot (stable point-in-time materialization)
thegent phench projects run \
  --target thegent-app \
  --snapshot-id snap-20260302T120000Z \
  --runner task \
  --command hello
```

### `thegent phench projects status` - Show target state

Show lock/runtime/env snapshot for a target.

**Syntax**:

```bash
thegent phench projects status --target <target>
```

### `thegent phench tui` - Interactive selector then run

Open interactive target/repo/ref selection and run immediately.

**Syntax**:

```bash
thegent phench tui --runner <runner> --command <command> [--target <target>]
```

If you omit `--target` and multiple targets exist, the CLI prompts for target.

---

## Provider Authentication

### `thegent login` / `thegent cliproxy login` - Provider Login

Run login for provider. Unified flow: open URL + prompt for API key.

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

## MCP Integration

### `thegent mcp serve` - Start MCP Server

Start thegent MCP server for IDE integration.

**Syntax**:

```bash
thegent mcp serve [OPTIONS]
```

**Options**:

- `--port <port>`: HTTP port (default: 8000)
- `--host <host>`: Host (default: localhost)

**Behavior**: Delegates to launchd/Homebrew service when available.

### MCP Tools

Thegent exposes MCP tools for:

- Agent execution (`thegent_run`, `thegent_bg`)
- Work stream management (`plan_do_next`, `plan_claim`, `plan_complete`)
- Session management (`ps`, `status`, `wait`)
- DAG operations (`dag_list`, `dag_run`, `dag_sync`)

---

## Command Examples

### Example 1: Continuous Autonomous Work (Recommended)

```bash
# Continuous loop processing work stream items
thegent plan loop
```

### Example 2: Single Work Item Execution

```bash
# Run next work item
thegent free --do-next

# Run next 5 items sequentially
thegent free --do-next --repeat 5
```

### Example 3: Idle Waiting (Instead of Busy Loops)

```bash
# Wait for work to become available
thegent plan wait-next

# Wait with timeout
thegent plan wait-next --timeout 300
```

### Example 4: Background Execution with Session Management

```bash
# Start background task
thegent bg "Long task" free

# Monitor sessions
thegent ps

# Wait for completion
thegent wait <session_id>

# Check status
thegent status <session_id>
```

### Example 5: Model-Specific Routing

```bash
# Model-first routing
thegent run "Complex task" -M claude-sonnet-4.5

# With routing policy
thegent run "Cost-sensitive task" -M gemini-3-flash -R cheapest

# With failover
thegent run "Critical task" -M claude-opus-4.6 --failover
```

### Example 6: Continuation from Prior Sessions

```bash
# Continue from prior session
thegent bg "Continue implementation" -C <session_id>

# Continue with stderr
thegent bg "Debug issue" -C <session_id> --continuation-stderr
```

---

## Environment Variables

### Timeout Configuration

- `THGENT_DEFAULT_TIMEOUT`: Default agent timeout (default: 90s)
- `THGENT_DEFAULT_TIMEOUT_CLAUDE`: Claude agent timeout (default: 300s)
- `THGENT_DEFAULT_TIMEOUT_FREE`: Free agent timeout (default: 300s)

### Routing Configuration

- `THGENT_DEFAULT_ROUTING`: Default routing policy (`prefer_direct` \| `prefer_proxy`)

### Session Configuration

- `THGENT_OWNER_TAG`: Explicit owner tag override
- `THGENT_OWNER_SCOPE`: Owner scope (supports `{user}`, `{uid}`, `{pid}`, `{ppid}`, `{cwd}` placeholders)

### Debug Configuration

- `THGENT_DEBUG`: Enable debug mode (1=enabled)

---

## Best Practices

1. **Use `thegent plan loop`** for continuous autonomous work (recommended)
2. **Use `thegent plan wait-next`** instead of busy loops
3. **Use `thegent free`** as default agent (free tier, work stream integration)
4. **Use `thegent bg`** for long-running or parallel tasks
5. **Use model-first routing** (`-M`) when model matters more than provider
6. **Use routing policies** (`-R`) for cost/quality optimization
7. **Use `--do-next`** for automatic work stream integration
8. **Use `--repeat`** for sequential work item execution
9. **Use session management** (`ps`, `wait`, `status`) for background tasks
10. **Use `--continuation`** to continue from prior sessions

---

## Anti-Patterns to Avoid

1. **Don't use busy loops**: Use `plan wait-next` or `wait <session_id>`
2. **Don't use bash wrappers**: Use native `--repeat`, `--do-next`, `plan loop`
3. **Don't poll manually**: Use `plan wait-next` with polling
4. **Don't ignore work stream**: Use `plan do-next` and `plan incorporate`
5. **Don't hardcode agents**: Use `free` as default, override when needed

---

## See also

- [CLAUDE.md](../../CLAUDE.md) — Claude-specific instructions with thegent command reference
- [THGENT_COMMAND_MODEL_OPTIONS_AND_AGENT_FEATURES_RESEARCH.md](../research/THGENT_COMMAND_MODEL_OPTIONS_AND_AGENT_FEATURES_RESEARCH.md) — Comprehensive research document
- [WORK_STREAM.md](../reference/WORK_STREAM.md) — Unified work stream
- [PROCESS_OPTIMIZATION_PLAN.md](../plans/PROCESS_OPTIMIZATION_PLAN.md) — Process optimization
