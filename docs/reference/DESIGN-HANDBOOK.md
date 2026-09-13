---
title: Design Handbook
date: 2026-02-22
status: LIVING
owner: thegent
tags: [handbook, design, architecture, patterns]
---

# thegent Design Handbook

> **Purpose**: How we design systems in thegent. Architecture patterns, decision processes, design anti-patterns.
> **Audience**: Any agent or human designing features or systems.
> **Update policy**: Update when architectural decisions change or new patterns are established.

---

## 1. Design Process

### Every Non-Trivial Change Needs a Design

No exceptions. "Simple" changes without a design are where unexamined assumptions cause the most wasted work.

### The Flow

```
Understand the problem
  → Research existing solutions (library-first)
  → Propose 2-3 approaches with trade-offs
  → Write design doc (docs/plans/YYYY-MM-DD-<topic>-design.md)
  → Get approval
  → Write implementation plan (WBS with DAG)
  → Execute
```

### Design Doc Sections

Every design doc MUST cover (scale depth to complexity):

1. **Problem** — what is broken/missing and why it matters
2. **Goal** — measurable success criteria
3. **Current State** — what exists, what the gap is
4. **Design** — proposed solution with components, data model, interfaces
5. **Alternatives Considered** — 2-3 other approaches and why they were rejected
6. **Implementation Phases** — phased WBS with rough effort
7. **Backmatter** — decision delta, validation commands, residual risks, follow-up date

### Planner Anti-Patterns

Planners MUST NOT:
- Write code in docs or plans (pseudocode only if essential)
- Include human checkpoints ("schedule audit", "get approval from X")
- Use calendar time ("2 weeks") — use agent-time ("3 subagents, 8-20 min wall clock")
- Describe vague outcomes ("improve performance") — write measurable criteria

---

## 2. Architecture Patterns

### Strategy Pattern for Agents

All agent personas use the AgentRunner strategy pattern:

```python
class AgentRunner(Protocol):
    role: str

    def run(self, task: str, context: AgentContext) -> AgentResult: ...
```

New agent types register in `AgentRunnerRegistry`. Never instantiate directly.

### Provider Pattern for Services

Extensible services (models, routing, storage) use `ProviderRegistry`:

```python
registry = ProviderRegistry()
registry.register("openrouter", OpenRouterProvider)
provider = registry.get("openrouter")
```

No conditional `if provider == "openrouter": ...` chains — polymorphism only.

### Hook Pattern for Lifecycle Events

Every lifecycle event is a hook, not inline code:

```
hooks/<event>-<name>.sh   — hook implementation
hooks/hook-config.yaml    — registration + config
hooks/lib/<utility>.sh    — shared logic (sourced, never called directly)
```

Hook dispatcher calls all registered hooks for an event. No inline lifecycle code in agent runners.

### FastMCP for Tool Registration

All MCP tools register through FastMCP:

```python
@mcp.tool()
async def my_tool(param: str) -> str:
    """Tool description."""
    ...
```

Never bypass FastMCP registration with direct MCP protocol calls.

### CSM (Canonical Structured Message) for Agent Outputs

All agent outputs use `CanonicalStructuredMessage` (WP-0002):

```python
from thegent.contracts.csm import CanonicalStructuredMessage, CSMPhase, CSMStatus

msg = CanonicalStructuredMessage(
    phase=CSMPhase.RESULT,
    status=CSMStatus.SUCCESS,
    content="...",
)
```

No ad-hoc dict outputs from agents.

### CEL Router for Policy Decisions

Routing and policy decisions use the CEL (Common Expression Language) router:

```python
from thegent.routing.cel_router import CELRouter

router = CELRouter(rules_path="contracts/routing-rules.json")
result = router.evaluate(context)
```

No hardcoded `if cost > X: route_to_cheap()` chains — policy lives in CEL rules, not code.

---

## 3. Data Design Patterns

### Pydantic for All Data Models

```python
from pydantic import BaseModel, field_validator


class TaskSpec(BaseModel):
    id: str
    title: str
    priority: Literal["P0", "P1", "P2", "P3"]

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v.startswith("WL-"):
            raise ValueError(f"ID must start with WL-, got: {v}")
        return v
```

No raw dicts for structured data. No dataclasses for data that needs validation.

### Default Factories

```python
# CORRECT
items: list[str] = Field(default_factory=list)
metadata: TaskMetadata = Field(default_factory=lambda: TaskMetadata())

# FORBIDDEN — mutable default
# items: list[str] = []
```

### Storage Hierarchy

| Data type | Storage |
|-----------|---------|
| Structured, queried | SQLite |
| Large blobs | Compressed files (zstandard) |
| Vectors/embeddings | sqlite-vec |
| Config | TOML (pydantic-settings) |
| Session state | JSON files in `~/.thegent/sessions/` |
| Audit logs | JSONL, append-only |

---

## 4. Interface Design

### CLI Design Principles

```bash
# Good: works from any directory
thegent run "task"

# Good: --limit instead of head -n
thegent ps --limit 10

# Good: --repeat instead of bash loop
thegent run --do-next --repeat 5

# Good: consistent --dry-run flag
thegent plan index rebuild --dry-run
```

Every CLI command should:
- Work from any directory (no `cd` required)
- Have `--dry-run` if destructive
- Have `--limit` if listing
- Output structured JSON with `--json`
- Be idempotent where possible

### MCP Tool Design

```python
@mcp.tool()
async def thegent_research_query(
    query: str,
    source: str | None = None,
    since: str | None = None,
) -> list[ResearchItem]:
    """Query the research knowledge base.

    Args:
        query: Natural language or keyword query
        source: Filter by source (arxiv, github, reddit, ...)
        since: ISO duration string (24h, 7d, 30d)
    """
```

Every MCP tool:
- Has a descriptive docstring (used by LLMs for tool selection)
- Uses typed parameters (no `**kwargs`)
- Returns structured data (Pydantic model or list thereof)
- Fails loudly on bad input

### Hook I/O Contract

All hooks:
- Read context from `$THGENT_*` env vars
- Return exit 0 (pass), exit 1 (fail), exit 124 (timeout)
- Write findings to stderr
- Write structured data to `$THGENT_HOOK_OUTPUT` if set

---

## 5. Error Design

### Every Error Must Be Actionable

```python
# BAD
raise ValueError("invalid config")

# GOOD
raise ValueError(
    f"Invalid routing config: provider {provider!r} not in SUPPORTED_PROVIDERS={SUPPORTED_PROVIDERS}. "
    f"Check routing/provider_types.py or run: thegent routing providers list"
)
```

### Error Hierarchy

```
ThegentError (base)
├── ConfigError          — bad config, actionable message
├── ProviderError        — provider not found/unavailable
├── RoutingError         — routing failure
├── SessionError         — session not found/expired
├── GovernanceError      — policy violation
└── QualityGateError     — quality check failure
```

All errors in `src/thegent/errors.py`.

---

## 6. Security Design

### Trust Model

| Layer | Trust level | Validation |
|-------|-------------|-----------|
| User CLI input | Untrusted | Validate at CLI boundary |
| MCP tool input | Untrusted | Validate in tool handler |
| Config files | Semi-trusted | Pydantic schema validation |
| Internal module calls | Trusted | Assert + type system |
| External API responses | Untrusted | Parse + validate |

### Subprocess Safety

Always use list form for subprocess. Never `shell=True` with dynamic input:

```python
# FORBIDDEN
subprocess.run(f"grep {user_query} /etc/passwd", shell=True)

# CORRECT
subprocess.run(["grep", user_query, "/etc/passwd"])
```

---

## 7. Observability Design

### Structured Logging

```python
import structlog

log = structlog.get_logger()
log.info("routing.decision", provider="openrouter", model="claude-3-5-sonnet", cost_estimate=0.002)
```

Never `print()`. Never unstructured `logger.info(f"blah {thing}")`.

### Tracing

Execution traces go through `TraceRecorder` (deterministic replay system):

```python
from thegent.trace import TraceRecorder, RecorderConfig

recorder = TraceRecorder(RecorderConfig(trace_dir=str(trace_dir)))
with recorder.session("my-task"):
    result = run_agent(task)
```

### Metrics

LOC/complexity metrics via `task diag:wl137`. SLO dashboard via `scripts/render_slo_dashboard.py`.

---

## 8. Testing Design

### Test Topology

```
tests/
  unit/           # Fast, no I/O, no network
  integration/    # Real I/O, mocked network
  e2e/            # Full stack, real network (nightly+)
  benchmarks/     # Performance (deep lane)
```

### Contract Testing

For every public interface: write a contract test that verifies the interface shape, not the implementation.

### Property-Based Testing

Use `hypothesis` for data model validation:

```python
from hypothesis import given, strategies as st

@given(st.text())
def test_research_item_title_roundtrip(title: str):
    item = ResearchItem(title=title, ...)
    assert item.title == title
```

---

## 9. Decisions Log (Key ADRs)

| Decision | Rationale | Date |
|----------|-----------|------|
| Pyright strict mode | Zero type errors as invariant; no runtime surprises | 2026-02-21 |
| Mandatory direct imports (no fallbacks) | Fail-loud at startup; no hidden optional deps | 2026-02-21 |
| Static `__all__` lists | Pyright can verify exports; no dynamic slop | 2026-02-21 |
| sqlite-vec for embeddings | No separate vector DB process; single .so | 2026-02-22 |
| CSM for agent outputs | Canonical contract across all harnesses | 2026-02-20 |
| CEL for policy routing | Policy in data, not code; hot-reloadable rules | 2026-02-20 |
| tenacity for all retry | No custom retry loops; backoff guaranteed correct | 2026-02-18 |
| structlog for logging | Structured JSON, aggregatable, no print() | 2026-02-18 |
| FastMCP for MCP tools | Type-safe registration; auto-generates schemas | 2026-02-18 |

Full ADRs in `ADR.md` at project root.

---

## 10. Anti-Patterns Catalog

| Anti-pattern | Why forbidden | Correct alternative |
|-------------|---------------|-------------------|
| `try: import X; except: X = None` | Hidden optional deps, breaks at runtime unpredictably | Mandatory import; fail at startup |
| `except E: pass` | Hides bugs | Let it propagate; fix root cause |
| `return default` on error | Caller can't distinguish error from empty result | Raise explicit typed error |
| `dict[str, Any]` everywhere | Type system is useless | Define Pydantic model |
| `v2_` file copies | Codebase bloat, divergence | Refactor in place |
| `sorted({*globals()})` for `__all__` | Pyright can't verify exports | Static literal list |
| `callable` as type annotation | `callable` is a builtin function, not a type | `Callable[..., Any]` |
| `any` (lowercase) as type | Same issue | `Any` from typing |
| Manual path construction | Cross-platform bugs | `pathlib.Path` + `safe_join` |
| `subprocess.run(cmd, shell=True)` with dynamic input | Command injection risk | `subprocess.run([cmd, arg1, arg2])` |

Full list: `docs/guides/anti-patterns.md`
