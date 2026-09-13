# Agent Registry & Interactive Session Management — Research & Plan

> **Design spec**: [AGENT_REGISTRY_DESIGN.md](./AGENT_REGISTRY_DESIGN.md) — holistic design, harmonization with work stream/gardener/lifecycle, data model, security, UX, roadmap.
> **Adjacent**: [UNIFIED_WORK_STREAM_DESIGN.md](./reference/UNIFIED_WORK_STREAM_DESIGN.md), [GARDENER_ARCHITECTURE.md](./reference/GARDENER_ARCHITECTURE.md), [LIBRARY_FIRST_AUDIT_AND_PLAN.md](./research/LIBRARY_FIRST_AUDIT_AND_PLAN.md)

## Goal

Create an automatic agent registry system that allows:

1. **Viewing all agent processes** (thegent run agents, internal sub-agents like "cc task", user/system called agents)
2. **For each agent process, being able to:**
   - "Open" the process
   - View the session/chat history/audit log
   - Send messages/reprompt the agent
3. **Work with both interactive and headless processes**
4. **Avoid requiring tmux/mux if possible** (but support it when available)

## Current State Analysis

### Existing Infrastructure

1. **Session Management** (`thegent/src/thegent/cli_impl.py`):
   - Sessions tracked via metadata files in `session_dir`
   - Each session has: `{session_id}.json` (meta), `{session_id}.stdout.log`, `{session_id}.stderr.log`
   - Background processes use `subprocess.Popen` with `stdin=subprocess.DEVNULL`
   - Sessions have `session_id`, `pid`, `agent`, `prompt`, `status`, etc.

2. **Takeover Mechanism** (`thegent/src/thegent/mcp_server.py:1202`):
   - Current approach: Write to `takeover.json` file
   - Agent must poll this file (not implemented in agents yet)
   - Limited to file-based communication

3. **Discovery** (`thegent/src/thegent/discovery.py`):
   - Discovers external agents via heliosShield
   - Tracks agents by PPID
   - Can detect tmux panes

4. **Tmux Integration** (`thegent/src/thegent/tools/terminal.py`):
   - Can list tmux panes
   - Can send keys to panes: `send_to_tmux_pane(pane_id, text)`
   - Can capture pane content: `capture_tmux_pane(pane_id)`

5. **TUI Explorer** (`thegent/src/thegent/tui.py`):
   - Read-only view of sessions
   - Shows terminals, background sessions, discovered agents
   - No interaction capability

### Key Challenges

1. **Headless Process Communication**:
   - Background processes have `stdin=subprocess.DEVNULL`
   - Cannot directly write to stdin
   - Need alternative IPC mechanism

2. **Chat History**:
   - Currently only stdout/stderr logs exist
   - No structured chat history/conversation log
   - Need to reconstruct from logs or maintain separate history

3. **Agent Reprompting**:
   - Agents don't currently support mid-execution reprompting
   - Need to inject new prompts into running agents
   - Must handle context continuation

4. **Process Attachment**:
   - Interactive processes (tmux) can be attached
   - Headless processes need different approach
   - Ghostty integration unknown

## Research: IPC Mechanisms for Process Communication

### Option 1: Named Pipes (FIFOs)

**How it works:**

- Create a FIFO per session: `mkfifo /path/to/session_{id}.in`
- Agent opens FIFO for reading (blocking read)
- Registry writes messages to FIFO
- Agent processes messages as they arrive

**Pros:**

- Standard Unix IPC mechanism
- Blocking reads (efficient, no polling)
- File-like interface (easy to use)
- Works for headless processes

**Cons:**

- Requires agent modification to read from FIFO
- One reader per FIFO (need separate FIFOs per session)
- FIFO cleanup needed when session ends
- May block if no reader attached

**Implementation:**

```python
# Registry side
fifo_path = session_dir / f"{session_id}.in"
os.mkfifo(fifo_path, 0o666)
with open(fifo_path, "w") as f:
    f.write(json.dumps({"type": "reprompt", "prompt": "..."}))

# Agent side (in agent loop)
fifo_path = Path(os.environ.get("THGENT_SESSION_INPUT_FIFO"))
if fifo_path.exists():
    with open(fifo_path, "r") as f:
        msg = json.loads(f.read())
        if msg["type"] == "reprompt":
            pass  # Handle reprompt
```

### Option 2: Unix Domain Sockets

**How it works:**

- Create a socket per session: `/tmp/thegent_{session_id}.sock`
- Registry connects and sends messages
- Agent listens on socket
- Bidirectional communication possible

**Pros:**

- More robust than FIFOs
- Bidirectional communication
- Can handle multiple connections (with proper design)
- Standard IPC mechanism

**Cons:**

- More complex than FIFOs
- Requires socket programming
- Need to handle connection management
- Agent modification required

**Implementation:**

```python
# Registry side
import socket

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect(f"/tmp/thegent_{session_id}.sock")
sock.sendall(json.dumps({"type": "reprompt", "prompt": "..."}).encode())
sock.close()

# Agent side
server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server.bind(f"/tmp/thegent_{session_id}.sock")
server.listen(1)
conn, addr = server.accept()
data = conn.recv(4096)
```

### Option 3: File-Based Messaging (Current Approach, Enhanced)

**How it works:**

- Write messages to `{session_id}.messages.jsonl`
- Agent polls file for new messages
- Use file locking or atomic writes
- Mark messages as processed

**Pros:**

- Simple, no special IPC setup
- Works with existing file-based approach
- Easy to debug (inspect files)
- No special permissions needed

**Cons:**

- Polling overhead
- File system latency
- Need to handle concurrent access
- Less efficient than FIFOs/sockets

**Implementation:**

```python
# Registry side
msg_file = session_dir / f"{session_id}.messages.jsonl"
with open(msg_file, "a") as f:
    f.write(json.dumps({"id": uuid4(), "type": "reprompt", "prompt": "...", "timestamp": now()}) + "\n")


# Agent side (polling)
def poll_messages(session_id):
    msg_file = Path(f"{session_id}.messages.jsonl")
    processed = set()
    if msg_file.exists():
        with open(msg_file) as f:
            for line in f:
                msg = json.loads(line)
                if msg["id"] not in processed:
                    processed.add(msg["id"])
                    yield msg
```

### Option 4: PTY/TTY Attachment

**How it works:**

- Create a PTY for the agent process
- Registry can write to PTY master
- Agent reads from PTY slave (appears as stdin)
- Works for interactive processes

**Pros:**

- Agent sees input as normal stdin
- No agent modification needed (if already reads stdin)
- Standard terminal interface

**Cons:**

- Only works if agent reads from stdin
- Background processes typically don't read stdin
- Requires PTY setup at process start
- Complex to attach to existing process

### Option 5: Signal-Based + File

**How it works:**

- Send SIGUSR1/SIGUSR2 to signal new message
- Agent handles signal, reads message file
- Combines signals (notification) with files (data)

**Pros:**

- Immediate notification (no polling)
- File-based data (simple, debuggable)
- Standard Unix mechanism

**Cons:**

- Requires signal handler in agent
- Limited signal types available
- Need to handle signal delivery issues

## Recommended Approach: Hybrid Solution

### Phase 1: File-Based Messaging (Quick Win)

**Why:**

- Works immediately with existing infrastructure
- No agent modification required initially
- Easy to debug and inspect
- Can be enhanced later

**Implementation:**

1. Create `{session_id}.messages.jsonl` for each session
2. Registry writes messages to this file
3. For interactive agents (tmux), use `send_to_tmux_pane()`
4. For headless agents, they poll the file (future enhancement)
5. TUI reads from this file to show chat history

**Message Format:**

```json
{
  "id": "uuid",
  "type": "reprompt|message|command|system",
  "timestamp": "ISO8601",
  "sender": "user|agent|system",
  "content": "...",
  "metadata": {}
}
```

### Phase 2: Named Pipes (For Headless Agents)

**Why:**

- More efficient than polling
- Standard Unix mechanism
- Works well for headless processes

**Implementation:**

1. Create FIFO: `{session_id}.in` when session starts
2. Pass FIFO path via `THGENT_SESSION_INPUT_FIFO` env var
3. Agent opens FIFO in a background thread
4. Registry writes to FIFO for immediate delivery
5. Fallback to file-based if FIFO unavailable

### Phase 3: Chat History Storage

**Why:**

- Need structured conversation history
- Separate from stdout/stderr logs
- Enables context-aware reprompting

**Implementation:**

1. Create `{session_id}.chat.jsonl` alongside logs
2. Each agent interaction writes to chat log:
   - User prompt → chat log
   - Agent response → chat log
   - Tool calls → chat log
   - System messages → chat log
3. TUI reads chat log for history view
4. Reprompt includes recent chat history as context

### Phase 4: TUI Chat Interface

**Why:**

- Need interactive interface to view and send messages
- Should work with opentui/react (project standard)

**Implementation:**

1. Use opentui/react for TUI
2. Components:
   - Session list (all agents)
   - Chat view (messages + history)
   - Input field (send message)
   - Status panel (process info)
3. Features:
   - Select session
   - View chat history
   - Send reprompt
   - View logs (stdout/stderr)
   - Process management (stop/pause/resume)

## Architecture Design

### Agent Registry Structure

```
session_dir/
├── {owner}/
│   ├── {session_id}.json          # Session metadata
│   ├── {session_id}.stdout.log    # Stdout log
│   ├── {session_id}.stderr.log    # Stderr log
│   ├── {session_id}.chat.jsonl    # Chat history (NEW)
│   ├── {session_id}.messages.jsonl # Pending messages (NEW)
│   └── {session_id}.in            # Named pipe (NEW, optional)
├── discovered/
│   └── ppid_{ppid}.json           # Discovered agents
└── run_registry.jsonl             # Run registry
```

### Message Flow

1. **User sends reprompt via TUI:**

   ```
   TUI → Registry.write_message() → {session_id}.messages.jsonl
   ```

2. **For tmux sessions:**

   ```
   Registry → send_to_tmux_pane() → tmux pane
   ```

3. **For headless agents (future):**

   ```
   Registry → write to FIFO → Agent reads FIFO → Processes message
   ```

4. **Chat history:**
   ```
   Agent → write_chat_entry() → {session_id}.chat.jsonl
   TUI → read_chat_history() → Display in UI
   ```

### Component Design

#### 1. Message Registry (`thegent/src/thegent/messaging.py`)

```python
class MessageRegistry:
    def send_message(session_id: str, message: dict) -> bool: ...
    def get_pending_messages(session_id: str) -> list[dict]: ...
    def mark_processed(session_id: str, message_id: str): ...
    def create_fifo(session_id: str) -> Path | None: ...
```

#### 2. Chat History (`thegent/src/thegent/chat.py`)

```python
class ChatHistory:
    def append(session_id: str, entry: dict): ...
    def get_history(session_id: str, limit: int = 100) -> list[dict]: ...
    def get_context(session_id: str, max_chars: int = 8000) -> str: ...
```

#### 3. Agent Registry TUI (`thegent/src/thegent/tui/agent_registry.py`)

```python
class AgentRegistryTUI:
    def render_session_list(): ...
    def render_chat_view(session_id: str): ...
    def handle_input(session_id: str, message: str): ...
    def attach_to_session(session_id: str): ...
```

## Implementation Plan

### Step 1: Message Infrastructure (Week 1)

- [ ] Create `MessageRegistry` class
- [ ] Implement file-based messaging
- [ ] Add message format validation
- [ ] Add tests

### Step 2: Chat History (Week 1)

- [ ] Create `ChatHistory` class
- [ ] Integrate with agent runners to log interactions
- [ ] Add context extraction for reprompting
- [ ] Add tests

### Step 3: TUI Foundation (Week 2)

- [ ] Set up opentui/react TUI structure
- [ ] Create session list component
- [ ] Create chat view component
- [ ] Add basic navigation

### Step 4: Interactive Features (Week 2)

- [ ] Add message input component
- [ ] Implement send message functionality
- [ ] Add session attachment (tmux support)
- [ ] Add log viewing

### Step 5: Headless Support (Week 3)

- [ ] Implement FIFO creation
- [ ] Add FIFO reading to agent runners
- [ ] Add fallback to file-based
- [ ] Test with background processes

### Step 6: Ghostty Integration (Week 3)

- [ ] Research Ghostty mux API
- [ ] Add Ghostty session detection
- [ ] Implement Ghostty attachment
- [ ] Test integration

### Step 7: Polish & Documentation (Week 4)

- [ ] Add error handling
- [ ] Performance optimization
- [ ] Documentation
- [ ] User testing

## Open Questions

1. ~~**Ghostty Mux**~~: Ghostty is a terminal emulator, not a mux. Use tmux/holdpty inside Ghostty.
2. **Agent Modification**: How much can we modify agents vs. work around them?
3. **Context Window**: How much chat history to include in reprompts?
4. **Concurrency**: How to handle multiple users sending messages to same session?
5. **Security**: Should messages be authenticated/authorized?

## Recommendations from Web Research

| Approach                     | When to Use                  | Notes                                                                                                          |
| ---------------------------- | ---------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **holdpty**                  | New agent launches           | Wrap `thegent run --bg` in `holdpty launch --bg --name {session_id} --`; enables attach/view/logs without tmux |
| **reptyr**                   | Existing process in terminal | Linux only; grab PID, run `reptyr PID` in tmux; requires ptrace                                                |
| **gdb + FIFO**               | Headless process, need stdin | Redirect fd 0 to named pipe; write from registry; invasive                                                     |
| **mcp-interactive-terminal** | MCP integration              | Consider mounting or adapting for agent PTY sessions; clean output via xterm-headless                          |
| **File-based + tmux**        | Quick win                    | Keep current approach; use `send_to_tmux_pane` for tmux sessions; file queue for headless                      |

## Web Research Findings (DDG-based)

### Attaching to Detached/Headless Processes

**Baeldung (Linux):** [Attach a Terminal to a Detached Process](https://www.baeldung.com/linux/attach-terminal-detached-process)

- Detached process = no TTY (stdin closed, stdout/stderr redirected)
- **gdb approach**: Use `gdb -p PID` to `call close(0/1/2)` then `call open("/path/to/fifo", ...)` — redirects stdin to named pipe; write to pipe from another terminal
- **reptyr**: Uses ptrace to reparent process to new terminal; changes controlling TTY; works for interactive takeover
- `/proc/PID/fd/` shows where stdio points; piping to `/dev/pts/N` doesn't help (fills wrong terminal)
- Linux-only; reptyr requires `ptrace_scope=0` on Ubuntu

### reptyr (nelhage/reptyr) — 6.1k stars

- **Purpose**: Reparent running program to new terminal
- **Usage**: `reptyr PID` — grabs process, attaches to current terminal
- **How**: ptrace at syscall level; actually changes controlling terminal
- **Limitations**: Linux/FreeBSD; needs ptrace; doesn't work for fully headless (stdin=/dev/null)
- **Use case**: Process started in one terminal, move to tmux/screen before closing SSH

### holdpty (marcfargas/holdpty) — Minimal detached PTY

- **Purpose**: Launch commands in real PTY, attach/view/record later
- **Key insight**: "Between nohup and screen" — preserves PTY (TUI, colors) without window management
- **Commands**: `holdpty launch --bg --name X -- cmd` | `holdpty attach X` | `holdpty view X` | `holdpty logs X`
- **Architecture**: Holder process creates PTY via node-pty, buffers 1MB ring, listens on Unix domain socket
- **Platform**: Windows (ConPTY), Linux, macOS
- **Relevance**: Could wrap agent launches in holdpty for attachability; no tmux needed

### mcp-interactive-terminal (amol21p) — MCP server for AI agents

- **Purpose**: Give Claude Code/Cursor real interactive terminal sessions (REPLs, SSH, psql, etc.)
- **Architecture**: MCP server → node-pty + xterm-headless → clean text output
- **Tools**: `create_session`, `send_command`, `read_output`, `list_sessions`, `close_session`, `send_control`, `confirm_dangerous_command`
- **Smart completion**: 4-layer detection (timeout, output settling, prompt detection, process exit)
- **Relevance**: Pattern for persistent PTY sessions; could integrate or adapt for thegent agent registry

### Ghostty

- **Reality**: Ghostty is a terminal emulator (like iTerm/Alacritty), not a multiplexer
- **Windowing**: Supports multi-window, tabs, splits (native app features)
- **No mux API**: No tmux-like attach/detach API; sessions are tied to Ghostty windows
- **Implication**: For Ghostty users, use tmux/screen/holdpty inside Ghostty; Ghostty doesn't replace tmux

### Prior Art (holdpty credits)

- **dtach** (Ned T. Crigler): Minimal detach/attach for Unix
- **abduco** (Marc André Tanner): Same concept, composable

---

## References

- [Named Pipes (Wikipedia)](https://en.wikipedia.org/wiki/Named_pipe)
- [Unix Domain Sockets](https://man7.org/linux/man-pages/man7/unix.7.html)
- [opentui/react Documentation](https://github.com/sst/opentui/tree/main/packages/react)
- [Baeldung: Attach Terminal to Detached Process](https://www.baeldung.com/linux/attach-terminal-detached-process)
- [reptyr](https://github.com/nelhage/reptyr)
- [holdpty](https://github.com/marcfargas/holdpty)
- [mcp-interactive-terminal](https://github.com/amol21p/mcp-interactive-terminal)
- [Ghostty](https://github.com/ghostty-org/ghostty)
- Existing code: `thegent/src/thegent/cli_impl.py`, `thegent/src/thegent/tools/terminal.py`
