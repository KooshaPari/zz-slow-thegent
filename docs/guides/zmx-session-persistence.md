# zmx Session Persistence

**Status**: Available (zmx optional)
**Backend env var**: `THGENT_SESSION_BACKEND`
**Related work stream item**: `muxless-zmx-integration`

---

## What is zmx?

[zmx](https://github.com/ghostty-org/zmx) is a Zig-based muxless terminal session persistence tool built on `libghostty-vt`. Unlike tmux or screen, zmx does not require a server daemon. Agent sessions can survive terminal detachment and be reattached from any window, including Ghostty.

Key capabilities:

- Create named sessions (`zmx new <name> -- <cmd>`)
- Detach and re-attach later (`zmx attach <name>`)
- List active sessions (`zmx list`)
- Terminate sessions (`zmx kill <name>`)
- Capture scrollback (`zmx capture <name> --lines N`)

---

## Installation

zmx is not yet available on most package managers. Build from source or grab a release binary:

```bash
# macOS/Linux: build from source
git clone https://github.com/ghostty-org/zmx
cd zmx
zig build -Doptimize=ReleaseSafe
# Place binary on PATH
cp zig-out/bin/zmx ~/.local/bin/zmx
```

Verify the install:

```bash
zmx --version
# or
zmx list
```

---

## Configuration

Set `THGENT_SESSION_BACKEND` in your environment or `.env` file:

| Value | Behavior |
|-------|----------|
| `auto` (default) | Probe for zmx; fall back to tmux/none |
| `zmx` | Use zmx explicitly; warn + fall back if not installed |
| `tmux` | Use existing tmux tooling (legacy path) |
| `none` | Disable session persistence entirely |

```bash
# .env or shell profile
export THGENT_SESSION_BACKEND=zmx

# Optional: override binary path if zmx is not on PATH
export THGENT_ZMX_BIN=/usr/local/bin/zmx
```

These map to `ThegentSettings.session_backend` and `ThegentSettings.zmx_bin`.

---

## How thegent uses zmx

When an agent run is started with session persistence enabled, thegent:

1. Calls `ZmxBackend.create(session_name, cmd)` to launch the agent command inside a zmx-managed pty.
2. Writes the session name to the session metadata so it can be resumed later.
3. To inspect output: `ZmxBackend.capture(session_name, last_lines=50)`.
4. To reattach interactively: `ZmxBackend.attach(session_name)`.
5. On agent completion or explicit stop: `ZmxBackend.kill(session_name)`.

### Fallback behavior

zmx not being installed does **not** break any agent run. The backend degrades gracefully:

```
auto  → zmx available?  yes → ZmxBackend
                         no  → None (use tmux or no persistence)
zmx   → zmx available?  yes → ZmxBackend
                         no  → warning logged, None returned
tmux  → None (caller uses thegent.tools.terminal)
none  → None
```

---

## Python API

```python
from thegent.session import ZmxBackend, resolve_session_backend

# Auto-detect
backend = resolve_session_backend()
if backend is not None:
    ok = backend.create("my-agent", ["claude", "--no-tty", "-p", "task.md"])
    sessions = backend.list()  # list[ZmxSession]
    output = backend.capture("my-agent", last_lines=100)
    backend.kill("my-agent")

# Explicit backend
backend = ZmxBackend(zmx_bin="zmx")
if backend.available:
    backend.create("agent-42", ["codex", "run", "task.md"])
```

### ZmxSession fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Session name |
| `pid` | `int \| None` | Process ID of session leader |
| `state` | `str` | `running`, `detached`, `exited`, or `unknown` |
| `cmd` | `str` | Command running in the session |
| `extra` | `dict[str, str]` | Additional metadata from zmx |

---

## Troubleshooting

**zmx not found after install**
Ensure the binary is on your `PATH` or set `THGENT_ZMX_BIN=/full/path/to/zmx`.

**Sessions not persisting after terminal close**
Confirm zmx was used to _start_ the session (not just the shell). The command must be wrapped by zmx: `zmx new <name> -- <cmd>`.

**`zmx list` shows sessions but `capture` returns empty**
Some zmx versions may not support `--lines`. The capture call falls back to returning empty string rather than raising.

**Enabling debug logs**

```bash
export THGENT_DEBUG=1
thegent run "..." --provider claude
```

Look for log lines starting with `zmx` to trace backend decisions.

---

## Related

- `src/thegent/session/zmx_backend.py` — Backend implementation
- `src/thegent/tools/terminal.py` — Existing tmux tooling
- `src/thegent/config.py` — `session_backend` and `zmx_bin` settings
- `docs/research/MUXLESS_AGENT_SESSION_MANAGEMENT_2026-02-19.md` — Research context
