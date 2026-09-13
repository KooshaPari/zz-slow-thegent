# CLI Reference

This page covers the core `thegent` commands used in local and CI workflows.

## Command Shape

```bash
thegent <command> [subcommand] [flags]
```

Global options are available on most commands:

- `--help` for command-specific usage.

## Session Commands

| Command                                                               | What it does                                    | Common usage                                          |
| --------------------------------------------------------------------- | ----------------------------------------------- | ----------------------------------------------------- |
| `thegent run agent <prompt>`                                          | Foreground run                                  | One-off tasks and interactive work                    |
| `thegent run agent <prompt> --skill <name>`                           | Foreground run with selected skill instructions | Skill-guided execution                                |
| `thegent run agent <prompt> --bg`                                     | Background run                                  | Longer jobs or parallel work                          |
| `thegent ps`                                                          | Session list                                    | Inspect active/recent sessions                        |
| `thegent stop <session_id>`                                           | Stop session                                    | Cancel or cleanup                                     |
| `thegent takeover <session_id>`                                       | Attach to session                               | Continue from existing context                        |
| `thegent run fork <session_id> [--from-turn N] [--new-session-id ID]` | Fork session history                            | Branch from a specific turn for alternative execution |
| `thegent run rollback <session_id> --n-turns N`                       | Roll back recent turns                          | Remove last N turns from a session                    |

Examples:

```bash
thegent run agent "audit this codepath" --agent codex
thegent run agent "refactor this module" --skill thegent-skills
thegent run agent "implement docs update" --agent claude --bg
thegent ps
thegent stop sess_abc123
thegent run fork sess_abc123 --from-turn 4 --new-session-id sess_branch_01
thegent run rollback sess_branch_01 --n-turns 1
```

Notes:

- `--from-turn` is 1-based and must be `>= 1`.
- `--n-turns` must be `>= 1`.

## Skill Commands

| Command                       | Purpose                                                                 |
| ----------------------------- | ----------------------------------------------------------------------- |
| `thegent skill list`          | Show discovered skills                                                  |
| `thegent skill list --json`   | Emit machine-readable discovered skills (stable deterministic ordering) |
| `thegent skill select <name>` | Validate skill and print `--skill` usage                                |

Example:

```bash
thegent skill list
thegent skill list --json
thegent skill select thegent-skills
thegent run agent "execute with selected skill" --skill thegent-skills
```

Error handling:

```bash
thegent skill select missing-skill
# Skill not found: missing-skill
```

## Planning Commands

| Command                                    | Purpose                                      |
| ------------------------------------------ | -------------------------------------------- |
| `thegent plan next`                        | Select highest-priority actionable work item |
| `thegent plan loop`                        | Continuously execute available tasks         |
| `thegent orchestrate loop "prompt" "todo"` | Worker/checker lifecycle loop                |

Example:

```bash
thegent plan next
thegent orchestrate loop "execute sprint tasks" "docs/reference/WORK_STREAM.md"
```

## Baseline Regression Commands

Use these commands to refresh benchmark baselines and enforce regressions in CI/local runs.

Current benchmark payloads must provide finite, non-negative `avg_microseconds` values per label.

| Command                                                                                                                                                               | Purpose                                                           |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `task bench:baseline:refresh`                                                                                                                                         | Regenerate `benchmarks/baseline.json` from WL-078 benchmark suite |
| `uv run python scripts/check_python_benchmark_regression.py --baseline benchmarks/baseline.json --current <path> --max-regression-pct 15`                             | Fail when current benchmarks regress beyond threshold             |
| `uv run python scripts/check_python_benchmark_regression.py --baseline benchmarks/baseline.json --current <path> --max-regression-pct 15 --require-complete-baseline` | Also fail if any baseline labels are missing in current results   |

Examples:

```bash
task bench:baseline:refresh

uv run python scripts/benchmark_python_suite.py \
  --iterations 50000 \
  --output benchmarks/results/python/latest.json \
  --overwrite

uv run python scripts/check_python_benchmark_regression.py \
  --baseline benchmarks/baseline.json \
  --current benchmarks/results/python/latest.json \
  --max-regression-pct 15

uv run python scripts/check_python_benchmark_regression.py \
  --baseline benchmarks/baseline.json \
  --current benchmarks/results/python/latest.json \
  --max-regression-pct 15 \
  --require-complete-baseline
```

## Health and Setup Commands

| Command                                       | Purpose                                                             |
| --------------------------------------------- | ------------------------------------------------------------------- | ------ | ------------------------------- |
| `thegent install -t all --scope both --setup` | Install user/system runtime assets and launch provider/setup wizard |
| `thegent setup`                               | Legacy compatibility alias to provider/setup wizard only            |
| `thegent doctor`                              | Verify dependencies and runtime health                              |
| `thegent install -t all`                      | Install runtime assets into user scope                              |
| `thegent shell-init <bash                     | zsh                                                                 | fish>` | Print shell integration snippet |

## MCP and Service Commands

| Command              | Purpose                                                        |
| -------------------- | -------------------------------------------------------------- |
| `thegent serve`      | Start MCP server for clients/tools                             |
| `thegent mcp reload` | Alias for `thegent mcp restart` (restart MCP + proxy services) |
| `thegent mcp hmr`    | Watch project changes and auto-restart MCP + proxy             |
| `thegent reload`     | Top-level shortcut for `thegent mcp reload`                    |
| `thegent hmr`        | Top-level shortcut for `thegent mcp hmr`                       |
| `thegent mcp prune`  | Cleanup stale MCP resources safely                             |

If you run into startup errors, use [Operations Troubleshooting](/operations/troubleshooting).
