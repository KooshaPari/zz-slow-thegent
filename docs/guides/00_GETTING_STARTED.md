# Getting Started with thegent

**Time to first success: ~5 minutes**
**Audience:** New developers, new AI agents, contributors encountering thegent for the first time

---

## What is thegent?

thegent is a unified agent orchestration CLI and platform. It sits between you (or your AI agents) and the various AI providers (Claude, Codex, Gemini, Copilot, Cursor, and others), providing:

- **A single command** to run tasks across any provider
- **Automatic routing** to the best provider based on cost, quality, and availability
- **Governance** so agents cannot run wild (cost limits, prompt guardrails, audit trails)
- **Coordination** so multiple agents can work on the same codebase without collisions
- **Lifecycle hooks** that enforce quality gates before and after every agent action

Think of it as a dispatcher, referee, and audit logger for AI-assisted development.

---

## Step 1: Install

```bash
# Recommended (macOS / Linux)
curl -fsSL https://raw.githubusercontent.com/kooshapari/thegent/main/scripts/bootstrap.sh | sh -s -- install

# Or via uv (fastest package install)
uv tool install thegent

# Or via pip
pip install thegent
```

Verify the installation:

```bash
thegent --version
thegent doctor        # Diagnoses environment issues
```

`thegent doctor` checks for required binaries, API keys, shell integration, and git hooks. Fix anything it flags before continuing.

---

## Step 2: Configure Providers

thegent needs at least one AI provider configured. Run the interactive setup:

```bash
thegent setup --full
```

This walks you through:

1. **Shell integration** -- adds thegent to your zsh/bash/pwsh profile
2. **Provider API keys** -- connects Claude, OpenAI, Gemini, or other providers
3. **Agent mesh** -- initializes the coordination layer for multi-agent work
4. **Git hooks** -- installs performance-optimized hooks for quality enforcement

If you prefer manual configuration, API keys are read from environment variables:

| Variable            | Provider       |
| ------------------- | -------------- |
| `ANTHROPIC_API_KEY` | Claude         |
| `OPENAI_API_KEY`    | OpenAI / Codex |
| `GOOGLE_API_KEY`    | Gemini         |

---

## Step 3: Run Your First Task

```bash
# Run a task using the default (free-tier) provider
thegent free "Explain what this project does"

# Run with a specific provider
thegent run "Refactor the auth module" -M claude-sonnet-4.5

# Run the cheapest available option
thegent run "Write unit tests for utils.py" -M gemini-3-flash -R cheapest
```

What happens when you run a command:

1. **Input guardrails** check the prompt (length, blocklist, allowed agents)
2. **Routing** selects the optimal provider
3. **The agent runs**, with output streamed to your terminal
4. **Output normalization** converts the response to a Canonical Structured Message (CSM)
5. **Audit logging** records the run with a hash-chained entry in the registry

---

## Step 4: Verify Your Environment

```bash
# Check everything is healthy
thegent doctor

# See what agents are available
thegent mesh status

# View recent runs
thegent ps
```

---

## Step 5: Understand the Project Layout

If you are working on thegent itself (not just using it), here is what the repo looks like:

```
thegent/
  agents/              # Agent runner implementations (strategy pattern)
  commands/            # CLI command modules
  contracts/           # Governance contracts and policy definitions
  hooks/               # Lifecycle hooks (quality gates, validation)
    hook-dispatcher/   # Hook dispatch engine
    lib/               # Shared hook utilities (sourced, never called directly)
  config/              # Configuration files (YAML)
  scripts/             # Operational scripts (swarm controller, utilities)
  docs/
    guides/            # How-to guides (you are here)
    reference/         # API references, trackers, work stream
    architecture/      # System design documents
    concepts/          # Domain concept explainers
    research/          # Research notes and conversation dumps
    governance/        # Governance policies and processes
    context/           # Technology context docs for integrations
    plans/             # Work breakdown structures, phase plans
  tests/               # Test suite
```

Key files at the root:

| File                         | Purpose                                               |
| ---------------------------- | ----------------------------------------------------- |
| `PRD.md`                     | Product requirements -- the "what" and "why"          |
| `FUNCTIONAL_REQUIREMENTS.md` | Formal FR-XXX-NNN SHALL statements                    |
| `ADR.md`                     | Architecture decision records                         |
| `PLAN.md`                    | Phased work breakdown with dependencies               |
| `CLAUDE.md`                  | Agent instructions and project governance             |
| `Taskfile.yml`               | All quality commands (`task lint`, `task test`, etc.) |

---

## Step 6: Run Quality Checks

Before making any changes, know the quality workflow:

```bash
task lint          # Run all linters (ruff, oxlint)
task test          # Run all tests (pytest, vitest)
task typecheck     # Type checking
task quality       # Full pipeline (lint + typecheck + test + security)
task gate          # Strictest 9-gate quality system
```

thegent enforces test-first development. Write a failing test before fixing a bug. Write a test file before a source file.

---

## What to Read Next

| Goal                            | Document                                                                               |
| ------------------------------- | -------------------------------------------------------------------------------------- |
| Understand core domain concepts | [CONCEPTUAL_FOUNDATIONS.md](./CONCEPTUAL_FOUNDATIONS.md)                               |
| Plan your learning path         | [LEARNING_PATHS.md](./LEARNING_PATHS.md)                                               |
| Dive into the CLI               | [QUICK_START.md](./QUICK_START.md)                                                     |
| Understand anti-patterns        | [anti-patterns.md](./anti-patterns.md)                                                 |
| Debug issues                    | [AGENT_DEBUGGING_AND_REMEDIATION_GUIDE.md](./AGENT_DEBUGGING_AND_REMEDIATION_GUIDE.md) |
| Set up cross-platform           | [CROSS_PLATFORM_QUICK_START.md](./CROSS_PLATFORM_QUICK_START.md)                       |

---

## Quick Reference Card

```bash
# Essential commands
thegent doctor                  # Health check
thegent free "prompt"           # Run with default provider
thegent run "prompt" -M model   # Run with specific model
thegent mesh status             # Agent coordination status
thegent ps                      # List active/recent runs
thegent serve                   # Start MCP server

# Development commands
task quality                    # Full quality pipeline
task test                       # Run tests
task lint                       # Run linters

# Work stream commands
thegent plan do-next            # Pick up next work item
thegent plan loop               # Continuous autonomous work
thegent free --do-next          # Execute next backlog item
```

---

## Common First-Timer Pitfalls

1. **Missing API keys** -- `thegent doctor` will tell you. Set them in your shell profile or `.env`.
2. **Old Python** -- thegent requires Python 3.11+ (CPython) or PyPy 3.11+.
3. **No `task` binary** -- Install go-task: `brew install go-task` or `sh -c "$(curl -ssL https://taskfile.dev/install.sh)"`.
4. **Editing the canonical repo directly** -- Use worktrees for feature work. The main checkout stays on `main`.
5. **Adding fallback code** -- thegent forbids fallback/legacy compatibility patterns. Code must fail fast and loud.
