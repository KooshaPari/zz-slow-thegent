# Deterministic Replay System — Research Synthesis

## Executive Summary

**What**: Implement a deterministic replay system that captures agent execution traces, re-executes workflows with identical inputs/parameters, and validates output consistency. Enables replay debugging, regression testing, and forensic analysis without re-running expensive LLM calls.

**Why**: Current agent execution is non-deterministic. Once a session completes, re-running the same workflow with the same inputs may produce different outputs (model variance, provider routing changes, cache misses). This blocks:
- Reproducing bugs in production
- Regression testing after model upgrades
- Cost analysis of "what-if" scenarios
- Forensic debugging after failures

**Impact**:
- Deterministic testing pipeline (same inputs → same outputs)
- 80% cost savings on replay vs. full re-execution (mock LLM calls)
- Faster debugging and regression validation
- Audit trail for compliance and forensics
- Foundation for simulation-based optimization

**Priority**: Medium–High (Phase 7–9 research block)
**Status**: Research complete, design ready
**Work Item**: WP-6001, WP-5001
**Related**: [Session Research Fragments](../../research/SESSION_RESEARCH_FRAGMENTS_EXPANDED.md), [Phase 7–9 WBS](../docset/thegent-wbs-phase7-9.md)

---

## Problem Statement

### Current State

- **Non-deterministic execution**: Same task with same inputs may produce different outputs
  - Model responses vary due to temperature/sampling
  - Provider routing changes based on load/cost
  - Cache invalidation between runs
  - External service state changes (DB, APIs)

- **Limited debugging**: When a bug occurs, only option is re-run the full task
  - Re-running is expensive (full LLM calls, external API hits)
  - Hard to isolate which step failed
  - No historical record of execution path taken

- **No regression testing**: Upgrading models or routing logic requires manual verification
  - Can't compare "before" vs. "after" on same inputs
  - High risk of silent regressions

- **Poor forensics**: Production failures leave incomplete traces
  - Can't replay exact steps leading to failure
  - Hard to separate deterministic vs. non-deterministic bugs

### Desired State

- **Deterministic replay**: Record execution, replay with same inputs → same outputs
- **Low-cost debugging**: Replay with mocked LLM calls (no new tokens consumed)
- **Regression testing**: Upgrade model/routing, replay old workflows, validate consistency
- **Forensics**: Replay production failure scenarios, capture execution trace
- **Simulation**: Use replay traces as baseline for "what-if" analysis

---

## Solution Overview

### Core Concepts

#### Trace Recording

Capture complete execution metadata during normal operation:
- **Session metadata**: task ID, model, provider, config, start/end time
- **Tool calls**: All tool invocations (read, write, bash, MCP calls)
  - Input parameters (with sensitive redaction)
  - Output/result (truncated if >10MB)
  - Duration, token usage, cost
- **Decision points**: Routing decisions, branching logic, loop iterations
- **External state**: API responses, DB queries, cache hits/misses
- **Errors**: Exceptions, retries, fallback activations

**Format**: Compact JSON lines (JSONL) → queryable, streamable

#### Trace Replay

Re-execute workflow with recorded inputs:
1. **Load trace**: Read JSONL file, parse tool calls in order
2. **Mock execution**:
   - LLM calls → return mocked response (from trace)
   - File I/O → read from trace-captured snapshots
   - Bash commands → return trace-captured output
   - External APIs → return trace-captured responses
3. **Compare outputs**: New execution vs. original trace
4. **Report diffs**: Highlight divergences (deterministic vs. non-deterministic changes)

#### Simulation Mode

Use trace as baseline for parametric analysis:
- **Modify inputs**: Change model, routing policy, config
- **Replay**: Execute with modified inputs, compare outputs
- **Cost/performance analysis**: Compare cost, latency, quality across scenarios

### Architecture

```
┌─ Execution Pipeline
│  ├─ Normal Run (live)
│  │  └─ TraceRecorder (captures all tool calls, decisions)
│  │     └─ trace-<session_id>.jsonl (persistent)
│
├─ Replay Pipeline
│  ├─ ReplayEngine (reads trace, mocks tool calls)
│  │  ├─ LLMCallMocker (returns traced responses)
│  │  ├─ FileIOStubber (reads from snapshots)
│  │  ├─ BashStubber (returns traced stdout/stderr)
│  │  └─ APIMocker (returns traced API responses)
│  │
│  └─ DiffAnalyzer
│     ├─ DeterministicChanges (expected: config changes, model upgrades)
│     └─ NonDeterministicChanges (unexpected: logic bugs, flaky code)
│
└─ Simulation Pipeline
   ├─ TraceVariator (modify trace inputs)
   ├─ ParametricReplay (re-run with variations)
   └─ ComparisonAnalyzer (cost, latency, quality across scenarios)
```

### Components

#### 1. TraceRecorder
- Wraps tool execution pipeline
- Captures all inputs, outputs, metadata
- Async logging to JSONL (non-blocking)
- TTL-based cleanup (keep 7 days by default)

**Key methods**:
- `record_tool_call(tool_name, inputs, result, duration, cost)`
- `record_decision(decision_type, reasoning, choice)`
- `flush()` — Ensure all writes persist

#### 2. ReplayEngine
- Load JSONL trace file
- Inject mocks into tool pipeline
- Execute workflow with mocked calls
- Stream output to comparison engine

**Key methods**:
- `load_trace(trace_file) → List[ToolCall]`
- `replay(workflow, trace, mode="mock") → ExecutionResult`
- `compare(original, replayed) → DiffReport`

#### 3. LLMCallMocker
- Intercepts LLM call requests
- Looks up trace for matching call (by model, inputs hash)
- Returns traced response (deterministic)
- Falls back to live call if trace missing (configurable)

**Key methods**:
- `mock_llm_call(model, prompt, params) → str | bytes`
- `set_fallback_mode(mode)` — "live" | "error" | "zero"

#### 4. DiffAnalyzer
- Compare original vs. replayed execution
- Classify differences:
  - **Deterministic**: Expected (config changes, model upgrades)
  - **Non-deterministic**: Unexpected (logic bugs, flaky code)
- Generate report with diff summaries

**Key methods**:
- `diff(original_result, replayed_result) → DiffReport`
- `classify_diff(diff) → DeterministicChange | NonDeterministicChange`

#### 5. TraceVariator (for simulation)
- Modify trace inputs parametrically
  - Change model (gpt-5 → gemini-3)
  - Change routing policy (cheapest → pareto)
  - Change config parameters
- Generate N variations of original trace
- Queue for batch replay

**Key methods**:
- `vary_model(trace, new_model) → Trace`
- `vary_routing(trace, new_policy) → Trace`
- `batch_vary(trace, parameter_grid) → List[Trace]`

### Data Structures

#### Trace File (JSONL)

```json
{"type": "session_start", "session_id": "s-123", "task": "refactor-auth", "model": "claude-opus-4.6", "config": {...}, "timestamp": "2026-02-18T10:00:00Z"}
{"type": "tool_call", "tool": "read_file", "inputs": {"path": "src/auth.py"}, "result": "...", "duration_ms": 120, "tokens": 500, "cost": 0.001}
{"type": "decision", "decision_type": "routing", "reasoning": "task is low-risk", "choice": "lifecycle_loop"}
{"type": "tool_call", "tool": "bash", "inputs": {"cmd": "pytest tests/"}, "result": {"stdout": "...", "returncode": 0}, "duration_ms": 5000}
{"type": "session_end", "status": "success", "total_cost": 0.15}
```

#### DiffReport

```python
@dataclass
class DiffReport:
    original_trace: str  # trace file path
    replayed_trace: str  # trace file path
    total_calls: int
    matching_calls: int
    divergent_calls: int
    deterministic_changes: List[DeterministicChange]
    non_deterministic_changes: List[NonDeterministicChange]
    summary: str  # "100% match" | "2 divergences (deterministic)"


@dataclass
class DeterministicChange:
    tool_name: str
    call_index: int
    original_output: str
    replayed_output: str
    reason: str  # "config change" | "model upgrade"


@dataclass
class NonDeterministicChange:
    tool_name: str
    call_index: int
    original_output: str
    replayed_output: str
    severity: str  # "warning" | "error"
```

### Use Cases

#### Use Case 1: Debugging Production Failure
1. Capture failure trace in production
2. Download trace file
3. `thegent replay trace-prod-failure.jsonl --mode=mock`
4. Execution re-runs with mocked LLM calls (no cost)
5. Diffs show exactly where logic diverged
6. Fix bug, re-run to verify

#### Use Case 2: Regression Testing After Model Upgrade
1. Record baseline trace with old model
2. Upgrade model in config
3. `thegent replay trace-baseline.jsonl --vary-model=new-model`
4. TraceVariator generates new trace with new model substituted
5. DiffAnalyzer shows where output changed
6. Manual review determines if changes acceptable

#### Use Case 3: Cost Analysis
1. Record trace for long task (e.g., 10-step workflow)
2. Generate variations:
   - `--vary-model gemini-3-flash` (cheaper)
   - `--vary-routing cheapest` (cost-optimized)
3. Batch replay all variations (mocked, so no cost)
4. Compare output quality vs. cost across scenarios
5. Choose optimal configuration

#### Use Case 4: Forensic Investigation
1. Task fails in production
2. Export failure trace + 5 prior successful traces
3. `thegent replay --forensic trace-failed.jsonl trace-success-*.jsonl`
4. DiffAnalyzer highlights what changed between success/failure
5. Root cause isolated without re-running

---

## Acceptance Criteria

### Functional

- [ ] TraceRecorder captures all tool calls, decisions, metadata
- [ ] ReplayEngine can re-execute workflows with mocked LLM calls
- [ ] LLMCallMocker returns deterministic responses from traces
- [ ] DiffAnalyzer classifies divergences (deterministic vs. non-deterministic)
- [ ] TraceVariator can modify traces parametrically (model, routing, config)
- [ ] Batch replay of 100+ trace variations runs without errors
- [ ] Trace files compress to <50% original size (lz4/zstd)

### Performance

- [ ] Replay latency <2s per 100 tool calls (mocked)
- [ ] Trace recording adds <10% overhead to normal execution
- [ ] Diff analysis completes in <500ms per trace pair
- [ ] Batch replay 50 traces in <30s (sequential replay)

### Operational

- [ ] Trace file format supports streaming (JSONL)
- [ ] TTL-based cleanup removes old traces
- [ ] Sensitive data redaction (API keys, user data) in traces
- [ ] Trace storage quota enforced (default 10GB/workspace)
- [ ] CLI support: `thegent replay`, `thegent vary`, `thegent diff-traces`

### Integration

- [ ] Traces stored in `~/.thegent/traces/` with automatic TTL
- [ ] Replay engine integrates with agent execution pipeline
- [ ] DiffAnalyzer integrates with quality-gate for regression detection
- [ ] MCP tool `thegent_replay_trace` exposed for agent use

---

## Success Metrics

| Metric | Target | Validation |
|--------|--------|------------|
| Trace record overhead | <10% | Timing measurements (before/after) |
| Replay cost savings | >80% vs. live | Token counting (mocked vs. live) |
| Output consistency (same inputs) | 100% | Diff report on baseline replay |
| Regression detection (model change) | 100% accuracy | Manual review of classification |
| Trace file compression | >50% | Actual file sizes |
| CLI availability | `thegent replay` works | CLI test |
| Integration readiness | Zero blocking issues | Integration test suite |

---

## Dependencies & Integrations

### Hard Dependencies

1. **Execution Pipeline**: Must instrument tool execution to capture metadata
2. **Agent Infrastructure**: Replay engine must integrate with agent runner
3. **Persistence Layer**: Need file storage for traces (local, S3, or cloud)

### Soft Dependencies

1. **Quality Gate** (WP-5001): Optional, for regression detection
2. **Supermemory L3** (WP-5001-SM): Optional, for trace context storage
3. **MAIF Artifacts** (WP-3002): Optional, for audit trail

### Integration Points

| System | Integration | Purpose |
|--------|-------------|---------|\
| Execution Pipeline | TraceRecorder wraps tool execution | Capture all calls |
| Agent Runner | ReplayEngine re-executes workflows | Re-run with mocks |
| Quality Gate | DiffAnalyzer flags non-deterministic changes | Regression detection |
| Storage | Traces → `~/.thegent/traces/` | Persistent trace store |
| CLI | `thegent replay`, `thegent vary` | User-facing commands |

---

## Risks & Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Trace file grows too large | Medium | TTL-based cleanup, compression |
| Mock responses diverge from live | High | Validate traces on sample runs |
| Sensitive data leaked in traces | High | Redaction policy, encryption at rest |
| Replay engine overhead too high | Medium | Async recording, batch processing |

### Operational Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Disk quota exceeded | Medium | Quota enforcement, auto-cleanup |
| Trace corruption | High | Checksum validation, recovery |
| Complex traces hard to debug | Medium | Trace summarization, filtering tools |

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- Trace data model (JSONL schema)
- TraceRecorder implementation
- File I/O and compression
- Basic unit tests

### Phase 2: Replay (Week 2)
- ReplayEngine implementation
- LLMCallMocker
- Execution mocking (file I/O, bash, APIs)
- Integration tests

### Phase 3: Analysis (Week 3)
- DiffAnalyzer implementation
- Classification of deterministic vs. non-deterministic changes
- Report generation

### Phase 4: Simulation (Week 4)
- TraceVariator for parametric variations
- Batch replay pipeline
- CLI support (`thegent replay`, `thegent vary`)

### Phase 5: Integration (Week 5)
- Integration with agent execution pipeline
- Quality-gate integration for regression detection
- Production deployment (canary)

---

## Open Questions

1. **Sensitive Data Redaction**: Which fields should be redacted? Recommend: API keys, user emails, financial data (configurable).
2. **Trace Retention**: Default TTL of 7 days? Recommend: Configurable, with archive option for long-term storage.
3. **Replay Fallback**: When trace missing, should replay fall back to live calls or error? Recommend: Configurable mode (live | error | zero).
4. **Cost Attribution**: How to attribute cost of trace recording? Recommend: Negligible (<1%) with async logging.

---

## Next Steps

1. **Design Review**: Validate trace schema and replay semantics
2. **Prototype**: Implement Phase 1–2 (Foundation + Replay) in isolated branch
3. **Integration**: Wire into agent execution pipeline
4. **Testing**:
   - Replay 100+ production traces
   - Validate output consistency
   - Measure overhead
5. **Deployment**: Canary to 5% of traffic, monitor 1 week
6. **Documentation**: CLI guide, trace format spec, troubleshooting

---

## References

- [Phase 7–9 WBS](../docset/thegent-wbs-phase7-9.md) — Phase 7–9 research roadmap
- [Agent Infrastructure](../../guides/START_HERE.md) — Agent execution fundamentals
- [Quality Gate System](../../reference/MONITORING_DASHBOARD_SPEC.md) — Monitoring and regression detection
- [WORK_STREAM.md](../../reference/WORK_STREAM.md) — Unified work stream

---

**Document Version**: 1.0
**Last Updated**: 2026-02-18
**Status**: Ready for design review
