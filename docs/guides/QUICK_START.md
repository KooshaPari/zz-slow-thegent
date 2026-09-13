# 🚀 thegent: Quick Start Guide

> **Status**: Active | **Last Updated**: 2026-02-19
> **Purpose**: Get up and running with thegent agent orchestration system in less than 5 minutes.

---

## 1. Installation

### One-liner (Recommended)

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/kooshapari/thegent/main/scripts/bootstrap.sh | sh -s -- install
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/kooshapari/thegent/main/scripts/install.ps1 | iex
```

### Manual (pip / uv)

```bash
# Using uv (fastest)
uv tool install thegent

# Or using pip
pip install thegent
```

---

## 2. Initial Setup

Run the unified setup command to configure your shell, providers, and agent mesh:

```bash
# Run full interactive setup
thegent setup --full
```

### What this does:

- Configures your shell (zsh/bash/pwsh) for `thegent` integration.
- Sets up AI providers (Claude, OpenAI, Gemini).
- Initializes the **Agent Mesh** (coordination layer).
- Installs git shims for performance-optimized hooks.

---

## 3. Basic Commands

| Command                  | Description                                     |
| ------------------------ | ----------------------------------------------- |
| `thegent doctor`         | Verify your installation and fix common issues. |
| `thegent mesh status`    | Check the status of active agents in the mesh.  |
| `thegent mesh discover`  | Discover and register running agents.           |
| `thegent run "<prompt>"` | Run an autonomous task across your local tools. |
| `thegent serve`          | Start the MCP (Model Context Protocol) server.  |

---

## 4. Agent Mesh Coordination

`thegent` includes a high-performance coordination layer (formerly _heliosShield_) that prevents agent collisions and optimizes git operations.

```bash
# Check coordination status
thegent mesh status

# View shared task list
thegent mesh tasks
```

---

## 5. Provider Login

Connect `thegent` to your preferred AI models:

```bash
thegent login claude
thegent login openai
thegent login gemini
```

---

## 6. Development Workflow

If you are developing _thegent_ or custom skills:

```bash
# Install in editable mode
pip install -e .

# Run tests
task test

# Build documentation
task docs:build
```

---

## Next Steps

- [COMPLETE_USER_GUIDE.md](./COMPLETE_USER_GUIDE.md) - Deep dive into all features.
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Fix common environment issues.
- [ARCHITECTURE_LAYERS.md](../architecture/ARCHITECTURE_LAYERS.md) - Understand how it works.

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Project backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) - Master plan index
