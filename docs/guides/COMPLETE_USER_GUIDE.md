# 📖 thegent: Complete User Guide

> **Status**: Active | **Last Updated**: 2026-02-19
> **Purpose**: Comprehensive documentation for all features, configurations, and advanced capabilities of thegent.

---

## 1. Introduction

`thegent` is an autonomous agent orchestration system designed for high-performance development workflows. It integrates multiple AI agents (Claude, Cursor, etc.) into a unified mesh with shared memory, conflict resolution, and shell optimizations.

---

## 2. Core Components

### 2.1 Agent Mesh (formerly heliosShield)

The Agent Mesh is the coordination layer that prevents agents from stepping on each other's toes.

- **Process Discovery**: Automatically detects running agents.
- **Shared Tasks**: Global task list for multi-agent delegation.
- **Conflict Resolution**: AST-aware merging for parallel code changes.
- **Locking**: Atomic directory-level locks for safe resource access.

### 2.2 Shell Environment

A heavily optimized Zsh/Bash environment with:

- **Instant Prompt**: Zero perceived startup lag (< 5ms).
- **Lazy Loading**: Defer expensive tool initialization (nvm, pyenv) until first use.
- **Eval Caching**: Cache tool init strings to save hundreds of milliseconds.
- **Safeguards**: Fork explosion prevention and recursive command protection.

### 2.3 Hook Runtime (Rust)

The `thegent` hook system manages git hooks and task automation with minimal overhead.

- **Native Performance**: Built in Rust for <50ms dispatch time.
- **Parallel Execution**: Run multiple hooks simultaneously with serialized output.

---

## 3. Installation & Setup

### 3.1 Basic Installation

```bash
curl -fsSL https://raw.githubusercontent.com/kooshapari/thegent/main/scripts/bootstrap.sh | sh -s -- install
```

### 3.2 Full Setup

```bash
thegent setup --full
```

This configures:

1. **Shell**: Integration with `.zshrc` / `.bashrc`.
2. **Providers**: Login to Anthropic, OpenAI, Gemini.
3. **Hooks**: Git hook installation.
4. **Skills**: Syncing system prompts to agents.

---

## 4. Using the CLI

### 4.1 Mesh Commands

Manage the agent coordination layer:

- `thegent mesh status`: View active agents and their heartbeats.
- `thegent mesh discover`: Scan for and register new agent processes.
- `thegent mesh tasks`: View and manage the global task queue.

### 4.2 Shell Commands

Optimize and debug your environment:

- `thegent shell benchmark`: Measure shell startup performance.
- `thegent shell doctor`: Diagnose and fix environment issues.
- `thegent shell clear-cache`: Clear the eval and tool caches.

### 4.3 General Commands

- `thegent run "<task>"`: Execute an autonomous task.
- `thegent serve`: Start the MCP server for external tool integration.

---

## 5. Advanced Configuration

### 5.1 ThegentSettings (`~/.config/thegent/config.yaml`)

You can customize the behavior of `thegent` via its configuration file:

- `harness_root`: Path to the mesh coordination directory (default: `~/.agent-harness`).
- `log_level`: Detail level for system logs.
- `shell_optimization_enabled`: Toggle for advanced shell features.

### 5.2 Environment Variables

- `THGENT_AGENT_SHELL`: Preferred shell for agent-spawned processes.
- `THGENT_INSTANT_PROMPT`: Set to `0` to disable the instant prompt feature.

---

## 6. Security & Governance

`thegent` implements several layers of security:

- **Sensitive File Relocation**: Credentials are moved to `~/.config/thegent/` with strict permissions.
- **Action Artifacts**: Every significant agent action is logged and signed (MAIF).
- **Resource Isolation**: Limits on CPU, memory, and file descriptors via `ulimit`.

---

## 7. Troubleshooting

### Common Issues

- **ELOOP (Too many symbolic links)**: Usually caused by recursive directory structures in the mesh root. Fix with `thegent mesh reset`.
- **"command not found" (after install)**: Ensure `~/.local/bin` is in your `PATH` or run `thegent shell doctor --fix`.
- **Agent collisions**: Ensure all agents are registered via `thegent mesh discover`.

---

## See Also

- [QUICK_START.md](./QUICK_START.md) - Get started in 5 minutes.
- [ARCHITECTURE_LAYERS.md](../architecture/ARCHITECTURE_LAYERS.md) - Internal design overview.
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Project development status.
