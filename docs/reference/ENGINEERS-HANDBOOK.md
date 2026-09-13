---
title: Engineers Handbook
date: 2026-02-22
status: LIVING
owner: thegent
tags: [handbook, engineering, reference, standards]
---

# thegent Engineers Handbook

> **Purpose**: Single reference for all engineering standards, patterns, and decisions.
> **Audience**: Any agent or human working on thegent.
> **Update policy**: Update in the same session as changes that affect these standards.

---

## 1. Core Philosophy

### Fail Loud, Never Silent

- Code MUST fail and stop on errors
- `except E: pass` is FORBIDDEN
- `try: new(); except: old()` is FORBIDDEN — fix the root cause
- Silent degradation = hidden bugs that compound

### Library-First

Before writing any custom logic for a generic problem (retry, cache, HTTP, file watch, rate limit, circuit breaker): find and use a library.

| Need            | Library                | NOT                        |
| --------------- | ---------------------- | -------------------------- |
| Retry/backoff   | tenacity               | Custom retry loops         |
| HTTP            | httpx                  | requests, urllib           |
| File watching   | watchdog               | os.walk polling            |
| Caching         | cachetools / diskcache | Custom TTL dicts           |
| Circuit breaker | pybreaker              | Custom state machines      |
| Logging         | structlog              | print(), logging.getLogger |
| Config          | pydantic-settings      | Manual env parsing         |
| CLI             | typer                  | argparse                   |
| Validation      | pydantic               | Manual if/else             |

### Zero Backwards Compatibility

All changes are breaking changes by design. Zero user debt. No:

- Migration shims
- Deprecation warnings pointing to old APIs
- `v2_` prefixed files
- `_legacy_` functions

Verify parity BEFORE removal, then delete cleanly.

### Primitives First

Build generic building blocks before application logic. Config-driven over code-driven. No feature flags for simple changes — just change the code.

---

## 2. Code Quality Standards

### Complexity Limits

| Metric                | Limit      |
| --------------------- | ---------- |
| Function length       | 40 lines   |
| Cyclomatic complexity | 10         |
| Cognitive complexity  | 15         |
| Code duplication      | 5% (jscpd) |

### Type Safety

- Pyright strict mode: **0 errors, 0 warnings** is the invariant
- No `# type: ignore` without inline justification
- No `Any` without justification
- Native extension stubs go in `typings/` (`.pyi` files)

### Import Rules

- Forbidden: `try: import X; except ImportError: X_AVAILABLE = False`
- Forbidden: `try: from X import Y; except: from Z import Y`
- Always: mandatory direct imports, fail at startup if missing
- Exception: native extensions with `# type: ignore[reportMissingImports]`

### `__all__` Rules

- Must be a **static literal list** — no `sorted({*globals(),...})`
- Private functions imported by other modules need public names or explicit `__all__`
- Remove symbols from `__all__` if they don't actually exist in the module

### Lint Pipeline

```bash
task quality  # Full strict pipeline
ruff check src/  # Fast lint
python -m pyright src/thegent  # Type check
```

Never bypass with `--no-verify` or `# noqa` without justification.

---

## 3. Testing Standards

### Test-First Mandate

1. Write failing test BEFORE writing implementation
2. For bugs: regression test MUST exist before fix
3. No committed code without paired test file

### Coverage Targets

| Project type         | Unit | Integration | E2E  |
| -------------------- | ---- | ----------- | ---- |
| Agent-only (thegent) | 100% | 100%        | 100% |
| Other                | 70%  | 20%         | 10%  |

### FR Traceability

All tests MUST reference FR ID:

```python
@pytest.mark.requirement("FR-XXX-NNN")
def test_something(): ...
```

Target: ≥ 85% FR traceability.

### Test Lanes

| Lane      | When         | Examples                 |
| --------- | ------------ | ------------------------ |
| `fast`    | Every commit | Unit tests, <2s total    |
| `nightly` | Daily CI     | Integration, slow unit   |
| `deep`    | Weekly       | E2E, mutation, benchmark |

---

## 4. Architecture

### Module Boundaries

Enforced by `tach.toml`. Never cross boundaries without updating the contract.

Key boundaries:

- `thegent.core` → no imports from `thegent.cli.*`
- `thegent.contracts` → no circular imports
- `thegent.routing` → only depends on `thegent.core`, `thegent.contracts`

### Where to Add Functionality

| Add...               | Put in...                                            |
| -------------------- | ---------------------------------------------------- |
| Agent persona        | `agents/<name>.md` + TOML role                       |
| Lifecycle hook       | `hooks/<event>-<name>.sh` + `hooks/hook-config.yaml` |
| Governance policy    | `contracts/<policy>.json` + `qa-policy-engine.sh`    |
| MCP tool             | MCP server (FastMCP pattern)                         |
| CLI command          | `commands/<command>/` + dispatch registration        |
| Quality gate         | `hooks/qa-<gate-name>.sh`                            |
| Research/context doc | `docs/context/<technology>.md`                       |

### Provider Pattern

New extensible services use `ProviderRegistry`. MCP tools go through FastMCP registration. No direct instantiation of providers outside their registry.

### Polyglot Rules

| Language | Target                                        | Toolchain                             |
| -------- | --------------------------------------------- | ------------------------------------- |
| Python   | CPython 3.14 (primary), PyPy 3.11 (secondary) | uv + ruff + pyright                   |
| Rust     | stable                                        | fmt + clippy -D warnings + cargo test |
| Go       | supported lanes                               | go test ./... + go vet ./...          |
| Zig      | pinned stable                                 | zig test                              |
| Mojo     | pinned                                        | parity checks vs reference impl       |

Conversion between languages only when measured SLO triggers are met and documented. Never speculative conversion.

---

## 5. Documentation Standards

### Doc Structure

```
docs/
  context/      # Technology reference docs (authoritative, no hallucinations)
  plans/        # Implementation plans (WBS, DAG, phased)
  research/     # CONVERSATION_DUMP_*.md, audit findings
  reports/      # Completion reports, status reports
  reference/    # WORK_STREAM.md, quick references
  guides/       # How-to guides
  changes/      # Per-change docs; archive/ for completed
  governance/   # Policy docs
```

Never create `.md` files in the project root except: `README.md`, `CHANGELOG.md`, `CLAUDE.md`, `PRD.md`, `ADR.md`, `PLAN.md`, `AGENTS.md`.

### Context Docs

Every technology integrated into thegent needs a `docs/context/<technology>.md` with:

1. Header (what, source URL, fetch date)
2. What is {Tech} (definition, capabilities, thegent integration)
3. Key Concepts
4. API/Interfaces (exact specs)
5. Authentication
6. Code Examples (working, tested)
7. Sources & References
8. Quick Reference cheat sheet

Refresh any doc > 90 days old.

### Conversation Dumps

After EVERY session that produces decisions/research/fixes:

- Write to `docs/research/CONVERSATION_DUMP_YYYY-MM-DD.md`
- Include: goal, files modified, decisions made, research findings, open questions, next steps
- Do not defer — write in the same session

### Work Stream

`docs/reference/WORK_STREAM.md` is canonical. Claim before starting work. Mark COMPLETED when done.

---

## 6. Security Standards

### Pipeline (5 layers, runs on Stop)

1. **Secrets**: gitleaks
2. **SAST**: semgrep, bandit (Python), gosec (Go)
3. **Dependencies**: pip-audit, npm audit, govulncheck
4. **Infrastructure**: hadolint, tfsec, trivy
5. **Supply Chain**: syft SBOM, osv-scanner

### Code Rules

- Never trust user input at system boundaries
- Validate at boundaries only (not internal functions)
- No command injection (never `subprocess.run(user_input, shell=True)`)
- No SQL injection (parameterized queries only)
- No secrets in code — use env vars or secret manager

---

## 7. Operations

### Service Management

- Never start/stop the whole dev stack — restart only the specific service
- Services use hot reload — save files and let watchers pick up changes
- Read logs via CLI or log files, never attach to user's TUI terminal

### Process Safety

FORBIDDEN (will be blocked by hooks):

```bash
pkill cursor-agent
kill -9 <pid>  # any agent/shell/terminal process
git restore .
git reset --hard
git clean -f
```

Safe alternatives:

```bash
thegent mcp prune       # clean orphaned LSP/MCP processes
thegent stop <id>       # stop a specific session
```

### Debugging

```bash
THGENT_DEBUG=1 thegent run ...    # full debug output
thegent run --debug "task"        # equivalent
thegent ps                        # list active sessions
thegent status <session_id>       # session status
```

---

## 8. Tooling Quick Reference

### Rust tools (prefer over system equivalents)

```bash
rg           # ripgrep: prefer over grep (5-10x faster)
fd           # prefer over find
jaq          # prefer over jq
```

Export `USE_BUILTIN_RIPGREP=0` for system ripgrep.

### Package manager detection

From lockfiles: `bun.lockb/bun.lock` → bun | `pnpm-lock.yaml` → pnpm | `yarn.lock` → yarn | `package-lock.json` → npm

### Python env

```bash
uv run python       # always use uv
uv pip install X    # install deps
task quality        # full quality pipeline
task test           # tests only
task diag:wl137     # weekly LOC/refactor diagnosis
```

---

## 9. Current Quality Metrics (as of 2026-02-22)

| Metric                | Current  | Target        |
| --------------------- | -------- | ------------- |
| Pyright errors        | **0**    | 0             |
| Pyright warnings      | **0**    | 0             |
| LOC (core surface)    | ~117,587 | trending down |
| `cli.py` lines        | 49       | <100          |
| `impl.py` lines       | 561      | <600          |
| `mcp/server.py` lines | 228      | <250          |
| Test coverage         | TBD      | 100%          |
| FR traceability       | TBD      | ≥85%          |

---

## 10. Open Work (as of 2026-02-22)

| ID            | Item                                       | Priority |
| ------------- | ------------------------------------------ | -------- |
| WL-147/148    | B90 multi-agent batch decomposition        | P1       |
| WL-NEW-01..14 | Research engine                            | P2       |
| WL-NEW-20..26 | Session dump automation + plan index       | P2       |
| WL-NEW-30..40 | Agent role system (tester, reviewer, etc.) | P2       |
| —             | `task quality` full pipeline pass          | P1       |
| —             | Test suite 100% coverage pass              | P1       |
| —             | FR traceability audit ≥85%                 | P1       |

See `docs/reference/WORK_STREAM.md` for full backlog.
