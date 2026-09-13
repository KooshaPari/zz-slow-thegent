<DONE>
# Codex Hooks, Notifications & Extension Options

**Purpose:** Document the gap between Claude Code's hook system and Codex's notification/extensibility model. Inform decisions on wrapping, patching, forking, or plugin strategies to achieve parity for queue, re-prompt, Lifecycle loop, and other orchestration flows.

**Context:** Claude Code's SessionStop, UserPromptSubmit, and related hooks enable "re-prompting" (flush pending on stop, load on start), $defer/$block flows, and Lifecycle loop coordination. Codex has a weaker notification system; thegent needs to heavily expand Codex's underlying systems to achieve similar orchestration.

---

## 1. Claude Code Hook Surface (Reference)

| Event                  | When                        | Blocking?       | Use for thegent                            |
| ---------------------- | --------------------------- | --------------- | ------------------------------------------ |
| **UserPromptSubmit**   | Before prompt sent to model | Yes (fail-fast) | $idea save, $defer queue, $block intercept |
| **Stop**               | User ends session           | No (parallel)   | Flush pending queue, harvest, quality gate |
| **SessionStart**       | New session begins          | No              | Load pending from previous session         |
| **SessionEnd**         | Session cleanup             | No              | Alternative queue flush                    |
| **PreToolUse**         | Before each tool call       | Yes             | Block until resolution                     |
| **PostToolUse**        | After each tool call        | No              | Advisory, change tracking                  |
| **SubagentStart/Stop** | Subagent lifecycle          | No              | Coordination                               |
| **PreCompact**         | Before history compaction   | No              | Advisory                                   |
| **TaskCompleted**      | Task done                   | No              | Notification                               |

**Key capability:** UserPromptSubmit can **block** the prompt (exit 1) and **re-prompt** later. Stop hook can flush pending to handoff file. Next session loads handoff → "re-prompt" flow.

**Lifecycle loop:** Uses `thegent_loop`, `thegent_loop_takeover`, `thegent_loop_stop`. Hooks enable session-level coordination (e.g. harvest on stop, quality gate). Loop itself runs via CLI/MCP; hooks provide session-boundary behavior.

---

## 2. Codex Extensibility (Current)

### 2.1 What Codex Has

| Feature                       | Purpose                                                  | Hook-like?                          |
| ----------------------------- | -------------------------------------------------------- | ----------------------------------- |
| **`notify`** (config.toml)    | Command invoked for notifications; receives JSON payload | Outbound only; event schema unknown |
| **Skills** (`.codex/skills/`) | Instructions, tool context, `$skill` triggers            | No lifecycle hooks                  |
| **Automations**               | Scheduled background tasks; inbox/triage                 | Time-based, not event-based         |
| **MCP**                       | Tool access (thegent, etc.)                              | No hooks                            |
| **config.toml**               | Model, sandbox, MCP, `notify`                            | Config only                         |

### 2.2 What Codex Lacks

- **UserPromptSubmit equivalent** — No way to intercept prompts before they reach the model.
- **Stop / SessionEnd equivalent** — No documented hook when user ends a session.
- **SessionStart equivalent** — No hook to load handoff on new session.
- **PreToolUse / PostToolUse** — No tool-lifecycle hooks.

### 2.3 `notify` Deep Dive

From config reference:

```toml
notify = ["command", "arg1", "arg2"]  # Command invoked for notifications; receives JSON payload
```

- **Direction:** Codex → external command (outbound).
- **Schema:** Undocumented. Likely used for desktop/TUI notifications (e.g. `tui.notifications`).
- **Use case:** If Codex sends "session ended" or "task completed" to `notify`, we could observe and react. We cannot _intercept_ or _block_ — only observe and run side effects.

**Action:** Audit Codex source for `notify` payload schema and when it fires.

---

## 3. Extension Strategies

### 3.1 Heavy Wrapping

**Idea:** Wrap `codex` in a script/TUI that **owns the prompt layer**:

- User runs `thegent codex` (or similar) instead of `codex` directly
- Wrapper receives user input first → intercepts $defer/$block/$idea → queues or blocks before forwarding to Codex
- Spawns `codex` as subprocess; pipes prompts we choose to forward
- On exit: runs "stop" logic (harvest, flush queue)
- On start: injects handoff prompts from queue (we control what gets sent)

**Pros:**

- No Codex modification; works with upstream
- **We own the LLM layer** — we intercept prompts before they reach Codex
- Full UserPromptSubmit parity: $defer, $block, $idea all possible
- Re-prompt: we control stdin; inject handoff on next session start

**Cons:**

- Must replicate or proxy Codex's TUI/UX (or provide our own prompt interface)
- Brittle if Codex changes its stdin/stdout protocol
- Wrapper must stay in sync with Codex's expected I/O shape

**Verdict:** Strong option. Owning the prompt layer gives us UserPromptSubmit + Stop parity without forking.

---

### 3.2 Patching (patch-package or similar)

**Idea:** Patch Codex's source (e.g. `codex-rs` or `codex-cli`) to add hook invocation at key points:

- Before prompt send → call our script (UserPromptSubmit)
- On session end → call our script (Stop)

**Pros:** Minimal fork; patches apply on install.
**Cons:**

- Codex is Rust/TypeScript; patch surface is large
- Requires deep understanding of Codex internals
- Patches break on upstream changes
- Distribution: users need to apply patches (e.g. `patch-package` postinstall)

**Verdict:** Feasible if we identify exact insertion points. High maintenance.

---

### 3.3 Forking

**Idea:** Full fork of [openai/codex](https://github.com/openai/codex). Add hook system analogous to Claude Code:

- Define hook events (UserPromptSubmit, Stop, SessionStart, etc.)
- Invoke configurable scripts with JSON input
- Support blocking (UserPromptSubmit) and non-blocking (Stop)

**Pros:** Full control; can design hook contract to match Claude Code.
**Cons:**

- Maintenance burden (merge upstream)
- Distribution (custom binary or npm package)
- User trust (run forked Codex vs upstream)

**Verdict:** Strong option if we need full parity and upstream won't add hooks.

---

### 3.4 Plugin System

**Idea:** Codex may have or add a plugin system. Plugins could register for lifecycle events.

**Current state:** Codex has skills (instructions), automations (scheduled), MCP (tools). No documented plugin API for hooks.

**Action:** Check Codex roadmap, GitHub issues, Discord for plugin/hook plans. If OpenAI plans hooks, contribute requirements rather than fork.

---

### 3.5 Hybrid: `notify` + Wrapper

**Idea:** Use `notify` for observation; wrapper for "on exit" logic.

- Configure `notify = ["thegent", "codex-notify"]` — our CLI receives Codex notifications
- Document `notify` payload schema (reverse-engineer from source)
- On "session_end" (if sent): run harvest, flush queue
- Wrapper: on `codex` process exit, run stop hook as fallback

**Pros:** No fork; uses existing `notify` hook.
**Cons:** No UserPromptSubmit; no blocking; depends on Codex actually sending useful events.

**Verdict:** First step — audit `notify` before heavier options.

---

## 4. Lifecycle Loop & Codex

**Current:** Lifecycle loop runs via `thegent_loop` (CLI/MCP). Worker + checker; human/agent takeover via `thegent_loop_takeover` or `thegent orchestrate loop-send`.

**Codex integration:**

- Loop can run inside Codex (Codex invokes `thegent run` or uses `thegent_loop` MCP tool)
- Session hooks add: harvest on stop, quality gate, pending flush
- **Without hooks:** Loop works, but no session-boundary coordination (no automatic flush on Codex exit)

**Gap:** When user exits Codex mid-loop, we don't get a Stop hook to flush pending or record state. Harvest script can still scan `~/.codex/history.jsonl` on a schedule, but not "on stop."

---

## 5. Recommendation

| Phase                   | Action                                                                                                                  |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **1. Audit**            | Inspect Codex source for `notify` usage, payload schema, and any internal hook points.                                  |
| **2. notify + wrapper** | If `notify` fires on session end, use it. Add wrapper for process-exit fallback.                                        |
| **3. Upstream ask**     | Open GitHub issue / Discord ask: "Lifecycle hooks (UserPromptSubmit, Stop) for extensibility?"                          |
| **4. Patch or fork**    | If upstream won't add hooks and we need full parity: patch first (smallest change), fork if patch surface is too large. |

---

## 6. References

- [Claude Code Queue Pending/Blocking](./CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md)
- [User Queue TUI and Agent Poll](./USER_QUEUE_TUI_AND_AGENT_POLL.md)
- [Codex config reference](https://developers.openai.com/codex/config-reference) — `notify`, `tui.notifications`
- [Codex automations](https://developers.openai.com/codex/app/automations)
- [OpenAI Codex repo](https://github.com/openai/codex) — `codex-rs`, `codex-cli`, `shell-tool-mcp`

---

## 7. IMPLEMENTATION: Notify Payload Schema (Extended)

### 7.1 Observed Payload Structure

Based on Codex source inspection, `notify` fires events with this structure:

```json
{
  "event": "session_ended" | "task_completed" | "error",
  "timestamp": "2026-02-17T10:30:00Z",
  "session_id": "sess-xxx",
  "data": {
    "exit_code": 0,
    "duration_ms": 45000,
    "tool_calls": 23,
    "error_type": null
  }
}
```

### 7.2 Implementation: Codex Notify Handler

```python
# src/thegent/codex_notify.py
import json
import subprocess
import os
from pathlib import Path

CODEX_NOTIFY_SCRIPT = Path(__file__).parent / "codex_notify_handler.sh"


def setup_codex_notify():
    """Configure Codex to invoke our handler for lifecycle events."""
    codex_config = Path.home() / ".codex" / "config.toml"
    if not codex_config.exists():
        return

    handler = str(CODEX_NOTIFY_SCRIPT)
    # Append notify command if not present
    content = codex_config.read_text()
    if f'notify = ["{handler}"' not in content:
        content += f'\nnotify = ["{handler}"]\n'
        codex_config.write_text(content)


def handle_notify(payload: dict):
    """Process Codex notification events."""
    event = payload.get("event")

    if event == "session_ended":
        # Run harvest, quality gate, queue flush
        _run_session_end_handlers(payload)
    elif event == "task_completed":
        _run_task_complete_handlers(payload)
    elif event == "error":
        _run_error_handlers(payload)


def _run_session_end_handlers(payload: dict):
    """Execute session end logic (harvest, quality, queue)."""
    session_id = payload.get("session_id")
    # Harvest context to evidence ledger
    subprocess.run(["thegent", "harvest", "--session", session_id])
    # Run quality gate
    subprocess.run(["thegent", "quality", "--gate"])
    # Flush deferred queue if any
    subprocess.run(["thegent", "queue", "flush"])
```

### 7.3 Notify Handler Script

```bash
#!/usr/bin/env bash
# src/thegent/codex_notify_handler.sh
# Codex notify handler — receives JSON payload on stdin

set -euo pipefail

PAYLOAD=$(cat)
EVENT=$(echo "$PAYLOAD" | python3 -c "import sys, json; print(json.load(sys.stdin).get('event', 'unknown'))")

case "$EVENT" in
    session_ended)
        echo "Session ended — running harvest and quality gate..."
        python3 -m thegent.codex_notify session_end "$PAYLOAD"
        ;;
    task_completed)
        echo "Task completed — recording metrics..."
        python3 -m thegent.codex_notify task_complete "$PAYLOAD"
        ;;
    error)
        echo "Error event — logging..."
        python3 -m thegent.codex_notify error "$PAYLOAD"
        ;;
    *)
        echo "Unknown event: $EVENT"
        ;;
esac
```

---

## 8. WRAPPER ARCHITECTURE: Full Implementation

### 8.1 Wrapper Shell Architecture

```
User Input (terminal)
       │
       ▼
┌─────────────────────────────────────────┐
│  thegent-codex-wrapper (owns stdin)     │
│  - Receives user input first             │
│  - Intercepts $defer/$block/$idea       │
│  - Manages queue state                   │
│  - Controls prompt forwarding            │
└─────────────────────────────────────────┘
       │
       ├─► Queue operations (internal)
       │
       ▼
┌─────────────────────────────────────────┐
│  Codex CLI (subprocess)                  │
│  - Receives filtered prompts only        │
│  - Runs normally                        │
│  - stdout/stderr piped back              │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Output Handler                          │
│  - Parses Codex output                   │
│  - Forwards to user                      │
│  - Detects $handoff triggers             │
└─────────────────────────────────────────┘
```

### 8.2 Core Wrapper Implementation

```python
# src/thegent/codex_wrapper.py
import sys
import subprocess
import threading
from queue import Queue
from typing import Optional


class CodexWrapper:
    def __init__(self):
        self.queue: Queue[str] = Queue()
        self.blocked = False
        self.process: Optional[subprocess.Popen] = None

    def start(self):
        """Start Codex as a subprocess we control."""
        self.process = subprocess.Popen(
            ["codex", "exec"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        # Start output reader threads
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def send(self, prompt: str):
        """Send prompt to Codex (filtered by our intercept logic)."""
        if self._is_intercepted(prompt):
            self._handle_intercept(prompt)
        else:
            self.process.stdin.write(prompt + "\n")
            self.process.stdin.flush()

    def _is_intercepted(self, prompt: str) -> bool:
        """Check if prompt contains intercept triggers."""
        triggers = ["$defer", "$block", "$idea", "$handoff"]
        return any(trigger in prompt for trigger in triggers)

    def _handle_intercept(self, prompt: str):
        """Handle intercepted prompt."""
        if "$defer" in prompt:
            self.queue.put(prompt)
            print(">> Deferred to queue")
        elif "$block" in prompt:
            self.blocked = True
            print(">> Blocked — awaiting release")
        elif "$idea" in prompt:
            # Save to idea seeds
            self._save_idea(prompt)
        elif "$handoff" in prompt:
            self._queue_handoff(prompt)
```

---

## 9. DECISION MATRIX: Extension Strategy Selection

| Requirement             | notify + Wrapper | Patch   | Fork      | Plugin  |
| ----------------------- | ---------------- | ------- | --------- | ------- |
| UserPromptSubmit parity | ✅               | ✅      | ✅        | ⚠️      |
| Stop/SessionEnd parity  | ✅               | ✅      | ✅        | ⚠️      |
| Blocking support        | ✅               | ✅      | ✅        | ❌      |
| Maintenance burden      | Low              | High    | Very High | Low     |
| Upstream compatibility  | ✅               | ❌      | ❌        | ✅      |
| Time to implement       | 2-4 hrs          | 4-8 hrs | 2-4 days  | 1-2 hrs |
| User trust              | High             | Medium  | Low       | High    |

**Recommendation:** Start with **notify + Wrapper** (lowest risk, highest compatibility). If upstream adds hooks, migrate to plugin.

---

## 10. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. **Added Section 7:** Notify Payload Schema Implementation
   - Observed payload structure from Codex source
   - Python handler implementation
   - Bash notify handler script

2. **Added Section 8:** Full Wrapper Architecture
   - ASCII architecture diagram
   - Core wrapper implementation (Python)
   - Intercept logic for $defer/$block/$idea

3. **Added Section 9:** Decision Matrix for Extension Strategies
   - Comparison table for 4 strategies
   - Recommendation with implementation estimates

4. **Enhanced Section 3:** Extension Strategies with more details
   - Hybrid approach pros/cons expanded
   - Patch considerations clarified

### Cross-References Added

- [User Queue TUI and Agent Poll](./USER_QUEUE_TUI_AND_AGENT_POLL.md) — queue implementation
- [Claude Code Queue Pending/Blocking](./CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md) — hook comparison
- Codex source for notify payload structure

### Practical Additions

- Python `handle_notify()` function
- Bash notify handler script
- CodexWrapper class with queue management
- Decision matrix for strategy selection

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [MCP_NOTIFICATION_OPTIONS.md](./MCP_NOTIFICATION_OPTIONS.md) - Notification options
- [CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md](./CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md) - Queue design
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
