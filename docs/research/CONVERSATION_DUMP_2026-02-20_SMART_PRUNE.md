<DONE>
# Conversation Dump: Smart Pruning System Implementation (2026-02-20)

## Issues Addressed

- **Resource Overload**: Reclaiming 1-2GB RAM per idle/finished agent session.
- **Documentation Hygiene**: Ensuring agents write conversation dumps before their environment is cleaned up.
- **Orphan vs. Redundant**: Moving beyond simple orphan pruning to "smart" pruning of active but idle sub-processes.

## Fixes and Improvements Applied

1.  **Core Logic**: Created `src/thegent/orchestration/smart_prune.py` with the `SmartPruner` class.
    - Implemented Triple-Lock Criteria: Idle (>60s) + Complete (Regex) + Docs Written (mtime audit).
    - Added support for Cursor-specific terminal monitoring via `~/.cursor/projects/.../terminals/`.
2.  **Sub-Process Targeting**: Enhanced `mcp_prune` in `src/thegent/main.py` to allow targeting sub-processes of a specific `parent_pid`.
    - Added `bash`, `zsh`, `sh` to the "leak" detection patterns.
3.  **CLI Integration**: Added `thegent mcp smart-prune` command.
4.  **Automation**: Added `smart_prune` gardening step to `src/thegent/sitback/gardening.py`.
5.  **Reprompting**: Implemented macOS AppleScript fallback to send instructions to Ghostty/Cursor if `tmux` is unavailable.
6.  **Regression Fix**: Fixed `NameError: List` in `cli_git.py`.

## Research Findings

- **Cursor Terminals**: Discovered that Cursor writes active terminal snapshots to `.cursor/projects/.../terminals/*.txt`, providing a high-confidence activity signal for IDE-managed agents.
- **MacOS Interaction**: AppleScript is the most reliable way to "type" into a non-tmux terminal process on macOS for reprompting.

## Next Steps

- **Monitor Load**: Observe if the load average drops below 20 after a few automated cycles.
- **Refine Regex**: Expand completion markers based on user-specific agent personas if false negatives occur.
- **Linux/Windows Automation**: Port the AppleScript reprompt logic to `xdotool` or `powershell` if needed for those platforms.

---

_Status: Strategy implemented and integrated._
