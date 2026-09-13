<DONE>
# Wait Command Keepalive Implementation

## Problem

The `thegent wait` command times out at 4 minutes (likely due to Cursor's guard timeout). When waiting for long-running background sessions, the command gets killed before completion.

## Solution

Implemented terminal keepalive mechanism that:

1. Detects the calling terminal/PID using `os.getppid()` and `psutil`
2. Identifies Cursor terminals via process name and environment variables
3. Sends keepalive input (Enter key) every 3 minutes to prevent timeout
4. Works with both direct stdin and tmux panes

## Implementation

### New Module: `terminal_keepalive.py`

Located at: `src/thegent/infra/terminal_keepalive.py`

**Features:**

- `TerminalKeepalive` class: Manages keepalive thread
- `_get_parent_terminal_info()`: Detects parent process and terminal type
- `_send_keepalive_to_stdin()`: Sends Enter to stdin
- `_send_keepalive_via_tmux()`: Sends Enter via tmux if in tmux session
- Auto-detection of Cursor terminals via:
  - Process name matching (`cursor`, `code`, `vscode`, `claude`)
  - Environment variables (`CURSOR_SANDBOX`, `CURSOR_ASKPASS`)
  - tmux session detection

**Usage:**

```python
from thegent.infra.terminal_keepalive import create_keepalive

keepalive = create_keepalive(interval=180.0)  # 3min intervals
keepalive.start()
# ... long-running operation ...
keepalive.stop()
```

### Integration

**Modified Files:**

1. `src/thegent/cli.py` - `wait_cmd()` function
2. `src/thegent/cli_impl.py` - `wait_impl()` function

Both functions now:

- Create keepalive instance on start
- Start keepalive thread automatically
- Stop keepalive on completion or error

## Detection Logic

The keepalive is enabled when:

1. Running in interactive terminal (`sys.stdin.isatty()`)
2. Parent process is Cursor/IDE (detected via process name)
3. OR Cursor environment variables are present
4. OR running in tmux (may be Cursor's terminal)

## Keepalive Methods

1. **Stdin Method**: Writes `\n` to `sys.stdin` (simulates Enter)
2. **Tmux Method**: Uses `tmux send-keys` to send Enter to current pane

Both methods are tried, and either can succeed.

## Configuration

- **Interval**: Default 180 seconds (3 minutes, under 4min timeout)
- **Enable/Disable**: Can be disabled via `enabled=False` parameter
- **Debug**: Set `THGENT_DEBUG_KEEPALIVE=1` to see keepalive logs

## Testing

Test detection:

```bash
python3 -c "from thegent.infra.terminal_keepalive import _get_parent_terminal_info; print(_get_parent_terminal_info())"
```

Test keepalive:

```bash
# In Cursor terminal, run a long wait
thegent wait <session_id>
# Keepalive will automatically send Enter every 3 minutes
```

## Notes

- Keepalive is optional - if it fails to start, the wait command continues normally
- Uses daemon thread so it doesn't prevent process exit
- Automatically stops when wait completes
- Works with both CLI and MCP server implementations
