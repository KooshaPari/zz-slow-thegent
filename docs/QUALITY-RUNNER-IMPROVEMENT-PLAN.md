# Quality Runner — Improvement Plan

**Research & planning document** for optimizations, polish, enhancements, intuitiveness/robustness, reliability/extensibility/maintainability, and feature extensions.

---

## Usage (trace; task commands only)

```bash
cd trace
task quality:dag              # Run quality DAG (CLI)
task quality:dag:tui          # Run DAG with TUI progress
task quality:tui              # Open TUI dashboard (R=run, f=fix)
task quality:fix              # Run fix agents for failed steps
task quality:dag:only ONLY=py-lint,py-type   # Run specific steps + deps
task quality:dag:skip SKIP=py-test,go-test   # Skip steps + dependents
task quality:dag:dry-run      # Preview tiers and commands
task quality:dag:v            # Verbose step logs
task quality:dag:ci           # CI mode: compact one-line summary
task quality:dag:ci:junit JUNIT=.quality/junit.xml   # CI + JUnit XML
```

---

## 1. Current State Summary

### 1.1 Components

| Component                | Location                         | Purpose                                                 |
| ------------------------ | -------------------------------- | ------------------------------------------------------- |
| `quality_runner.py`      | thegent (shared) + trace (local) | DAG executor, soft-fail, writes logs + last-run.json    |
| `quality_fix_planner.py` | thegent (shared)                 | Reads last-run.json, returns failed steps with logs     |
| `quality_fix_runner.py`  | thegent (shared) + trace (local) | Runs fix commands for failed steps                      |
| `quality-report.py`      | trace only                       | Parses logs, action plan by file; hardcoded SPLIT_STEPS |
| `QualityRunnerApp` (TUI) | trace only                       | Textual dashboard, live logs, step status               |
| `quality-dag.yaml`       | per-project                      | Step dependencies and commands                          |
| `quality-fix-dag.yaml`   | per-project                      | Fix job commands per checker                            |

### 1.2 Data Flow

```
quality_runner.py → .quality/logs/<step>.log, .quality/logs/<step>.exit, .quality/last-run.json
                         ↓
quality_fix_planner.py → (step_name, log_path) for failed steps
                         ↓
quality_fix_runner.py → runs fix commands → .quality/fix-agents.json
```

### 1.3 Identified Gaps

| Area                  | Issue                                          | Impact                             |
| --------------------- | ---------------------------------------------- | ---------------------------------- |
| **Config validation** | No schema or cycle detection                   | Bad YAML → cryptic errors          |
| **Fix DAG deps**      | `quality_fix_runner` ignores `deps` in fix-dag | Fix jobs run in arbitrary order    |
| **Progress.json**     | `duration: 0` for all completed                | TUI can't show real durations      |
| **Quality report**    | Hardcoded SPLIT_STEPS, trace-only              | Shared projects get no action plan |
| **ROOT resolution**   | Shared script uses `Path.cwd()` only           | No --root, no env override         |
| **Error handling**    | Minimal, no structured logging                 | Hard to debug failures             |
| **TUI sharing**       | Trace TUI hardcodes ROOT                       | Other projects can't use TUI       |
| **Step filtering**    | No --only / --skip                             | Must run full DAG                  |
| **Timeout**           | Fixed 600s per step                            | No per-step override               |
| **Dry-run**           | None                                           | Can't preview without running      |

---

## 2. Research: Comparable Tools

| Tool                | Pattern                         | Relevance                          |
| ------------------- | ------------------------------- | ---------------------------------- |
| **tox**             | Env matrix, dependency ordering | Parallel envs, config-driven       |
| **nox**             | Python tasks, session deps      | Session = step, deps = DAG         |
| **make**            | DAG of targets                  | Classic DAG execution              |
| **Task (Taskfile)** | Task deps, optional             | Similar to our DAG                 |
| **Earthly**         | DAG builds, caching             | Parallel tiers, soft-fail patterns |

**Takeaways:**

- Config validation (schema) is standard
- Dry-run / list targets is common
- Per-step timeout/retry is rare but useful
- Progress/duration reporting improves UX

---

## 3. Improvement Plan by Category

### 3.1 Optimizations

| #   | Improvement                | Description                                                                  | Effort |
| --- | -------------------------- | ---------------------------------------------------------------------------- | ------ |
| O1  | **Parallel cap**           | Add `max_workers` per tier (default: len(tier)) to avoid resource exhaustion | Low    |
| O2  | **Lazy log writes**        | Buffer log writes, flush on step completion (reduce I/O)                     | Low    |
| O3  | **Progress.json batching** | Throttle writes (e.g. max 1/sec) during parallel runs                        | Low    |
| O4  | **Skip unchanged steps**   | Optional: hash inputs, skip if cache hit (like make)                         | High   |

### 3.2 Polish

| #   | Improvement                   | Description                                        | Effort |
| --- | ----------------------------- | -------------------------------------------------- | ------ |
| P1  | **Duration in progress.json** | Store actual `duration` in completed steps for TUI | Low    |
| P2  | **Step display names**        | Use `display` from DAG in logs, progress, last-run | Low    |
| P3  | **Structured exit codes**     | last-run.json: include `duration` per step         | Low    |
| P4  | **Clearer error messages**    | "Step X failed (exit 1)" with path to log          | Low    |

### 3.3 Enhancements

| #   | Improvement           | Description                                                 | Effort |
| --- | --------------------- | ----------------------------------------------------------- | ------ |
| E1  | **--only / --skip**   | `quality_runner --only py-lint,fe-lint` or `--skip py-test` | Medium |
| E2  | **--dry-run**         | Print tiers and commands, no execution                      | Low    |
| E3  | **--config / --root** | Override config path and project root                       | Low    |
| E4  | **Per-step timeout**  | `timeout: 300` in quality-dag.yaml                          | Low    |
| E5  | **Retry on failure**  | Optional `retries: 2` per step                              | Medium |

### 3.4 Intuitiveness & Robustness

| #   | Improvement                 | Description                                                         | Effort |
| --- | --------------------------- | ------------------------------------------------------------------- | ------ |
| I1  | **DAG config validation**   | Validate schema, detect cycles, undefined deps                      | Medium |
| I2  | **Graceful missing config** | If no quality-dag.yaml, suggest `task quality:gate` or link to docs | Low    |
| I3  | **Fix DAG ordering**        | Run fix agents in topological order (respect deps)                  | Medium |
| I4  | **Env var overrides**       | `QUALITY_ROOT`, `QUALITY_CONFIG` for CI/scripts                     | Low    |
| I5  | **Pre-flight checks**       | Warn if commands not found (e.g. `task`, `uv`)                      | Low    |

### 3.5 Reliability, Extensibility, Maintainability

| #   | Improvement                     | Description                                            | Effort |
| --- | ------------------------------- | ------------------------------------------------------ | ------ |
| R1  | **Unify trace + shared**        | Trace uses shared scripts; single source of truth      | Medium |
| R2  | **Quality report from DAG**     | Derive SPLIT_STEPS from quality-dag.yaml; share report | Medium |
| R3  | **Config schema (JSON Schema)** | Document and optionally validate quality-dag.yaml      | Medium |
| R4  | **Structured logging**          | Optional `--verbose` with timestamps, step names       | Low    |
| R5  | **Test coverage**               | Unit tests for topological_tiers, run_step, load_dag   | Medium |

### 3.6 Feature Extensions

| #   | Improvement                 | Description                                              | Effort |
| --- | --------------------------- | -------------------------------------------------------- | ------ |
| F1  | **TUI for shared projects** | QualityRunnerApp accepts ROOT; runnable from any project | Medium |
| F2  | **CI summary output**       | `--ci` mode: compact one-line summary, JUnit XML         | Medium |
| F3  | **Fix agent by-file**       | Optional: spawn fix per file (from quality-report)       | High   |
| F4  | **Watch mode**              | Re-run DAG on file changes (like pytest-watch)           | High   |
| F5  | **Quality baseline**        | Compare to baseline, fail only on regressions            | High   |

---

## 4. Prioritized Roadmap

### Phase A: Quick Wins (1–2 days)

1. **P1** Duration in progress.json and last-run.json
2. **P4** Clearer error messages
3. **E3** --config / --root
4. **I4** Env var overrides (QUALITY_ROOT, QUALITY_CONFIG)
5. **E2** --dry-run

### Phase B: Robustness (2–3 days)

6. **I1** DAG config validation (schema + cycles)
7. **I3** Fix DAG ordering in quality_fix_runner
8. **I2** Graceful missing config
9. **R4** Structured logging (--verbose)

### Phase C: Extensibility (3–5 days) — Complete

10. **E1** --only / --skip
11. **R1** Unify trace + shared (trace calls shared scripts)
12. **R2** Quality report from DAG (derive SPLIT_STEPS)
13. **F1** TUI for shared projects (ROOT injection)
14. **Task wrappers** quality:dag:only, quality:dag:skip (ONLY=, SKIP=)

### Phase D: Advanced (in progress)

14. **O4** Skip unchanged steps (cache)
15. **F2** CI summary / JUnit XML — done
16. **F3** Fix agent by-file
17. **R5** Test coverage

---

## 5. Detailed Design Notes

### 5.1 DAG Config Validation

```yaml
# quality-dag.yaml schema (conceptual)
steps:
  <name>:
    deps: [<name>] # must reference existing steps
    command: str # required
    display: str # optional
    timeout: int # optional, seconds
    retries: int # optional, default 0
```

**Validation rules:**

- No cycles (topological sort must consume all nodes)
- All `deps` must exist in `steps`
- `command` required, non-empty
- `timeout` > 0 if present

### 5.2 Fix Runner DAG Ordering

Current: `for step_name, _ in jobs: run fix_config[step_name]` (arbitrary order)

Proposed: `tiers = topological_tiers(fix_config); for tier in tiers: run tier in parallel`

### 5.3 Progress.json Enhancement

```json
{
  "running": ["py-lint"],
  "completed": {
    "naming": { "code": 0, "duration": 0.23 },
    "go-proto": { "code": 0, "duration": 1.1 }
  },
  "timestamp": "2026-02-16T09:00:00Z"
}
```

### 5.4 TUI ROOT Injection

- QualityRunnerApp: accept `ROOT` via env `QUALITY_ROOT` or `Path.cwd()`
- quality_runner_tui.py: pass ROOT when invoking app
- Shared entry point: `python -m quality_runner_tui` with cwd as default ROOT

### 5.5 Quality Report from DAG

- Replace hardcoded SPLIT_STEPS with: `steps.keys()` from quality-dag.yaml
- Add `suite` or `category` (lint/test) per step in config
- quality-report.py reads DAG, uses step names as log stems

---

## 6. Implementation Checklist (Phase A)

- [x] quality_runner.py: add `duration` to progress.json completed
- [x] quality_runner.py: add `duration` per step in last-run.json (step_details)
- [x] quality_runner.py: improve FileNotFoundError message with hint
- [x] quality_runner.py: add `--config`, `--root` args
- [x] quality_runner.py: support QUALITY_ROOT, QUALITY_CONFIG env
- [x] quality_runner.py: add `--dry-run` (print tiers + commands, exit 0)
- [x] Trace TUI step_status_table: show duration from step_details
- [x] Trace quality_runner: same Phase A features

---

## Phase B Implementation (Complete)

- [x] I1 DAG config validation (undefined deps, cycles, missing command)
- [x] I3 Fix DAG ordering in quality_fix_runner (topological tiers, parallel within tier)
- [x] I2 Graceful missing config (hint: task quality:gate)
- [x] R4 Structured logging (--verbose / -v with timestamped step logs)

---

## 7. Risks & Mitigations

| Risk                   | Mitigation                                              |
| ---------------------- | ------------------------------------------------------- |
| Breaking trace TUI     | Keep trace local scripts as fallback; migrate gradually |
| Config schema drift    | Add JSON Schema, validate in CI                         |
| Performance regression | Benchmark before/after; keep O2/O3 optional             |
| Over-engineering       | Phase A only; defer Phase D until needed                |

---

## 8. References

- [Trace QUALITY-RUNNER-DESIGN.md](../trace/docs/QUALITY-RUNNER-DESIGN.md)
- [thegent templates](../thegent/templates/shared/scripts/quality/)
- [Trace TUI](../trace/src/tracertm/tui/apps/quality_runner_app.py)
- [tox](https://github.com/tox-dev/tox), [nox](https://github.com/wntrblm/nox)
