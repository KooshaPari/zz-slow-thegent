<DONE>
# Vetter Orchestration Layer — Research and Design
**Date:** 2026-02-20
**Status:** DESIGN — Ready for WL assignment and implementation
**Traces:** WL-090 through WL-099, FR-VET-001 through FR-VET-010
**Author:** Research/Design pass — Vetter Architecture

---

## 1. Executive Summary

The Vetter is a dedicated post-agent verification and validation orchestration layer that
sits **between agent output and downstream action**. Every RunResult produced by an
AgentRunner passes through the VetterOrchestrator before it is accepted, committed,
queued, or escalated.

The Vetter is not a new concept imported from scratch — it is the **natural integration
layer** between four existing thegent subsystems that currently operate independently:

| Existing System                                 | Current Role                | Vetter Integration                       |
| ----------------------------------------------- | --------------------------- | ---------------------------------------- |
| `SemanticFirewall` (WP-28002)                   | Blocks regex-matched output | Promoted to `SafetyVetterCheck`          |
| `HITLApprovalWorkflow` (WL-019)                 | Approve/reject blocked runs | Escalation target for `escalate` verdict |
| `EvidenceStore` / `ComplianceEvidence` (WL-051) | Hash-chained audit store    | Every vetting decision appended          |
| `PromptQueueManager` (WL-014)                   | Queues pending prompts      | Revision re-queue destination            |

The Vetter adds three new primitives: `VetterPolicy`, `VetterCheck`, and
`VetterResult`, plus the `VetterOrchestrator` that orchestrates them. A new
`PostAgentRun` hook fires the vetter automatically after every agent run, and a
`thegent govern vet` CLI command enables manual invocation and inspection.

**Verdict taxonomy:** `approved` | `rejected` | `escalated` | `revision_requested`

---

## 2. Industry Patterns

### 2.1 Output Validation Patterns

**Schema validation** is the lowest-cost check: before any LLM-as-judge call, confirm
the output conforms to an expected structure. Pydantic v2 is the natural fit for
thegent (already used throughout). Structured-output mode in OpenAI/Anthropic APIs
(constrained decoding) reduces schema violations at inference time, but does not
eliminate them — the vetter still validates the deserialized object.

**Hallucination detection** splits into two tiers:

- **Local/deterministic** (free): cross-reference claimed file paths against the
  real filesystem; verify claimed line numbers match actual diffs; check that
  referenced symbols exist in the codebase via AST or ripgrep.
- **LLM-as-judge** (paid, slower): send the original task + agent output to a
  second model with a structured rubric. Scores: factual accuracy, task completion,
  no regressed tests, no introduced secrets.

**Diff size gating** is the simplest safety valve: large diffs (> N lines changed)
correlate with higher regression risk and should require either human approval or
a full test pass before acceptance.

### 2.2 LLM-as-Judge Patterns

LLM-as-judge (G-Eval, MT-Bench, Prometheus, Alpaca Eval) uses a separate,
independent model to grade agent output on a rubric. Key design choices:

- **Model independence:** judge model should differ from producer model to avoid
  systematic blind spots. Claude grades Codex output; GPT-5-mini grades Claude output.
- **Structured scoring:** judge returns a Pydantic object with per-criterion scores
  (1-5 Likert) plus a `pass_verdict` bool. Unstructured "good/bad" answers from
  judges are unreliable.
- **Few-shot anchoring:** provide the judge with 2-3 reference examples (golden
  outputs) to calibrate the scale. Without anchoring, judges drift toward the middle.
- **Confidence-weighted threshold:** `pass_verdict = True` only if `mean_score >=
threshold` AND `min_score >= floor`. The floor prevents a high average masking a
  catastrophic individual criterion failure.
- **Cost control:** LLM-as-judge is triggered only when cheaper checks fail OR when
  the policy's `quality_score_check.always_run = True`.

### 2.3 Constitutional AI / Self-Critique Patterns

Anthropic's Constitutional AI (CAI) has the model critique its own output against a
set of principles, then revise. For agent output vetting, this maps to:

1. Agent produces `RunResult`.
2. Vetter sends output back to the **same** or a **smaller** model with a critique
   prompt ("Does this output satisfy the original task? Does it introduce any
   security issues? Does it regress tests?").
3. The critique is parsed. If it identifies problems, the vetter issues a
   `revision_requested` verdict with the critique embedded as
   `revision_instructions`.
4. The revised output is re-vetted (up to `max_revision_rounds`, default 2).

Self-critique is weaker than judge-model critique (same blind spots) but is cheap
and catches obvious refusals, incomplete implementations, and hallucinated imports.

### 2.4 Red Team / Blue Team Agent Patterns

Red-team/blue-team (RTBT) patterns assign adversarial agents that actively try to
break or bypass the output being evaluated:

- **Red agent:** given the task and the proposed output, attempts to construct a
  counter-example that breaks the output's stated behavior.
- **Blue agent:** defends the output, producing a rebuttal.
- **Arbiter:** scores the exchange and issues a verdict.

This is computationally expensive and is reserved for `escalation_lane:
adversarial_review` — high-stakes production runs where correctness is critical.
The pattern is supported architecturally but gated behind an explicit policy flag.

### 2.5 Regression Testing as Vetting

Running the project's existing test suite against the modified files before accepting
the agent's diff is the most reliable form of output validation for code-writing
agents. The `TestPassVetterCheck` captures this: it runs `pytest` (or the project's
configured test runner) scoped to the files the agent changed, and rejects if any
test fails.

Similarly, `RuffVetterCheck` runs `ruff check` on modified files. Both checks use
the project's existing toolchain, making them zero-config for most thegent projects.

---

## 3. thegent Vetter Architecture

### 3.1 VetterPolicy

Defines **what to check** and the response on failure. Stored as a JSON contract
in `contracts/vetter/` and resolved through `FederatedPolicyManager` for
org/project/env inheritance.

```
VetterPolicy
  policy_id: str                         # e.g. "default", "production-strict"
  checks: list[VetterCheck]              # ordered; earlier checks short-circuit if blocking
  on_fail: "reject" | "escalate" | "revision_requested"
  escalation_lane: str                   # HITL lane name; used when on_fail == "escalate"
  max_revision_rounds: int               # default 2; limits self-critique loops
  evidence_kind: EvidenceKind            # appended to EvidenceStore on each decision
  require_all_checks: bool               # default True; False = first passing check wins
```

### 3.2 VetterCheck — Individual Checks

All checks conform to a common interface: `run(result: RunResult) -> CheckOutcome`.
`CheckOutcome` carries `passed: bool`, `check_id: str`, `reason: str`, and optional
`revision_hint: str`.

#### SchemaVetterCheck

Validates that the agent's output (parsed as JSON or a named Pydantic model)
conforms to the expected schema.

- `schema_model: type[BaseModel]` — Pydantic model class
- `target: "stdout" | "stderr" | "combined"` — which stream to parse
- Raises `VetterCheckError` (not caught silently) if JSON parsing fails entirely.
- `passed = False` if `model_validate` raises `ValidationError`.
- Includes validation errors in `reason`.

#### DiffSizeVetterCheck

Rejects diffs exceeding a lines-changed threshold.

- `max_lines_changed: int` — default 500
- `count_method: "lines" | "hunks"` — default `"lines"`
- Parses unified diff from stdout using `difflib` (no subprocess).
- Designed to gate massive refactors that bypass human review.

#### SafetyVetterCheck

Promotes the existing `SemanticFirewall` (WP-28002) into the Vetter chain. Adds
thegent-specific patterns to the existing regex set:

- PII patterns (email, phone, SSN regex)
- Secret patterns (API keys, tokens — same patterns as `gitleaks` config)
- Forbidden shell commands (`rm -rf /`, `kill -9` agent processes)
- Agent-specific injection strings (`$defer SYSTEM:`, `$exec`)

Reports violations with `action` (`block` → `reject`, `warn` → `revision_requested`).

#### QualityScoreVetterCheck

LLM-as-judge scoring via a configurable model.

- `judge_model: str` — e.g., `"gpt-5-mini"` or `"claude-haiku-4.5"`
- `rubric: list[dict]` — list of `{criterion: str, weight: float}` dicts
- `pass_threshold: float` — weighted mean must exceed this (default 0.75)
- `min_criterion_score: float` — no single criterion below this (default 0.5)
- `always_run: bool` — default False; if False, only runs when cheaper checks pass
- Calls the judge via `thegent free` or direct `httpx` to the model API.
- Returns `passed`, `scores_by_criterion`, and `revision_hint` (judge's critique).

#### TestPassVetterCheck

Runs the project's test suite scoped to modified files.

- `test_runner: str` — default `"pytest"`
- `scope: "changed_files" | "full"` — default `"changed_files"`
- `timeout_seconds: int` — default 120
- Extracts changed files from the diff in `RunResult.stdout`.
- Runs `pytest {changed_files} --tb=short -q` via subprocess.
- `passed = (returncode == 0)`.
- On failure, includes pytest short output in `reason`.

#### RuffVetterCheck

Runs `ruff check` on files touched by the agent.

- `fix_mode: bool` — default False; if True, runs `--fix` and checks if violations remain
- `select_rules: list[str]` — default `[]` (inherit from project `ruff.toml`)
- Extracts changed `.py` files from diff.
- `passed = (ruff returncode == 0)`.

### 3.3 VetterResult

Returned by `VetterOrchestrator.evaluate()`.

```
VetterResult
  verdict: "approved" | "rejected" | "escalated" | "revision_requested"
  session_id: str
  run_id: str
  policy_id: str
  failed_checks: list[str]              # check_id values for failed checks
  passed_checks: list[str]
  evidence: ComplianceEvidence          # appended to EvidenceStore; tamper-evident
  revision_instructions: str | None     # populated when verdict == "revision_requested"
  escalation_event_id: str | None       # HITL await_approval event_id if escalated
  evaluated_at_utc: str
  duration_ms: int
```

### 3.4 VetterOrchestrator

Central coordinator. Lives in `src/thegent/governance/vetter.py`.

```
VetterOrchestrator
  __init__(
    session_dir: Path,
    evidence_store: EvidenceStore,
    hitl_workflow: HITLApprovalWorkflow,
    event_log: GovernanceEventLog,
    prompt_queue: PromptQueueManager,
    federated_policy: FederatedPolicyManager,
  )

  evaluate(
    result: RunResult,
    policy: VetterPolicy,
    run_context: RunContext,
  ) -> VetterResult
```

**Internal flow:**

```
evaluate()
  1. Resolve effective policy via FederatedPolicyManager (jurisdiction overlays applied)
  2. Run checks in order: for each check in policy.checks:
       outcome = check.run(result)
       record outcome
       if not outcome.passed and policy.require_all_checks: break
  3. Aggregate verdict:
       all passed → "approved"
       any failed AND on_fail == "reject" → "rejected"
       any failed AND on_fail == "escalate" → trigger HITL, verdict = "escalated"
       any failed AND on_fail == "revision_requested" → build revision_instructions, verdict = "revision_requested"
  4. Append ComplianceEvidence to EvidenceStore (kind="agent_decision")
  5. Emit governance_events.jsonl entry (event_type="vetter_decision")
  6. If "escalated": call HITLApprovalWorkflow.request_approval()
  7. If "revision_requested": enqueue revised prompt via PromptQueueManager
  8. Return VetterResult
```

**Revision prompt construction:**

The revised prompt prepends structured critique to the original prompt:

```
[VETTER REVISION REQUEST]
Round: {n} of {max}
Failed checks: {failed_check_ids}
Instructions:
{concatenated revision_hints from failed checks}

[ORIGINAL TASK]
{original prompt}
```

This is injected into `PromptQueueManager` as a `pending` item with
`metadata.vetter_revision = True` and `metadata.original_run_id = run_id`.

---

## 4. Integration Map

### 4.1 HITLManager / HITLApprovalWorkflow

**When escalate verdict fires:**

1. `VetterOrchestrator.evaluate()` calls
   `HITLApprovalWorkflow.request_approval(run_id, action, context)` (or emits an
   `await_approval` event directly via `GovernanceEventLog`).
2. The escalation lane is set to `policy.escalation_lane` (e.g., `"critical"`,
   `"production-safety"`).
3. Existing `thegent govern approve <run_id>` and `thegent govern reject <run_id>`
   CLI/MCP commands resolve the escalation — no new commands required.
4. On `approved`: the original `RunResult` is accepted downstream.
5. On `rejected`: the `RunResult` is discarded; a `revision_requested` re-queue
   may optionally follow (configurable in policy).

**Escalation event shape added to governance_events.jsonl:**

```json
{
  "event_type": "vetter_escalation",
  "event_id": "vet_<hex8>",
  "run_id": "<run_id>",
  "session_id": "<session_id>",
  "policy_id": "<policy_id>",
  "failed_checks": ["<check_id>", ...],
  "escalation_lane": "<lane>",
  "status": "pending",
  "emitted_at_utc": "<iso>"
}
```

### 4.2 GovernanceEventLog

Every vetting decision emits an event. Two new `event_type` values:

- `"vetter_decision"` — fires on every evaluate() call; records verdict, checks,
  durations, policy_id.
- `"vetter_escalation"` — fires when verdict is `"escalated"`; creates a pending
  approval that the existing HITL resolution path handles.

The `GovernanceEventLog.list_pending_approvals()` query already handles `status ==
"pending"` filtering, so vetter escalations surface in `thegent govern list` without
modification.

### 4.3 EvidenceStore / ComplianceEvidence

Every `VetterResult` appends a `ComplianceEvidence` record:

```
kind: "agent_decision"
actor: "vetter_orchestrator"
resource: "session:{session_id}/run:{run_id}"
payload: {
  "policy_id": "...",
  "verdict": "...",
  "failed_checks": [...],
  "passed_checks": [...],
  "duration_ms": ...,
}
```

The hash chain in `EvidenceStore` ensures tamper-evident vetting history. This
satisfies EU AI Act Art. 14 (human oversight logs) and SOC-2 CC7.1 (system
monitoring) via the existing `ComplianceExporter` — no changes to the exporter
needed; "agent_decision" is already a valid `EvidenceKind`.

### 4.4 PromptQueueManager

When verdict is `revision_requested`:

1. `VetterOrchestrator` constructs the revised prompt string (see Section 3.4).
2. Calls `PromptQueueManager.enqueue(prompt=revised_prompt, project_path=...,
metadata={"vetter_revision": True, "original_run_id": run_id, "round": n})`.
3. The revised task is picked up by the next `do_next` cycle.
4. After the agent completes the revision, the `PostAgentRun` hook fires the vetter
   again — the revision counter increments, and on exhausting `max_revision_rounds`,
   the policy's `on_fail` action applies (reject or escalate, never infinite loop).

### 4.5 CapabilityIndex

For `QualityScoreVetterCheck` with `judge_model: "auto"`, the vetter uses
`CapabilityIndex.recommend(task="quality scoring for code output")` to select the
best available judge agent. This avoids hardcoding a specific model and adapts to
whatever models are registered in the agent registry.

### 4.6 FederatedPolicyManager

`VetterPolicy` JSON files are stored at:

```
contracts/vetter/<policy_id>.json
```

For namespace-specific overrides:

```
<base_dir>/<org>/<project>/<env>/vetter_<policy_id>.json
```

`VetterOrchestrator` resolves the effective policy by calling
`FederatedPolicyManager.resolve_policy(ns, policy_id)` before running checks.
Jurisdiction overlays (EU-AI-ACT forces `on_fail = "escalate"` for critical checks;
US-SEC forces `evidence_kind = "agent_decision"` with retention ≥ 2555 days) are
applied via `apply_jurisdiction_constraints()`.

---

## 5. Hook Pipeline Integration

### 5.1 New Hook: post-agent-run-vetter

**File:** `hooks/post-agent-run-vetter.sh`
**Event:** `PostAgentRun` (new event type)
**Hook config entry:**

```yaml
hooks:
  post-agent-run-vetter:
    scope: all
    timeout: 120
    event: PostAgentRun
    description: "Run VetterOrchestrator on agent output before downstream action (WL-090)"
```

**Shell hook behavior:**

```bash
#!/usr/bin/env bash
# hooks/post-agent-run-vetter.sh
# Fires VetterOrchestrator on each completed agent run.
# Env: THGENT_SESSION_ID, THGENT_RUN_ID, THGENT_VETTER_POLICY (default: "default")
set -euo pipefail
SESSION_ID="${THGENT_SESSION_ID:?}"
RUN_ID="${THGENT_RUN_ID:?}"
POLICY="${THGENT_VETTER_POLICY:-default}"
exec thegent govern vet "$RUN_ID" --policy "$POLICY" --session "$SESSION_ID"
```

The hook exits non-zero on `rejected` verdict (blocking downstream action) and
zero on `approved` or `escalated` (pending human resolution) or
`revision_requested` (re-queued; not blocking the hook itself).

### 5.2 New CLI Command: thegent govern vet

Added to `src/thegent/cli/apps/govern.py`:

```
thegent govern vet <run_id>
  --policy  TEXT     Vetter policy ID [default: default]
  --session TEXT     Session directory path [default: auto-detect]
  --dry-run          Run checks but do not write evidence or emit events
  --json             Output VetterResult as JSON
```

**Implementation path:**

- New `govern_vet_impl()` in `cli/commands/impl.py`
- Instantiates `VetterOrchestrator` with session-local deps
- Resolves `RunResult` from `governance_events.jsonl` by `run_id`
- Calls `evaluate()` and prints result

**MCP tool:** `thegent_govern_vet` — same interface as `thegent_govern_approve` and
`thegent_govern_reject`. Registered in `mcp/server.py` alongside existing govern tools.

### 5.3 PostAgentRun Event Registration

The `PostAgentRun` hook event fires in `AgentRunner` subclasses immediately after
`run()` returns a `RunResult` and before `_process_output_deferrals()`. This
ordering is important: deferrals inject into the queue, which is also used by the
vetter for revision re-queues — vetting must complete first.

Concrete injection points:

- `src/thegent/agents/in_process_runner.py` — after `result = self.run(...)`
- `src/thegent/agents/cursor_api_runner.py` — after subprocess completes
- `src/thegent/agents/codex_proxy.py` — after response assembled
- `src/thegent/orchestration/unified_worker.py` — in the worker task completion path

Each calls `_dispatch_post_agent_run_hook(result, run_id, session_id)` — a shared
utility in `hooks/lib/post-agent-run.sh` (shell side) and
`thegent.governance.vetter._fire_post_agent_run_hook` (Python side).

---

## 6. Implementation Phases

### Phase 1 — Core Vetter (WL-090, WL-091, WL-092)

**Effort:** M (4-8h) | **Wall clock:** ~20 min with agent-led execution

| Task                                                                     | WL     | File(s)                           |
| ------------------------------------------------------------------------ | ------ | --------------------------------- |
| `VetterPolicy`, `VetterCheck` ABC, `VetterResult` dataclasses            | WL-090 | `governance/vetter.py`            |
| `SchemaVetterCheck`, `DiffSizeVetterCheck`, `SafetyVetterCheck`          | WL-091 | `governance/vetter.py`            |
| `VetterOrchestrator.evaluate()` (no HITL/queue yet, just approve/reject) | WL-092 | `governance/vetter.py`            |
| Unit tests (60+ test cases)                                              | WL-090 | `tests/governance/test_vetter.py` |

### Phase 2 — HITL + Evidence Integration (WL-093, WL-094)

**Effort:** M (4-8h)

| Task                                                                           | WL     | File(s)                                            |
| ------------------------------------------------------------------------------ | ------ | -------------------------------------------------- |
| Escalation path: `HITLApprovalWorkflow` integration, `vetter_escalation` event | WL-093 | `governance/vetter.py`, `governance/hitl.py`       |
| `EvidenceStore` append on every verdict, `vetter_decision` governance event    | WL-094 | `governance/vetter.py`, `governance/compliance.py` |
| Integration tests with real `EvidenceStore`                                    | WL-094 | `tests/governance/test_vetter_integration.py`      |

### Phase 3 — Quality Score + Revision Queue (WL-095, WL-096)

**Effort:** M (4-8h)

| Task                                                         | WL     | File(s)                                        |
| ------------------------------------------------------------ | ------ | ---------------------------------------------- |
| `QualityScoreVetterCheck` (LLM-as-judge via `thegent free`)  | WL-095 | `governance/vetter.py`                         |
| Revision prompt construction + `PromptQueueManager` re-queue | WL-096 | `governance/vetter.py`, `core/prompt_queue.py` |
| Round counter / max_revision_rounds enforcement              | WL-096 | `governance/vetter.py`                         |

### Phase 4 — Test + Lint Checks (WL-097)

**Effort:** S (1-3h)

| Task                                                   | WL     | File(s)                           |
| ------------------------------------------------------ | ------ | --------------------------------- |
| `TestPassVetterCheck` (pytest scoped to changed files) | WL-097 | `governance/vetter.py`            |
| `RuffVetterCheck` (ruff check on changed `.py` files)  | WL-097 | `governance/vetter.py`            |
| 20+ tests covering pass/fail/timeout paths             | WL-097 | `tests/governance/test_vetter.py` |

### Phase 5 — Hook + CLI Integration (WL-098)

**Effort:** M (4-8h)

| Task                                                     | WL     | File(s)                                                                               |
| -------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------- |
| `post-agent-run-vetter.sh` hook + hook-config.yaml entry | WL-098 | `hooks/post-agent-run-vetter.sh`, `hooks/hook-config.yaml`                            |
| `thegent govern vet` CLI command + `govern_vet_impl()`   | WL-098 | `cli/apps/govern.py`, `cli/commands/impl.py`                                          |
| `thegent_govern_vet` MCP tool registration               | WL-098 | `mcp/server.py`                                                                       |
| `PostAgentRun` hook dispatch wired into 3 runner classes | WL-098 | `agents/in_process_runner.py`, `agents/cursor_api_runner.py`, `agents/codex_proxy.py` |

### Phase 6 — Federated Policy + Contracts (WL-099)

**Effort:** S (1-3h)

| Task                                                                   | WL     | File(s)                                     |
| ---------------------------------------------------------------------- | ------ | ------------------------------------------- |
| `contracts/vetter/default.json` base policy                            | WL-099 | `contracts/vetter/default.json`             |
| `contracts/vetter/production-strict.json` (escalate on any failure)    | WL-099 | `contracts/vetter/production-strict.json`   |
| `FederatedPolicyManager` integration: jurisdiction overlay application | WL-099 | `governance/vetter.py`                      |
| EU-AI-ACT overlay test: critical checks force `on_fail = "escalate"`   | WL-099 | `tests/governance/test_vetter_federated.py` |

---

## 7. Proposed WL Items

| WL ID  | Title                                                                                                 | Phase | Priority | Effort | Depends On             |
| ------ | ----------------------------------------------------------------------------------------------------- | ----- | -------- | ------ | ---------------------- |
| WL-090 | Vetter Core: VetterPolicy, VetterCheck, VetterResult dataclasses + unit tests                         | 1     | P1       | M      | WL-019, WL-051         |
| WL-091 | Vetter Checks Phase 1: Schema, DiffSize, Safety                                                       | 1     | P1       | S      | WL-090                 |
| WL-092 | VetterOrchestrator: evaluate() — approve/reject path only                                             | 1     | P1       | M      | WL-090, WL-091         |
| WL-093 | Vetter HITL Escalation: escalated verdict + HITL await_approval integration                           | 2     | P1       | M      | WL-092, WL-019         |
| WL-094 | Vetter Evidence: EvidenceStore append + vetter_decision governance event                              | 2     | P1       | S      | WL-092, WL-051         |
| WL-095 | QualityScoreVetterCheck: LLM-as-judge via configurable model                                          | 3     | P2       | M      | WL-092, WL-034         |
| WL-096 | Vetter Revision Queue: revision_requested verdict + PromptQueueManager re-queue                       | 3     | P2       | M      | WL-092, WL-014         |
| WL-097 | Vetter Code Checks: TestPassVetterCheck + RuffVetterCheck                                             | 4     | P1       | S      | WL-092                 |
| WL-098 | Vetter Hook + CLI: post-agent-run hook, govern vet command, MCP tool, runner wiring                   | 5     | P1       | M      | WL-092, WL-093, WL-094 |
| WL-099 | Vetter Contracts + Federation: default/production-strict policies, FederatedPolicyManager integration | 6     | P2       | S      | WL-098, WL-020         |

---

## 8. Acceptance Criteria Summary

### FR-VET-001 (WL-090)

`VetterPolicy` SHALL define `checks`, `on_fail`, `escalation_lane`, and `max_revision_rounds`.
`VetterCheck` SHALL define a `run(result: RunResult) -> CheckOutcome` interface.
`VetterResult` SHALL carry `verdict`, `failed_checks`, `evidence`, and `revision_instructions`.

### FR-VET-002 (WL-091)

`SafetyVetterCheck` SHALL detect all `SemanticFirewall` patterns PLUS secret and PII patterns.
`DiffSizeVetterCheck` SHALL reject diffs exceeding `max_lines_changed` (configurable, default 500).
`SchemaVetterCheck` SHALL validate agent JSON output against a Pydantic model.

### FR-VET-003 (WL-092)

`VetterOrchestrator.evaluate()` SHALL run all checks in order, aggregate verdict per policy
`on_fail`, and return a `VetterResult`. It SHALL NOT silently catch check errors.

### FR-VET-004 (WL-093)

When verdict is `"escalated"`, the orchestrator SHALL emit a `vetter_escalation` event to
`governance_events.jsonl` with `status: "pending"`. The event SHALL appear in
`thegent govern list` output without CLI changes.

### FR-VET-005 (WL-094)

Every `VetterResult` SHALL append a `ComplianceEvidence` record (kind=`"agent_decision"`)
to the session's `EvidenceStore`. The `verify_integrity()` check SHALL pass after appending.

### FR-VET-006 (WL-095)

`QualityScoreVetterCheck` SHALL call a configurable judge model, parse structured scores,
and apply `pass_threshold` and `min_criterion_score`. It SHALL return `revision_hint` from
the judge's critique when `passed = False`.

### FR-VET-007 (WL-096)

When verdict is `"revision_requested"`, the orchestrator SHALL enqueue a revised prompt via
`PromptQueueManager` with `metadata.vetter_revision = True` and `metadata.round = n`.
After `max_revision_rounds` exhaustion, the orchestrator SHALL apply `policy.on_fail`.

### FR-VET-008 (WL-097)

`TestPassVetterCheck` SHALL run `pytest` scoped to files changed in the agent's diff.
`RuffVetterCheck` SHALL run `ruff check` on modified `.py` files. Both SHALL fail fast
(non-zero exit = `passed = False`) without silent error handling.

### FR-VET-009 (WL-098)

`hooks/post-agent-run-vetter.sh` SHALL fire after every `AgentRunner.run()` completes.
`thegent govern vet <run_id>` SHALL be available as a CLI command and MCP tool.
The hook SHALL exit non-zero on `rejected` verdict to block downstream action.

### FR-VET-010 (WL-099)

`VetterPolicy` SHALL be resolvable via `FederatedPolicyManager` namespace hierarchy.
EU-AI-ACT jurisdiction overlay SHALL force `on_fail = "escalate"` for any failed
safety or quality check. The default policy at `contracts/vetter/default.json`
SHALL include `SafetyVetterCheck` and `DiffSizeVetterCheck` at minimum.

---

## 9. File Map

```
src/thegent/governance/
  vetter.py                          # VetterPolicy, VetterCheck (all variants), VetterResult,
                                     # VetterOrchestrator — NEW (WL-090 through WL-099)

tests/governance/
  test_vetter.py                     # Unit tests — NEW
  test_vetter_integration.py         # Integration with EvidenceStore, HITLWorkflow — NEW
  test_vetter_federated.py           # FederatedPolicyManager + jurisdiction overlays — NEW

hooks/
  post-agent-run-vetter.sh           # PostAgentRun hook — NEW
  hook-config.yaml                   # post-agent-run-vetter entry ADDED

contracts/vetter/
  default.json                       # Base vetter policy — NEW
  production-strict.json             # Strict escalate-on-any-failure policy — NEW

src/thegent/cli/apps/govern.py       # thegent govern vet command ADDED
src/thegent/cli/commands/impl.py     # govern_vet_impl() ADDED
src/thegent/mcp/server.py            # thegent_govern_vet MCP tool ADDED
src/thegent/agents/in_process_runner.py    # PostAgentRun dispatch ADDED
src/thegent/agents/cursor_api_runner.py    # PostAgentRun dispatch ADDED
src/thegent/agents/codex_proxy.py          # PostAgentRun dispatch ADDED
src/thegent/orchestration/unified_worker.py  # PostAgentRun dispatch ADDED
```

---

## 10. Open Questions

1. **judge_model transport:** Should `QualityScoreVetterCheck` call the judge via
   `thegent free` subprocess (simple, consistent) or directly via `httpx` to the
   model API (faster, fewer process forks)? Recommendation: `thegent free` subprocess
   first; optimize to direct call in a follow-on.

2. **PostAgentRun event registration:** Claude Code SDK has a `Stop` hook event but
   not a `PostAgentRun` event. How does the hook dispatcher surface per-run events
   from sub-runners? Recommendation: add `PostAgentRun` to `hook-config.yaml` event
   vocabulary and fire it from a shared utility method in `AgentRunner` base.

3. **Revision prompt size:** Large agent outputs + vetter critique may exceed model
   context windows when re-queued. Recommendation: truncate `revision_instructions`
   to 2000 chars and include a `revision_context_truncated: true` flag in metadata.

4. **Adversarial reviewer:** Red-team/blue-team arbiter pattern (Section 2.4) is
   architecturally supported but not scheduled. Assign to WL-1xx range when
   `QualityScoreVetterCheck` (WL-095) is validated and the cost is understood.

5. **Vetter bypass:** Should there be an explicit `THGENT_VETTER_BYPASS=1` env var
   for local development? Recommendation: yes, but it MUST be logged as a
   `vetter_decision` event with `verdict = "bypassed"` so the bypass is auditable.
