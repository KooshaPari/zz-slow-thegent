---
task_id: research-simulation-replay
status: in_progress
---

# Deterministic Replay System — Implementation Tasks

## Work Breakdown Structure (WBS)

### Overview

| Phase                    | Duration | Tasks | Key Deliverable                |
| ------------------------ | -------- | ----- | ------------------------------ |
| **Phase 1: Foundation**  | Week 1   | 3     | Trace data model + recorder    |
| **Phase 2: Replay**      | Week 2   | 4     | ReplayEngine + mocking layer   |
| **Phase 3: Analysis**    | Week 3   | 3     | DiffAnalyzer + reports         |
| **Phase 4: Simulation**  | Week 4   | 3     | TraceVariator + batch replay   |
| **Phase 5: Integration** | Week 5   | 4     | CLI, MCP, quality-gate, canary |
| **TOTAL**                | 5 weeks  | 17    | Deterministic replay system    |

---

## Phase 1: Foundation (Week 1)

### T1.1: Trace Data Model & Schema

**Objective**: Define JSONL trace format, implement serialization.

**Description**:

- Design trace record schema (ToolCallRecord, DecisionRecord, SessionRecord)
- Define JSONL structure and validation
- Create schema documentation
- Implement dataclass serialization/deserialization

**Inputs**:

- Design spec (proposal.md, design.md)
- JSON schema examples

**Outputs**:

- `thegent/trace/schema.py` (dataclasses + schema)
- `docs/reference/TRACE_FORMAT_SPEC.md` (format documentation)
- Unit tests (test_schema.py)

**Dependencies**: None

**Acceptance Criteria**:

- [ ] ToolCallRecord, DecisionRecord, SessionRecord defined
- [ ] JSONL serialization round-trips correctly
- [ ] Schema validation works (optional fields, types)
- [ ] 100% test coverage

**Effort**: 2 engineer-days

---

### T1.2: TraceRecorder Implementation

**Objective**: Implement core recording functionality (async, non-blocking).

**Description**:

- Async write worker for non-blocking recording
- Sensitive data redaction (API keys, passwords, tokens)
- Result truncation (>10MB cap)
- File I/O with gzip compression
- TTL-based cleanup

**Inputs**:

- Schema from T1.1
- Configuration spec

**Outputs**:

- `thegent/trace/recorder.py` (TraceRecorder class)
- `thegent/trace/cleanup.py` (TTL cleanup scheduler)
- Unit tests (test_recorder.py)

**Dependencies**: T1.1

**Acceptance Criteria**:

- [ ] Async recording <10% overhead on execution
- [ ] Redaction hides API keys, passwords, tokens
- [ ] Compression achieves >50% reduction
- [ ] TTL cleanup removes stale traces
- [ ] No data loss on graceful shutdown

**Effort**: 3 engineer-days

---

### T1.3: TraceRecorder Integration & Testing

**Objective**: Integrate recorder into agent execution pipeline, validate in test environment.

**Description**:

- Inject TraceRecorder into agent runner
- Wrap tool execution layer with recording
- Test with real agent workflows
- Measure overhead (latency, memory)
- Integration test suite

**Inputs**:

- TraceRecorder from T1.2
- Agent runner code

**Outputs**:

- Integration hooks in agent runner
- Integration tests (test_integration_recorder.py)
- Performance report

**Dependencies**: T1.2

**Acceptance Criteria**:

- [ ] Recording integrates without errors
- [ ] Overhead <10% measured on real workflows
- [ ] Traces persist correctly
- [ ] All integration tests pass
- [ ] Performance report shows acceptable overhead

**Effort**: 2 engineer-days

---

## Phase 2: Replay (Week 2)

### T2.1: ReplayEngine & Trace Loading

**Objective**: Implement core replay engine with trace loading and mock dispatch.

**Description**:

- ReplayEngine class for managing replay execution
- Trace file loading (JSONL parsing, compression handling)
- Mock executor factory
- Fallback mode support (mock | live | error)

**Inputs**:

- Trace schema from T1.1
- Replay design spec

**Outputs**:

- `thegent/trace/replay.py` (ReplayEngine class)
- `thegent/trace/mocking.py` (mock executor factory)
- Unit tests (test_replay.py)

**Dependencies**: T1.1

**Acceptance Criteria**:

- [ ] Traces load correctly (JSONL parsing)
- [ ] Mock executor factory works for all tool types
- [ ] Fallback modes (mock | live | error) functional
- [ ] <2s replay latency per 100 tool calls
- [ ] 100% test coverage

**Effort**: 3 engineer-days

---

### T2.2: LLMCallMocker Implementation

**Objective**: Implement mock LLM call interception and response lookup.

**Description**:

- LLMCallMocker class for mocking LLM/Claude/GPT calls
- Trace record matching by model + prompt prefix
- Deterministic response return from trace
- Fallback to live execution (expensive) if trace missing
- Integration with ReplayEngine

**Inputs**:

- ReplayEngine from T2.1
- LLM call patterns from execution pipeline

**Outputs**:

- `thegent/trace/llm_mocker.py` (LLMCallMocker class)
- Unit tests (test_llm_mocker.py)

**Dependencies**: T2.1

**Acceptance Criteria**:

- [ ] LLM calls intercepted correctly
- [ ] Mocked responses match traced responses
- [ ] Fallback mode works (live execution available)
- [ ] <50ms lookup latency
- [ ] 100% test coverage

**Effort**: 2 engineer-days

---

### T2.3: File I/O & Bash Stubbing

**Objective**: Implement stubs for file I/O and bash command execution during replay.

**Description**:

- FileIOStubber (read/write/delete operations)
- BashStubber (command execution)
- Snapshot storage for file contents
- Bash output/returncode mocking
- Integration with ReplayEngine

**Inputs**:

- ReplayEngine from T2.1
- Tool execution interface

**Outputs**:

- `thegent/trace/file_io_stubber.py` (FileIOStubber)
- `thegent/trace/bash_stubber.py` (BashStubber)
- Unit tests (test_stubs.py)

**Dependencies**: T2.1

**Acceptance Criteria**:

- [ ] File I/O operations mocked correctly
- [ ] Bash commands return traced output
- [ ] Return codes preserved
- [ ] Snapshot storage works for file contents
- [ ] 100% test coverage

**Effort**: 2 engineer-days

---

### T2.4: Replay Testing & Validation

**Objective**: Test replay end-to-end with real workflows, validate output consistency.

**Description**:

- Record real agent workflow
- Replay workflow with mocks
- Compare outputs (100% match expected)
- Test fallback modes (live execution, error)
- Performance benchmarking

**Inputs**:

- Complete replay infrastructure from T2.1–T2.3
- Real agent workflows

**Outputs**:

- End-to-end test suite (test_replay_e2e.py)
- Performance report
- Replay validation checklist

**Dependencies**: T2.1, T2.2, T2.3

**Acceptance Criteria**:

- [ ] 100% output consistency on same inputs
- [ ] Fallback modes functional
- [ ] Replay 10x faster than live execution
- [ ] All E2E tests pass
- [ ] Performance benchmarks document latency

**Effort**: 2 engineer-days

---

## Phase 3: Analysis (Week 3)

### T3.1: DiffAnalyzer Implementation

**Objective**: Compare original vs. replayed execution traces, identify divergences.

**Description**:

- DiffAnalyzer class for trace comparison
- Record-by-record comparison logic
- Difference detection (output changes)
- Integration with trace loading

**Inputs**:

- Trace schema from T1.1
- Comparison logic design

**Outputs**:

- `thegent/trace/diff_analyzer.py` (DiffAnalyzer class)
- Unit tests (test_diff_analyzer.py)

**Dependencies**: T1.1

**Acceptance Criteria**:

- [ ] Traces compared correctly (record-by-record)
- [ ] Differences detected accurately
- [ ] Diff analysis <500ms per trace pair
- [ ] 100% test coverage

**Effort**: 2 engineer-days

---

### T3.2: Difference Classification

**Objective**: Classify differences as deterministic or non-deterministic.

**Description**:

- Classification logic (config change detection)
- Heuristics for deterministic vs. non-deterministic
- Confidence scoring
- Integration with DiffAnalyzer

**Inputs**:

- DiffAnalyzer from T3.1
- Classification design spec

**Outputs**:

- Classification module (in diff_analyzer.py)
- Classification rule documentation
- Unit tests (test_classification.py)

**Dependencies**: T3.1

**Acceptance Criteria**:

- [ ] Config changes detected as deterministic
- [ ] Logic bugs detected as non-deterministic
- [ ] Classification accuracy >95% (manual validation)
- [ ] 100% test coverage

**Effort**: 2 engineer-days

---

### T3.3: Report Generation & Visualization

**Objective**: Generate human-readable diff reports with summaries.

**Description**:

- DiffReport dataclass (structured output)
- Report generation (JSON, markdown, CLI table)
- Summary statistics (matching %, divergence rate)
- Highlighting of non-deterministic changes
- Integration with DiffAnalyzer

**Inputs**:

- DiffAnalyzer from T3.1
- Report format spec

**Outputs**:

- Report generation module (in diff_analyzer.py)
- Report templates (JSON, markdown, plain text)
- Unit tests (test_reporting.py)

**Dependencies**: T3.1, T3.2

**Acceptance Criteria**:

- [ ] Reports generated in multiple formats
- [ ] Summaries accurate and helpful
- [ ] Non-deterministic changes highlighted
- [ ] Report generation <200ms per trace pair
- [ ] 100% test coverage

**Effort**: 1 engineer-day

---

## Phase 4: Simulation (Week 4)

### T4.1: TraceVariator Implementation

**Objective**: Modify traces parametrically for simulation (model changes, routing policies).

**Description**:

- TraceVariator class for trace transformation
- Model variation (substitute model, adjust token counts)
- Routing policy variation (change decision choices)
- Config parameter variation
- Batch variation support (parameter grid)

**Inputs**:

- Trace schema from T1.1
- Variator design spec

**Outputs**:

- `thegent/trace/variator.py` (TraceVariator class)
- Unit tests (test_variator.py)

**Dependencies**: T1.1

**Acceptance Criteria**:

- [ ] Model variations generated correctly
- [ ] Routing variations generated correctly
- [ ] Config variations work
- [ ] Batch variation generates N variations
- [ ] 100% test coverage

**Effort**: 2 engineer-days

---

### T4.2: Batch Replay Pipeline

**Objective**: Implement batch replay of trace variations with result collection.

**Description**:

- Batch replay orchestration (sequential and parallel)
- Result collection and aggregation
- Cost/performance comparison across variations
- Progress tracking
- Error handling and retries

**Inputs**:

- ReplayEngine from T2.1
- TraceVariator from T4.1

**Outputs**:

- `thegent/trace/batch_replay.py` (BatchReplayOrchestrator)
- Unit tests (test_batch_replay.py)

**Dependencies**: T2.1, T4.1

**Acceptance Criteria**:

- [ ] Batch replay 50+ traces sequentially
- [ ] Result aggregation works
- [ ] Cost/performance comparisons accurate
- [ ] Progress tracking functional
- [ ] 100% test coverage

**Effort**: 2 engineer-days

---

### T4.3: Simulation Analysis & Reporting

**Objective**: Analyze simulation results, generate comparison reports.

**Description**:

- SimulationAnalyzer class for result analysis
- Cost comparison (variation A vs. B)
- Quality comparison (output consistency)
- Performance comparison (latency)
- Recommendation generation

**Inputs**:

- Batch replay results from T4.2
- Analysis spec

**Outputs**:

- `thegent/trace/simulation_analyzer.py` (SimulationAnalyzer)
- Report templates
- Unit tests (test_simulation_analyzer.py)

**Dependencies**: T4.2

**Acceptance Criteria**:

- [ ] Cost comparisons accurate
- [ ] Quality metrics calculated
- [ ] Performance metrics calculated
- [ ] Reports generated in markdown/JSON
- [ ] 100% test coverage

**Effort**: 1 engineer-day

---

## Phase 5: Integration & Deployment (Week 5)

### T5.1: CLI Commands

**Objective**: Implement `thegent replay` and `thegent vary` CLI commands.

**Description**:

- CLI command interface (`replay`, `vary`, `diff-traces`)
- Argument parsing (trace file, mode, model, routing policy)
- Help/usage documentation
- Integration with replay/variator modules

**Inputs**:

- ReplayEngine, TraceVariator, DiffAnalyzer
- CLI design spec

**Outputs**:

- `thegent/cli/replay_commands.py` (CLI handlers)
- CLI tests (test_cli_replay.py)
- CLI documentation

**Dependencies**: T2.1, T3.1, T4.1

**Acceptance Criteria**:

- [ ] `thegent replay` works end-to-end
- [ ] `thegent vary` generates variations
- [ ] `thegent diff-traces` compares traces
- [ ] Help text accurate and helpful
- [ ] All CLI tests pass

**Effort**: 1 engineer-day

---

### T5.2: MCP Tool Registration

**Objective**: Expose replay as MCP tool for agent use.

**Description**:

- MCP tool registration (`thegent_replay_trace`)
- Tool parameters and documentation
- Integration with FastMCP registration
- Tool response format

**Inputs**:

- ReplayEngine from T2.1
- MCP server interface

**Outputs**:

- MCP tool registration (in MCP server code)
- Tool documentation
- Integration tests (test_mcp_replay.py)

**Dependencies**: T2.1

**Acceptance Criteria**:

- [ ] MCP tool callable from agents
- [ ] Tool parameters documented
- [ ] Response format correct
- [ ] Integration tests pass

**Effort**: 1 engineer-day

---

### T5.3: Quality-Gate Integration

**Objective**: Integrate DiffAnalyzer into quality-gate for regression detection.

**Description**:

- Quality-gate hook for trace-based regression detection
- Model upgrade detection
- Automatic replay with new model
- Regression failure reporting
- Integration with existing quality-gate

**Inputs**:

- DiffAnalyzer from T3.1
- Quality-gate infrastructure
- Design spec

**Outputs**:

- `thegent/hooks/qa-replay-regression.sh` (quality-gate hook)
- Hook integration tests
- Documentation

**Dependencies**: T3.1

**Acceptance Criteria**:

- [ ] Hook detects model upgrades
- [ ] Automatic replay triggered
- [ ] Regression detection works
- [ ] Hook integrates with quality-gate
- [ ] All tests pass

**Effort**: 1 engineer-day

---

### T5.4: Canary Deployment & Validation

**Objective**: Deploy to production (canary), validate, monitor 1 week.

**Description**:

- Canary deployment to 5% of traffic
- Monitoring setup (recording overhead, replay latency, errors)
- Production validation (real traces, replay accuracy)
- Alert configuration
- Metrics collection (1 week)

**Inputs**:

- Complete replay system (T1–T5.3)
- Production environment
- Monitoring setup

**Outputs**:

- Production deployment (canary)
- Monitoring dashboard
- Metrics report (1 week)

**Dependencies**: T1–T5.3

**Acceptance Criteria**:

- [ ] Canary deployment successful
- [ ] Recording overhead <10% (measured)
- [ ] Replay latency acceptable (<2s per 100 calls)
- [ ] No critical errors in production
- [ ] Metrics collected for 1 week
- [ ] Readiness for 100% rollout

**Effort**: 2 engineer-days (distributed over 1 week)

---

## Dependency Graph (DAG)

```
T1.1 (Schema)
  ├─ T1.2 (TraceRecorder)
  │  └─ T1.3 (Integration)
  │      └─ T2.1 (ReplayEngine) ← T1.1
  │          ├─ T2.2 (LLMCallMocker)
  │          ├─ T2.3 (File I/O Stubs)
  │          └─ T2.4 (Replay Testing)
  │              └─ T5.1 (CLI) ← T3.1, T4.1
  │              └─ T5.2 (MCP)
  │
  ├─ T3.1 (DiffAnalyzer)
  │  ├─ T3.2 (Classification)
  │  ├─ T3.3 (Reporting)
  │  └─ T5.3 (Quality-Gate Integration)
  │
  ├─ T4.1 (TraceVariator)
  │  ├─ T4.2 (Batch Replay)
  │  └─ T4.3 (Simulation Analysis)
  │
  └─ T5.4 (Canary Deployment)
```

---

## Risk Assessment

### Technical Risks

| Risk                              | Impact | Probability | Mitigation                                |
| --------------------------------- | ------ | ----------- | ----------------------------------------- |
| Async recorder thread crashes     | High   | Low         | Graceful error handling, separate process |
| Trace file corruption             | High   | Low         | Checksum validation, backup on write      |
| Mock execution diverges from live | Medium | Medium      | Extensive testing, live fallback          |
| Replay latency exceeds target     | Medium | Medium      | Caching, lazy loading                     |

### Operational Risks

| Risk                         | Impact | Probability | Mitigation                           |
| ---------------------------- | ------ | ----------- | ------------------------------------ |
| Disk quota exceeded          | Medium | Medium      | TTL cleanup, quota enforcement       |
| Sensitive data leaked        | High   | Low         | Redaction policy, encryption at rest |
| Complex traces hard to debug | Medium | Medium      | Trace filtering, visualization       |

---

## Quality Gates

### Phase 1 Exit Criteria

- [ ] TraceRecorder tested with <10% overhead
- [ ] Compression achieves >50% reduction
- [ ] Integration with agent runner complete
- [ ] All Phase 1 tests passing

### Phase 2 Exit Criteria

- [ ] Replay engine tested end-to-end
- [ ] 100% output consistency on replay
- [ ] Mock execution <2s per 100 calls
- [ ] All Phase 2 tests passing

### Phase 3 Exit Criteria

- [ ] DiffAnalyzer classification accuracy >95%
- [ ] Reports generated correctly
- [ ] Diff analysis <500ms per trace pair
- [ ] All Phase 3 tests passing

### Phase 4 Exit Criteria

- [ ] Batch replay 50+ traces successfully
- [ ] Simulation analysis generates comparisons
- [ ] Cost/performance comparisons accurate
- [ ] All Phase 4 tests passing

### Phase 5 Exit Criteria

- [ ] CLI commands functional
- [ ] MCP tool registered and callable
- [ ] Quality-gate integration working
- [ ] Canary deployment stable (1 week)
- [ ] Ready for 100% rollout

---

## Success Criteria by Milestone

| Milestone                    | Success Criteria                                       |
| ---------------------------- | ------------------------------------------------------ |
| **End of Phase 1**           | Traces recorded with <10% overhead, compressed >50%    |
| **End of Phase 2**           | Replay works, 100% output consistency, <2s latency     |
| **End of Phase 3**           | Diffs accurate, classification >95%, reports clear     |
| **End of Phase 4**           | Simulation runs 50+ variations, comparisons generated  |
| **End of Phase 5 (Canary)**  | Deployed to 5%, metrics collected, ready for rollout   |
| **End of Phase 5 (Rollout)** | Deployed to 100%, monitoring active, 0 critical issues |

---

## Schedule

```
Week 1 (Phase 1):
  Day 1-2: T1.1 (Schema) + T1.2 (Recorder)
  Day 3-4: T1.2 (continued) + T1.3 (Integration)
  Day 5: Integration testing + buffer

Week 2 (Phase 2):
  Day 1-2: T2.1 (ReplayEngine) + T2.2 (LLMCallMocker)
  Day 3: T2.3 (File I/O Stubs)
  Day 4-5: T2.4 (Replay Testing)

Week 3 (Phase 3):
  Day 1-2: T3.1 (DiffAnalyzer) + T3.2 (Classification)
  Day 3-4: T3.3 (Reporting)
  Day 5: Testing + buffer

Week 4 (Phase 4):
  Day 1-2: T4.1 (TraceVariator) + T4.2 (Batch Replay)
  Day 3-4: T4.3 (Simulation Analysis)
  Day 5: Integration testing

Week 5 (Phase 5 — Integration & Canary):
  Day 1: T5.1 (CLI) + T5.2 (MCP)
  Day 2: T5.3 (Quality-Gate Integration)
  Day 3-5: T5.4 (Canary Deployment & Monitoring)
```

---

## Deliverables Summary

| Task    | Deliverable                               | Type          |
| ------- | ----------------------------------------- | ------------- |
| T1.1    | `thegent/trace/schema.py`                 | Code          |
| T1.1    | `docs/reference/TRACE_FORMAT_SPEC.md`     | Documentation |
| T1.2    | `thegent/trace/recorder.py`               | Code          |
| T1.2    | `thegent/trace/cleanup.py`                | Code          |
| T2.1    | `thegent/trace/replay.py`                 | Code          |
| T2.2    | `thegent/trace/llm_mocker.py`             | Code          |
| T2.3    | `thegent/trace/{file_io,bash}_stubber.py` | Code          |
| T3.1    | `thegent/trace/diff_analyzer.py`          | Code          |
| T4.1    | `thegent/trace/variator.py`               | Code          |
| T4.2    | `thegent/trace/batch_replay.py`           | Code          |
| T5.1    | `thegent/cli/replay_commands.py`          | Code          |
| T5.2    | MCP tool registration                     | Code          |
| T5.3    | `thegent/hooks/qa-replay-regression.sh`   | Code          |
| Phase 1 | Unit tests + integration tests            | Tests         |
| Phase 2 | End-to-end replay tests                   | Tests         |
| Phase 3 | Regression detection tests                | Tests         |
| Phase 5 | CLI tests, MCP tests                      | Tests         |
| Phase 5 | Canary report + metrics                   | Report        |

---

**Document Version**: 1.0
**Last Updated**: 2026-02-18
**Status**: Ready for assignment to implementation team
