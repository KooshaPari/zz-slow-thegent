# CRUN CLI Command Reference

**Complete guide to CRUN command-line interface commands and options (current behavior)**

## Table of Contents

1. [Global Options](#global-options)
2. [AI Plan Commands](#ai-plan-commands)
3. [Plan Commands](#plan-commands)
4. [Monitoring Commands](#monitoring-commands)
5. [UI Commands](#ui-commands)
6. [Examples](#examples)
7. [Error Messages & Solutions](#error-messages--solutions)

---

## Global Options

Global options work with any CRUN command:

```bash
crun [OPTIONS] COMMAND [ARGS]
```

| Option           | Description               | Example               |
| ---------------- | ------------------------- | --------------------- |
| `--help`         | Show help message         | `crun --help`         |
| `-v, --version`  | Show CRUN version         | `crun --version`      |
| `--list-clients` | List available UI clients | `crun --list-clients` |

---

## AI Plan Commands

AI planning commands are in the `ai-plan` namespace.

> Legacy docs may still show `crun plan generate-massive`. The current command path is `crun ai-plan generate-massive`.

### `crun ai-plan generate-massive`

Generate a large, detailed project plan using AI.

**Usage:**

```bash
crun ai-plan generate-massive [OPTIONS] DESCRIPTION_FILE
```

**Arguments:**

- `DESCRIPTION_FILE` - Path to PRD/description file (text or JSON)

**Options:**

| Flag                         | Default                     | Description                   |
| ---------------------------- | --------------------------- | ----------------------------- |
| `-o, --output`               | `massive-plan.json`         | Output path for generated WBS |
| `--max-depth`                | `4`                         | Maximum WBS hierarchy depth   |
| `--model`                    | `anthropic/claude-sonnet-4` | Primary model for generation  |
| `--fast-model`               | `anthropic/claude-haiku-4`  | Fast model for simpler tasks  |
| `--streaming/--no-streaming` | `--streaming`               | Enable streaming progress     |
| `--api-key`                  | from `OPENROUTER_API_KEY`   | API key override              |

**Examples:**

```bash
# Basic
crun ai-plan generate-massive project_spec.txt -o my_plan.json

# Custom depth and model
crun ai-plan generate-massive project_spec.txt --max-depth 5 --model anthropic/claude-opus-4 -o big_plan.json

# Use stdin
echo "Build a task management app" | crun ai-plan generate-massive - -o plan.json
```

### `crun ai-plan visualize`

**Usage:**

```bash
crun ai-plan visualize [OPTIONS] PLAN_FILE
```

**Arguments:**

- `PLAN_FILE` - Path to WBS plan file (JSON)

**Options:**

| Flag                                           | Default                | Description                           |
| ---------------------------------------------- | ---------------------- | ------------------------------------- |
| `-f, --format`                                 | `gantt`                | `gantt`, `dag`, `timeline`, `mermaid` |
| `-o, --output`                                 | auto                   | Output path                           |
| `--highlight-critical/--no-highlight-critical` | `--highlight-critical` | Highlight critical path               |

**Example:**

```bash
crun ai-plan visualize my_plan.json --format dag --output dag.png
```

### `crun ai-plan edit`

**Usage:**

```bash
crun ai-plan edit [OPTIONS] PLAN_FILE
```

**Options:**

| Flag             | Description                                                   |
| ---------------- | ------------------------------------------------------------- |
| `-t, --task`     | (required) Task ID to edit                                    |
| `--set-status`   | Set status (`pending`, `in_progress`, `completed`, `blocked`) |
| `--set-assignee` | Set assignee                                                  |
| `--set-priority` | Set priority                                                  |
| `--add-tag`      | Add a tag                                                     |
| `--remove-tag`   | Remove a tag                                                  |

### `crun ai-plan monitor`

**Usage:**

```bash
crun ai-plan monitor [OPTIONS] PLAN_FILE
```

**Options:**

| Flag                  | Default         | Description                                      |
| --------------------- | --------------- | ------------------------------------------------ |
| `-f, --follow`        | `False`         | Stream execution updates                         |
| `-w, --workers`       | `10`            | Maximum workers                                  |
| `-p, --priority`      | `critical_path` | `critical_path`, `slack`, `complexity`, `hybrid` |
| `--dry-run/--execute` | `--dry-run`     | Simulate or execute                              |

---

## Plan Commands

`crun plan` covers planning setup, validation, analysis, and task management commands (non-AI generation commands).

### Representative commands

- `crun plan init`
- `crun plan new`
- `crun plan show`
- `crun plan estimate`
- `crun plan cp`
- `crun plan risk`
- `crun plan sync`
- `crun plan watch`
- `crun plan install-hooks`
- `crun plan uninstall-hooks`
- `crun plan export-tasks`
- `crun plan run-tasks`
- `crun plan template list`
- `crun plan template show`
- `crun plan validate`
- `crun plan migrate`

Use `crun plan --help` to view the full command list available in your installed build.

---

## Monitoring Commands

Monitoring is under `crun monitor` for static quality/test monitoring.
Some builds may also expose adapter-based dashboards under `crun monitoring` (project/agent/quality/all).

### `crun monitor start`

Start static monitoring and optional lint/test fixing over a workspace.

Options:

- `--workspace, -w`: Workspace directory (default `.`)
- `--languages, -l`: Comma-separated languages to scan (default `python,typescript`)
- `--lint` (default true): Enable lint fixing
- `--tests` (default true): Enable test fixing
- `--workers, -j`: Max worker count (default `4`)

Example:

```bash
crun monitor start --workspace . --languages python,typescript
```

### `crun monitor list-models`

List models available to the monitor runner.

```bash
crun monitor list-models
```

### Legacy `crun monitoring` alias (when available)

If your installed build includes the optional adapter package, these legacy subcommands may appear:

`crun monitoring project | agent | quality | all`

---

## UI Commands

### `crun gui`

Launch the graphical user interface.

### `crun tui`

Launch the terminal user interface.

---

## Examples

### AI plan flow

```bash
cat > my_project.txt << 'EOF'
Build a REST API with:
- Authentication
- PostgreSQL
- Redis
- Docker containerization
EOF

crun ai-plan generate-massive my_project.txt -o api_plan.json
crun ai-plan visualize api_plan.json --format dag -o dag.png
crun ai-plan monitor api_plan.json --workers 8
```

### Planning setup flow

```bash
crun plan init
crun plan sync
crun plan show
```

### Monitoring flow

```bash
crun monitor start --workspace .
```

---

## Error Messages & Solutions

### Error: `Command not found: crun`

**Cause:** CRUN is not installed in the active environment.

**Solution:**

```bash
source venv/bin/activate
pip install -e ".[all]"
```

### Error: `Error: API key required`

**Cause:** OpenRouter API key missing.

**Solution:**

```bash
export OPENROUTER_API_KEY=or-your-key
```

### Error: `No such option: --use-tot`

**Cause:** `--use-tot` and `--use-adapt` were removed from `ai-plan`.

**Solution:** Use `--max-depth` and model selection (`--model`, `--fast-model`) instead.

### Error: `Usage: crun quality`

**Cause:** `crun quality` is not a top-level command.

**Solution:**

```bash
crun monitor start --workspace . --languages python,typescript --lint --tests
```

---

## Environment Variables for CLI

```bash
export CRUN_DEFAULT_MODEL=anthropic/claude-sonnet-4
export CRUN_DEBUG=true
export CRUN_LOG_LEVEL=DEBUG
export OPENROUTER_API_KEY=or-your-key
```

## Command Chaining

```bash
crun ai-plan generate-massive spec.txt -o plan.json && \
crun ai-plan visualize plan.json --format dag && \
crun ai-plan monitor plan.json --dry-run
```

**Version:** CRUN 3.0.0 | Last Updated: 2026-02-22
