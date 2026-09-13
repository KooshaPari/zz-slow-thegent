# CLAUDE Appendix: thegent-specific and domain workflow rules

### thegent-Specific Rules

- Use tach.toml for boundary enforcement (already configured)
- All new agents must use the agent runner strategy pattern
- **Rust tooling**: Prefer `rg` over `grep`, `fd` over `find`, `jaq` over `jq` for faster hook/agent execution. Hooks use grep-wrapper (routes to rg), fd-wrapper, and JQ_CMD (jaq first). For Claude Code: `export USE_BUILTIN_RIPGREP=0` to use system ripgrep (5-10x faster than bundled).
- All new hooks must follow existing hook patterns in hooks/
- Provider pattern: use ProviderRegistry for extensible services
- MCP tools go through the standard FastMCP registration

---

## Domain-Specific Patterns

### What thegent Is

thegent is an **MCP server + agent hook system** for governing AI agent lifecycle and quality. The core domain is: define agents (personas with capabilities), dispatch hooks at lifecycle events (session start, tool use, stop), enforce governance policies (cost, quality, security), and expose MCP tools for agent management. It is fundamentally an **agent orchestration and governance platform**.

### Local Development (Present)

**Dev stack**: MCP server + CLIProxyAPIPlus proxy via process-compose. Taskfile drives setup and dev.

| Task                                     | Purpose                                                                    |
| ---------------------------------------- | -------------------------------------------------------------------------- |
| `task setup`                             | Install deps, build cliproxy plusplus source, ensure config, install shims |
| `task dev`                               | Build cliproxy, ensure config, start MCP + proxy (TUI)                     |
| `task dev:bg`                            | Same as dev, background                                                    |
| `task dev:down`                          | Stop all services                                                          |
| `task dev:logs`                          | Follow service logs                                                        |
| `task cliproxy:build`                    | Build `../cliproxyapi-plusplus/cli-proxy-api-plus`                         |
| `task cliproxy:ensure-config`            | Ensure cliproxy config (port, auth-dir)                                    |
| `task cliproxy:start`, `stop`, `restart` | Proxy lifecycle                                                            |

**Proxy binary**: `scripts/start_proxy_dev.sh` uses the plusplus binary when built (`task cliproxy:build`), else falls back to `cli-proxy-api-plus` from PATH. process-compose runs this wrapper for the proxy process.

**Ports**: MCP 3847, proxy 8317. Canonical source at `../cliproxyapi-plusplus`; metrics at `GET /v1/metrics/providers`.

**Debug**: `thegent run --debug` sets `THGENT_DEBUG=1`; proxy gets `-debug` when env set. See `docs/plans/DEBUG_TAGS_AND_METRICS.md`.

### Key Ports and Interfaces

| Port                | Responsibility                                                  | Location                                          |
| ------------------- | --------------------------------------------------------------- | ------------------------------------------------- |
| **AgentRunner**     | Strategy pattern for executing agent personas                   | `agents/`                                         |
| **HookDispatcher**  | Dispatches lifecycle hooks (pre/post tool use, stop, etc.)      | `hooks/hook-dispatcher/`, `hooks/*-dispatcher.sh` |
| **PolicyEngine**    | Evaluates governance rules (cost caps, quality gates, security) | `hooks/qa-policy-engine.sh`, `contracts/`         |
| **MCPToolRegistry** | Registers and serves MCP tools to connected clients             | MCP server entry point                            |
| **CommandRegistry** | CLI commands for agent management, DAG compilation, spec ops    | `commands/`                                       |
| **ContractStore**   | Stores and validates governance contracts and policies          | `contracts/`                                      |

### Provider Registry and Agent Strategy

- **Agent personas** live in `agents/` as markdown definitions. New agents = new `.md` file describing the persona, capabilities, and constraints.
- **Hooks** follow a strict naming and dispatch pattern. The dispatcher routes events to matching hook scripts. New hooks = new `.sh` file in `hooks/` following the naming convention (`qa-*.sh` for quality gates, `pre-*.sh` for pre-tool hooks, etc.).
- **Commands** in `commands/` define CLI-accessible operations (DAG compilation, ledger init, spec hashing). New commands = new entry in `commands/` + registration.
- **Contracts** define governance policies (cost limits, SLOs, migration rules). New governance rule = new contract JSON in `contracts/`.

### Common Anti-Patterns to Avoid

- **Direct MCP message handling in domain logic** -- MCP protocol concerns stay in the MCP server layer. Domain logic (agents, hooks, policies) must not import or depend on MCP transport
- **Custom agent discovery** -- Use the agent registry pattern. Never glob for agent files at runtime outside the registry
- **Hooks that bypass the dispatcher** -- All hooks fire through `hook-dispatcher/`. Never call hook scripts directly from application code
- **Inline governance rules** -- Cost caps, quality thresholds, and policy rules belong in `contracts/` or `hooks/hook-config.yaml`, not hardcoded in hook scripts
- **Monolithic hook scripts** -- Shared logic goes in `hooks/lib/`. Hook scripts should be thin dispatchers that call library functions

### Sitback Agent

`thegent sitback` launches Claude Code with a Sitback Agent persona: dashboard (cockpit + terminals + ps), FastMCP tools first, CLI fallback. Skills: `skills/sitback-agent/` (default), overridable via `--skill`. MCP precondition: `thegent serve` for full toolset.

### Workflow Triggers (Skill / MCP / Instruction)

Idea/task prompts, quality green, and "next thing to do" are wired at multiple levels:

| Level            | Location                                                                                                              | Purpose                                                                                                                                                |
| ---------------- | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Hook**         | `hooks/prompt-submit-guard.sh`                                                                                        | UserPromptSubmit: pattern-detect, inject instructions to agent context                                                                                 |
| **Skill**        | `skills/agent-orchestra/SKILL.md`, `skills/sitback-agent/SKILL.md`                                                    | Baked-in workflow section; agents with these skills follow it                                                                                          |
| **MCP resource** | `thegent://workflow/triggers`                                                                                         | URI-addressable; agent can read when needed                                                                                                            |
| **MCP resource** | `thegent://workstream`                                                                                                | Work stream (canonical backlog)                                                                                                                        |
| **MCP prompts**  | `thegent_workflow_idea`, `thegent_workflow_quality_green`, `thegent_workflow_next_item`, `thegent_workflow_gardening` | Template prompts for structured invocation                                                                                                             |
| **MCP resource** | `thegent://workflow/gardening`                                                                                        | Gardening workflow (converge to empty backlog + green)                                                                                                 |
| **MCP tool**     | `thegent_do_next`                                                                                                     | Find next actionable items from WORK_STREAM (canonical), PLAN_STATUS, FR_TRACKER, docs/plans/, escalation; returns prompt_suggestion for `thegent run` |
| **CLI**          | `thegent plan next`                                                                                                   | Same as thegent_do_next                                                                                                                                |

**Unified work stream**: Single source of truth is `docs/reference/WORK_STREAM.md`. All agents read it for work items; claim in CLAIMED before starting; update COMPLETED when done. Incorporator agent (`work-stream-incorporator`) merges fragments from plans, research, specs into the stream. See [UNIFIED_WORK_STREAM_DESIGN.md](docs/reference/UNIFIED_WORK_STREAM_DESIGN.md).

**Idea/task** → dump research to docs/research/, specs to docs/docset/, work items to unified stream. **Quality green** → `task quality-a-r`. **Next item** → `thegent_do_next` (or read WORK_STREAM.md), pick highest-priority, execute via `thegent run`/`--bg` with `prompt_suggestion`. **Gardening** → check gov traceability, tests, plan items; dispatch; converge to empty backlog and complete green (`thegent govern go health`, `go cycle`, `task quality-a-r`).

### Cycleloop Loops

| Command / Tool                                        | Purpose                                                 |
| ----------------------------------------------------- | ------------------------------------------------------- |
| `thegent orchestrate loop "prompt" "todo"`            | Run Cycleloop loop (worker + checker)                   |
| `thegent orchestrate loop-send <session_id> <prompt>` | Send next prompt to running loop (human/agent takeover) |
| `thegent orchestrate loop-stop <session_id>`          | Stop loop                                               |
| `thegent takeover <session>`                          | Attach to tmux session; human types next prompt         |
| `thegent_loop_takeover` (MCP)                         | Agent injects prompt into running loop                  |
| `--continuation <session_id>`                         | Resume from prior session (adds resumption appendix)    |
| `--resume` (Codex/Claude)                             | Use when agent supports native resume                   |

**Premature session end:** If Codex/Claude supports `--resume`, use it. Otherwise: `thegent run agent --continuation <prior_session_id> "Task"` — builds context from prior stdout + resumption appendix.

### WBS Agent Coordination (Multi-Agent "Do All")

When the user says **"do all"** or assigns work to multiple agents:

1. **Read** `docs/reference/WORK_STREAM.md` (canonical) — or `docs/plans/02-UNIFIED-WBS.md` + `docs/reference/WBS_AGENT_PROGRESS.md` for WBS-only coordination
2. **Claim before starting**: Append your work items to the **CLAIMED** table in `WORK_STREAM.md` (or `WBS_AGENT_PROGRESS.md` if using WBS-only) with a unique agent_id (e.g. `agent-1`, `runner-A`)
3. **Avoid overlap**: Do NOT pick items already in CLAIMED. Pick an equal batch of unclaimed items.
4. **Update progress**: When done, move items from CLAIMED to COMPLETED and update source file (e.g. `02-UNIFIED-WBS.md`) status to DONE

**Preferred**: Use `WORK_STREAM.md` — single file for all work types. `WBS_AGENT_PROGRESS.md` remains for backward compatibility with WBS-only "do all" flows.

### Where to Add New Functionality

| Want to add...        | Put it in...                                                               |
| --------------------- | -------------------------------------------------------------------------- |
| New agent persona     | `agents/<persona-name>.md` -- follows existing agent template              |
| New lifecycle hook    | `hooks/<event>-<name>.sh` + register in `hooks/hook-config.yaml`           |
| New governance policy | `contracts/<policy>.json` + wire into `qa-policy-engine.sh`                |
| New MCP tool          | MCP server registration (FastMCP pattern)                                  |
| New CLI command       | `commands/<command>/` + register in command dispatch                       |
| New quality gate      | `hooks/qa-<gate-name>.sh` following existing `qa-*.sh` patterns            |
| Shared hook utility   | `hooks/lib/<utility>.sh` -- sourced by hook scripts, never called directly |

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
