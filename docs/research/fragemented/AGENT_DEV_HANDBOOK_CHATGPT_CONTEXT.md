<DONE>
# Agent-Driven Development Handbook — Research Context & Prompt Input

**Date:** 2026-02-22
**Purpose:** Context document for ChatGPT deep research to produce an authoritative handbook for agent-managed, agent-executed software development teams. This document captures current as-is practices extracted from the thegent and trace codebases, plus the gaps and target vision the handbook must address.

---

## WHAT THIS IS AND WHAT YOU ARE BEING ASKED TO DO

You are being asked to research, synthesize, and produce an **Agent-Driven Software Development Handbook** — a canonical reference covering:

1. **Agent team management** — how an AI agent acting as engineering manager coordinates a team of AI agent specialists
2. **Software development process** — BDD/SDD/TDD/DDD-first, polyglot, spec-before-code, fail-fast, zero-legacy-compat
3. **Role-specific professional practices** — what each "role agent" (Architect, PM, QA, Dev, SecEng, DevOps, Tech Writer) does, produces, and enforces
4. **Micro-decision canonicalization** — capturing the hundreds of recurring choices that currently require human re-adjudication
5. **Process streamlining** — eliminating repeated manual decisions via documented, enforceable standards

This handbook is for **zero-human-feedback loops**: the agents are the only actors. There are no daily standups with humans, no PR reviewers who are humans, no QA engineers who are humans. All human input arrives via:
- Seed idea/MVP prompt at project start
- Post-release feedback (Discord tickets, report buttons, usage analytics)
- Occasional corrections to agent behavior via governance updates

The handbook must be operable by agents without any human mediation.

---

## PART 1: WHO WE ARE — TEAM PROFILE

### What We Build
- **Program types:** All types — CLIs, MCP servers, APIs, TUIs, desktop apps, mobile apps, games, embedded systems, libraries, SDKs, data pipelines, AI agent frameworks, orchestration platforms, web apps, infrastructure tooling
- **Languages:** Python, Go, Rust, C++, C, Zig, C#, Mojo — chosen by performance/safety optimality for each use case, NOT by developer experience preference
- **Scale of projects:** Start with a seed MVP idea prompt → fully fleshed feature scope within the same day. Projects range from 500-LOC scripts to 340,000+ LOC polyglot monorepos
- **DX philosophy:** DX is not a factor for aesthetic comfort (no "nice to haves"). DX counts for raw engineering virtues only: extensibility, maintainability, debuggability, intrinsic comprehensibility. Performance and safety always beat DX comfort.

### What We Don't Do
- No human-in-the-loop code reviews
- No user testing sessions
- No sprint planning meetings
- No "asking a human to run a command"
- No fallbacks, no legacy compatibility, no silent degradation
- No manual retry loops, no custom implementations where a library exists

### Execution Environment
- **Agent orchestrator:** thegent (custom MCP server + CLI for agent lifecycle management)
- **Agent harnesses used:** Claude Code CLI, Codex CLI, Cursor, Factory Droid, OpenCode, others
- **Governance:** All quality gates, compliance checks, and architectural enforcement are automated hooks
- **Work stream:** Canonical backlog in `docs/reference/WORK_STREAM.md` — agents claim, execute, and complete tasks autonomously
- **Session continuity:** Agents run in background sessions; can be paused, continued, and monitored via `thegent ps` / `thegent wait`

---

## PART 2: CURRENT AS-IS PRACTICES (Fully Extracted)

### 2.1 Workflow: From Idea to Deployed Software

**Phase 1 — Discovery & Ideation**
- User (or agent) writes seed prompt describing the idea
- Agent creates entry in `docs/reference/WORK_STREAM.md` (CLAIMED section)
- Agent logs discoveries in `docs/research/CONVERSATION_DUMP_YYYY-MM-DD.md`
- Agent uses `thegent_memory_add` to persist lessons across sessions
- Agent checks existing research (`docs/research/`, `docs/reference/`) before any implementation
- Agent searches PyPI/GitHub/npm for 80%+ pre-built solutions (library-first mandate)

**Phase 2 — Specification & Design**
- Produce spec documents BEFORE any code:
  - `PRD.md` — epics, user stories, acceptance criteria (ID scheme: E{n}.{m}.{k})
  - `FUNCTIONAL_REQUIREMENTS.md` — FR SHALL statements (ID scheme: FR-{CATEGORY}-{NNN})
  - `ADR.md` — architecture decisions with rationale, alternatives, decision delta, residual risks, follow-up date
  - `PLAN.md` — phased WBS with explicit DAG predecessors, no cycles
  - `USER_JOURNEYS.md` — ASCII flow diagrams of user paths
- Trackers in `docs/reference/`: PRD_TRACKER, FR_TRACKER, ADR_STATUS, PLAN_STATUS, JOURNEY_VALIDATION, CODE_ENTITY_MAP
- BDD requirement: feature files map to PRD user stories; Given/When/Then steps traceable to FR IDs
- Context docs created per technology at `docs/context/{technology}.md` (8 required sections: Header, What is X, Key Concepts, API/Interfaces, Auth, Code Examples, Sources, Quick Reference)

**Phase 3 — Test-First Implementation (TDD Mandate)**
- Test file MUST exist before source file
- Bug fix: failing test MUST be written before fix
- Refactor: existing tests must pass before AND after
- All tests include FR traceability: `@pytest.mark.requirement("FR-XXX-NNN")` or `# @trace FR-XXX-NNN`
- Test naming: `test_FR_XXX_NNN_<description>()`
- 3 required traceability markers: decorator, docstring, test name
- Code runs fast lane immediately: `pytest -m "not slow and not integration and not e2e"`

**Phase 4 — Quality Validation (Automated, Stop-Event Hooks)**

| Gate | Timeout | What It Checks |
|------|---------|----------------|
| governance-gates.sh | Master | All policies from contracts/ |
| quality-gate | 15s | ruff, semgrep, bandit, pytest, coverage |
| spec-verifier | 60s | All FRs have ≥1 test; all tests reference ≥1 FR |
| complexity-ratchet | 120s | CC ≤10, cognitive ≤15, dead code, max 40 LOC/fn |
| security-pipeline | 15s | 5-layer: secrets (gitleaks), SAST (semgrep/bandit), deps (pip-audit), infra (hadolint), supply chain (syft/osv) |
| test-maturity | 300s | Must reach Level 5 for agent-only projects |
| regression-spiral-guard | 30s | 8 thresholds; GREEN/YELLOW/RED directives |

**Phase 5 — Commit & Work Stream Update**
- Commit with format: brief description + detailed why + `Co-Authored-By: <agent>` trailer
- Never `--no-verify`; never amend prior commits; always new commits
- Update WORK_STREAM.md: move from CLAIMED → COMPLETED with commit reference
- Write CONVERSATION_DUMP immediately (never defer)

**Phase 6 — Deployment & Monitoring**
- Build via `task build`
- Test distribution: `task test:dist`
- Monitor logs via CLI only; never attach to user's TUI
- Services hot-reload (Air/uvicorn --reload/Vite HMR); never restart entire stack

### 2.2 Test Maturity Model (5 Levels)

| Level | Coverage | FR Traceability | Key Capabilities |
|-------|----------|-----------------|-----------------|
| 1 | Baseline | Low | Smoke tests runnable |
| 2 | ≥60% | Low | Integration tests, no bare suppressions |
| 3 | ≥80% | ≥50% | Full E2E suite, security scanning, strict linters |
| 4 | ≥85% | ≥80% | Contract tests, snapshot tests, architecture enforcement |
| 5 | **100%** | **100%** | Mutation tests (≥80% score), BDD, chaos, fuzz, SDD alignment |

**Agent-Only Projects REQUIRE Level 5.** No exceptions. Rationale: no humans test the system; automated tests are the only safety net.

### 2.3 Hook Pipeline (Agent Lifecycle Governance)

| Event | Hooks |
|-------|-------|
| SessionStart | spec-preflight, qa-preflight |
| PreToolUse:Write | doc-location-guard, pre-write-validator, suppression-blocker |
| PreToolUse:Edit | pre-write-validator, suppression-blocker |
| PostToolUse:Edit/Write | change-doc-tracker, post-edit-checker, async-test-runner |
| SubagentStart/Stop | subagent-quality-gate |
| Stop | quality-gate, stop-reconcile, spec-verifier, complexity-ratchet, security-pipeline, test-maturity, regression-spiral-guard, session-cleanup |

**Smart skip:** hooks cache results (600s TTL); only re-run if relevant files changed.

### 2.4 Library-First Policy (Mandatory, Enforced)

| Need | Required Library | Forbidden Alternative |
|------|-----------------|----------------------|
| Retry/resilience | tenacity | Custom retry loops |
| HTTP client | httpx | requests, urllib |
| Logging | structlog | logging.getLogger(), print() |
| Config management | pydantic-settings | Manual env parsing |
| CLI | typer | argparse |
| Validation | pydantic | Manual if/else |
| Rate limiting | tenacity + asyncio.Semaphore | Custom rate limiter |
| File watching | watchdog | os.walk polling |
| Caching | cachetools / diskcache | Custom TTL logic |
| Circuit breaker | pybreaker | Custom state |
| JSON (CPython) | orjson | json stdlib |
| Task runner | Taskfile (Go-based) | Make (for new work) |

First question before any implementation: "Is there a library that solves this?" Custom code only for domain-specific logic. ADR required if choosing custom over library.

### 2.5 Forbidden Patterns (Absolutely Zero Tolerance)

1. **Fallbacks:** `try: new(); except: old()` — FORBIDDEN
2. **Legacy compatibility:** `if legacy_flag: old() else: new()` — FORBIDDEN
3. **Silent error handling:** `try: thing(); except: pass` — FORBIDDEN
4. **Import fallbacks:** `try: from X import Y; except: from Z import Y` — FORBIDDEN
5. **Backwards-compat shims:** `def old(): warnings.warn(); return new()` — FORBIDDEN
6. **Just-in-case code:** code added "just in case" something fails — FORBIDDEN
7. **Killing processes:** `kill -9`, `pkill`, `killall` on agent/shell processes — FORBIDDEN
8. **Suppressing lints without justification:** `# noqa` without inline reason — FORBIDDEN
9. **Placeholder TODOs in committed code:** `# TODO: implement` — FORBIDDEN
10. **AI slop:** Lorem ipsum, placeholder bodies, LLM-leakage phrases — FORBIDDEN

### 2.6 Code Quality Metrics (Hard Limits)

- Max function length: **40 lines**
- Max cyclomatic complexity: **10**
- Max cognitive complexity: **15**
- Max duplication: **5%** (jscpd)
- Zero new lint suppressions without `# reason` inline justification
- Dead code: detected by vulture (Python), knip (TypeScript)
- AI slop detection: post-edit-checker runs on every Write/Edit

### 2.7 Documentation Organization

Root-level files (ONLY allowed): `README.md`, `CHANGELOG.md`, `AGENTS.md`, `CLAUDE.md`, `00_START_HERE.md`, `PRD.md`, `ADR.md`, `FUNCTIONAL_REQUIREMENTS.md`, `PLAN.md`, `USER_JOURNEYS.md`

All other `.md` files go in `docs/`:
- `docs/guides/` — Implementation guides, quick-start
- `docs/reports/` — Completion reports, status, summaries
- `docs/research/` — Research summaries, CONVERSATION_DUMP files, analysis
- `docs/reference/` — Quick references, trackers, canonical maps
- `docs/checklists/` — Implementation checklists
- `docs/changes/` — Per-change docs; `docs/changes/archive/` for completed
- `docs/context/` — Authoritative per-technology reference docs
- `docs/governance/` — Governance policies, matrices

### 2.8 Specification Documentation (Smart Contract Pattern)

```
Specs (PRD/FR)
    → Tests (MUST reference FR IDs)
        → Checks (MUST be green: lint, type, security, coverage)
            = VERIFIED (spec-verifier.sh output)
```

- Every FR-XXX-NNN MUST have ≥1 test referencing it
- Every test MUST reference ≥1 FR-XXX-NNN
- All linters + type checkers + scanners MUST pass (0 errors)
- Coverage MUST meet threshold

### 2.9 Polyglot Runtime Governance

**Required Baseline Per Language:**

| Language | Runtime | Quality Commands |
|----------|---------|-----------------|
| Python | uv + CPython 3.14 (primary), PyPy 3.11 (secondary), CPython 3.13 (fallback) | ruff, basedpyright, mypy, pytest, tach, vulture, radon, bandit, semgrep |
| Rust | stable | fmt, clippy -D warnings, test |
| Go | supported stable | go build, go vet, go test ./..., golangci-lint (41+ linters) |
| TypeScript | Bun (preferred), Node LTS | tsc --strict, oxlint (13 plugins), vitest, playwright |
| Zig | pinned stable | zig fmt, zig test |
| Mojo | pinned stable | parity checks against reference implementations |
| C/C++ | platform toolchain | clang-tidy, asan/ubsan/lsan, valgrind |
| C# | .NET LTS | dotnet format, dotnet test, dotnet analyzers |

**Conversion rules:**
1. Refactor-in-place before full language conversion
2. Convert only when measured SLO/tooling triggers are met and documented
3. Every conversion requires: baseline metrics + parity harness + phased cutover plan

### 2.10 Agent Execution Workflow Patterns

| Pattern | Command | Use Case |
|---------|---------|----------|
| Default single task | `thegent free "Task"` | Standard work item |
| Next backlog item | `thegent free --do-next` | Continuous work stream |
| N items sequentially | `thegent free --do-next --repeat N` | Batch execution |
| Background + session | `thegent bg "Task" free` | Long-running, non-blocking |
| Continuous loop | `thegent plan loop` | Autonomous backlog processing |
| Wait for work | `thegent plan wait-next` | Idle state (NEVER busy-loop) |
| Continue session | `thegent bg "Task" -C <session_id>` | Resume prior work |
| Model-specific | `thegent run "Task" -M claude-sonnet-4.5` | Capability routing |
| Cost-optimized | `thegent run "Task" -M gemini-3-flash -R cheapest` | Budget routing |
| Role-based | `thegent research/review/fix/code/explain/summarize "..."` | Semantic dispatch |

### 2.11 BMAD Workflow System (Strategic SDLC Layer)

The BMad Method (BMAD) provides structured workflows for strategic software development phases:

| Workflow | Purpose | Output |
|----------|---------|--------|
| `prd` | Create Product Requirements Document | PRD.md + epic breakdown |
| `tech-spec` | Quick-flow technical specification | Tech spec + stories |
| `create-epics-and-stories` | Decompose PRD into executable stories | Story.md + Kanban |
| `create-ux-design` | Collaborative UX design | UX doc + wireframes |
| `architecture` | Architectural decision facilitation | ADR + architecture doc |
| `domain-research` | Deep domain requirements research | Domain doc + patterns |
| `document-project` | Auto-document brownfield project | Full doc set |
| `dev-story` | Execute story (implement + test + validate) | Working code + tests |
| `code-review` | Senior dev code review | Review report |
| `sprint-planning` | Generate sprint tracking | Sprint status file |
| `story-done` | DoD validation + status update | Status: DONE |
| `retrospective` | Epic-level retrospective | Lessons + next steps |

Each workflow has:
- `workflow.yaml` — Config, variables, component refs
- `instructions.md` — Executable workflow steps (XML-tagged actions)
- `template.md` — Output document template (when applicable)
- `checklist.md` — Completion validation checklist

### 2.12 Agent Memory & Knowledge Persistence

```bash
# Log discoveries during work
thegent_memory_add \
  --discovery "Found 47 untested functions in execution.py" \
  --friction "project" "MI score 0.00; splitting needed" \
  --lesson "positive" "Library-first saved 500 LOC in cel_router.py"

# Friction types: agent | ephemeral | project | process

# Synthesize before finishing major task
thegent_memory_synthesize \
  --include "project" "process" \
  --output docs/research/task-summary.md
```

Memory persists across sessions in audit log. Accessed via `docs/research/CONVERSATION_DUMP_*`.

### 2.13 Context Management Strategy (Manager Pattern)

Agents operate as **strategic managers, not workers.** Delegation rules:

| Delegate when | Handle directly when |
|--------------|---------------------|
| >3 files to explore | Single file change |
| Codebase-wide search | Quick targeted lookup |
| >2000 tokens of expected output | Short config tweak |
| Multi-step sequential logic | Single atomic action |
| Independent parallel work streams | Quick answer needed |

**Anti-patterns to avoid:**

| Bad | Good |
|-----|------|
| Read 10 files to "understand" | Delegate exploration; get summary |
| `ls -l` in project root (node_modules!) | `fd -t f -d 1` or `ls -l src/` |
| Multi-file edits inline | Delegate to general-purpose agent |
| Sequential explorations one-by-one | Batch parallel explores |
| `git restore .` to "reset" | Leave modified files (active agent work) |
| Custom retry/cache/watch code | tenacity, cachetools, watchdog |

### 2.14 Current Technology Snapshot (thegent + trace)

**thegent (Agent Orchestration Platform):**
- Python (primary, CPython 3.10+) + Rust extensions (23 crates)
- FastMCP (MCP server), Typer (CLI), Pydantic (validation), Rich (TUI)
- LiteLLM (multi-provider routing), tenacity (resilience), httpx (HTTP)
- 50+ agent personas, 15 lifecycle hooks, 100+ MCP tools
- 4,814 test files (983 empty stubs = 29.2% — critical gap)
- ~208k LOC Python source

**trace (TracerTM — Requirements Traceability):**
- Go 1.25+ (backend) + Python 3.12 (services) + TypeScript/React 19 (frontend)
- Echo v4 (Go HTTP), FastAPI (Python), TanStack Router v1 (React)
- PostgreSQL 17, Neo4j 5, Redis 7, NATS 2.9, Temporal, MinIO
- OpenTelemetry, Prometheus, Grafana, Jaeger, Loki, Sentry
- Bun (package manager), Turbo (monorepo), Vite 8 (build)
- 337,000+ LOC total; 672 API endpoints; 17 tach-enforced architecture modules
- Governance score: 9.2/10

---

## PART 3: CURRENT GAPS & PAIN POINTS (What Needs to Be Canonicalized)

### 3.1 Recurring Micro-Decisions (Currently Re-Adjudicated Manually)

These are decisions that keep coming up and require human involvement because they aren't documented in a form agents can reliably act on:

1. **When to split a module vs. extend it** — Currently ad-hoc; need a LOC/complexity/responsibility matrix
2. **Which language to use for a new component** — Has heuristics but no canonical decision tree with examples
3. **How to structure multi-actor agent coordination** — Patterns exist but aren't documented as reusable playbooks
4. **When a task warrants a subagent vs. inline execution** — Informal; need formal decision criteria
5. **How to handle external API failures** — tenacity covers retry, but not all failure modes (auth, rate limit, 5xx, timeout, partial response)
6. **Database choice for new services** — No canonical matrix of when to use Postgres vs. SQLite vs. Neo4j vs. Redis as primary store
7. **When to write a context doc vs. rely on inline comments** — No trigger criteria
8. **How to scope a "story" vs. "task" vs. "epic"** — BMAD has definitions but not size/complexity rules
9. **How to do polyglot integration testing** — When Go calls Python service, who owns the contract test?
10. **When to escalate a governance gate failure** — Manual judgment; need escalation tree
11. **How granular to make FR decomposition** — No canonical granularity rules
12. **When to use sync vs. async patterns** — Has preferences but not a decision framework
13. **How to version APIs across language boundaries** — No formal cross-language versioning protocol
14. **How to structure error types across a polyglot stack** — Currently inconsistent
15. **When and how to write ADRs** — Trigger criteria are vague

### 3.2 Process Gaps

1. **No canonical onboarding playbook for a new project** — Starting from scratch still requires manual steps
2. **No formal role handoff protocol** — When Architect finishes, how does Developer pick up? What's the interface?
3. **No canonical release gate definition** — What exactly must be true before deploying v1.0?
4. **No incident response playbook for agent failures** — What happens when a quality gate fails mid-sprint?
5. **No canonical story sizing approach** — Stories vary wildly in effort
6. **No formal "definition of done" per role** — Each role has different completion criteria
7. **No canonical branching / work isolation strategy** — When to use git worktrees vs. feature branches
8. **No formal spec for how agents communicate failures upstream** — Currently ad-hoc message formats
9. **No canonical performance benchmarking protocol** — When to profile, what to measure, what thresholds trigger action
10. **No canonical security review checklist per project type** — The 5-layer pipeline runs but criteria differ by project type

### 3.3 Tooling Gaps (Currently Being Fixed)

From the deep audit:
- `structlog` NOT in `pyproject.toml` (490 files need it)
- 983 empty test stubs (29.2% of test suite)
- `governance-gates.sh` has 62 `|| true` fallbacks — moving to Rust binary
- `execution.py` (2,577 LOC), `install.py` (1,759 LOC) — monolithic, need splitting
- 21 copies of config provider logic — need dedup
- json → orjson migration (292 files)

---

## PART 4: TARGET HANDBOOK VISION

### What the Handbook Must Cover

The handbook should be organized as a living reference in the following structure:

#### Volume 1: Agent Team Architecture & Coordination

1. **Team composition model** — What agent roles exist, their responsibilities, their artifacts, their interfaces with other roles
2. **Agent manager playbook** — How the orchestrating agent manages team agents: spawning, tasking, monitoring, unblocking, escalating
3. **Communication protocols** — How agents communicate: work stream claims, completion signals, escalation messages, blocking reports
4. **Parallel execution patterns** — Which roles can work in parallel; dependency ordering; convergence points
5. **Session management** — How long-running work is tracked, resumed, and handed off across sessions
6. **Failure recovery** — What happens when an agent fails, loops, or produces invalid output

#### Volume 2: Software Development Lifecycle (SDLC)

1. **Project initialization** — From seed prompt to first commit: spec creation, environment setup, tool selection
2. **Requirements engineering** — BDD/DDD-first: how to write FRs, trace them to tests, validate coverage
3. **Architecture decision making** — When to write an ADR, how to structure it, how to enforce decisions in code
4. **Test-first development** — TDD mandate, test types, maturity levels, coverage targets, mutation testing
5. **Implementation patterns** — Library-first, max LOC/complexity, forbidden patterns, safe language idioms
6. **Code review (agent-to-agent)** — What reviewers check, how findings are structured, resolution protocols
7. **Release gates** — What must be true before any deployment; go/no-go criteria per project type
8. **Post-release monitoring** — Metrics, alerting, incident response, feedback ingestion

#### Volume 3: Role-Specific Professional Practices

For each role (**PM/Analyst, Architect, Developer, QA Engineer, Security Engineer, DevOps/Infra, Tech Writer, Data Engineer, Game Designer, Embedded Engineer**):

1. **Role definition** — What this agent does, doesn't do, and is accountable for
2. **Inputs** — What artifacts/context this role consumes
3. **Outputs** — What artifacts this role produces; exact format/location requirements
4. **Quality criteria** — What "done" means for this role's outputs
5. **Decision frameworks** — Canonical answers to the 10-15 most common micro-decisions in this role
6. **Anti-patterns** — What this role must never do (with "aim towards" framing)
7. **Handoff protocol** — How this role hands work to the next role
8. **Tool kit** — Specific tools, libraries, and commands this role uses

#### Volume 4: Language & Stack Playbooks

For each language/stack:

1. **Project scaffolding** — Exact steps to initialize a new project (deps, structure, linters, tests)
2. **Quality baseline** — Linters, type checkers, test frameworks, coverage tools, exact configs
3. **Library catalog** — Canonical library choices per need category; alternatives and why they're not preferred
4. **Testing patterns** — How to write unit, integration, E2E, property-based, mutation tests
5. **Common patterns** — Error handling, logging, config, retry, caching patterns for this language
6. **Interop patterns** — How this language communicates with other languages in the stack
7. **Performance profiling** — Tools and trigger criteria for performance work

#### Volume 5: Governance & Enforcement

1. **Contract system** — How governance policies are written, stored, evaluated, and evolved
2. **Hook pipeline** — How to add new quality gates, register hooks, test hooks
3. **Security policies** — What the 5-layer security pipeline checks, how to address findings
4. **Compliance matrix** — Which compliance regimes (GDPR, HIPAA, PCI) require what changes
5. **Audit trail** — How work is logged, attributed, and retrievable
6. **Policy evolution** — How governance rules are updated without breaking existing work

#### Volume 6: Documentation System

1. **Document taxonomy** — What type of document goes where, with canonical templates
2. **Context docs** — How to create, maintain, and verify technology context docs
3. **Conversation dumps** — When to write, what to include, how to reference across sessions
4. **Spec traceability** — How PRD → FR → Test → Code links are maintained
5. **Staleness management** — When to update docs, how to detect stale content

---

## PART 5: RESEARCH INSTRUCTIONS FOR CHATGPT

### Research Mandate

Using the above context as your grounding, produce the handbook volumes described in Part 4. Your research should:

1. **Ground in current practice (Part 2)** — The handbook extends and canonicalizes what is already working, does not replace it. Preserve all current rules unless you identify a clear conflict.

2. **Fill the gaps (Part 3)** — Each micro-decision gap must become a canonical decision framework with: trigger criteria, options, selection heuristics, examples, and anti-patterns.

3. **Research best practices aggressively** — For each area, consult:
   - Academic literature on software engineering process (Agile, XP, DDD, BDD, TDD, SRE, DevSecOps)
   - Industry standards (ISO 29148 requirements, IEEE 829 testing, OWASP, SLSA, DORA metrics)
   - Leading engineering teams' published practices (Google SRE Book, Accelerate research, Netflix Tech Blog, Stripe Engineering, Cloudflare, etc.)
   - Emerging AI-native development practices (agent frameworks, LLM-driven SDLC, multi-agent coordination)
   - Language-specific best practices for Python, Go, Rust, TypeScript, C++, Zig, Mojo, C#

4. **Operationalize everything** — Every principle must be accompanied by:
   - Concrete decision criteria (if X then Y)
   - Example inputs and outputs
   - Anti-pattern (what NOT to do) with "aim towards" framing
   - Measurable success criteria

5. **Write for agents, not humans** — Assume the reader has no emotional state, no implicit context, no ability to "use judgment." All guidance must be explicit enough that an LLM with no project history can correctly apply it on first read.

6. **Handle multi-language reality** — All process guidance must either be language-agnostic (with language-specific callouts where needed) or have per-language variants.

7. **Zero-human-loop assumption** — Never recommend "get human approval," "ask the team," or "hold a meeting." All human input channels are post-release (bug reports, tickets). All in-process decisions must be resolvable by the agent.

### Specific Research Questions to Answer

1. What is the canonical agent team structure for a startup-scale AI-native development organization? (roles, reporting, accountability)
2. How should agent-to-agent communication be structured for maximum clarity and minimum ambiguity? (message formats, escalation trees, failure signals)
3. What is the optimal granularity for user stories / functional requirements in an AI-executed development context?
4. What is the canonical decision tree for language selection in polyglot projects?
5. How should cross-language API contracts be defined, enforced, and versioned?
6. What are the canonical patterns for error handling, logging, retry, and circuit-breaking across Python / Go / Rust / TypeScript?
7. What constitutes a "complete" architecture decision record in a zero-human-review context?
8. How should mutation testing be structured and threshold-managed for agent-only projects?
9. What is the canonical incident response playbook for autonomous agent systems?
10. How should performance budgets be defined and enforced across a polyglot, microservice-style system?
11. What are the canonical patterns for managing shared state and avoiding race conditions in multi-agent execution?
12. How should "definition of done" be structured per work item type (story, task, bug, spike, epic)?
13. What are the canonical database selection criteria for new services in a polyglot platform?
14. What is the canonical release qualification checklist for an autonomous CI/CD pipeline?
15. How should governance policies be written to be both machine-evaluable and human-readable?

### Output Format Requirements

- Produce as a structured markdown handbook
- Each volume as a separate top-level section with numbered sub-sections
- Every decision framework as a table or flowchart-in-text with clear if/then/else structure
- Every anti-pattern section uses "aim towards" framing (positive direction, not just "don't do X")
- Every role description includes: Definition, Inputs, Outputs, Quality Criteria, Decision Frameworks, Anti-patterns, Handoff Protocol, Toolkit
- Estimated reading time per volume
- A "quick reference card" for each volume (single-page summary of most-referenced rules)
- An index of all decision frameworks with page references

---

## APPENDIX: KEY FILE PATHS FOR REFERENCE

```
# Canonical governance files
thegent/CLAUDE.md                                   # Project-local instructions
~/.claude/CLAUDE.md                                 # Global instructions
thegent/contracts/constitution.yaml                  # 4 core principles
thegent/hooks/hook-config.yaml                       # Hook pipeline config
thegent/docs/governance/GOVERNANCE_SUMMARY.md        # CI gates, contracts
thegent/docs/governance/POLYGLOT_RUNTIME_*.md        # Language coverage matrix
thegent/docs/reference/WORK_STREAM.md               # Canonical backlog

# Key specs
trace/FUNCTIONAL_REQUIREMENTS_MANIFEST.txt           # Sample FR format
trace/VERIFICATION_POLICY.md                         # Quality verification policy
trace/CLAUDE.md                                      # Trace project instructions

# Reference architectures
thegent/src/thegent/mcp/server.py                   # MCP server (100+ tools)
thegent/agents/                                      # 50+ agent persona specs
thegent/hooks/                                       # 15 lifecycle hooks
thegent/contracts/                                   # Policy contracts

# BMAD workflow system
~/.bmad/bmm/workflows/                              # All BMAD workflows
~/.bmad/bmm/workflows/document-project/             # This workflow
~/.bmad/core/tasks/workflow.xml                     # Workflow execution engine
```

---

## PART 6: COMPLETE OPINIONATED DECISIONS CATALOG

*Source: Exhaustive extraction from global CLAUDE.md, trace CLAUDE.md, thegent pyproject.toml, hook-config.yaml, constitution.yaml, WORK_STREAM.md*
*Total: 118 rules — 85 HARD (enforced by hooks/tooling) | 33 SOFT (convention/preference)*

---

### 6.1 SECURITY & PROCESS — ABSOLUTE RULES

**RULE-001 [HARD]** Never kill agent or terminal processes. FORBIDDEN: `kill -9`, `pkill cursor-agent`, `killall`, `ps | xargs kill`. Protected: cursor-agent, thegent, claude, codex, droid, bash, zsh, ghostty. Use safe alternatives: `thegent mcp prune`, `thegent stop <id>`.

**RULE-002 [HARD]** Never add fallbacks, legacy compatibility, or silent failures. FORBIDDEN: `try: new(); except: old()`, `try: thing(); except: pass`, import fallbacks, "just in case" code, backwards compat shims, migration versioning for simple changes. Code MUST fail fast and stop. Fix bugs, don't hide them.

---

### 6.2 ARCHITECTURE & CODE ORGANIZATION

**RULE-003 [HARD]** Library-first policy. Before any implementation: "Is there a library that solves this?" Generic problems (retry, cache, file watch, circuit breaker, rate limit) MUST use a library. Custom logic only for domain-specific behavior. ADR required if choosing custom over library.

**RULE-004 [HARD]** Canonical library selections: retry/backoff → tenacity (use `wait_random_exponential`); HTTP → httpx (not requests/urllib); file watching → watchdog (not os.walk polling); caching → cachetools/diskcache; circuit breaker → pybreaker; logging → structlog (structured JSON); config → pydantic-settings; CLI → typer; validation → pydantic; rate limiting → tenacity + asyncio.Semaphore.

**RULE-005 [HARD]** Extend, never duplicate. Refactor originals. Never create v2 files. Never create a new class if existing one can be made generic. One canonical source per abstraction.

**RULE-006 [HARD]** Architecture boundary enforcement via tach.toml. All new modules must satisfy tach check before merge.

**RULE-007 [HARD]** thegent component placement: agent persona → `agents/<name>.md`; lifecycle hook → `hooks/<event>-<name>.sh` + `hooks/hook-config.yaml`; governance policy → `contracts/<policy>.json` + `qa-policy-engine.sh`; MCP tool → MCP server (FastMCP pattern); CLI command → `commands/<command>/` + register in dispatch; quality gate → `hooks/qa-<gate-name>.sh`.

**RULE-008 [HARD]** Provider pattern: use ProviderRegistry for extensible services. MCP tools via FastMCP registration only.

**RULE-009 [HARD]** New hooks: `hooks/<event>-<name>.sh` + register in `hooks/hook-config.yaml`. Shared hook logic: `hooks/lib/<utility>.sh` (sourced, never called directly).

**RULE-010 [HARD]** Rust tooling: prefer `rg` over `grep`, `fd` over `find`, `jaq` over `jq`. Export `USE_BUILTIN_RIPGREP=0` for system ripgrep (5-10x faster).

**RULE-011 [HARD]** Proactive governance evolution: when work touches a governance domain (retry, cache, file watch, HTTP, auth, logging), check existing governance, follow it, update if missing/outdated, run governance checkpoint at task completion.

**RULE-012 [SOFT]** Primitives first: build generic building blocks before application logic. Config-driven over code-driven. Research before implementing (check PyPI/GitHub for 80%+ implementations).

**RULE-013 [SOFT]** DDD bounded contexts with explicit context maps. Each context owns its aggregate roots. Anti-corruption layers at context boundaries.

---

### 6.3 CODE QUALITY

**RULE-014 [HARD]** Max function length: 40 lines. Enforced by `complexity-ratchet.sh` hook.

**RULE-015 [HARD]** Max cyclomatic complexity: 10 per function.

**RULE-016 [HARD]** Max cognitive complexity: 15 per function.

**RULE-017 [HARD]** Max code duplication: 5% (checked by jscpd).

**RULE-018 [HARD]** Zero linting suppressions without inline justification. Format: `# noqa: E501 -- reason`. `suppression-blocker.sh` blocks violations pre-commit.

**RULE-019 [HARD]** No placeholder TODOs in committed code. All TODOs must be actionable or removed before commit.

**RULE-020 [HARD]** All code must pass: ruff check, type checker (basedpyright/pyright), all tests. No exceptions.

**RULE-021 [HARD]** Python type checker: basedpyright, typeCheckingMode="standard", pythonVersion="3.10", reportMissingImports=true, reportUnusedImport=true, reportUnusedClass=true, reportUnusedFunction=true, reportUnusedVariable=true.

**RULE-022 [HARD]** Ruff config: line length 120, target py310. Rules: E, W, F, I, N, UP, S, B, A, C4, DTZ, T20, SIM, TCH, RUF, PT, ERA, PL, PERF, FURB, PIE, ARG, PTH, ANN, BLE, FBT, RET, SLF. See pyproject.toml for full ignore list.

**RULE-023 [HARD]** Rust baseline: stable `fmt + clippy -D warnings + test`.

**RULE-024 [HARD]** Go baseline: `go test ./...` and `go vet ./...`.

**RULE-025 [HARD]** Zig: pinned stable `zig test`.

**RULE-026 [HARD]** Mojo: pinned version with parity checks against reference implementations.

**RULE-027 [SOFT]** Ubiquitous language enforcement: all domain class/variable names must match glossary terms. Enforced by automated lint script against `UBIQUITOUS_LANGUAGE.md`.

**RULE-028 [SOFT]** Dead code detection: vulture (Python), knip (JS/TS), cargo deadcode (Rust).

**RULE-029 [SOFT]** AI slop detection runs on every Write/Edit.

**RULE-030 [SOFT]** Polyglot conversion rules: prefer refactor-in-place over language conversion; convert only when measured SLO/tooling triggers met; every conversion requires baseline metrics, parity harness, phased cutover plan.

---

### 6.4 TESTING

**RULE-031 [HARD]** Test-first mandate: write tests BEFORE implementation. Failing test MUST exist before bug fix. Test file before source file.

**RULE-032 [HARD]** Agent-Only project coverage: 100% unit, 100% integration, 100% E2E. No humans will test — comprehensive automated coverage is non-negotiable.

**RULE-033 [HARD]** Spec traceability in all tests: `@pytest.mark.requirement("FR-XXX-NNN")`, `# @trace FR-XXX-NNN`, or test name must reference FR ID.

**RULE-034 [HARD]** Test maturity: Agent-Only projects require Level 5 (100% all test types, mutation testing, BDD, SDD alignment, FR traceability ≥85%).

**RULE-035 [HARD]** Pytest markers: `unit`, `integration`, `e2e`, `slow`, `asyncio`, `load`, `requirement` (with FR/WL ID), `fast` (no I/O), `deep` (chaos/slow).

**RULE-036 [SOFT]** Test lanes: fast (`not slow and not integration and not e2e and not load`); nightly (`slow or integration or e2e or load`).

---

### 6.5 DOCUMENTATION ORGANIZATION

**RULE-037 [HARD]** Root-level files ONLY: `README.md`, `CHANGELOG.md`, `AGENTS.md`, `CLAUDE.md`, `00_START_HERE.md`, `PRD.md`, `ADR.md`, `FUNCTIONAL_REQUIREMENTS.md`, `PLAN.md`, `USER_JOURNEYS.md`. No other `.md` files in root. `doc-location-guard` hook blocks violations.

**RULE-038 [HARD]** `docs/` structure: `guides/` (implementation, quick-start/), `reports/` (completion, status), `research/` (CONVERSATION_DUMP_*.md, analysis), `reference/` (quick refs, trackers, maps), `checklists/` (verification).

**RULE-039 [HARD]** Mandatory conversation dumps: after any conversation producing research/plans/decisions/implementation details, write to `docs/research/CONVERSATION_DUMP_YYYY-MM-DD.md`. Do NOT defer. Write as part of the same response/task.

**RULE-040 [HARD]** Context docs required before integration: check/create `docs/context/{technology}.md` before integrating any technology. Must include: header, What is {Tech}, Key Concepts, API/Interfaces (exact specs), Authentication, Code Examples (1-3 working), Sources & References, Quick Reference. Refresh any doc >90 days old.

**RULE-041 [SOFT]** Spec doc system: PRD.md, ADR.md, FUNCTIONAL_REQUIREMENTS.md, PLAN.md, USER_JOURNEYS.md. Trackers in `docs/reference/`. IDs: E{n}.{m}.{k} (epics), FR-{CAT}-{NNN} (requirements), ADR-{NNN} (decisions), P{n}.{m} (tasks), UJ-{N} (journeys).

**RULE-042 [SOFT]** Governance/spec docs must use standard frontmatter: title, date, status, owner, tags. Decision-heavy docs must include backmatter: decision delta, validation commands, residual risks, follow-up review date.

**RULE-043 [HARD]** CLAUDE.md size policy: keep as concise index/policy spine. If grows beyond ~20k tokens: split detailed sections into `docs/docsets/claude/`, maintain explicit links from canonical. Typo files (calude.md) merged into canonical and removed.

---

### 6.6 DEVELOPMENT & DEPLOYMENT

**RULE-044 [HARD]** Never restart entire dev stack (`make dev`, `make dev-tui`). Use hot reload. Restart only the specific service that needs it. Never whole stack unless user explicitly asks.

**RULE-045 [HARD]** bun for JS/TS package management (trace): `bun install`, `bun run`, `bun add`. NOT npm.

**RULE-046 [SOFT]** Package manager detection from lockfiles: `bun.lockb`/`bun.lock` → bun | `pnpm-lock.yaml` → pnpm | `yarn.lock` → yarn | `package-lock.json` → npm.

**RULE-047 [HARD]** Native over Docker for local dev. OSS/free/local first. No paid SaaS as default recommendation when local/OSS/free alternative exists.

**RULE-048 [HARD]** FORBIDDEN: `git restore`, `git reset`, `git clean` — destroys other agents' work-in-progress. Respect dirty files — they are active work. Never revert/overwrite without explicit instruction.

**RULE-049 [HARD]** Smart command debouncing via `make lint`, `make test`, `make quality`, `make validate` (wrapped in `smart-command.sh` to prevent concurrent conflicts between multiple agents).

**RULE-050 [SOFT]** Service logs: `.process-compose/logs/` (ephemeral, truncated on `make dev` start). Lifecycle markers: `[LIFECYCLE] START/STOP <service> <timestamp>`. Never attach to user's TUI terminal.

---

### 6.7 QA GOVERNANCE

**RULE-051 [HARD]** Quality gate command: run `task quality` before stopping work. Full strict pipeline: max-lines, lint, core-boundary, deprecated-aliases, instruction-architecture, harness-contracts, runtime-contracts.

**RULE-052 [HARD]** Hook pipeline v3 (non-negotiable): SessionStart → spec-preflight, qa-preflight. PreToolUse:Write → doc-location-guard, pre-write-validator, suppression-blocker. PreToolUse:Edit → pre-write-validator, suppression-blocker. PostToolUse:Edit|Write → change-doc-tracker, post-edit-checker, async-test-runner. Stop → quality-gate, stop-reconcile, spec-verifier, complexity-ratchet, security-pipeline, test-maturity.

**RULE-053 [HARD]** Security pipeline (5 layers): Layer 1: Secrets (gitleaks). Layer 2: SAST (semgrep, bandit, gosec). Layer 3: Dependencies (pip-audit, npm audit, govulncheck). Layer 4: Infrastructure (hadolint, tfsec, trivy). Layer 5: Supply Chain (syft SBOM, osv-scanner).

**RULE-054 [HARD]** Regression spiral guard thresholds: max failed tests=10, max flaky=8, max missing test pairs=0, max missing test types=0. Directives: green→continue_delivery, yellow→stabilize_before_new_changes, red→hard_interrupt_remediate_now.

**RULE-055 [HARD]** Hook timeouts (runtime config): quality-gate=15s, task-completion=15s, security-pipeline=15s, agileplus-cycle=10s. Cache TTL=600s. Smart skip=true. Parallel stages=true.

**RULE-056 [HARD]** Constitution: P1-SAFETY (never irreversible destructive actions without simulation and sign-off), P2-PRIVACY (never leak PII/secrets into logs or external prompts), P3-EFFICIENCY (favor existing patterns over new deps), P4-IDEMPOTENCY (all agent actions idempotent + unique token).

---

### 6.8 AGENT BEHAVIOR MANDATE

**RULE-057 [HARD]** Never ask user to run a command, search code, or perform an edit that you have tools to do yourself. Proactive execution is the default state. Only ask if requirements are truly ambiguous or require strategic user decision.

**RULE-058 [HARD]** Strategic manager pattern: operate as manager, not worker. Delegate when: >3 files, codebase-wide search, >2000 tokens output, multi-step sequences, independent parallel work. Handle directly: single file, quick answer, <3 files, config/tweak.

**RULE-059 [HARD]** Context budget rule: if task adds >2000 tokens of file content/output, delegate it to a subagent.

**RULE-060 [HARD]** When idle: ALWAYS check backlog with `thegent plan do-next`. Work on items DIRECTLY. Never terminate session while work exists.

**RULE-061 [HARD]** Work stream protocol: read BACKLOG before picking work; filter out CLAIMED items; pick items whose Depends are satisfied; append to CLAIMED when starting (ID, Agent, Started); move to COMPLETED when done.

**RULE-062 [SOFT]** Subagent deployment: use BOTH native subagents (Cursor Agent, Gemini CLI, Codex, Copilot CLI, Claude Code) AND thegent subagents. Native for tool-specific behavior; thegent for cross-provider orchestration.

**RULE-063 [SOFT]** Fire tasks async; do NOT block. Run up to 50 concurrent parallel agents. Reawaken on completion; spawn more agents, follow-up work, or consolidate.

---

### 6.9 PLANNING & ESTIMATES

**RULE-064 [HARD]** Plans MUST have: Phases (Discovery → Design → Build → Test/Validate → Deploy/Handoff), DAG (explicit predecessors, no cycles), Phase|Task ID|Description|Depends On table.

**RULE-065 [HARD]** Assume agent-driven environment. FORBIDDEN in plans: "Schedule audit", "Stakeholder Presentation", "Human checkpoint", "Get approval from X". Use: "N tool calls", "N parallel subagents", "~M min wall clock".

**RULE-066 [HARD]** Planner agents (PM, Analyst, Architect, SM, TEA, UX Designer, Tech Writer) MUST NEVER write code in documentation or plans. Specs, acceptance criteria, architecture decisions, and clear handoffs only.

**RULE-067 [SOFT]** Aggressive timescale mapping: Trivial = 1-2 tool calls, <1 min. Small feature = 3-6 calls, 1-3 min. Cross-stack = 2-3 subagents, 3-8 min. Major refactor = 3-5 subagents, 8-20 min. Multi-phase = agent batches each 10-20 min max. No "days" or "weeks" in estimates.

---

### 6.10 OPTIONALITY & FAILURE BEHAVIOR

**RULE-068 [HARD]** Force requirement where it belongs. Do NOT make dependencies "optional" to avoid failure. If service/config is required for correctness, fail when missing.

**RULE-069 [HARD]** Fail clearly, not silently. Use explicit failures, NOT reduced functionality, logging-only warnings, or hidden errors. Users/operators MUST see WHAT failed and that process did NOT silently degrade.

**RULE-070 [HARD]** Graceful via: retries with visible feedback ("Waiting for X… (2/6)"), error messages listing each failing item, actionable messages, non-obscure stack traces. NOT via optionality or silent fallbacks.

---

### 6.11 SPECIFICATION & FR TRACEABILITY

**RULE-071 [HARD]** Every non-trivial implementation MUST have a corresponding FR statement (FR-{CAT}-{NNN} SHALL …). FRs are source of truth for what was built.

**RULE-072 [HARD]** @trace markers in code: every implementation block that satisfies an FR must have `# @trace FR-CAT-NNN` comment on the implementing function/class.

**RULE-073 [HARD]** FR traceability ≥85%: at least 85% of FR statements must have @trace in code AND ≥1 test tagged with matching requirement marker.

**RULE-074 [HARD]** Smart contract pattern: Spec (FR) → Test (tagged) → Code (@trace) → Verified (gate passes) = VERIFIED. If any step missing, gate fails.

**RULE-075 [SOFT]** ADR for every significant architectural decision: library choice, language choice, pattern adoption, third-party service selection. Format: ADR-NNN, status, decision, rationale, consequences.

---

### 6.12 BMAD METHOD INTEGRATION

**RULE-076 [SOFT]** BMAD workflow sequencing (brownfield): document-project → prd → architecture → epic-tech-context → create-epics-and-stories → dev-story.

**RULE-077 [SOFT]** BMAD planner agents activated via slash commands: `/bmad-pm`, `/bmad-architect`, `/bmad-dev`, `/bmad-sm`, `/bmad-tea`, etc. Start new conversation to switch agent personas.

**RULE-078 [SOFT]** BMAD sprint artifacts in `{project-root}/docs/sprint-artifacts/`. MCP enhancements enabled.

---

### 6.13 FRICTION REDUCTION

**RULE-079 [SOFT]** `friction-detector.sh` hook runs automatically. Act on alerts: `cd &&` → CLI should work from any directory. `head -n` → CLI should have `--limit`. Bash loops → `--repeat N`. Multiple sequential `read_file()` → use `batch_read_files()`. Manual path resolution → use `normalize_path()`.

**RULE-080 [SOFT]** Friction helpers: `batch_file_ops.py` (3-5x fewer tool calls), `scripts/path_utils.py` (cross-platform safe paths).

---

### Enforcement Summary

| Enforcement Level | Count | Mechanism |
|-------------------|-------|-----------|
| CRITICAL (hook blocks) | 4 | constitution.yaml, security hooks |
| HARD (hook fails build) | ~64 | pre-write-validator, suppression-blocker, complexity-ratchet, quality-gate, doc-location-guard |
| HARD (gate fails) | ~21 | spec-verifier, test-maturity, security-pipeline, tach boundary check |
| SOFT (convention) | ~33 | Guidelines in CLAUDE.md, style guides, pattern docs |

---

## PART 7: BDD + SDD + TDD + DDD UNIFIED METHODOLOGY

*Source: Comprehensive synthesis of how agent-driven teams execute all four methodologies together, with canonical tooling per language, agent-specific adaptations, failure modes, and concrete examples*

---

### 7.1 The Four Methodologies — What Each Contributes

| Methodology | Primary Purpose | When Applied | Core Artifacts | Quality Verification |
|-------------|-----------------|--------------|----------------|----------------------|
| **DDD** | Domain model richness + isolation | Phase 1: Before any code | Ubiquitous language, aggregates, bounded contexts, context maps, value objects | No anemic entities, ubiquitous language enforced, context boundaries isolated |
| **SDD** | Formal requirements + traceability | Phase 2: Before implementation | FUNCTIONAL_REQUIREMENTS.md, smart contracts, ADR, FR SHALL statements | ≥85% FR traceability, all smart contracts satisfied |
| **BDD** | User-visible behavior specification | Phase 3: After SDD spec | `.feature` files (Gherkin), step definitions, scenario outlines | All scenarios pass 100% |
| **TDD** | Code correctness + maintainability | Phase 4: During implementation | Unit/integration/E2E/property/mutation tests | ≥100% coverage (agent-only), ≥85% mutation score |

---

### 7.2 Canonical Execution Sequence

```
PHASE 1: DDD DOMAIN DISCOVERY
  └── Build UBIQUITOUS_LANGUAGE.md (glossary of domain terms → code representations)
  └── Define bounded contexts + context maps
  └── Identify aggregates (roots), value objects, entities, domain events
  └── Draft anti-corruption layers for external integrations
  └── GATE: ubiquitous-language-lint passes (all domain identifiers use glossary terms)

PHASE 2: SDD SPECIFICATION
  └── Write PRD.md (epics, user stories, acceptance criteria)
  └── Write FUNCTIONAL_REQUIREMENTS.md (FR-{CAT}-{NNN} SHALL statements)
  └── Write ADR.md (architectural decisions, rationale, consequences)
  └── Write USER_JOURNEYS.md (ASCII flow diagrams)
  └── GATE: spec-preflight hook passes (all required sections present)

PHASE 3: BDD SCENARIO SYNTHESIS
  └── Synthesize Gherkin scenarios from FR statements + domain rules
  └── Write step definitions referencing domain aggregates (not mocks)
  └── Tag scenarios with @FR-CAT-NNN
  └── GATE: all scenarios parseable and step definitions compilable

PHASE 4: TDD IMPLEMENTATION (Red-Green-Refactor)
  ┌── RED: write failing test tagged @pytest.mark.requirement("FR-CAT-NNN")
  ├── PROPERTY: add hypothesis property-based test for invariants
  ├── GREEN: write minimum implementation with @trace FR-CAT-NNN
  ├── REFACTOR: enforce ≤40 lines/function, CC≤10, no duplication
  └── REPEAT per FR statement

PHASE 5: SPECIFICATION VERIFICATION
  └── FR traceability gate: ≥85% FRs have @trace in code + test tagged
  └── Mutation testing gate: ≥85% mutation score
  └── BDD-SDD alignment gate: all FR scenarios have passing BDD test
  └── DDD boundary gate: tach check passes, no anemic domain objects
  └── Security gate: all 5 layers pass
  └── FULL quality gate: task quality passes
```

---

### 7.3 Canonical Tooling Per Language

#### Python

```
BDD:    pytest-bdd (Gherkin integration with pytest)
SDD:    Custom FR parser + @pytest.mark.requirement("FR-...")
TDD:    pytest + hypothesis (property-based) + mutmut (mutation) + pytest-benchmark
DDD:    tach (boundary enforcement) + custom ubiquitous-language-lint

Quality gates:
  pytest features/ -v                    # BDD
  pytest tests/ --cov=src --cov-fail-under=100  # TDD coverage
  mutmut run && cat mutmut.json          # Mutation (≥85%)
  python scripts/spec_compliance_check.py # SDD traceability
  python scripts/ubiquitous_language_lint.py  # DDD terminology
  tach check                             # DDD boundaries
  task quality                           # Full pipeline
```

#### Go

```
BDD:    godog (Cucumber for Go, Gherkin scenarios)
SDD:    Custom Go script parsing FUNCTIONAL_REQUIREMENTS.md + struct tags
TDD:    go test ./... + testify/suite + go-fuzz (fuzzing) + go-mutesting
DDD:    gocyclo (CC ≤10) + gosec (SAST) + custom boundary checks

Quality gates:
  godog features/                        # BDD
  go test -cover ./...                   # TDD coverage
  go test -race ./...                    # Race detection
  go-mutesting ./...                     # Mutation
  go vet ./...                           # Static analysis
  gosec ./...                            # Security
  task quality                           # Full pipeline
```

#### Rust

```
BDD:    cucumber-rs (Gherkin for Rust, #[given]/#[when]/#[then])
SDD:    Custom Rust binary for FR parsing + serde validation (smart contracts)
TDD:    #[test] + proptest (property-based) + tarpaulin (coverage) + cargo-mutants
DDD:    clippy -D warnings + custom cargo boundary plugin + Rust type system

Quality gates:
  cargo test --test cucumber             # BDD
  cargo tarpaulin --out Xml             # TDD coverage
  cargo mutants                         # Mutation
  cargo clippy -- -D warnings           # DDD lint
  cargo audit                           # Security (deps)
  task quality                          # Full pipeline
```

#### TypeScript

```
BDD:    cucumber-js (Gherkin for JS/TS, @Given/@When/@Then)
SDD:    Custom Node.js script + Zod (runtime smart contracts)
TDD:    vitest/jest + fast-check (property-based) + stryker-js (mutation) + nyc/c8
DDD:    tsc --strict + eslint-plugin-complexity + ts-prune (dead code)

Quality gates:
  npx cucumber-js                        # BDD
  npm run coverage                       # TDD coverage
  npx stryker run                        # Mutation
  tsc --strict --noEmit                 # DDD types
  npm audit                             # Security
  npm run quality                       # Full pipeline
```

#### C++

```
BDD:    Cucumber-cpp (Gherkin port for C++)
SDD:    Custom parser + static_assert (smart contracts)
TDD:    Google Test (gtest) + Google Mock (gmock) + gcov + mutate_cpp
DDD:    clang-tidy + clang-format + clang -Werror -Wall

Quality gates:
  make test                             # All tests
  make coverage                         # gcov
  make mutation                         # mutate_cpp
  clang-tidy src/                       # DDD lint
  clang -fsanitize=address,undefined    # Security
  task quality                          # Full pipeline
```

#### Zig

```
BDD:    std.testing + custom Gherkin parser (ecosystem is young)
SDD:    Custom Zig parser + @assert (smart contracts)
TDD:    std.testing + std.time (benchmarks) + Clang backend for coverage
DDD:    zig fmt + Zig tagged unions for value objects + const for immutability

Quality gates:
  zig build test                        # All tests
  zig fmt --check .                     # Formatting
  zig build -Doptimize=ReleaseSafe      # Safety checks
  task quality                          # Full pipeline (if configured)
```

---

### 7.4 Agent-Specific Adaptations

When no humans are involved, these adaptations replace human-dependent steps:

#### Ubiquitous Language (No Team Discussions)
- **Problem:** Ubiquitous language normally requires team consensus sessions
- **Agent solution:** UBIQUITOUS_LANGUAGE.md is the canonical source; automated lint enforces it; any new term requires ADR entry before use
- **Gate:** `ubiquitous-language-lint` fails build if domain identifiers don't match glossary

#### BDD Scenario Authoring (No Product Owner Interviews)
- **Problem:** Scenarios normally come from product owner/BA workshops
- **Agent solution:** Scenarios are synthesized algorithmically from FR statements + domain rules; each FR maps to ≥1 scenario via automated synthesis script
- **Gate:** All FRs must have ≥1 tagged BDD scenario before implementation starts

#### TDD Red-Green (No Pairing)
- **Problem:** Red-Green-Refactor normally benefits from pair programming discipline
- **Agent solution:** Pre-commit hook validates that every new implementation function has a corresponding failing test first; `test-first-enforcer.sh` blocks commits with implementation before test
- **Gate:** Test must exist (and fail) before implementation is written

#### Spec Change Propagation (No Change Management Meetings)
- **Problem:** Spec changes normally require stakeholder communication
- **Agent solution:** When FR changes, automated impact analysis identifies all @trace markers, tagged tests, and BDD scenarios affected; generates cascading update checklist
- **Gate:** All downstream items must be updated before spec change is merged

#### Code Review (No Human Reviewers)
- **Problem:** Code review normally catches DDD violations, test quality, spec drift
- **Agent solution:** All review criteria are encoded as automated gates; `code-review-agent` runs via `bmad:bmm:workflows:code-review` on every story completion; findings block merge
- **Gate:** `bmad dev-story` workflow must complete all checkboxes including code-review gate

---

### 7.5 Failure Mode Guards

#### FM-1: Spec-Code Drift (SDD)
- **Symptom:** FR says "must complete in <100ms" but code has no timeout; tests don't verify this
- **Guard:** Nightly gate checks: for each FR, ≥1 @trace reference in code, ≥1 test tagged, non-functional FRs have benchmark test
- **Response:** RED spiral → `hard_interrupt_remediate_now` until all FRs traced

#### FM-2: BDD Scenario Decay (BDD)
- **Symptom:** Feature file says "Given valid card" but step definition creates mock dict, not real domain aggregate
- **Guard:** Step definition linter flags any step using `mock.Mock()` — must use real domain objects
- **Response:** Failing BDD test blocks merge

#### FM-3: TDD Coverage Blind Spots (TDD)
- **Symptom:** 95% line coverage but mutation score 40% — tests don't actually catch bugs
- **Guard:** Mutation gate (≥85% score) runs BEFORE coverage check; property-based test required per public function
- **Response:** Gate failure blocks merge; agent must improve tests

#### FM-4: DDD Boundary Leakage (DDD)
- **Symptom:** MerchantContext imports PaymentContext schema; domain model queries ORM directly
- **Guard:** `tach check` on every commit; domain files scanned for infrastructure imports (sqlalchemy, requests, django)
- **Response:** tach failure blocks merge; import removed, repository pattern added

#### FM-5: Agent Hallucination (All)
- **Symptom:** Test claims to test FR-PAY-101 but tests different behavior; @trace marker on wrong function
- **Guard:** Semantic verification: parse test docstring + FR statement, verify alignment; round-trip validation on all @trace claims
- **Response:** Misaligned markers flagged; agent must fix before gate passes

#### FM-6: Inconsistent Terminology (DDD)
- **Symptom:** Feature says "payment", code says "transaction", Gherkin says "order"
- **Guard:** `ubiquitous-language-lint` scans all domain class/variable names against glossary
- **Response:** Non-glossary term fails lint; agent must rename using canonical glossary term

#### FM-7: Test Interdependencies (TDD)
- **Symptom:** Tests pass together but fail in isolation (shared database state)
- **Guard:** `pytest --random-order --forked` — randomized order + process isolation
- **Response:** Flaky test detected → YELLOW spiral → stabilize before new changes

#### FM-8: Performance Regression (TDD)
- **Symptom:** FR says <100ms but benchmark uses mock data that skips real I/O
- **Guard:** Performance tests must use realistic dataset sizes; FR non-functional requirements enforced by dedicated benchmark gate
- **Response:** Benchmark failure fails gate; agent adds load test with realistic data

---

### 7.6 Complete Example: Payment Card Validation (All 4 Methodologies)

This example walks through all four methodologies applied to a single feature. It demonstrates the canonical agent workflow end-to-end.

#### Step 1: DDD Domain Discovery

**UBIQUITOUS_LANGUAGE.md entry:**
```
| Card         | Payment instrument         | ValueObject: Card { last_four, brand, validity } |
| CardValidity | State of card validation   | Enum: VALID | INVALID | UNKNOWN              |
| Payment      | Transfer of funds          | PaymentAggregate (root: PaymentTransaction)      |
| CardValidator| Service validating cards   | Service: CardValidator.validate(card)            |
```

**Context map:** Payment Context owns PaymentTransaction aggregate; Card is a value object within it. External gateway has anti-corruption layer (PaymentGatewayAdapter).

#### Step 2: SDD Specification

**FUNCTIONAL_REQUIREMENTS.md:**
```
FR-PAY-101: System SHALL accept credit card numbers satisfying Luhn checksum.
            System SHALL reject card numbers that do not satisfy Luhn checksum.
FR-PAY-102: System SHALL reject card input that is not numeric or is malformed.
FR-PAY-103: Card validation SHALL complete within 100ms (P95).
```

**ADR-042:** Luhn on client-side (deterministic, fast, <1ms, no deps); server MUST re-validate (client is untrusted).

#### Step 3: BDD Scenarios (features/payments/card_validation.feature)

```gherkin
# @domain:payment @epic:E2.1.3
Feature: Card Validation

  Background:
    Given a CardValidator instance

  @FR-PAY-101
  Scenario: Valid Visa card is accepted
    Given a card number "4532015112830366"
    When the card is validated
    Then the card validity is "VALID"
    And the card brand is "VISA"

  @FR-PAY-101
  Scenario: Invalid checksum is rejected
    Given a card number "4532015112830367"
    When the card is validated
    Then the card validity is "INVALID"

  @FR-PAY-102
  Scenario Outline: Non-numeric input is rejected
    Given a card number "<input>"
    When the card is validated
    Then the card validity is "INVALID"
    Examples:
      | input       |
      | abc         |
      | 123-456     |
      |             |

  @FR-PAY-103 @performance
  Scenario: Validation completes within 100ms P95
    Given 1000 valid card numbers
    When all cards are validated
    Then 95th percentile latency is less than 100ms
```

#### Step 4: TDD Implementation (Red-Green-Refactor)

```python
# tests/unit/payment/card_validator_test.py
@pytest.mark.requirement("FR-PAY-101")
def test_valid_visa_accepted(validator):
    result = validator.validate("4532015112830366")
    assert result.validity == CardValidity.VALID


@pytest.mark.requirement("FR-PAY-101")
def test_invalid_checksum_rejected(validator):
    result = validator.validate("4532015112830367")
    assert result.validity == CardValidity.INVALID


@given(card_number=st.integers(min_value=int(1e15), max_value=int(1e16)).map(str))
@pytest.mark.requirement("FR-PAY-101")
def test_validator_never_crashes(validator, card_number):
    """Invariant: validator never throws (handles all input)"""
    result = validator.validate(card_number)
    assert isinstance(result.validity, CardValidity)
```

```python
# src/payment/domain/card_validator.py
"""
@trace FR-PAY-101, FR-PAY-102, FR-PAY-103
"""


class CardValidator:
    def validate(self, card_number: str) -> CardValidationResult:
        if not self._is_valid_format(card_number):  # FR-PAY-102
            return CardValidationResult(CardValidity.INVALID, ...)
        if not self._luhn_valid(card_number):  # FR-PAY-101
            return CardValidationResult(CardValidity.INVALID, ...)
        brand = self._detect_brand(card_number)  # FR-PAY-101
        return CardValidationResult(CardValidity.VALID, Card(card_number[-4:], brand))
```

#### Step 5: Quality Gates Execution

```bash
pytest features/ -v                                    # ✓ 4 scenarios passed
pytest tests/ --cov=src/payment --cov-fail-under=100  # ✓ 100% coverage
mutmut run && jq '.mutation_score' mutmut.json         # ✓ 85% mutation score
python scripts/spec_compliance_check.py                # ✓ FR-PAY-101/102/103 all traced
python scripts/ubiquitous_language_lint.py             # ✓ All identifiers use glossary
tach check                                             # ✓ No boundary violations
task quality                                           # ✓ All gates passed — READY TO MERGE
```

---

### 7.7 Agent Role Responsibilities in the Unified Workflow

| Agent Role | DDD | SDD | BDD | TDD |
|------------|-----|-----|-----|-----|
| **PM/Analyst** | Defines ubiquitous language with user stories | Authors FR SHALL statements | Reviews scenario coverage | Reviews acceptance criteria |
| **Architect** | Defines bounded contexts, context maps, aggregates | Authors ADR decisions | Reviews BDD scenario structure | Reviews test architecture |
| **Dev** | Implements domain model (value objects, aggregates) | Adds @trace markers | Implements step definitions | Writes unit/integration tests |
| **QA/Test** | Enforces DDD boundary gates | Runs spec compliance gates | Maintains feature file quality | Owns mutation/property test gates |
| **Tech Writer** | Documents ubiquitous language in glossary | Maintains FR traceability report | — | Documents test coverage report |

All roles are agent personas. All handoffs are via artifact files (FUNCTIONAL_REQUIREMENTS.md, feature files, ADR). No synchronous human coordination.

---

*Document generated: 2026-02-22*
*Source: 6 parallel Haiku explore agents scanning thegent, trace, kush workspace, quality gates, CLAUDE.md, and BDD/SDD/TDD/DDD synthesis*
*Total tokens synthesized: ~650,000 across 6 agents*
*Parts 6 and 7 added 2026-02-22 from second-pass expansion agents*
