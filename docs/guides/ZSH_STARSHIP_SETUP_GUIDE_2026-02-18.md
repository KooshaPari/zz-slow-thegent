# ZSH Integration & Starship Setup Guide

**Date:** 2026-02-18
**Version:** 1.0.0

This guide covers the zsh-thegent-integration plugin and Starship custom module for enhanced thegent workflow.

---

## Table of Contents

1. [Quick Install](#quick-install)
2. [ZSH Plugin](#zsh-plugin)
3. [Starship Module](#starship-module)
4. [Configuration](#configuration)
5. [Key Bindings](#key-bindings)
6. [Commands Reference](#commands-reference)

---

## Quick Install

```bash
# Run the installer
zsh ~/thegent/shell/install-zsh-plugin.sh

# Or manually source the plugin
echo 'source "$HOME/thegent/shell/zsh-thegent-integration/thegent.plugin.zsh"' >> ~/.zshrc
source ~/.zshrc
```

---

## ZSH Plugin

The plugin provides:

- **tg** - Quick thegent alias
- **tgf** - Run agent on file
- **tgw** - Watch mode
- **tgs** - Run skill
- **tgp** - Quick prompt
- **Async operations** - Background job management
- **Tab completions** - For all thegent commands

### Directory Structure

```
shell/zsh-thegent-integration/
├── thegent.plugin.zsh    # Main plugin file
└── lib/
    ├── functions.zsh     # Helper functions
    ├── completions.zsh   # Tab completions
    └── async.zsh         # Async operations
```

### Source Files

If you prefer manual setup:

```zsh
# In your .zshrc
export THEGENT_WORK_STREAM="$HOME/thegent/docs/reference/WORK_STREAM.md"
export THEGENT_ASYNC_ENABLE=1

source "$HOME/thegent/shell/zsh-thegent-integration/lib/functions.zsh"
source "$HOME/thegent/shell/zsh-thegent-integration/lib/async.zsh"
source "$HOME/thegent/shell/zsh-thegent-integration/lib/completions.zsh"
```

---

## Starship Module

The Starship module shows:

- Agent status (running/idle)
- Current work stream item
- Active LSP servers

### Manual Setup

```bash
# 1. Copy module to starship modules directory
mkdir -p ~/.config/starship/modules
cp ~/thegent/shell/starship/thegent.py ~/.config/starship/modules/

# 2. Add to starship.toml
cat >> ~/.config/starship/config.toml << 'EOF'

[thegent]
symbol = "🤖"
format = "[$symbol($status )($work_stream )($lsp )]($style)"
style = "bold green"
disabled = false
show_work_stream = true
show_lsp = true
EOF
```

### Test Starship Module

```bash
# Test the module
python3 ~/thegent/shell/starship/thegent.py

# Or test with starship
starship preset nerdfont-complete -o ~/.config/starship/config.toml
STARSHIP_CONFIG=~/.config/starship/config.toml starship module thegent
```

---

## Configuration

### Environment Variables

| Variable                  | Default                                   | Description               |
| ------------------------- | ----------------------------------------- | ------------------------- |
| `THEGENT_BIN`             | `thegent`                                 | thegent executable path   |
| `THEGENT_DEFAULT_TIMEOUT` | `300`                                     | Default timeout (seconds) |
| `THEGENT_ASYNC_ENABLE`    | `1`                                       | Enable async operations   |
| `THEGENT_WORK_STREAM`     | `~/thegent/docs/reference/WORK_STREAM.md` | Work stream file          |
| `THEGENT_LOG_FILE`        | `~/.thegent/logs/thegent.log`             | Log file location         |

### Plugin Options

```zsh
# Disable async
export THEGENT_ASYNC_ENABLE=0

# Custom thegent path
export THEGENT_BIN="/usr/local/bin/thegent"

# Custom timeout
export THEGENT_DEFAULT_TIMEOUT=600
```

---

## Key Bindings

| Binding | Command | Description          |
| ------- | ------- | -------------------- |
| `Alt+G` | `tg p ` | Quick thegent prompt |
| `Alt+F` | `tgf `  | Quick file agent     |
| `Alt+S` | `tgs `  | Skills menu          |

---

## Commands Reference

### Core Commands

| Command               | Description                                                                   |
| --------------------- | ----------------------------------------------------------------------------- |
| `tg <cmd>`            | Quick thegent alias (run, free, bg, ps, skills, hooks, lsp, mcp, serve, plan) |
| `tgf <file>`          | Run agent on file                                                             |
| `tgf <file> <prompt>` | Run agent on file with custom prompt                                          |
| `tgw [path]`          | Watch mode for file changes                                                   |
| `tgs <skill>`         | Run skill                                                                     |
| `tgs`                 | List available skills                                                         |
| `tgp <prompt>`        | Quick prompt                                                                  |
| `tgmcp <cmd>`         | Quick MCP commands (up, down, status, prune)                                  |

### Status Commands

| Command         | Description                    |
| --------------- | ------------------------------ |
| `tgwho`         | Show current agent context     |
| `tgwork`        | Show work stream               |
| `tgnext`        | Get next item from work stream |
| `tgstatus`      | Quick status check             |
| `tglog [lines]` | View thegent logs              |

### Documentation

| Command         | Description                  |
| --------------- | ---------------------------- |
| `tgdoc`         | List documentation           |
| `tgdoc <topic>` | Find documentation for topic |

### Async Operations

| Command         | Description             |
| --------------- | ----------------------- |
| `tgxa <cmd>`    | Async execute           |
| `tgxj`          | List all jobs           |
| `tgxj <job_id>` | Check job status        |
| `tgxl <job_id>` | View job logs           |
| `tgxk <job_id>` | Kill job                |
| `tgxw <job_id>` | Wait for job            |
| `tgxclean`      | Clean up completed jobs |

### Background Execution

| Command         | Description                    |
| --------------- | ------------------------------ |
| `tgbg <prompt>` | Run in background with polling |
| `tgsessions`    | List all sessions              |

---

## Examples

### Quick Tasks

```zsh
# Run a quick prompt
tgp Analyze the architecture

# Run on a file
tgf src/main.py

# Run on file with custom prompt
tgf src/utils.py "Find all async functions"

# List skills
tgs

# Run a skill
tgs sitback-agent
```

### Status Checks

```zsh
# Quick status
tgstatus

# Show work stream
tgwork

# Get next task
tgnext

# View recent logs
tglog 50
```

### Async Workflow

```zsh
# Start async task
tgxa "run 'Analyze codebase structure'"

# Check status
tgxj

# View output
tgxl job_12345

# Or wait for completion
tgxw job_12345
```

### Background Tasks

```zsh
# Run in background
tgbg "Review all PRs"

# Check sessions
tgsessions

# Stop session
thegent stop <session_id>
```

---

## Troubleshooting

### Plugin Not Loading

```bash
# Check if plugin loads
zsh -x 2>&1 | grep thegent

# Check PATH
echo $PATH

# Verify files exist
ls -la ~/.zsh/zsh-thegent-integration/
```

### Starship Not Showing

```bash
# Test module directly
python3 ~/thegent/shell/starship/thegent.py

# Check starship config
cat ~/.config/starship/config.toml | grep -A5 thegent

# Debug starship
STARSHIP_DEBUG=1 starship module thegent
```

### thegent Not Found

```bash
# Find thegent
which thegent
which -a thegent

# Install if needed
pip install thegent

# Or use full path
export THEGENT_BIN="/full/path/to/thegent"
```

---

## Files

| File                                                | Purpose          |
| --------------------------------------------------- | ---------------- |
| `shell/zsh-thegent-integration/thegent.plugin.zsh`  | Main plugin      |
| `shell/zsh-thegent-integration/lib/functions.zsh`   | Functions        |
| `shell/zsh-thegent-integration/lib/completions.zsh` | Completions      |
| `shell/zsh-thegent-integration/lib/async.zsh`       | Async            |
| `shell/starship/thegent.py`                         | Starship module  |
| `shell/install-zsh-plugin.sh`                       | Installer script |
