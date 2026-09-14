# Agents

## Key Commands

```bash
# Development
task install    # Install dependencies
task lint       # Lint all source
task test       # Run test suite
task quality    # Full quality gate (lint + test + type check)
task dev        # Start development server with hot reload
task dev:tui    # Start services with interactive TUI dashboard
```

## Stack

- **Core**: Python (src/thegent/)
- **CLI**: Typer, Rich
- **Agent Integration**: BlackBoxProxy, Agent Discovery & Registration
- **Dotfiles**: Managed via `src/thegent/dotfiles/`

## Conventions

- Max function length: 40 lines. Cognitive complexity ≤ 15.
- No placeholder TODOs in committed code.
- All new code must pass: `ruff check .`, `ruff format .`, `pytest -q`.
- AGENTS.md symlink removed — file is now repo-native.

## Do Not Touch

- `services/colab/` — submodule (git@github.com:KooshaPari/colab.git); do not edit in-place

## ⛔ FORBIDDEN: Killing Agent or Terminal Processes

- **NEVER attempt to kill, terminate, or force-quit any agent processes, terminal sessions, or background workers.**
- **NEVER attempt to shut down, restart, or reboot the system or any services.**
- **NEVER attempt to kill terminal processes or close terminal windows.**
- If a process appears stuck, report it and wait for human intervention.

## ⛔ FORBIDDEN: Fallbacks, Legacy Compatibility, and Silent Failures

- **Do not degrade to shell scripts when Python/Bash/TypeScript is available.**
- **Do not fall back to simpler implementations when the spec requires a more robust approach.**
- **Always use the project's established tools and conventions.**
