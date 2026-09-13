<DONE>
# Codex CLI Harness Overhaul — Full Design V2

**Date:** 2026-02-20
**Status:** Design Specification
**Supersedes:** `CODEX_OVERHAUL_DESIGN.md` (V1, proxy-side only)
**Scope:** Fork strategy, CLI-layer extensions, SDK extraction, new modalities, phased roadmap
**Audience:** Engineering, infrastructure, agent-orchestration team

---

## 0. Orientation: What the Source Actually Reveals

Before designing extensions, the upstream source was audited. Key facts that directly shape every decision below:

### 0.1 Project Memory — Already Present (AGENTS.md / skills)

The upstream Rust CLI already implements project-memory loading in `codex-rs/core/src/project_doc.rs`. It walks the directory tree from the Git root to `cwd`, concatenates every `AGENTS.md` found, and injects the result as user instructions. Key config knobs:

- `project_doc_fallback_filenames` — ordered list of alternative filenames; `AGENTS.md` is the default
- `project_doc_max_bytes` — per-file budget (default 32 KiB)
- `AGENTS.override.md` — local override file; preferred over `AGENTS.md` when both exist
- `project_root_markers` — defaults to `[".git"]`; configurable

The config schema (`config.schema.json`) already exposes `instructions` (inline system instructions), `developer_instructions` (injected as developer-role message), and `model_instructions_file` (path to file overriding built-in model instructions). **Critically, the fallback filename list can be set to `["CODEX.md", "CLAUDE.md"]` via config — zero code changes needed for custom project-doc filenames.**

### 0.2 Skills — Already Present (SKILL.md standard)

The upstream CLI ships a complete skills system at `codex-rs/core/src/skills/`. It loads `SKILL.md` files from `~/.codex/skills/<name>/SKILL.md` (and project-level equivalents). Skills are injected into the system prompt alongside project docs. The skills format is the Anthropic Agent Skills standard (same as Claude Code and Gemini CLI — full cross-harness portability).

Skills have: frontmatter (name, description), optional `metadata.toml` (interface, dependencies, brand color), `scripts/` directory for runnable code, `assets/` for templates. The `SkillsConfig` struct in `config/types.rs` allows explicit path + enabled/disabled per skill.

### 0.3 Session Resume — Already Present

The CLI already ships `codex resume [SESSION_ID]` and `codex resume --last` (interactive TUI). The exec binary also supports `codex exec resume --last <prompt>` for non-interactive session continuation. Sessions are stored as thread state in `~/.codex/` (SQLite-backed via `codex_core::ThreadManager`). **Session persistence is solved for interactive mode; the gap is in non-interactive (`exec`) mode with the `--json` JSONL output path.**

### 0.4 TypeScript SDK — Already Present

`sdk/typescript/` ships `@openai/codex-sdk`. It wraps the binary via stdin/stdout JSONL. Public API: `Codex`, `Thread`, `turn.run()`, `thread.runStreamed()` (async generator). Events: `item.completed`, `turn.completed`. The SDK is already extracted — the gap is thegent's `codex_proxy.py` not using it.

### 0.5 App-Server Mode — Already Present

`codex app-server` exposes a local HTTP/WebSocket-based server (the same protocol used by the VS Code extension). It supports `codex app-server generate-ts` and `codex app-server generate-json-schema` for protocol introspection. **An OpenAI-compatible REST API is not yet implemented**, but the app-server infrastructure exists.

### 0.6 What is Genuinely Missing

After audit, the actual gaps are narrower than V1 assumed:

| Feature | Status in Upstream | Gap |
|---|---|---|
| Project memory (AGENTS.md) | Fully implemented | Config aliases for CODEX.md / CLAUDE.md |
| Skills system (SKILL.md) | Fully implemented | thegent doesn't populate `~/.codex/skills/` |
| Session resume (interactive) | Fully implemented | `exec --json` mode doesn't support resume |
| TypeScript SDK | Ships with repo | thegent uses subprocess directly; SDK not used |
| HTTP API mode | App-server present, not OpenAI-compat | `/v1/chat/completions`-style REST endpoint missing |
| WebSocket mode | App-server protocol | Stable programmatic client not shipped |
| Hooks system | `notify` callback (exit only) | No pre/post-tool hooks |
| Batch mode | Not present | No multi-prompt file input |
| Eval mode | Not present | No benchmark harness |
| Sub-agent spawning as a tool | Not present | No `codex spawn` tool call |
| `--codex-home` flag | Not present | State isolation requires `HOME` env override |
| Context compression in exec | Not present | `compact_remote.rs` only for TUI |

---

## 1. Fork vs Contribute Strategy

### 1.1 Decision Framework

The fork/contribute decision is based on one question per change: **does the change alter the behavioral contract of the upstream CLI in a way that OpenAI is unlikely to accept, or does it require adding behavior that only makes sense in the thegent governance context?**

### 1.2 Changes That MUST Be Forked

These modify behavioral semantics or add infrastructure that upstream will not carry:

| Change | Why Fork Required | Fork Location |
|---|---|---|
| Pre/post-tool hooks (`pre-tool-<name>.sh`, `post-tool-<name>.sh`) | Runs arbitrary local scripts before/after every model tool call. Security surface that upstream cannot generalize. | `codex-rs/core/src/hooks/` (new module) |
| Session-start / session-end hooks | Same reasoning; hooks into session lifecycle internals | `codex-rs/exec/src/lib.rs` hook dispatch points |
| Sub-agent spawning as a first-class tool (`codex_spawn`) | Adds a new built-in tool to the tool registry; upstream would need governance policy for this | `codex-rs/core/src/tools/spawn.rs` (new) |
| Global memory injection (`~/.codex/memory.md`) | Already possible via `instructions` config; fork only if we need automatic watch+reload semantics | Thin: config layer only, no fork needed |
| `--codex-home` flag | Structural change to how `CODEX_HOME` is resolved; upstream has open interest in this but hasn't shipped it | `codex-rs/core/src/config/mod.rs` — `find_codex_home()` |
| Context compression in `exec --json` mode | Upstream `compact.rs` and `compact_remote.rs` are TUI-gated; wiring them into exec path requires threading through the event processor | `codex-rs/exec/src/event_processor_with_jsonl_output.rs` |

**Minimal fork delta rule:** The fork MUST be a thin patch layer. Every forked file MUST have a comment block at the top: `// THEGENT FORK: <reason> -- upstream PR: <link or "pending">`. This makes merge tracking explicit.

### 1.3 Changes That CAN Be Upstreamed

These are generally useful improvements with no thegent-specific behavior:

| Change | Upstream PR Rationale | Effort |
|---|---|---|
| `--codex-home` / `CODEX_HOME` env var for state isolation | Directly useful for multi-instance workloads; OpenAI has acknowledged the need | Small: ~30 lines in `find_codex_home()` |
| `exec resume --last --json` (non-interactive resume with JSONL output) | The exec binary already has `resume` for interactive; the JSON path is missing | Medium: wire `ThreadManager::resume` through exec event processor |
| Enhanced JSONL output events (`session.started` with session_id, `tool.started` / `tool.completed` with duration) | Useful for any programmatic consumer | Small: add fields to existing event structs in `exec_events.rs` |
| `--output-last-message` writes session_id in addition to final message | Trivial, high utility for scripting | Trivial |
| SSE/streaming improvements in the responses-api-proxy | Bug-class fix; upstream benefits directly | Medium |
| `project_doc_fallback_filenames` documented example for CLAUDE.md | Documentation only | Trivial |

### 1.4 Changes That Are Config-Only

These require zero code changes — configure via `~/.codex/config.toml` or `-c` overrides:

```toml
# ~/.codex/config.toml additions for thegent integration

# Accept CLAUDE.md and CODEX.md as project-doc filenames (config-only, no fork)
project_doc_fallback_filenames = ["CODEX.md", "CLAUDE.md"]

# Memory file as inline instructions supplement
instructions = "see ~/.codex/memory.md"
# OR point directly at a file:
# model_instructions_file = "/Users/<user>/.codex/memory.md"

# Skills are config-only: populate ~/.codex/skills/<name>/SKILL.md
# No code change needed; the skills system is already live

# Notify hook (exit-time shell callback — already shipped)
notify = ["thegent", "codex-session-end", "--json-payload"]
```

---

## 2. CLI Harness Extensions (Fork-Required)

### 2.1 Hooks System

**Existing hook infrastructure:** The upstream CLI ships one hook point: `notify` — a shell command called when the agent finishes a turn. It receives a JSON payload via argument. This is the `notify` field in `ConfigToml`. There is no pre/post-tool hook or session-lifecycle hook.

**Target hook architecture:** Model after Gemini CLI's hook system (which is the richest among the surveyed harnesses), constrained to what can be injected without restructuring the upstream event loop.

#### 2.1.1 Hook Directory Structure

```
.codex/hooks/              # project-local hooks (highest precedence)
  pre-tool-<name>.sh       # called before each tool execution
  post-tool-<name>.sh      # called after each tool execution
  session-start-<name>.sh  # called once at session start
  session-end-<name>.sh    # called once when session ends

~/.codex/hooks/            # user-global hooks (lower precedence)
  pre-tool-<name>.sh
  post-tool-<name>.sh
  session-start-<name>.sh
  session-end-<name>.sh
```

Hooks are discovered at startup. Multiple hooks per event are supported (lexicographic order). A hook that exits non-zero **blocks** the tool call and surfaces an error to the model — intentional fail-fast behavior consistent with thegent policy.

#### 2.1.2 Hook Payload Format (stdin JSON)

Each hook receives a JSON object on stdin:

```json
{
  "event": "pre-tool",
  "session_id": "uuid-string",
  "tool": {
    "name": "shell",
    "id": "tool_abc123",
    "input": {"command": "rm -rf /tmp/foo"}
  },
  "context": {
    "cwd": "/repo/src",
    "model": "gpt-5.3-codex",
    "turn_index": 4
  }
}
```

For `post-tool`, the payload adds `"result": { "output": "...", "exit_code": 0, "duration_ms": 340 }`.

For `session-start` / `session-end`, the payload uses `"event": "session-start"` and includes `"context"` only.

Hook stdout is ignored. Hook stderr is surfaced as a warning in the JSONL stream. A hook's exit code non-zero causes the parent operation to fail with the hook's stderr as the error message.

#### 2.1.3 Rust Injection Points

The hooks system needs three injection points in the forked Rust code:

**Point 1:** Session lifecycle — in `codex-rs/exec/src/lib.rs`, after `ThreadManager::create_thread()` succeeds, call `HookDispatcher::dispatch_session_start()`. Before the event processor loop exits, call `HookDispatcher::dispatch_session_end()`.

**Point 2:** Pre-tool — in `codex-rs/core/src/exec.rs`, the function that prepares a tool call for execution. Before the actual tool subprocess is spawned (after approval, if any), call `HookDispatcher::dispatch_pre_tool()`. If the hook returns non-zero, return an error event instead of executing the tool.

**Point 3:** Post-tool — in the same `exec.rs` function, after the tool result is collected, call `HookDispatcher::dispatch_post_tool()` with the result payload.

**New module:** `codex-rs/core/src/hooks/mod.rs`:

```
hooks/
  mod.rs          — HookDispatcher struct, dispatch_* methods
  discovery.rs    — Scan ~/.codex/hooks/ and .codex/hooks/, build ordered lists
  runner.rs       — Spawn hook script, pipe JSON to stdin, collect stderr, return exit code
```

The `HookDispatcher` is constructed once at session start from the `Config` (which has `codex_home` and `cwd`). It holds the discovered hook lists as `Vec<PathBuf>` per event type.

#### 2.1.4 Config Registration (Fork)

Add to `ConfigToml` in `config/mod.rs`:

```rust
/// Hook configuration.
pub hooks: Option<HooksConfig>,
```

```rust
#[derive(Serialize, Deserialize, Debug, Clone, Default, JsonSchema)]
pub struct HooksConfig {
    /// Whether hooks are enabled. Defaults to true when hooks directory exists.
    #[serde(default = "default_true")]
    pub enabled: bool,

    /// Maximum time in milliseconds a hook may run before being killed.
    #[serde(default = "default_hook_timeout_ms")]
    pub timeout_ms: u64,
}

fn default_hook_timeout_ms() -> u64 { 5000 }
fn default_true() -> bool { true }
```

### 2.2 Skills and CODEX.md Equivalent

**Current state:** The upstream skills system is fully operational. Skills live in `~/.codex/skills/<name>/SKILL.md`. The project-doc system already loads `AGENTS.md` from the git-root to cwd path. Adding `CODEX.md` as a recognized alias is a config-only change.

**What thegent needs to do (no fork):**

1. Configure `project_doc_fallback_filenames = ["CODEX.md", "CLAUDE.md"]` in `~/.codex/config.toml` to accept both naming conventions. This lets projects place a `CODEX.md` or `CLAUDE.md` and have it auto-loaded alongside (or instead of) `AGENTS.md`.

2. Populate `~/.codex/skills/<name>/SKILL.md` with thegent-specific skills (governance hooks, quality-gate procedures, code review workflows). These are normal text files — no code change needed.

3. For global memory (`~/.codex/memory.md`): use the `model_instructions_file` config field, which already accepts an absolute path to any file. The file is loaded verbatim as base model instructions.

**Thin fork needed only for:** Auto-populating `~/.codex/skills/` from a `SKILLS.md`-index file or from a remote skills registry. This is a thegent orchestration feature, not a Codex core feature — implement in thegent's setup tooling, not the Codex fork.

#### 2.2.1 Project Memory File Hierarchy

```
~/.codex/memory.md           — global memory (injected via model_instructions_file)
~/.codex/skills/<name>/
  SKILL.md                   — skill instructions (YAML frontmatter + markdown body)
  metadata.toml              — optional: interface, dependencies
  scripts/                   — optional: runnable scripts
  assets/                    — optional: templates

<repo-root>/AGENTS.md        — project-level memory (auto-loaded by Codex core)
<repo-root>/CODEX.md         — alternative naming (via project_doc_fallback_filenames)
<cwd>/AGENTS.md              — sub-project docs (appended if different from root)
<cwd>/AGENTS.override.md     — local override (takes precedence over AGENTS.md)
```

**Config to wire this up (zero code change):**

```toml
# ~/.codex/config.toml

project_doc_fallback_filenames = ["CODEX.md", "CLAUDE.md"]
model_instructions_file = "/Users/<user>/.codex/memory.md"
project_doc_max_bytes = 65536  # 64 KiB; upstream default is 32 KiB
```

### 2.3 Session Persistence in Exec Mode

**Current state:** `codex resume` works for interactive (TUI) mode. The exec binary supports `codex exec resume --last <prompt>` (verified in `exec/src/main.rs` tests). The session ID is printed at end-of-session as a resume hint. **The gap is that `codex exec --json` does not emit the session_id in its JSONL output**, making it impossible for the thegent orchestrator to track sessions without parsing the human-readable hint.

**Fork changes needed:**

**Change 1:** In `exec_events.rs`, add `session_id` to the `session.started` event (or create this event type if missing):

```
// THEGENT FORK: emit session_id in JSONL output for orchestrator tracking
// upstream PR: pending
```

The `session_id` (thread UUID) is available from `ThreadManager` at the time the session is created. It should be emitted as the first JSONL event.

**Change 2:** Add `codex exec --continue <session_id>` as a flag that wires through to `ExecCli` and calls `ThreadManager::resume_thread(session_id)` instead of `create_thread()`. The interactive path already does this; the exec path needs the same wiring.

**Session storage format (already in upstream):** `~/.codex/` contains SQLite via `codex_core::ThreadManager`. The session IDs are UUIDs. For thegent's purposes, sessions can be addressed by UUID or by thread name (human-readable label set via `--name` flag, if we add it).

**Proposed enhanced session output format:**

```jsonl
{"type": "session.started", "session_id": "uuid", "model": "gpt-5.3-codex", "cwd": "/repo", "timestamp": "2026-02-20T14:30:00Z"}
{"type": "response.chunk", ...}
{"type": "tool.started", "tool": "shell", "tool_id": "xyz", "input": {...}, "timestamp": "..."}
{"type": "tool.completed", "tool_id": "xyz", "exit_code": 0, "duration_ms": 340, "timestamp": "..."}
{"type": "session.completed", "session_id": "uuid", "resume_cmd": "codex exec resume --last", "usage": {"input_tokens": 4200, "output_tokens": 340}, "timestamp": "..."}
```

**thegent-side session storage** (separate from Codex's SQLite): After receiving `session.started`, the thegent orchestrator writes a session record to its own store (`~/.thegent/sessions/codex/<session_id>.json`) so it can correlate tasks to sessions across the thegent work queue. This does not require any Codex fork.

### 2.4 Sub-Agent Spawning

**Architecture decision:** Sub-agent spawning is implemented as an MCP tool, not as a built-in Codex tool. This avoids forking the core tool registry and instead leverages the existing MCP integration.

**Rationale:** Codex already supports MCP servers via `codex mcp` and `codex mcp-server`. An MCP tool named `codex_spawn` can be served by a thegent MCP server (already running on port 3847). When the model calls `codex_spawn`, the thegent MCP server creates a new Codex subprocess with isolated state.

**MCP tool definition (in thegent's FastMCP server):**

```python
@mcp.tool()
async def codex_spawn(
    prompt: str,
    cwd: str | None = None,
    model: str | None = None,
    max_depth: int = 2,
    timeout_sec: int = 600,
) -> dict:
    """
    Spawn a sub-agent Codex instance to work on a sub-task.
    Returns the sub-agent's final response and session_id.
    Enforces max_depth to prevent runaway recursion.
    """
```

**Resource limits enforced by the MCP server (not Codex fork):**
- `max_depth`: passed as metadata; MCP server checks against a session depth counter
- `max_concurrent`: semaphore on the MCP server (default: 4)
- `timeout_sec`: enforced via `asyncio.wait_for`

**Alternative (fork-required) approach:** Add `codex_spawn` as a built-in shell-level tool in `codex-rs/core/src/tools/`. This is the path if MCP round-trip latency is unacceptable (the MCP path adds ~5–20ms per call for local stdio transport, which is negligible). Only fork this if the MCP approach proves insufficient.

---

## 3. SDK Extraction Design

### 3.1 What Already Exists

`sdk/typescript/` in the upstream repo ships `@openai/codex-sdk` (TypeScript/Node.js). It already exposes:

- `Codex` — top-level client; holds executable path + config overrides
- `Thread` — represents a conversation thread; calls `codex exec` subprocess
- `thread.run(prompt)` — returns `TurnResult` with `finalResponse` and `items`
- `thread.runStreamed(prompt)` — returns async generator of typed events
- `threadOptions`: `SandboxMode`, `ModelReasoningEffort`, `ApprovalMode`, `WebSearchMode`

The SDK wraps the binary via JSONL over stdin/stdout. Events are typed TypeScript interfaces. The pattern is sound — it is essentially the same approach as Claude Code's SDK.

### 3.2 What Is Missing From the SDK

The current SDK lacks:

1. **Session resume API:** No `thread.resume(sessionId)` or `new Thread({ sessionId })` constructor.
2. **Hook configuration pass-through:** No way to configure `.codex/hooks/` from the SDK.
3. **Multi-thread coordination:** No `CodexPool` for concurrent thread management.
4. **Event `session.started`:** SDK doesn't receive/expose the session_id from JSONL output (because Codex doesn't emit it yet — the fork change in 2.3 fixes this).
5. **Abort/interrupt semantics:** `AbortSignal` exists in `CodexExecArgs` but is not surfaced in the `Thread` API.

### 3.3 Proposed SDK Enhancements

These are additive changes to the existing `sdk/typescript/src/` — no destructive modifications.

**New class: `CodexPool`** (in `sdk/typescript/src/pool.ts`)

Manages N concurrent `Thread` instances with isolated state directories:

```typescript
interface CodexPoolOptions {
  size: number;
  codexHomesBaseDir?: string;  // defaults to /tmp/codex-pool-<pid>
  sharedAuthPath?: string;     // path to shared ~/.codex/auth symlink
  configOverrides?: CodexConfigObject;
}

class CodexPool {
  constructor(options: CodexPoolOptions): void;
  async acquire(): Promise<Thread>;
  release(thread: Thread): void;
  async drain(): Promise<void>;  // wait for all active threads to finish
  async dispose(): Promise<void>;  // release resources, clean temp dirs
}
```

**Enhanced `Thread` class:**

```typescript
interface ThreadOptions {
  sessionId?: string;       // resume existing session by ID
  sessionName?: string;     // human-readable thread label
  hooksDir?: string;        // path to hooks directory for this thread
  codexHome?: string;       // isolated codex home dir (for pool usage)
}
```

**Event additions** (depend on the fork changes in section 2.3):

```typescript
interface SessionStartedEvent {
  type: "session.started";
  session_id: string;
  model: string;
  cwd: string;
  timestamp: string;
}

interface ToolStartedEvent {
  type: "tool.started";
  tool: string;
  tool_id: string;
  input: unknown;
  timestamp: string;
}

interface ToolCompletedEvent {
  type: "tool.completed";
  tool_id: string;
  exit_code: number;
  duration_ms: number;
  timestamp: string;
}
```

### 3.4 How thegent's `codex_proxy.py` Should Use the SDK

**Current state:** `codex_proxy.py` spawns the `codex` binary directly via `subprocess`, parses JSONL manually, and manages env isolation by overriding `HOME`.

**Recommended transition path:**

Phase 1 (no change): Keep the current Python subprocess approach while the SDK matures. The Python proxy is well-tested and working.

Phase 2 (after fork changes land): Introduce a thin Python wrapper around the Node.js SDK using `node` as a child process, or implement the SDK protocol directly in Python (it is just JSONL over stdin/stdout — trivial to reimplement).

**The practical answer:** Do not use the Node.js SDK from Python. Instead, replicate the SDK's minimal protocol in Python — it is already what `codex_proxy.py` does. The value of the TypeScript SDK is for TypeScript-native callers (IDE extensions, web apps). For thegent's Python orchestrator, the direct subprocess approach is correct.

**What to adopt from the SDK design in `codex_proxy.py`:**

1. Typed event classes mirroring the SDK's TypeScript interfaces (use `pydantic` models)
2. `CodexThread` class with `run()` and `run_streamed()` methods matching the SDK's API shape
3. `CodexPool` pattern (already partially implemented as `CodexWorkerPool` in V1 design)
4. `AbortEvent` / cancellation via `asyncio.Event`

---

## 4. New Modalities

### 4.1 HTTP API Mode (`codex serve`)

**What exists:** `codex app-server` exposes a local HTTP server using the app-server protocol (a bespoke JSON message format used by the VS Code extension). It does NOT expose an OpenAI-compatible REST API.

**What is needed:** An OpenAI-compatible `/v1/responses` endpoint (Codex uses the Responses API, not chat completions — the upstream removed `/v1/chat/completions` entirely in Feb 2026) that allows any OpenAI-compatible client to send requests to a local Codex session.

**Design: `codex serve` subcommand (fork-required):**

```
codex serve [--port 8080] [--bind 127.0.0.1] [--workers 4]
```

This starts the existing `app-server` under an OpenAI-compatible API shim. The shim translates `/v1/responses` requests into the app-server's internal message protocol.

**Why this is feasible:** The app-server already runs on a local Unix domain socket or TCP port (used by the VS Code extension). The shim is a thin HTTP proxy layer — translate OpenAI Responses API request bodies into app-server messages, stream the response back as SSE.

**Implementation location (fork):** `codex-rs/cli/src/main.rs` — add `Subcommand::Serve(ServeArgs)` that calls a new `codex_serve::run_main()`.

**New crate:** `codex-rs/serve/` with a minimal Axum HTTP server.

```toml
# Cargo.toml for codex-rs/serve
[dependencies]
axum = "0.8"
tokio = { features = ["full"] }
codex-app-server = { path = "../app-server" }
codex-app-server-protocol = { path = "../app-server-protocol" }
```

**Scope limitation:** The `/v1/responses` shim handles single-turn and multi-turn Responses API requests. It does NOT attempt to emulate the full OpenAI API surface (no `/v1/models`, no `/v1/files`, etc.). SSE streaming is fully supported.

**For thegent's `codex serve` use case:** thegent currently uses `codex exec --json` (subprocess model). The HTTP mode is for third-party integrations (IDEs, browser extensions, CI pipelines) that cannot spawn subprocesses. thegent itself should continue using the subprocess model for lower overhead.

### 4.2 WebSocket Mode

**What exists:** The app-server protocol is already WebSocket-compatible for the VS Code extension. The `codex-rs/app-server/src/lib.rs` uses the app-server message protocol over a local WebSocket.

**Design:** Expose this as `codex serve --transport websocket`. The existing app-server already supports this. The gap is documentation and a stable client library.

**For thegent:** Not immediately relevant. The subprocess model is lower latency and simpler. WebSocket mode is for persistent IDE connections.

### 4.3 Batch Mode (`codex batch`)

**What exists:** Nothing. Each invocation of `codex exec` processes one prompt.

**Design: `codex batch` subcommand (fork-required):**

```
codex batch --input prompts.jsonl [--workers 4] [--output results.jsonl]
```

Input file format (JSONL, one task per line):

```jsonl
{"id": "task-001", "prompt": "Fix auth module", "cwd": "/repo/src/auth", "model": "gpt-5.3-codex"}
{"id": "task-002", "prompt": "Write tests for API routes", "cwd": "/repo/src/api"}
```

Output format:

```jsonl
{"id": "task-001", "session_id": "uuid", "exit_code": 0, "final_response": "...", "usage": {...}, "duration_ms": 4200}
{"id": "task-002", "session_id": "uuid", "exit_code": 0, "final_response": "...", "usage": {...}, "duration_ms": 3800}
```

**Implementation:** `codex-rs/batch/` new crate. Uses `tokio::task::JoinSet` to run N concurrent `codex exec` instances (calling `codex_exec::run_main()` directly in-process, not as subprocesses). State isolation is achieved by passing distinct `codex_home` paths.

**Dependency on fork change 2.3:** Batch mode requires the `--codex-home` flag (so each worker gets an isolated state directory) and the `session.started` JSONL event (so results can be correlated to session IDs).

**For thegent:** Once `codex batch` ships, `CodexWorkerPool` in `codex_proxy.py` can be simplified to call `codex batch` instead of managing N subprocesses.

### 4.4 Eval Mode

**What exists:** Nothing in the CLI. The HARNESS_PARITY_MATRIX.md documents this as P2.

**Design: `codex eval` subcommand (fork-required):**

```
codex eval --suite <suite-dir> [--harness <name>] [--output metrics.json]
```

Suite directory structure:

```
my-suite/
  eval.toml             — suite metadata (name, description, scoring formula)
  cases/
    fibonacci.json      — test case: prompt + expected outputs + graders
    sorting.json
    rest-api-handler.json
  graders/
    assert-passes.sh    — grader script: receives actual output, exits 0 if pass
    regex-match.sh
```

Test case format:

```json
{
  "id": "fibonacci",
  "prompt": "Implement a fibonacci function in Python",
  "expected_patterns": ["def fibonacci", "return"],
  "graders": ["assert-passes.sh"],
  "max_turns": 5,
  "timeout_sec": 120
}
```

Metrics output:

```json
{
  "suite": "code-gen",
  "harness": "codex",
  "model": "gpt-5.3-codex",
  "timestamp": "2026-02-20T14:30:00Z",
  "results": [
    {"case": "fibonacci", "passed": true, "turns": 2, "latency_ms": 4200, "tokens": 340},
    {"case": "sorting", "passed": true, "turns": 3, "latency_ms": 6100, "tokens": 520}
  ],
  "summary": {
    "success_rate": 1.0,
    "avg_latency_ms": 5150,
    "avg_turns": 2.5,
    "avg_tokens": 430,
    "overall_score": 91.4
  }
}
```

Scoring formula (matches the HARNESS_PARITY_MATRIX.md spec):

```
success_rate = passed / total
efficiency_score = 100 - (avg_latency_sec * 0.1 + avg_turns * 2)
token_efficiency = success_rate / avg_tokens_per_case
overall = (success_rate * 0.5 + efficiency_score * 0.3 + token_efficiency * 0.2)
```

**For thegent:** The eval suite for thegent's Codex integration lives at `tests/eval/codex/` in the thegent repo. It uses the benchmark spec from `HARNESS_PARITY_MATRIX.md`. Running `codex eval --suite tests/eval/codex/` produces metrics comparable across harnesses.

---

## 5. Implementation Roadmap

### 5.1 DAG of Dependencies

```
P1.1 Config changes (CODEX.md alias, memory.md)  ─────────────────────────────┐
P1.2 Populate ~/.codex/skills/ from thegent skills                             │
P1.3 session_id in JSONL output (fork)          ──┐                            │
P1.4 codex exec resume --json flag (fork)          ├─► P2.1 thegent proxy      │
P1.5 HooksConfig in ConfigToml (fork)           ──┘         session tracking   │
                                                                               │
P2.1 Session tracking in codex_proxy.py         ───────────────────────────────┤
P2.2 Pre/post-tool hook runner (fork)           ──┐                            │
P2.3 Session-start/end hook dispatch (fork)       ├─► P3.1 Full hooks E2E     │
P2.4 Hook discovery module (fork)              ──┘                             │
P2.5 --codex-home flag (upstream PR + fork)     ───────────────────────────────┤
                                                                               │
P3.1 MCP tool: codex_spawn in thegent server    ─────────────────────────────  │
P3.2 SDK enhancements (CodexPool, typed events)                                │
P3.3 codex serve (fork: Axum HTTP shim)                                        │
P3.4 codex batch (fork: new crate)             ────────────────────────────────┘

P4.1 codex eval suite + graders (fork: new crate)
P4.2 Upstream PRs: --codex-home, session_id JSONL, enhanced events
```

### 5.2 Phase 1 — Foundation: Project Memory + Skills (2 weeks)

**Approach: Config-only, zero fork, immediate value.**

| Task ID | Description | Depends On | Effort | Owner |
|---|---|---|---|---|
| P1.1 | Update `~/.codex/config.toml` with `project_doc_fallback_filenames`, `model_instructions_file` | — | 1 tool call | thegent |
| P1.2 | Create `~/.codex/memory.md` with thegent global context | P1.1 | 1 tool call | thegent |
| P1.3 | Port thegent governance skills to `~/.codex/skills/` SKILL.md format | P1.1 | 3–5 subagents | thegent |
| P1.4 | Update `codex_proxy.py` to pass `model_instructions_file` and `project_doc_fallback_filenames` via `-c` overrides | P1.1 | 2 tool calls | thegent |
| P1.5 | Integration test: verify AGENTS.md + CODEX.md + skills all inject into prompts | P1.3, P1.4 | 1 subagent | thegent |

**Milestone:** Codex sessions started by thegent automatically load global memory, project docs (AGENTS.md or CODEX.md), and thegent skills. No fork. Purely additive.

**Acceptance criteria:**
- `codex exec --json "what skills are available?"` returns a response that lists thegent skills
- `CODEX.md` in a project root is injected as system instructions
- `~/.codex/memory.md` content appears in every session

### 5.3 Phase 2 — Session + Hooks (4 weeks)

**Approach: Thin Rust fork with minimal delta. Upstream PRs filed in parallel.**

| Task ID | Description | Depends On | Effort | Owner |
|---|---|---|---|---|
| P2.1 | Fork: add `session_id` to `session.started` JSONL event | — | ~50 lines | thegent/fork |
| P2.2 | Fork: add `codex exec --continue <session_id>` flag | P2.1 | ~100 lines | thegent/fork |
| P2.3 | Fork: add `tool.started` / `tool.completed` JSONL events with duration | P2.1 | ~80 lines | thegent/fork |
| P2.4 | Fork: add `HooksConfig` to `ConfigToml`; add hook discovery module | P2.1 | ~200 lines | thegent/fork |
| P2.5 | Fork: implement `HookRunner` (spawn script, pipe JSON, return exit code) | P2.4 | ~150 lines | thegent/fork |
| P2.6 | Fork: inject pre/post-tool hook calls into `exec.rs` tool dispatch | P2.4, P2.5 | ~100 lines | thegent/fork |
| P2.7 | Fork: inject session-start/end hook calls into `exec/src/lib.rs` | P2.4, P2.5 | ~60 lines | thegent/fork |
| P2.8 | Fork: add `--codex-home <dir>` flag; update `find_codex_home()` | — | ~40 lines | thegent/fork |
| P2.9 | Update `codex_proxy.py` to read `session.started` session_id; store in thegent session DB | P2.1 | ~80 lines | thegent |
| P2.10 | Write pre-tool hook: `pre-tool-governance-check.sh` | P2.6 | 1 tool call | thegent |
| P2.11 | Write session-end hook: `session-end-memory-update.sh` | P2.7 | 1 tool call | thegent |
| P2.12 | Integration tests: hooks fire, block on non-zero exit, session_id flows | P2.6–2.11 | 1 subagent | thegent |

**Milestone:** Every Codex tool call fires pre/post hooks. Sessions emit IDs that thegent tracks. `--continue <session_id>` enables non-interactive session resumption.

**Fork delta estimation:** ~580 lines total across 5 files. Each forked file has a `// THEGENT FORK` header. Upstream PRs for P2.1, P2.2, P2.8 filed simultaneously (these are generalizable).

### 5.4 Phase 3 — Sub-Agents, SDK, HTTP API (8 weeks)

| Task ID | Description | Depends On | Effort | Owner |
|---|---|---|---|---|
| P3.1 | thegent MCP server: implement `codex_spawn` tool | P2.8 | 3–5 tool calls | thegent |
| P3.2 | thegent MCP server: enforce spawn depth/concurrency limits | P3.1 | 2 tool calls | thegent |
| P3.3 | Fork: `codex batch` subcommand + new crate | P2.8 | ~500 lines | thegent/fork |
| P3.4 | Fork: `codex serve` subcommand (Axum HTTP shim over app-server) | — | ~400 lines | thegent/fork |
| P3.5 | TypeScript SDK: `CodexPool` class | P2.8 | ~200 lines | thegent/fork |
| P3.6 | TypeScript SDK: typed `SessionStartedEvent`, `ToolStartedEvent`, `ToolCompletedEvent` | P2.1 | ~100 lines | thegent/fork |
| P3.7 | TypeScript SDK: `Thread({ sessionId })` resume constructor | P2.2 | ~80 lines | thegent/fork |
| P3.8 | `codex_proxy.py` refactor: typed Pydantic event models mirroring SDK | P2.9 | ~200 lines | thegent |
| P3.9 | Integration tests: spawn, batch, serve | P3.1–3.7 | 2 subagents | thegent |

**Milestone:** Agents can spawn sub-agents via MCP. Batch execution of N tasks uses a single `codex batch` invocation. A local HTTP endpoint allows non-subprocess access.

### 5.5 Phase 4 — Eval Mode + Upstream Contribution (ongoing)

| Task ID | Description | Depends On | Effort | Owner |
|---|---|---|---|---|
| P4.1 | Fork: `codex eval` subcommand + grader protocol | P3.3 | ~600 lines | thegent/fork |
| P4.2 | Write eval suite for HARNESS_PARITY_MATRIX benchmark categories | P4.1 | 5–8 subagents | thegent |
| P4.3 | Upstream PR: `--codex-home` | P2.8 | PR filing | thegent |
| P4.4 | Upstream PR: `session_id` in JSONL + tool events | P2.1–2.3 | PR filing | thegent |
| P4.5 | Upstream PR: `codex exec --continue` | P2.2 | PR filing | thegent |
| P4.6 | If upstream merges PRs: remove fork patches for those changes, rebase | P4.3–4.5 | merge work | thegent |

---

## 6. Fork Maintenance Strategy

### 6.1 The "Thin Fork" Rule

The fork MUST remain a thin patch set, not a divergent clone. The definition of thin: **all fork-specific changes fit in patches of < 1000 total lines of Rust**, excluding new crates (`serve/`, `batch/`, `eval/`).

### 6.2 Patch Tracking

Maintain a file `codex-rs/THEGENT_PATCHES.md` in the fork that lists every divergence:

```markdown
# thegent Fork Patches

| File | Change | Lines | Upstream PR | Status |
|------|--------|-------|-------------|--------|
| core/src/config/mod.rs | HooksConfig struct | +35 | #TBD | pending |
| core/src/hooks/mod.rs | HookDispatcher (new file) | +180 | N/A | fork-only |
| core/src/exec.rs | pre/post-tool hook dispatch | +60 | N/A | fork-only |
| exec/src/lib.rs | session-start/end hook + session_id event | +80 | #TBD | pending |
| exec/src/cli.rs | --continue flag, --codex-home flag | +40 | #TBD | pending |
| exec/src/exec_events.rs | session.started, tool.started/completed events | +50 | #TBD | pending |
```

### 6.3 Rebase Cadence

Rebase against upstream `main` monthly. The fork's CI MUST run the full upstream test suite plus thegent-specific integration tests. If a rebase conflict occurs in a patched file, resolve toward keeping upstream behavior unless the patch is intentionally overriding it.

### 6.4 Upstream Contribution Priority

Priority order for pushing changes upstream (highest chance of acceptance first):

1. `--codex-home` / `CODEX_HOME` (pure DX improvement, zero behavior change)
2. `session_id` in JSONL `session.started` event (zero behavior change, pure addition)
3. Tool timing events (`tool.started`, `tool.completed` with `duration_ms`) (additive)
4. `codex exec --continue <session_id>` (the interactive version already exists; exec parity)

Changes NOT to push upstream:
- Pre/post-tool hooks (security surface, thegent-specific governance concern)
- `codex spawn` tool (orchestration-specific)
- `codex eval` (thegent eval suite is custom; upstream may build their own)

---

## 7. thegent Integration: Updated `codex_proxy.py` Behavior

### 7.1 Current Integration (Baseline)

```python
# Current call pattern in codex_proxy.py
cmd = [
    "codex",
    "exec",
    "-",
    "--skip-git-repo-check",
    "--dangerously-bypass-approvals-and-sandbox",
    "--cd",
    str(task.cwd),
    "--json",
    "--model",
    task.model,
    "--sandbox",
    "workspace-write",
    "--full-auto",
]
```

### 7.2 Updated Integration After Phase 1

```python
# Phase 1: config-only improvements (no fork)
cmd = [
    "codex",
    "exec",
    "-",
    "--skip-git-repo-check",
    "--dangerously-bypass-approvals-and-sandbox",
    "--cd",
    str(task.cwd),
    "--json",
    "--model",
    task.model,
    "--sandbox",
    "workspace-write",
    "--full-auto",
    # Phase 1 additions:
    "-c",
    f'project_doc_fallback_filenames=["CODEX.md","CLAUDE.md"]',
    "-c",
    f"model_instructions_file={global_memory_path}",
    "-c",
    f"project_doc_max_bytes=65536",
]
```

### 7.3 Updated Integration After Phase 2 (Fork Available)

```python
# Phase 2: fork-enabled improvements
env = os.environ.copy()
env["HOME"] = str(isolated_codex_home)  # Until --codex-home lands

cmd = [
    "codex",
    "exec",
    "-",
    "--skip-git-repo-check",
    "--dangerously-bypass-approvals-and-sandbox",
    "--cd",
    str(task.cwd),
    "--json",
    "--model",
    task.model,
    "--sandbox",
    "workspace-write",
    "--full-auto",
    # Phase 2: state isolation (fork adds --codex-home; use HOME env until then)
    # Phase 2: session resume
    *(["--continue", task.session_id] if task.session_id else []),
]

# Phase 2: parse session_id from JSONL output
# event: {"type": "session.started", "session_id": "uuid", ...}
```

### 7.4 Hook Configuration for thegent Governance

With Phase 2 complete, place these hooks in `~/.codex/hooks/`:

```bash
# ~/.codex/hooks/pre-tool-governance.sh
# Receives JSON on stdin; exit non-zero to block the tool call

payload=$(cat)
tool_name=$(echo "$payload" | jq -r '.tool.name')
command=$(echo "$payload" | jq -r '.tool.input.command // empty')

# Block destructive operations outside the workspace
if [[ "$tool_name" == "shell" ]] && echo "$command" | grep -q "rm -rf /"; then
    echo "BLOCKED: destructive command outside workspace" >&2
    exit 1
fi

exit 0
```

```bash
# ~/.codex/hooks/session-end-memory.sh
# Called at session end; payload includes session_id and summary

payload=$(cat)
session_id=$(echo "$payload" | jq -r '.session_id')

# Record the session in thegent's memory system
thegent memory add --source codex --session "$session_id" <<< "$payload"
exit 0
```

---

## 8. Architectural Summary

```
                     thegent Orchestrator
                           |
                    ┌──────┴───────┐
                    │              │
             codex_proxy.py   thegent MCP Server
             (subprocess)     (port 3847)
                    │              │
                    │         codex_spawn tool
                    │              │
              ┌─────┴──────────────┘
              │
        codex exec --json (forked binary)
              │
    ┌─────────┼──────────────────────┐
    │         │                      │
HookDispatcher  ProjectDocLoader   SkillsManager
    │             (AGENTS.md,        (~/.codex/skills/)
    │              CODEX.md)
    │
pre-tool-governance.sh
post-tool-log.sh
session-end-memory.sh
```

**Data flows:**
1. Task enters via thegent work queue → `codex_proxy.py` spawns forked `codex exec --json`
2. Session starts → `session.started` event with `session_id` written to thegent session DB
3. Model calls a tool → `pre-tool-governance.sh` fires → if exit 0, tool executes → `post-tool-log.sh` fires
4. Session ends → `session-end-memory.sh` fires → thegent memory updated
5. For sub-tasks: model calls `codex_spawn` MCP tool → thegent MCP server spawns isolated child

---

## 9. Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Upstream changes `exec.rs` tool dispatch and invalidates fork patch | Medium | High | Keep patch minimal; file upstream PR for hooks so they pull the change in |
| Hook scripts introduce security vulnerabilities (command injection in payload parsing) | Medium | High | Validate hook scripts are executable by owner only (0700); sanitize JSON before passing to shell; use `jq` not eval |
| SQLite contention in multi-agent `--codex-home` scenario before flag lands | Low | Medium | Continue using `HOME` env override; each agent gets isolated `HOME`; SQLite is per-home |
| TypeScript SDK not maintained by upstream; diverges from binary protocol | Low | Low | SDK is thin wrapper over JSONL; reimplement in Python if needed (already done in `codex_proxy.py`) |
| `codex serve` Axum shim lags Responses API changes | Medium | Medium | Pin to specific codex version; update shim on API changes; treat as beta |
| Eval suite becomes stale as models improve | High | Low | Schedule quarterly eval runs; metrics are relative (harness comparison), not absolute |

---

## 10. Success Criteria

| Criterion | Target | Measurement |
|---|---|---|
| Project memory injection | CODEX.md + AGENTS.md loaded in every session | Verify with `codex exec --json "what are the project docs?"` |
| Skills availability | All thegent governance skills listed in system prompt | Same test with "what skills are available?" |
| Hook execution | Pre-tool hook fires before every shell command | Instrumented test: hook writes to log; verify log has N entries after N tool calls |
| Session ID tracking | thegent session DB has session_id within 2s of session start | E2E test with DB read |
| Session resume | `--continue <id>` resumes prior conversation context | Test: session A sets a variable; session B (resumed) can read it |
| Sub-agent spawning | `codex_spawn` tool call spawns isolated child; result returned | MCP tool integration test |
| Fork delta size | All non-crate fork patches < 1000 lines | `git diff upstream/main -- codex-rs/{core,exec}/src | wc -l` |
| Upstream PR acceptance | At least `--codex-home` merged upstream within 3 months | PR tracking |
| Eval score baseline | Codex overall score ≥ 87 on HARNESS_PARITY_MATRIX benchmark | `codex eval --suite tests/eval/codex/ --output metrics.json` |

---

## 11. Open Questions

1. **`notify` hook timing:** The existing `notify` field fires when the agent turn completes. For session-end hooks, is turn-complete the right granularity, or do we need a distinct session-terminated event? The two are different in multi-turn sessions (one session = many turns).

2. **Hook payload confidentiality:** Tool input may contain secrets (API keys in shell commands). Should pre-tool hooks receive a redacted payload, or full payload? Decision: full payload, but hooks run as the user's own process — same security level as the shell commands themselves.

3. **`codex batch` vs N-subprocesses:** For the current thegent use case (5–10 concurrent agents), is `codex batch` worth forking, or is the existing `CodexWorkerPool` with N `subprocess.Popen` calls sufficient? Answer: the worker pool approach works today. `codex batch` is a simplification that also enables the eval mode foundation. Build it in Phase 3, but don't block Phase 1–2 on it.

4. **`codex serve` scope:** Should the HTTP shim support multi-session (multiple concurrent `Thread` instances per server process), or single-session? Multi-session requires a session registry and adds complexity. Recommendation: start single-session (`--session-id` in the request header); add multi-session in a follow-up.

5. **Eval grader contracts:** Should eval graders be shell scripts (simple but fragile) or structured programs with a defined interface? Recommendation: shell scripts for now (same pattern as Ante's eval system and the existing thegent hooks); migrate to structured Python graders if shell fragility becomes a problem.

---

## 12. Related Documents

- `HARNESS_PARITY_MATRIX.md` — feature gap analysis across harnesses
- `CODEX_OVERHAUL_DESIGN.md` — V1 design (proxy-side only; superseded for fork design but retains multi-agent scaling patterns)
- `CODEX_CLI_V2_PROTOCOL_RESEARCH_2026-02-20.md` — wire protocol research
- `CODEX_V2_GAP_ANALYSIS_2026-02-20.md` — detailed gap analysis
- `CODEX_CLIPROXY_CONFIG_AUDIT_AND_PLAN.md` — codex_proxy.py audit
- Upstream source: `/Users/kooshapari/temp-PRODVERCEL/485/API/codex-upstream/`
  - `codex-rs/core/src/project_doc.rs` — AGENTS.md loading
  - `codex-rs/core/src/skills/` — skills system
  - `codex-rs/exec/src/cli.rs` — exec CLI flags
  - `codex-rs/exec/src/lib.rs` — exec main logic + event processor dispatch
  - `sdk/typescript/` — TypeScript SDK

---

## Signature

**Author:** Architecture Team (thegent)
**Reviewed:** —
**Approved:** —
**Last Updated:** 2026-02-20
**Version:** 2.0
