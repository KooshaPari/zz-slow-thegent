# Cursor Rules Security Update

## Summary

Added explicit security rules to prevent agents from killing other agent processes.

## Files Updated

1. **`AGENTS.md`** - Added security section at the top
2. **`.cursor/rules/thegent.mdc`** - Added security section at the top
3. **`CLAUDE.md`** - Added security section at the top

## Rules Added

### ⛔ FORBIDDEN Commands

Explicitly forbidden patterns:

- `ps -ao pid,command | grep "cursor-agent" | grep -v grep | grep -v 40690 | awk '{print $1}' | xargs kill -9`
- `ps | grep cursor-agent | xargs kill -9`
- `pkill cursor-agent`
- `killall cursor-agent`
- Any `kill -9` targeting agent processes
- Any `kill` targeting shell/terminal processes

### ✅ Correct Alternatives

- `thegent mcp prune` - Safe cleanup
- `thegent mcp prune --dry-run` - Preview
- `thegent ps` - List sessions
- `thegent stop <session_id>` - Proper stop

### 🛡️ Protected Processes

- Agent processes: cursor-agent, thegent, claude, codex, droid, opencode, copilot, gemini
- Shell processes: bash, zsh, sh, fish, tcsh, csh
- Terminal emulators: ghostty, terminal, iterm, alacritty, kitty, wezterm, warp

## Enforcement

- Rules are prominently placed at the top of all cursor rules files
- Code-level validation blocks these commands
- Violations are logged
- Rate limiting prevents abuse

## Status

✅ **COMPLETE** - Rules added to all cursor rules files. Agents will see these rules prominently displayed and commands will be blocked at the code level.
