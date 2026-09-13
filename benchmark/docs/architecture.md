# Harbor Architecture

## Core Concepts

### Jobs

- Orchestrate multiple trials
- Configured via YAML/JSON
- Results stored in jobs-dir

### Tasks

- Individual evaluations
- Containerized environment

### Agents

- oracle, codex, claude-code, etc.
- Execute in sandbox

### Environments

- docker (default)
- daytona (cloud)
- e2b, modal, gke

## Options for Lightweight Execution

```bash
# Use minimal resources
--override-cpus 1
--override-memory 512
--delete  # Auto-cleanup

# Or use oracle (no model needed)
--agent oracle
```
