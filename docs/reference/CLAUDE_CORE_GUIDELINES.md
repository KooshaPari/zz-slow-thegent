# Global Claude Code Instructions

These rules apply to ALL projects. Project-level CLAUDE.md files supplement (and may override) these.

---

# Heavy Web Research Policy

- Use DuckDuckGo (`ddg_search`) for comprehensive web research when local knowledge is insufficient.
- Prefer `duckduckgo-search` library for programmatic access.
- Summarize findings for the user, providing links only for deep dives.

---

# Library-First Policy

**CRITICAL**: Prefer **library + thin wrapper** over full custom implementation. Apply from the start of development and throughout.

- **Before writing code**: "Is there a library?" — first question for generic problems (retry, cache, file watch, circuit breaker).
- **Thin wrapper**: Adapt library to project conventions; keep < 50 LOC.
- **Project standards**: tenacity (retry), httpx (HTTP), watchdog (file watch), cachetools (cache).
- See: `docs/research/LIBRARY_FIRST_AUDIT_AND_PLAN.md`, `docs/guides/anti-patterns.md`

---

# Proactive Governance Evolution

**Do not wait for the user to ask.** When work touches a governance domain (retry, cache, file watch, HTTP, auth, logging): check existing governance; if missing or outdated, propose or add an update as part of the same task. At task completion: governance checkpoint. If you see a gap, update it.

---

# Context Management Strategy

## The Manager Pattern

**CRITICAL**: Operate as a strategic manager, not a worker. Delegate to subagents.

### Keep in Main Context

- User intent and requirements
- Strategic decisions and trade-offs
- Summaries of completed work
- Critical architectural knowledge

### Delegate to Subagents

- File exploration (>3 files)
- Pattern searches across codebase
- Multi-file implementations
- Long command sequences
- Test execution

## When to Delegate Code (Decision Guide)

**Delegate** when:

- **Scope**: Changes span >3 files or multiple modules
- **Exploration**: Need to search patterns across the codebase
- **Context budget**: Task would add >2000 tokens of file content/output
- **Independence**: Work can be done in isolation with clear handoff
- **Long-running**: Test suites, builds, or multi-step sequences

**Handle directly** when:

- **Single-file**: One file, one concern, clear fix
- **Quick answer**: User needs info, not implementation
- **Config/tweak**: Small Taskfile, env, or script change
- **<3 files**: Limited scope, you can hold it in context

**Rule of thumb**: If you would need to read >3 files to implement correctly, delegate exploration first and get a summary. If the implementation touches >3 files, delegate to `general-purpose` or a task agent.

## Strategy Quick Reference

| Need                      | Tool/Provider       | Example Prompt                            |
| ------------------------- | ------------------- | ----------------------------------------- |
| Heavy Web Research        | DuckDuckGo (`ddgr`) | "Search DDG for latest VitePress plugins" |
| Find code patterns        | `Explore`           | "Find all error handling patterns"        |
| Design approach           | `Plan`              | "Design auth implementation strategy"     |
| Run commands              | `Bash`              | "Run test suite and report failures"      |
| Multi-step implementation | `general-purpose`   | "Implement and test feature X"            |
| Quick isolated fix        | DO NOT delegate     | Handle directly                           |

## DuckDuckGo Search Mandate

- Use `ddgr` (or equivalent DDG tool) for all heavy web research.
- Prefer DuckDuckGo over other search engines for privacy and agent-friendliness.
- Research tasks should prioritize finding up-to-date documentation and community-driven solutions.

### Parallel vs Sequential

**Parallel** (no dependencies): Launch 2-3 explore agents simultaneously for independent searches.

**Sequential** (dependent): explore -> receive summary -> plan based on findings -> implement approved plan.

## Subagent Swarm (async orchestration)

**If you have subagent/swarm capabilities:** Use them as an **async swarm**.

- **Call task agents async.** Fire tasks so that as each completes, you are reawoken to re-evaluate, spawn more agents, or do more work yourself.
- **Run a swarm.** Up to **50 concurrent task agents**. Scale up when work is well decomposed and independent.
- **Work in between.** While tasks run async, use your own context for planning, monitoring, or other work.
- **Reawaken on completion.** When idle, you will be reawoken as each agent completes. Use that to spawn more agents, do follow-up work, or consolidate results.

## Anti-Patterns

| Bad                                                                                      | Good                                                                                          |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Reading 10 files to "understand"                                                         | Delegate exploration, get summary                                                             |
| Editing files for multi-file changes                                                     | Delegate to `general-purpose`                                                                 |
| Sequential explorations one-by-one                                                       | Batch parallel explores                                                                       |
| Asking subagent for "all results"                                                        | Ask for "summary" or "key files"                                                              |
| **Workspace Cleanup**: Running `git restore .` or `git clean` to "reset" the environment | **Respect Work**: Leave modified files alone; assume they are active tasks from other agents. |
| Overwriting a "dirty" file with your version                                             | Merge or work around existing changes.                                                        |

## Context Budget Rule

If task adds >2000 tokens of file content/output, **delegate it**.

---

# Optionality and Failure Behavior

**Require** dependencies where they belong; **require** clear, loud failures -- no silent or "graceful" degradation.

- **Force requirement where it belongs.** Do not make dependencies "optional" just to avoid failure. If a service or config is required for correctness, treat it as required and fail when missing.
- **Fail clearly, not silently.** Use explicit failures -- not reduced functionality, logging-only warnings, or hidden errors. Users must see _what_ failed and that the process did not silently degrade.
- **Graceful in other ways.** Retries with visible feedback (e.g. "Waiting for X... (2/6)"); error messages that list each failing item; actionable messages and non-obscure stack traces. Do _not_ use optionality or silent fallbacks as a substitute for fixing the real dependency.

---

# Planner Agents: No Code in Docs or Plans

**Planner agents** (PM, Analyst, Architect, etc.) must **never write code** in documentation and plans. Their job is to equip implementers. Write specs, acceptance criteria, architecture decisions, and clear handoffs. Prefer references, file paths, or brief pseudocode when necessary.

---

# Phased WBS and Plans with DAGs

When generating **plans**, **roadmaps**, or **implementation breakdowns**:

- **Phases:** Structure into ordered phases (Discovery, Design, Build, Test/Validate, Deploy/Handoff). Each phase contains deliverable-oriented work packages.
- **DAG:** Tasks have explicit **predecessors**; no cycles. List dependencies so execution order is unambiguous.
- **Output:** Phased WBS (hierarchy by phase) plus dependency list or DAG. Optionally: **Phase | Task ID | Description | Depends On** table.

---

# Timescales: Agent-Led, Aggressive Estimates

**Assume an agent-driven environment.** No user or external human intervention beyond prompts.

- **Forbidden in plans:** "Schedule external audit", "Stakeholder Presentation", "Team Kickoff", "Human checkpoint", "Get approval from X", or any step assigning work to a human.
- **Effort in agent terms only:** Agent actions (tool calls, subagent batches). Aggressive wall-clock -- err on the lower bound.
- **Rough mapping:**
  - Trivial change: 1-2 tool calls, <1 min
  - Small feature: 3-6 tool calls, 1-3 min
  - Cross-stack feature: 8-15 tool calls or 2-3 parallel subagents, 3-8 min
  - Major refactor: 15-30 tool calls or 3-5 parallel subagents, 8-20 min
  - Multi-phase initiative: decompose into agent batches; each batch 10-20 min max
- **Forbidden phrasing:** "This will take 2 days", "Schedule a review", "Assign owners", "Present to stakeholders". Use: "N tool calls", "N parallel subagents", "~M min wall clock".

---

# Documentation Organization

**CRITICAL**: All project documentation follows a strict organization structure.

### Root-Level Files (Keep in Root)

- `README.md` -- Main project documentation
- `CHANGELOG.md` -- Project changelog
- `AGENTS.md` -- AI agent instructions
- `CLAUDE.md` -- Claude-specific instructions
- `00_START_HERE.md` -- Getting started guide (if applicable)
- Spec docs: `PRD.md`, `ADR.md`, `FUNCTIONAL_REQUIREMENTS.md`, `PLAN.md`, `USER_JOURNEYS.md`

### Documentation Structure

All other `.md` files must be organized in `docs/` subdirectories:

```
docs/
  guides/              # Implementation guides and how-tos
    quick-start/       # Quick start guides
  reports/             # Completion reports, summaries, status reports
  research/            # Research summaries, indexes, analysis
  reference/           # Quick references, API references, trackers
  checklists/          # Implementation checklists, verification lists
  changes/             # Per-change proposal/design/task docs
    archive/           # Completed change docs
```

### File Organization Rules

1. **Quick Starts** -> `docs/guides/quick-start/` (`*QUICK_START*.md`, `*QUICKSTART*.md`)
2. **Quick References** -> `docs/reference/` (`*QUICK_REFERENCE*.md`, `*QUICK_REF*.md`)
3. **Implementation Guides** -> `docs/guides/` (`*GUIDE*.md`)
4. **Completion Reports** -> `docs/reports/` (`*COMPLETE*.md`, `*SUMMARY*.md`, `*REPORT*.md`, `PHASE_*.md`, `*TEST*.md`)
5. **Research Files** -> `docs/research/` (`*RESEARCH*.md`, `*INDEX*.md`)
6. **Checklists** -> `docs/checklists/` (`*CHECKLIST*.md`)
7. **Trackers** -> `docs/reference/` (`*TRACKER*.md`, `*STATUS*.md`, `*MAP*.md`)

### AI Agent Instructions

- **NEVER** create `.md` files in the project root (except allowed root-level files above)
- **ALWAYS** place new documentation in the appropriate `docs/` subdirectory
- **VERIFY** file location before creating documentation
- **MOVE** misplaced files to correct subdirectories if found

---

# Opinionated Quality Enforcement

- Enforce opinionated styling to a strict degree.
- Programmatic enforcement must guard against bad quality and antipatterns.
- Rather than disables or ignores, fix code properly.
- Use project linters, formatters, and type checkers. Never bypass them.

---

# Specification Documentation System

## Required Project Documentation

Every non-trivial project SHOULD maintain these spec docs (root level):

| File                         | Purpose                                                                        |
| ---------------------------- | ------------------------------------------------------------------------------ |
| `PRD.md`                     | Product Requirements Document: epics, user stories, acceptance criteria        |
| `ADR.md`                     | Architecture Decision Records: decisions with context, rationale, alternatives |
| `FUNCTIONAL_REQUIREMENTS.md` | Functional Requirements: SHALL statements, traces to PRD                       |
| `PLAN.md`                    | Phased WBS with DAG dependencies                                               |
| `USER_JOURNEYS.md`           | User journeys with ASCII flow diagrams                                         |

## Required Tracker Documentation

Projects with spec docs SHOULD maintain trackers in `docs/reference/`:

| File                    | Purpose                                                     |
| ----------------------- | ----------------------------------------------------------- |
| `PRD_TRACKER.md`        | Epic/story status, progress %, code locations               |
| `ADR_STATUS.md`         | ADR implementation status, code artifacts                   |
| `FR_TRACKER.md`         | FR implementation status, test coverage                     |
| `PLAN_STATUS.md`        | Phase/task completion status                                |
| `JOURNEY_VALIDATION.md` | Journey validation status, gaps                             |
| `CODE_ENTITY_MAP.md`    | Forward and reverse mapping: code entities <-> requirements |

## Auto-Detection Behavior

**On session start:**

- If spec docs are missing, acknowledge it and offer to generate them
- Greenfield project: offer to scaffold all spec docs from project analysis
- Brownfield project: offer to analyze existing codebase and generate docs mapping to what exists
- Do NOT auto-generate without user confirmation -- offer, don't force

## VitePress Docsite Setup (Greenfield/Brownfield)

**MUST include docsite setup in any new project initialization:**

For greenfield projects:

- Copy VitePress template from `thegent/templates/vitepress-full/` to new project
- Run `pnpm install && pnpm docs:build` to verify setup
- Document in project CLAUDE.md

For brownfield projects (existing projects without docsites):

- Check if `docs-dist/index.html` exists -- if not, propose adding docsite
- Use same template from `thegent/templates/vitepress-full/`
- Run `pnpm install && pnpm docs:build` to verify

**Quick setup (30 seconds):**

```bash
cp -r thegent/templates/vitepress-full myproject/docs/.vitepress
# Rename .template files, edit config.ts placeholders
cd myproject && pnpm install && pnpm docs:build
open docs-dist/index.html
```

**Why:** All projects should have statically viewable docs that can be opened via `file://` in browser.

---

## Project Setup Checklist (Greenfield/Brownfield)

**MUST initialize these for ALL new projects:**

### 1. Docsite (VitePress)

- [ ] Copy `thegent/templates/vitepress-full/` to `docs/.vitepress/`
- [ ] Run `pnpm install && pnpm docs:build`
- [ ] Verify `docs-dist/index.html` opens in browser
- [ ] Add to CLAUDE.md

### 2. Taskfile (NOT Make)

- [ ] Create `Taskfile.yml` with standard tasks:
  - `lint` - Run all linters
  - `test` - Run tests
  - `quality` - Run quality gates
  - `docs:build` - Build docsite

### 3. Linters (Language-Specific)

| Stack      | Linter                | Formatter          | Config Template                                    |
| ---------- | --------------------- | ------------------ | -------------------------------------------------- |
| Python     | ruff                  | ruff format        | `thegent/templates/python/pyproject.template.toml` |
| TypeScript | oxlint                | oxfmt/prettier     | `thegent/templates/typescript/oxlint.config.json`  |
| Go         | golangci-lint         | gofumpt            | `thegent/templates/go/.golangci.yml`               |
| Rust       | clippy                | rustfmt            | `thegent/templates/rust/clippy.toml`               |
| Ruby       | rubocop               | rubocop            | `thegent/templates/ruby/.rubocop.yml`              |
| Java       | checkstyle + spotbugs | google-java-format | `thegent/templates/java/checkstyle.xml`            |
| C/C++      | clang-tidy            | clang-format       | `thegent/templates/cpp/.clang-tidy`                |
| PHP        | phpstan + psalm       | PHP CS Fixer       | `thegent/templates/php/phpstan.neon`               |
| Bash       | shellcheck            | shfmt              | `thegent/templates/bash/.shellcheckrc`             |

### 4. Project Scaffolding Tools (CLI/App Frameworks)

| Stack      | CLI Framework    | Web Framework        | Config                   |
| ---------- | ---------------- | -------------------- | ------------------------ |
| Python     | typer            | FastAPI/starlette    | `pyproject.toml`         |
| TypeScript | commander.js     | Express/Fastify/Hono | `package.json`           |
| Rust       | clap             | axum/actix           | `Cargo.toml`             |
| Go         | cobra/urfave/cli | gin/echo/fiber       | `go.mod`                 |
| Ruby       | thor             | Rails/Hanami         | `Gemfile`                |
| Java       | picocli          | Spring Boot          | `pom.xml`/`build.gradle` |
| C#         | commandline      | ASP.NET Core         | `.csproj`                |

### 5. Pre-commit Hooks

- [ ] Add `.pre-commit-config.yaml`
- [ ] Include: ruff-check, ruff-format, gitleaks, trailing-whitespace
- [ ] Run `pre-commit install`

### 6. Quality Gates

- [ ] Create `hooks/quality-gate.sh` with lint/test/coverage/security checks
- [ ] Run on pre-commit or Stop hook

### 7. Test Infrastructure (Per Language)

| Stack      | Test Runner           | Coverage           | Test Config                    |
| ---------- | --------------------- | ------------------ | ------------------------------ |
| Python     | pytest + pytest-xdist | coverage.py        | `pyproject.toml` [tool.pytest] |
| TypeScript | vitest                | v8                 | `vitest.config.ts`             |
| Rust       | cargo test            | tarpaulin/grcov    | `Cargo.toml`                   |
| Go         | go test               | gocov/coverprofile | `_test.go` files               |
| Ruby       | rspec                 | simplecov          | `.rspec`                       |
| Java       | JUnit 5               | JaCoCo             | `pom.xml`/`build.gradle`       |
| C++        | catch2/doctest        | lcov               | `CMakeLists.txt`               |
| PHP        | phpunit               | phpunit-coverage   | `phpunit.xml`                  |
| Bash       | bats-core             | -                  | `*.bats` files                 |

### 8. Full Traceability Setup

- [ ] Create `FUNCTIONAL_REQUIREMENTS.md` with FR-{CAT}-NNN IDs
- [ ] Create `docs/reference/FR_TRACKER.md` to track FR implementation status
- [ ] Create `docs/reference/CODE_ENTITY_MAP.md` mapping code <-> requirements
- [ ] Add FR ID tags to all test functions:
  - Python: `@pytest.mark.requirement("FR-XXX-NNN")`
  - TypeScript: `describe("FR-XXX-NNN: description", () => {...})`
  - Rust: `#[test] fn test_FR_XXX_NNN() {...}`
  - Add docstring: `Traces to: FR-XXX-NNN`
- [ ] Verify: `grep -r "FR-" tests/` shows all FRs have tests
- [ ] Run: `task quality` to verify spec verification

### 9. CLAUDE.md Project Instructions

Create project-specific CLAUDE.md with project info, library preferences, domain patterns.

---

## Quick Project Initialization

### Option 1: Copier (Recommended)

```bash
# Install copier if needed
pip install copier

# Initialize with all prompts
copier copy thegent/templates/initialize-project ./my-new-project

# Or with options specified
copier copy thegent/templates/initialize-project ./my-new-project \
  --project-name="my-project" \
  --project-description="A description" \
  --language="python" \
  --include-docs=true \
  --include-ci=true
```

### Option 2: Manual Template Selection

```bash
# Full setup for new project:
mkdir -p docs hooks
cp -r thegent/templates/vitepress-full/* docs/.vitepress/
mv docs/package.json.template docs/package.json
pnpm install && pnpm docs:build
open docs-dist/index.html
```

### Available Templates

| Template  | Location                                       | Purpose                                     |
| --------- | ---------------------------------------------- | ------------------------------------------- |
| CLAUDE.md | `templates/claude/CLAUDE.md.template`          | Project-specific agent instructions         |
| Taskfile  | `templates/{language}/Taskfile.{language}.yml` | Build automation                            |
| Quality   | `templates/quality/`                           | 50+ lint/coverage configs for 25+ languages |
| VitePress | `templates/vitepress-full/`                    | Full docsite with versioning                |
| Specs     | `templates/specs/`                             | PRD, ADR, FR, PLAN templates                |
| CI/CD     | `templates/operational/ci/`                    | GitHub Actions workflows                    |
| Docker    | `templates/operational/docker/`                | Dockerfiles & compose                       |

**During work:**

- When making significant code changes (new modules, features, architecture changes), note which spec docs would need updating
- When completing a task, mentally check if trackers should be updated
- If you add new functions/modules, note they should be added to CODE_ENTITY_MAP.md

**On session end:**

- If there are unmapped code changes, acknowledge and update trackers if appropriate
- Treat session end as a documentation checkpoint

## Change Documentation (per-change, for significant changes)

For significant changes (new features, major refactors, architecture changes):

- Create `docs/changes/{change-name}/` with:
  - `proposal.md` -- What and why
  - `design.md` -- Technical approach, affected components
  - `tasks.md` -- Implementation checklist
- Archive completed changes to `docs/changes/archive/`
- NOT required for small fixes, typos, or minor adjustments

## Doc Format Standards

- **ID systems:** E{n}.{m}.{k} for epics/stories, FR-{CAT}-{NNN} for requirements, ADR-{NNN} for decisions, P{n}.{m} for plan tasks, UJ-{N} for journeys
- **Cross-reference** between docs (FR traces to PRD epics, code maps to FRs and ADRs)
- **ASCII diagrams** for flows and architecture (not images)
- **Tables** for tracking, matrices, and summaries
- Templates are available at `~/.claude/templates/` for consistent formatting (if present)

### Global Reference Docs for Code Generation

**Use these references when generating code:**

| Domain          | Reference Path                                           |
| --------------- | -------------------------------------------------------- |
| UI Design       | `docs/reference/UI_DESIGN_PRINCIPLES_REFERENCE.md`       |
| Architecture    | `docs/reference/SOFTWARE_ARCHITECTURE_REFERENCE.md`      |
| Design Patterns | `docs/reference/SOFTWARE_DESIGN_PATTERNS_REFERENCE.md`   |
| Performance     | `docs/reference/performance/PERFORMANCE_OPTIMIZATION.md` |
| Testing         | `docs/reference/testing/TESTING_STRATEGIES.md`           |
| Security        | `docs/reference/security/SECURITY_BEST_PRACTICES.md`     |
| **Full Index**  | `docs/reference/INDEX.md`                                |

For hyperspecialization, agents can use `docs/reference/INDEX.md` to find domain-specific references mapped to their roles.

## Session State Continuity

- The hooks system (if configured) tracks file changes per session via `.claude/session-changes.log`
- On stop, changes are reconciled against trackers
- This provides session-to-session continuity for documentation maintenance

---

# Generalized Dev Environment Pattern

## Service Management

- **The user runs a dev TUI/dashboard in their own terminal.** This is their primary observation interface. **Never** start, stop, or restart the entire dev stack (`make dev`, `make dev-tui`, `make dev-down`) — only the user does that.
- **Use CLI introspection and per-service manipulation commands** to interact with the running stack without disrupting the user's TUI session. Process orchestrators (e.g. `process-compose`) expose a CLI/API that operates on the same running instance.
- **Assume services use hot reload** (file watchers, HMR, etc.). Save files and let watchers pick up changes — do not restart services just because you edited files.
- **When a service needs restarting** (e.g. config change, dependency update, crash), restart only that specific service via CLI, not the whole stack.
- **Read logs via CLI or log files** — never attach to or interfere with the user's TUI terminal.
- Before starting dev yourself, verify processes are not already up (check health endpoints, status commands, or log files) to avoid duplicate stacks.

## Package Manager

**Use the project's preferred package manager.** Detect from lockfiles:

- `bun.lockb` or `bun.lock` -> use `bun`
- `pnpm-lock.yaml` -> use `pnpm`
- `yarn.lock` -> use `yarn`
- `package-lock.json` -> use `npm`
- If unclear, check `package.json` `packageManager` field or project CLAUDE.md

## Native Over Docker

**Prefer native services over Docker** for local development. Run databases, caches, reverse proxies as native processes. Use Docker only when native install is not feasible or explicitly required.

## OSS and Free First

**Strictly prefer local, OSS, and free tools** over paid SaaS. If a feature requires external services, prefer OSS/self-hosted or free options first. Document paid options only as labeled fallback.

## Multi-Actor Coordination (generalized)

When multiple agents or actors share a dev environment:

- **Concurrent Agent Environment**: Assume multiple agents are working in the same workspace simultaneously.
- **Git Safety - FORBIDDEN**: Never run `git restore`, `git reset`, or `git clean` on the workspace. These commands destroy work-in-progress from other agents.
- **Respect Dirty Files**: Modified files are active work-in-progress. Do not revert, "cleanup", or overwrite them unless specifically instructed to finish a task started by another agent. Work around existing changes.
- **Debounce commands:** Use project-provided wrappers (Makefile targets, scripts) that prevent concurrent execution conflicts.
- **Shared service management:** Use the project's process orchestrator as source of truth for service health.
- **Hold-if-running logic:** Prefer wrappers that allow multiple actors to share processes without force-killing.
- **Consolidated targets:** Prefer consolidated build/lint/test targets over a multitude of specialized ones.

---

# Plugin Ecosystem Awareness

Documentation and workflow frameworks (BMAD, AgilePlus, GSD, etc.) may be available as plugins or slash commands.

- Check available slash commands (`/`) for documentation workflows
- These complement the auto-detection system -- invoke explicitly for deeper workflows
- Auto-detection hooks handle common cases; plugins handle advanced scenarios
- If BMAD agents are installed (`.claude/commands/bmad/`), they can be activated via slash commands for specialized agent personas
- Start a new conversation to switch agent personas

---

# QA Governance

## Test-First Mandate

- Write tests BEFORE implementation. Test file must exist before source file for new modules.
- For bug fixes, write a failing test that reproduces the bug first, then fix.
- Test naming: descriptive, includes the FR ID when applicable.

## Suppression Policy

- **Zero new suppressions** without inline justification comment.
- Acceptable format: `# noqa: E501 -- line is a long URL` (note the `--` reason separator).
- The `suppression-blocker.sh` hook will BLOCK any Write/Edit that introduces new suppressions.
- If a suppression is genuinely needed, include the specific rule code AND a reason.

## Spec Traceability

- All test functions MUST reference an FR ID via one of:
  - Tag: `# @trace FR-XXX-NNN` in test file or function
  - Marker: `@pytest.mark.requirement("FR-XXX-NNN")`
  - Docstring: `Traces to: FR-XXX-NNN`
  - Test name: `@test "FR-XXX-NNN: description"` (BATS)
- Orphaned FRs (no test) and orphaned tests (no FR) are reported by the quality gate.

## Quality Gate Awareness

- `quality-gate.sh` runs on every Stop event -- it reports lint, security, and traceability findings.
- **Proactively run linters** before finishing work to avoid surprises at the quality gate.
- The gate is advisory (does not block Stop) but findings should be addressed.

## Static Analysis Config

- When scaffolding a new project, copy relevant templates from `~/.claude/templates/quality/` for detected stacks.
- Available templates: ruff.toml, ty-config.toml, oxlintrc.json, tsconfig-strict.json, golangci.yml, clippy.toml, shellcheckrc, pre-commit-config.yaml, pytest-config.toml, coverage-config.toml.

## Test Pyramid Targets

- **Unit**: 70% (tolerance: +/-5%)
- **Integration**: 20% (tolerance: +/-5%)
- **E2E**: 10% (tolerance: +/-5%)
- Projects may override in `.qa-config.json` or `.claude/quality.json`.

## Hook Pipeline Summary (v3)

| Event                   | Hooks (execution order)                                                                           |
| ----------------------- | ------------------------------------------------------------------------------------------------- |
| SessionStart            | spec-preflight, qa-preflight                                                                      |
| UserPromptSubmit        | prompt-submit-guard                                                                               |
| PreToolUse:Write        | doc-location-guard, pre-write-validator, suppression-blocker                                      |
| PreToolUse:Edit         | pre-write-validator, suppression-blocker                                                          |
| PostToolUse:Edit\|Write | change-doc-tracker, post-edit-checker, async-test-runner                                          |
| SubagentStart           | subagent-quality-gate (start)                                                                     |
| SubagentStop            | subagent-quality-gate (stop)                                                                      |
| TaskCompleted           | task-completion-verifier                                                                          |
| PreCompact              | pre-compact-snapshot                                                                              |
| Stop                    | quality-gate, stop-reconcile, spec-verifier, complexity-ratchet, security-pipeline, test-maturity |
| SessionEnd              | session-cleanup                                                                                   |

## Test-First Development (TDD/BDD)

### TDD Mandate

- For NEW modules: test file MUST exist before implementation file
- For BUG FIXES: failing test MUST be written before the fix
- For REFACTORS: existing tests must pass before AND after

### BDD Requirements

- Feature files (_.feature / _.bdd) map to user stories in PRD
- Given/When/Then steps must be traceable to FRs
- BDD test names reference FR IDs: "Feature: FR-AUTH-001 User Login"

### Test Type Requirements (by project maturity)

| Test Type       | New Project | Established        | Critical System |
| --------------- | ----------- | ------------------ | --------------- |
| Unit            | Required    | Required           | Required        |
| Integration     | Required    | Required           | Required        |
| E2E             | Optional    | Required           | Required        |
| Property-based  | Optional    | Optional           | Required        |
| Contract        | Optional    | Required (if APIs) | Required        |
| Mutation        | Optional    | Optional           | Required        |
| Security (SAST) | Required    | Required           | Required        |
| Accessibility   | Optional    | Required (if UI)   | Required        |
| Performance     | Optional    | Optional           | Required        |
| Snapshot/Golden | Optional    | Optional (if UI)   | Required        |

### Smart Contract Pattern (Spec Verification)

Specs (PRD/FR) -> Tests (must reference FR IDs) -> Checks (must be green) = Verified

- Every FR-XXX-NNN in FUNCTIONAL_REQUIREMENTS.md MUST have >=1 test referencing it
- Every test MUST reference >=1 FR-XXX-NNN (no orphan tests)
- All linters + type checkers + security scanners MUST pass (0 errors)
- Coverage MUST meet threshold (default 80%)
- If ALL checks green AND ALL FRs have tests -> spec is "programmatically verified"

### Architecture Enforcement

- Python: import-linter config enforces layer boundaries
- Go: depguard in golangci.yml enforces package dependency rules
- TypeScript: eslint-plugin-boundaries enforces module boundaries
- When scaffolding: always add architecture enforcement config

### Universal Language Support

The QA system supports 25+ language stacks. See `~/.claude/qa-config.json` for the full list.
Stack detection is automatic via marker files (package.json, go.mod, Cargo.toml, etc.).
Quality templates for all supported languages are in `~/.claude/templates/quality/`.

## Subagent Quality Enforcement

Subagents and tasks are NOT exempt from quality gates. The following hooks fire on subagent lifecycle:

- SubagentStart: tracks subagent scope and expected file changes
- SubagentStop: runs lint/syntax/security on all files the subagent modified
- TaskCompleted: verifies task output meets quality standards (test files, lint, syntax)

## Specification Verification ("Smart Contract")

The spec-verifier runs on Stop and produces a verification verdict:

- VERIFIED: all FRs have tests, all checks green, coverage met
- GAPS: lists uncovered FRs, orphan tests, failing checks
  This is the "if green, it works" guarantee — programmatic proof that specs are implemented.

## Complexity Ratchet

Complexity must never increase. The ratchet enforcer:

- Measures cyclomatic complexity, cognitive complexity, maintainability index
- Compares against baseline — any increase is flagged
- Baseline auto-updates downward (tighter over time)
- Max function: 40 lines. Max cyclomatic: 10. Max cognitive: 15.

## Security Pipeline

4-layer security scanning on every Stop:

1. Secret detection (gitleaks + regex patterns)
2. SAST (Semgrep, bandit, gosec, brakeman, psalm)
3. Dependency audit (pip-audit, npm audit, govulncheck, cargo audit)
4. Infrastructure (tfsec, hadolint, trivy)

## Test Maturity Model

Projects are assessed on a 5-level scale:

- Level 1 — MVP: tests exist and are runnable
- Level 2 — Production-Ready: coverage >= 60%, integration tests, no bare suppressions
- Level 3 — Scale: coverage >= 80%, FR traceability >= 50%, security scanning, strict linters
- Level 4 — High-Reliability: FR traceability >= 80%, architecture enforcement, complexity ratchet
- Level 5 — Mission-Critical: 100% FR traceability, mutation testing, chaos tests, runtime verification
  Target: Level 3 for all projects, Level 4+ for critical systems.

## Runtime Verification

For projects that opt in (via qa-config.json `runtime_verification`):

- Python: beartype (O(1) type checking at runtime), deal (Design by Contract)
- Go: goleak (goroutine leak detection), race detector
- Resilience: toxiproxy (network fault injection), chaos-toolkit (experiments)
  Templates available in `~/.claude/templates/quality/runtime/`.

## QA Governance v3.1 — Deep Enforcement Enhancements

### Cognitive Complexity Enforcement

The complexity-ratchet hook now measures both cyclomatic AND cognitive complexity:

- Cognitive complexity weights branching by nesting depth (branch at nesting level N = score 1+N)
- Max cognitive complexity per function: 15 (configurable in qa-config.json)
- Code duplication detection via jscpd (max 5% duplication)
- Dead code detection via vulture (Python) and knip (JS/TS)

### AI Slop Detection

The post-edit-checker now scans every Write/Edit for AI-generated antipatterns:

- Placeholder TODOs ("TODO: implement", "TODO: add")
- Lorem ipsum filler text
- Placeholder domains (example.com in non-test files)
- LLM leakage ("As an AI", "I cannot", "I apologize")
- Lazy AI comments ("This function does...", "This is a helper...")
- Placeholder bodies (pass # TODO, throw new Error("not implemented"))
  Advisory only — prints warnings, does not block.

### Dead Import & Dead Code Detection

Quality-gate.sh (Stop) and post-edit-checker.sh (PostToolUse) now detect:

- Dead imports: ruff F401 (Python), oxlint no-unused-vars (JS/TS)
- Dead code: vulture --min-confidence 80 (Python), knip --no-progress (JS/TS)
- Code duplication: jscpd with 5% threshold

### Supply Chain Security (Layer 5)

Security pipeline expanded from 4 to 5 layers:

1. Secrets (gitleaks + regex patterns)
2. SAST (semgrep, bandit, gosec)
3. Dependencies (pip-audit, npm audit, govulncheck, cargo-audit, osv-scanner)
4. Infrastructure (hadolint, tfsec, trivy)
5. **Supply Chain** (syft SBOM generation, OSV-Scanner, opengrep)

### Enhanced Test Maturity Model

Test maturity expanded from 16 to 20 criteria across 5 levels:

- **L4 new**: Snapshot/golden tests (3pts), Approval tests (2pts)
- **L5 new**: Chaos/resilience tests (3pts), Fuzz testing (3pts)
- Enhanced property-based test detection: hypothesis, fast-check, gopter, proptest
- Points rebalanced: 20pts per level, 100pts total

### Hook Stderr Convention

All hooks that exit non-zero now write descriptive failure messages to stderr.
Format: `HOOK_NAME FAIL: reason` (e.g., "SUPPRESSION BLOCKER FAIL: 2 new lint suppression(s)")
This ensures Claude Code displays the actual failure reason instead of "No stderr output".

---

## Development Philosophy

### Proactive Agent Mandate

- **NEVER** ask the user to run a command, search for code, or perform an edit that you have the tools to perform yourself.
- If a task is clear, execute it. If a dependency is missing and you can install/fix it, do so.
- Only ask for clarification if the requirements are truly ambiguous or require a strategic decision that only the user can make.
- "Proactive execution" is the default state. Assume you have permission to use all available tools to achieve the goal.

### Extend, Never Duplicate

- NEVER create a v2 file. Refactor the original.
- NEVER create a new class if an existing one can be made generic.
- NEVER create custom implementations when an OSS library exists.
- Before writing ANY new code: search the codebase for existing patterns.

### Primitives First

- Build generic building blocks before application logic.
- A provider interface + registry is better than N isolated classes.
- Template strings > hardcoded messages. Config-driven > code-driven.

### Research Before Implementing

- Check project deps (pyproject.toml) for existing libraries.
- Search PyPI before writing custom code.
- For non-trivial algorithms: check GitHub for 80%+ implementations to fork/adapt.

### Library Preferences (DO NOT REINVENT)

| Need             | Use                          | NOT                          |
| ---------------- | ---------------------------- | ---------------------------- |
| Retry/resilience | tenacity                     | Custom retry loops           |
| HTTP client      | httpx                        | Custom wrappers              |
| Logging          | structlog                    | print() or logging.getLogger |
| Config           | pydantic-settings            | Manual env parsing           |
| CLI              | typer                        | argparse                     |
| Validation       | pydantic                     | Manual if/else               |
| Rate limiting    | tenacity + asyncio.Semaphore | Custom rate limiter class    |

### Code Quality Non-Negotiables

- Zero new lint suppressions without inline justification
- All new code must pass: ruff check, type checker, tests
- Max function: 40 lines. Max cognitive complexity: 15.
- No placeholder TODOs in committed code

## thegent-specific and workflow rules are moved to:

- /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/docs/reference/CLAUDE_THEGENT_RUNTIME_APPENDIX.md

Keep this file aligned with the appendixed doc; load both documents for the full policy set.

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
