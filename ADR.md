# Architecture Decision Records — thegent

**Document:** Architecture Decisions for thegent unified agent orchestration
**Version:** 1.0
**Date:** 2026-03-29
**Status:** Active

---

## ADR-001: Multi-Agent Orchestration via Native CLI Runners

**Status:** ✅ **ACCEPTED**

### Context

thegent must support 10+ AI agents (Claude, Codex, Gemini, Copilot, Cursor, etc.) with heterogeneous invocation methods:
- Some expose native CLIs (claude-code, cursor-agent)
- Some require HTTP proxies (CLIProxyAPIPlus for minimax, GLM)
- Some use OpenAI-compatible APIs (cursor-api)

Direct reimplementation of all agent protocols would require ~10K LOC of duplicate client logic across projects.

### Decision

Implement a **three-tier agent runner architecture** with protocol-specific runners:

1. **DirectAgentRunner** — Invoke native CLI binaries via subprocess
2. **CodexProxyRunner** — Proxy requests through CLIProxyAPIPlus HTTP interface
3. **CursorApiRunner** — HTTP backend via OpenAI-compatible endpoint

Each runner implements a common `AgentRunner` interface with:
- `run(prompt, cwd, mode, timeout, streaming, stdout_cb, stderr_cb) -> RunResult`
- Consistent return values: `exit_code`, `stdout`, `stderr`, `timed_out`

### Rationale

- **Code reuse:** Share runner interfaces across CLI, MCP server, and test suites
- **Extensibility:** Add new runners without modifying existing agent resolution logic
- **Testability:** Mock runners independently for unit tests
- **Operational flexibility:** Switch runners without recompiling CLI

### Consequences

- ✅ Supports current agent portfolio + future additions
- ✅ Single source of truth for agent metadata (registry, models, fallback chains)
- ⚠️ Requires CLIProxyAPIPlus process management (health checks, timeouts)
- ⚠️ Stderr filtering must stay current as agents evolve

### Links

- Traces to: FR-AGT-001, FR-AGT-002, FR-AGT-004, FR-AGT-005, FR-AGT-006, FR-AGT-007

---

## ADR-002: Provider Fallback Chains for Rate Limits & Quota Exhaustion

**Status:** ✅ **ACCEPTED**

### Context

Single-agent deployments hit rate limits (429 responses) and quota exhaustion (billing/subscription errors) during sustained workflows. Users need automatic failover without manual intervention.

### Decision

Implement **ordered fallback chains** per provider:

```
Primary Chain:
  Claude (Anthropic) → Gemini (Google) → Codex (OpenAI) → Cursor-API

Fallback Classification:
  - RATE_LIMIT (429): Retry same agent after backoff
  - USAGE_LIMIT (billing): Failover to next provider in chain
  - TRANSIENT (502/503): Retry same agent with backoff
  - UNKNOWN: Propagate error to user
```

Each agent has `get_fallback_agents()` that returns ordered alternatives, excluding current agent to prevent infinite loops.

### Rationale

- **Resilience:** Never stuck waiting for rate limit reset; move to next provider
- **Cost control:** Users can define cheap → expensive chains (Local OSS → Claude)
- **Transparency:** Clear error classification so users understand which limit was hit
- **Idempotency:** Fallover deterministic; no random selection

### Consequences

- ✅ Graceful degradation during high-load periods
- ✅ Cost optimization (user can prioritize OSS/local agents)
- ⚠️ Requires up-to-date provider configurations in registry
- ⚠️ Fallback logic must respect user-configured chain order
- ⚠️ Token state may not transfer between providers (separate sessions)

### Links

- Traces to: FR-AGT-008, FR-AGT-009, FR-AGT-010

---

## ADR-003: Exponential Backoff Retry Strategy for Transient Failures

**Status:** ✅ **ACCEPTED**

### Context

Agent subprocess calls can fail transiently (network timeouts, temporary API unavailability, resource contention). Immediate retries often succeed but hammer the service with thundering herd.

### Decision

Use **tenacity library** with exponential backoff:

```python
@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=2, max=60),
    retry=retry_if_exception_type(TransientAgentError),
    before_sleep=before_sleep_log(logger, logging.INFO)
)
def run_agent(...) -> RunResult:
    # Execute agent subprocess
```

Retries only on `TransientAgentError` classified as:
- `rate_limit` (429 → use fallback instead)
- `transient` (502/503/504/network timeout)

Do NOT retry:
- `usage_limit` (quota exhausted → use fallback)
- `permanent_error` (bad request, auth failure)
- `unknown` (propagate to user for manual investigation)

### Rationale

- **Cost efficiency:** Exponential backoff prevents log spam and resource waste
- **Reliability:** 95%+ transient failures resolve on 2nd-3rd attempt
- **Transparency:** Logged attempts with timestamps for debugging
- **Safety:** Max 4 attempts (30s total) prevents hanging indefinitely

### Consequences

- ✅ Improved reliability without user interaction
- ✅ Reduced infrastructure load via backoff discipline
- ⚠️ Small delays in user-facing operations (transparent to UX)
- ⚠️ Requires accurate failure classification (False positives cause delays)

### Links

- Traces to: FR-AGT-009

---

## ADR-004: Failure Classification via Stderr Pattern Matching

**Status:** ✅ **ACCEPTED**

### Context

Agent processes emit unstructured stderr. Distinguishing transient failures (retry candidate) from permanent errors (fallback required) requires heuristic pattern matching.

### Decision

Define **canonical regex patterns** for each failure category:

| Category | Pattern Example |
|----------|-----------------|
| RATE_LIMIT | `429\|too.many.requests\|rate.limit` |
| TRANSIENT | `502\|503\|504\|reconnecting\|timeout\|ECONNRESET` |
| USAGE_LIMIT | `quota.exceeded\|subscription\|billing\|expired` |
| UNKNOWN | (no match) |

Match patterns case-insensitive across both `stderr` and `stdout`. First match wins; return `FailureKind` enum.

### Rationale

- **Automation:** No manual failure triage; heuristics encode common patterns
- **Extensibility:** New patterns added without code changes (configuration-driven)
- **Interoperability:** Works with any agent (vendor stderr format varies)
- **Debuggability:** Failed classification logged with matched text

### Consequences

- ✅ Supports heterogeneous agent outputs (native CLI, HTTP proxies, etc.)
- ⚠️ Pattern maintenance required as agents evolve
- ⚠️ False positives (pattern matches unrelated text): treated as UNKNOWN, escalated to user
- ⚠️ False negatives (agent fails, pattern missing): classified as UNKNOWN, retry attempt

### Mitigation

Maintain pattern registry in config with version history and match frequency metrics. Quarterly audit against collected stderr samples from deployments.

### Links

- Traces to: FR-AGT-010

---

## ADR-005: Noisy Stderr Filtering for Production Usability

**Status:** ✅ **ACCEPTED**

### Context

Agent CLIs (especially Node.js-based) emit non-error noise to stderr:
- Node deprecation warnings
- Hook registry messages
- Usage/telemetry messages
- Build progress indicators

Real errors buried in noise; users confused by false warnings.

### Decision

Define **known noise patterns** and strip from output before returning results:

```python
NOISE_PATTERNS = [
    r"(node:.*DeprecationWarning:.*)",
    r"(Hook\..*registry.*)",
    r"(collecting.*usage.*stats)",
    r"(.*/copilot.*info:.*)",
]


def filter_stderr(stderr: str) -> str:
    for pattern in NOISE_PATTERNS:
        stderr = re.sub(pattern, "", stderr)
    return stderr.strip()
```

**Only meaningful errors preserved:** stack traces, assertion failures, permission denied, etc.

### Rationale

- **UX improvement:** Users see only actionable errors
- **Maintainability:** Centralized noise filtering logic; one source of truth
- **Safety:** Conservative approach — only filter known patterns, preserve unknowns
- **Debuggability:** Original stderr logged separately for troubleshooting

### Consequences

- ✅ Cleaner user-facing error messages
- ⚠️ Pattern maintenance required as agents evolve
- ⚠️ Risk of accidentally filtering real errors (mitigated by conservative filtering)

### Links

- Traces to: FR-AGT-003

---

## ADR-006: CLIProxyAPIPlus Lifecycle Management

**Status:** ✅ **ACCEPTED**

### Context

Agents requiring proxy routing (minimax, GLM, antigravity) use CLIProxyAPIPlus, a separate binary with:
- Configuration (YAML with provider blocks, base URL, auth)
- Process startup (fork + keep alive)
- Health checks (must respond to `/v1/models` before ready)
- Graceful shutdown (SIGTERM)

Manual lifecycle management error-prone; need unified control.

### Decision

Implement **CLIProxyAPIPlusManager** with:

1. **Binary resolution:** Check `CLIPROXYAPI_CMD` env var, `$PATH`, fallback to ~/.local/bin
2. **Config generation:** Render YAML with provider blocks (minimax, glm, antigravity via iFlow)
3. **Process startup:** Fork with timeout enforcement (5s default)
4. **Health polling:** GET `/v1/models` until 200 response or timeout
5. **Graceful shutdown:** SIGTERM on context exit, wait for exit code

Manager holds process handle; automatic cleanup on context exit prevents zombie processes.

### Rationale

- **Reliability:** Ensures proxy ready before agent requests; prevents 503 errors
- **Resource safety:** Guaranteed cleanup via context manager pattern
- **Observability:** Health check logs and startup timing visible to users
- **Flexibility:** Timeout configurable per deployment (dev vs. production)

### Consequences

- ✅ Robust proxy lifecycle; handles edge cases (slow startup, process crash)
- ✅ Memory-safe (automatic cleanup)
- ⚠️ Adds 5s startup latency on first agent call (amortized across session)
- ⚠️ Requires CLIProxyAPIPlus binary in PATH or CLIPROXYAPI_CMD

### Links

- Traces to: FR-AGT-006

---

## ADR-007: Agent Registry for Single Source of Truth

**Status:** ✅ **ACCEPTED**

### Context

Agent metadata scattered:
- Names in CLI argument parsers
- Models in runner implementations
- Aliases in multiple places
- Fallback chains ad-hoc

Inconsistency → bugs, missing agents, wrong model routing.

### Decision

Create **canonical agent registry** with:

```python
AGENT_REGISTRY = {
    "claude": {
        "aliases": ["claude-code", "claude-dev"],
        "runner_type": "DirectAgentRunner",
        "default_model": "claude-opus",
        "fallbacks": ["gemini", "codex"],
    },
    "gemini": {
        "runner_type": "DirectAgentRunner",
        "default_model": "gemini-2.0",
        "fallbacks": ["claude", "codex"],
    },
    # ... 10+ agents
}
```

Single source of truth:
- `get_runner(agent_name)` → appropriate runner
- `resolve_alias(alias)` → canonical name
- `get_fallback_agents(agent_name)` → ordered chain
- CLI argument validation against registered names

### Rationale

- **Consistency:** All components use same metadata
- **Extensibility:** Add agent in one place; automatically available everywhere
- **Debuggability:** Clear agent → runner → model flow
- **Testability:** Mock registry in unit tests

### Consequences

- ✅ Single source of truth prevents configuration drift
- ✅ Easy to add new agents or aliases
- ⚠️ Requires synchronization with upstream agent releases (new models, deprecated agents)

### Links

- Traces to: FR-AGT-007

---

## ADR-008: Separation of Concerns: Agents vs. Memory vs. Orchestration

**Status:** ✅ **ACCEPTED**

### Context

thegent combines three concerns:
1. **Agent selection & invocation** (runners, registries, fallbacks)
2. **Conversation memory** (session state, history, context window management)
3. **Task orchestration** (multi-turn workflows, error recovery, output parsing)

Monolithic approach → tight coupling, hard to test, difficult to reuse.

### Decision

Separate into **three independent modules**:

```
┌──────────────────────────────────────────────┐
│   Task Orchestrator (Workflow Engine)        │
│   - Multi-turn workflows                     │
│   - Error recovery & retries                 │
│   - Output parsing & validation              │
│   - Tool invocation (shell, file, MCP)       │
└──────────────────────────────────────────────┘
            ↓ uses            ↓ uses
┌──────────────────┐  ┌──────────────────┐
│ Agent Runners    │  │ Memory Manager   │
│ - DirectRunner   │  │ - Session state  │
│ - ProxyRunner    │  │ - Context window │
│ - CursorRunner   │  │ - History truncate
└──────────────────┘  └──────────────────┘
```

Each module has:
- Clear interface (ports)
- Minimal dependencies on others
- Independent unit tests
- Pluggable implementations

### Rationale

- **Reusability:** Agents can be used in non-orchestration contexts (standalone CLI)
- **Testability:** Mock memory/agent independently; test orchestration logic separately
- **Extensibility:** Add new orchestration strategies (dag-based workflows, streaming) without modifying agent logic
- **Maintainability:** Smaller focused modules easier to understand

### Consequences

- ✅ High modularity; components usable standalone
- ✅ Easier testing and debugging
- ⚠️ More files/classes to navigate
- ⚠️ Requires clear API contracts between modules

### Links

- Traces to: FR-CTR-001 (Contracts/Ports), FR-PLN-001 (Planning), FR-OPS-001 (Operations)

---

## Summary Table

| ADR | Title | Status | Impact |
|-----|-------|--------|--------|
| 001 | Multi-Agent Orchestration | ✅ ACCEPTED | Architecture foundation |
| 002 | Fallback Chains | ✅ ACCEPTED | Resilience & cost control |
| 003 | Exponential Backoff Retry | ✅ ACCEPTED | Reliability improvement |
| 004 | Failure Classification | ✅ ACCEPTED | Automation & observability |
| 005 | Stderr Noise Filtering | ✅ ACCEPTED | UX improvement |
| 006 | Proxy Lifecycle Management | ✅ ACCEPTED | Resource safety |
| 007 | Agent Registry | ✅ ACCEPTED | Single source of truth |
| 008 | Separation of Concerns | ✅ ACCEPTED | Modularity & extensibility |

---

## Traceability

All ADRs link to Functional Requirements:
- **FR-AGT-*** (Agents): ADR-001, ADR-002, ADR-003, ADR-004, ADR-005, ADR-006, ADR-007
- **FR-CTR-*** (Contracts): ADR-008
- **FR-PLN-*** (Planning): ADR-008
- **FR-OPS-*** (Operations): ADR-006, ADR-008

---

## Document Governance

- **Owner:** thegent Architecture Team
- **Last Updated:** 2026-03-29
- **Next Review:** 2026-04-30
- **Approval Status:** ✅ Ready for Implementation
