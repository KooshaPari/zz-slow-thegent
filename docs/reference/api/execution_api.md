# execution API Reference

> **Source**: `src/thegent/execution.py`

Execution run metadata and registry for thegent orchestration.

---

## AgentSource

Source of the agent process for session registry (WP-9001).

**Inherits from**: `StrEnum`

---

## AuditEntry

Audit trail entry for session actions (WP-9005).

**Inherits from**: `BaseModel`

---

## AuditRegistry

Manages the session audit trail (WP-9005).

### Methods

#### AuditRegistry.**init**

```python
__init__(self: Any, audit_path: Path)
```

---

#### AuditRegistry.record

```python
record(self: Any, entry: AuditEntry)
```

Record an action in the audit trail.

---

---

## Auditor

Provides integrity verification for the run registry.

### Methods

#### Auditor.**init**

```python
__init__(self: Any, registry_path: Path)
```

---

#### Auditor.generate_maif_artifact

```python
generate_maif_artifact(self: Any, run: RunMeta, output: Any)
```

Generate a signed MAIF artifact for a run (WP-3002).

---

#### Auditor.persist_maif_artifact

```python
persist_maif_artifact(self: Any, session_dir: Path, artifact: MAIFArtifact)
```

Persist a MAIF artifact to the artifacts directory (WP-3002).

---

#### Auditor.sign_run

```python
sign_run(self: Any, run: RunMeta)
```

Generate a cryptographic signature for a run record.

---

#### Auditor.verify_registry

```python
verify_registry(self: Any)
```

Verify the integrity of all records in the registry, including the hash chain.

ROB-006: Hash chain integrity verification on audit read - Detect tampered audit logs.

---

---

## CalibrationRegistry

WP-4008: Persists calibration factors and curves for agents (G-GP-09).

### Methods

#### CalibrationRegistry.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### CalibrationRegistry.get_factor

```python
get_factor(self: Any, agent: str)
```

Return the persisted calibration factor for an agent.

---

#### CalibrationRegistry.update_agent

```python
update_agent(self: Any, agent: str, factor: float, sample_size: int)
```

Persist a new calibration factor for an agent.

---

---

## ChatEntry

Structured chat message for session history (WP-9003).

**Inherits from**: `BaseModel`

---

## ChatHistory

Manages structured conversation history for a session (WP-9003).

### Methods

#### ChatHistory.**init**

```python
__init__(self: Any, chat_path: Path)
```

---

#### ChatHistory.append

```python
append(self: Any, entry: ChatEntry)
```

Append a new chat entry to the session log.

---

#### ChatHistory.load

```python
load(self: Any, limit: Any)
```

Load chat history from the session log.

---

---

## CheckpointMeta

Metadata for a DAG/state checkpoint.

**Inherits from**: `BaseModel`

---

## CheckpointRegistry

Manages persistence and retrieval of state checkpoints.

### Methods

#### CheckpointRegistry.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### CheckpointRegistry.create_checkpoint

```python
create_checkpoint(self: Any, reason: str, dag_content: str, owner: str)
```

Record a new checkpoint.

---

#### CheckpointRegistry.get_checkpoint

```python
get_checkpoint(self: Any, checkpoint_id: str)
```

Retrieve a specific checkpoint.

---

#### CheckpointRegistry.list_checkpoints

```python
list_checkpoints(self: Any, limit: int)
```

List recent checkpoints.

---

---

## CircuitBreakerRegistry

Tracks failures and manages circuit states for models/agents.

ROB-003: Poison pill detection for repeated identical failures - Stop infinite retry loops.

### Methods

#### CircuitBreakerRegistry.**init**

```python
__init__(self: Any, session_dir: Path, threshold: int, window_s: int, recovery_s: int)
```

---

#### CircuitBreakerRegistry.is_open

```python
is_open(self: Any, target: str, category: str)
```

Check if the circuit for a target in a category is open (blocked).

---

#### CircuitBreakerRegistry.record_failure

```python
record_failure(self: Any, target: str, category: str, error_message: Any)
```

Record a failure for a target in a specific category.

ROB-003: Detects poison pills (repeated identical failures) and prevents infinite retry loops.

---

---

## ConcurrencyController

WP-5001: Advanced resource-based adaptive concurrency controller.

Features:

- Extended resource indices (CPU, memory, FD, network, disk, GPU, etc.)
- Prediction engine for forecasting resource needs
- Harness card modeling (codex/claude/droid usage profiles)
- Bottleneck detection and analysis
- Speculative execution strategies
- Work chunking and parallelization

### Methods

#### ConcurrencyController.**init**

```python
__init__(self: Any, session_dir: Path, max_concurrency: int, use_load_based: bool)
```

---

#### ConcurrencyController.acquire

```python
acquire(self: Any, lane: str, harness_type: Any)
```

Acquire a concurrency slot using advanced resource-based limits.

Uses:

- Extended resource monitoring (CPU, memory, FD, network, disk, etc.)
- Prediction engine for forecasting
- Harness card modeling for harness-specific limits
- Bottleneck detection
- 5% minimum buffer (hard limit, prevents crashes)
- 15% discretionary buffer (soft limit, allows scaling)

---

#### ConcurrencyController.get_bottlenecks

```python
get_bottlenecks(self: Any)
```

Get current bottlenecks and slow points.

---

---

## ContinuityWatchdog

WP-5005: Background watchdog for stale ownership and automatic handoffs.

ROB-012: Continuity watchdog with escalation on stale ownership - No orphaned critical tasks.

### Methods

#### ContinuityWatchdog.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### ContinuityWatchdog.check_and_escalate_stale_critical

```python
check_and_escalate_stale_critical(self: Any, max_idle_s: int)
```

ROB-012: Check for stale critical tasks and escalate if needed.

Returns list of escalated sessions.

---

#### ContinuityWatchdog.scan_stale_sessions

```python
scan_stale_sessions(self: Any, max_idle_s: int)
```

Scan for sessions with no activity for max_idle_s.

---

#### ContinuityWatchdog.trigger_auto_handoff

```python
trigger_auto_handoff(self: Any, session_id: str, _backup_owner: str)
```

Automatically trigger a handoff for a stale session (WP-5006).

---

---

## DLQManager

WP-Y2: Dead-Letter Queue (DLQ) for permanently failing items.

### Methods

#### DLQManager.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### DLQManager.enqueue

```python
enqueue(self: Any, run_meta: RunMeta, error: str)
```

Add a failing run to the DLQ.

---

#### DLQManager.list_items

```python
list_items(self: Any, status: Any, run_id: Any)
```

List items in the DLQ with optional filtering.

---

#### DLQManager.resolve

```python
resolve(self: Any, run_id: str, resolution: str)
```

Mark a DLQ item as resolved (e.g. replayed, fixed).

---

---

## DeferralQueue

WP-5004: Manages non-critical tasks deferred during burst load.

### Methods

#### DeferralQueue.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### DeferralQueue.defer

```python
defer(self: Any, run_id: str, reason: str, eta_s: int)
```

Defer a task with an estimated time to resume.

---

---

## EscalationQueue

WP-3008: Governance queue for blocked decisions with SLA tracking.

### Methods

#### EscalationQueue.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### EscalationQueue.add

```python
add(self: Any, run_id: str, reason: str, sla_minutes: int, owner: Any, agent: Any, lane: Any, priority: int)
```

Add a blocked run to the escalation queue.

---

#### EscalationQueue.list_pending

```python
list_pending(self: Any, past_sla_only: bool, limit: int)
```

List escalation items. If past_sla_only, return only items past escalate_by.

---

#### EscalationQueue.resolve

```python
resolve(self: Any, run_id: str, resolution: str)
```

Mark an escalation item as resolved. Returns True if found and updated.

---

---

## EvidenceLinter

WP-2007: Checks evidence struct completeness and consistency.

### Methods

#### EvidenceLinter.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### EvidenceLinter.lint

```python
lint(self: Any, csm: Any)
```

Verify CSM evidence is complete based on phase.

---

---

## FreshnessValidator

WP-4005: Detects stale state and enforces refresh logic.

### Methods

#### FreshnessValidator.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### FreshnessValidator.is_stale

```python
is_stale(self: Any, path: Path, max_age_s: int)
```

Check if a file or registry is stale.

---

#### FreshnessValidator.validate_action

```python
validate_action(self: Any, run_id: str, context_files: list[Path])
```

Validate if the action is safe to perform based on context freshness.

---

---

## HandoffManager

WP-4006/9004: Manages shift handoffs and continuity snapshots with enforcement.

### Methods

#### HandoffManager.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### HandoffManager.confirm_handoff

```python
confirm_handoff(self: Any, snapshot_id: str, incoming_owner: str, confidence: float)
```

WP-9004/12005: Incoming owner confirms handoff completeness with confidence.

---

#### HandoffManager.create_snapshot

```python
create_snapshot(self: Any, owner: str, run_ids: list[str])
```

Create a continuity snapshot for a handoff.

---

#### HandoffManager.is_handoff_enforced

```python
is_handoff_enforced(self: Any, run_id: str)
```

WP-9004: Check if a run is blocked by a pending handoff confirmation.

---

#### HandoffManager.verify_integrity

```python
verify_integrity(self: Any, snapshot_id: str)
```

Verify the integrity of a handoff snapshot.

---

---

## IdempotencyManager

WP-1003: Ensures idempotent execution using 4-tuple keys.

### Methods

#### IdempotencyManager.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### IdempotencyManager.check_and_record

```python
check_and_record(self: Any, registry: RunRegistry, key: str)
```

Check if key exists in registry; return True if already executed.

---

#### IdempotencyManager.generate_key

```python
generate_key(self: Any, run_id: str, step_index: int, action_type: str, content: str)
```

Generate a 4-tuple idempotency key (run_id, step, action, hash).

---

---

## InteractivityMode

Interactivity mode of the session (WP-9002).

**Inherits from**: `StrEnum`

---

## InterruptionTracker

WP-4004: Fatigue tracking and interruption controls.

### Methods

#### InterruptionTracker.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### InterruptionTracker.get_fatigue_score

```python
get_fatigue_score(self: Any, window_s: int)
```

Calculate fatigue score based on recent interruptions (0.0-1.0).

---

#### InterruptionTracker.record_interruption

```python
record_interruption(self: Any, run_id: str, severity: str)
```

Record an agent interruption event.

---

---

## KPIManager

WP-Y7: TRAFFIC KPI framework (10-metric).

### Methods

#### KPIManager.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### KPIManager.get_kpis

```python
get_kpis(self: Any)
```

Calculate the 10 core KPIs for the dashboard.

---

---

## LaneController

WP-1002: Priority and urgency lane model for task management.

### Methods

#### LaneController.**init**

```python
__init__(self: Any, session_dir: Path, capacity: int)
```

---

#### LaneController.check_capacity

```python
check_capacity(self: Any, lane: str)
```

Check if a lane has capacity to run (starvation prevention).

---

#### LaneController.get_lane_priority

```python
get_lane_priority(self: Any, lane: str)
```

Return numeric priority for a lane (lower is higher priority).

---

#### LaneController.sort_tasks

```python
sort_tasks(self: Any, tasks: list[dict[(str, Any)]])
```

Sort tasks by lane priority and then by creation time.

---

---

## LoadClassifier

WP-5002: Classifies system load and detects burst conditions.

### Methods

#### LoadClassifier.**init**

```python
__init__(self: Any, session_dir: Path, spike_threshold: Any, surge_threshold: Any)
```

---

#### LoadClassifier.get_load_level

```python
get_load_level(self: Any)
```

Return current load level: normal, high, burst.

Uses resource-based thresholds when load-based limits are enabled:

- Normal: Below 70% of resource-based limit
- High: 70-95% of resource-based limit (15% discretionary buffer)
- Burst: Above 95% of resource-based limit (5% minimum buffer)

---

---

## MAIFArtifact

WP-3002: Model AI Information Format (MAIF) for signed artifacts.

**Inherits from**: `BaseModel`

---

## MessageEntry

Pending message in the session queue (WP-9004).

**Inherits from**: `BaseModel`

---

## MessageRegistry

Manages the pending message queue for a session (WP-9004).

### Methods

#### MessageRegistry.**init**

```python
__init__(self: Any, messages_path: Path)
```

---

#### MessageRegistry.list_pending

```python
list_pending(self: Any)
```

List all pending messages in the queue.

---

#### MessageRegistry.mark_processed

```python
mark_processed(self: Any, msg_id: str, status: str)
```

Mark a message as processed (appends an update event).

---

#### MessageRegistry.push

```python
push(self: Any, entry: MessageEntry)
```

Add a message to the queue.

---

---

## OverrideRegistry

Stores policy overrides with TTL. WP-3003: revalidation on expiry.

### Methods

#### OverrideRegistry.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### OverrideRegistry.has_unexpired

```python
has_unexpired(self: Any, owner: str)
```

True if owner has an override that has not yet expired.

---

#### OverrideRegistry.record

```python
record(self: Any, owner: str, reason: str, ttl_seconds: int)
```

Record an override; valid until now + ttl_seconds.

---

---

## PolicyEngine

Evaluates execution requests against governance policies.

### Methods

#### PolicyEngine.**init**

```python
__init__(self: Any, settings: Any)
```

---

#### PolicyEngine.evaluate

```python
evaluate(self: Any, run: RunMeta, registry: Any)
```

Evaluate a run against active policies.

Returns (result, reason) where result is 'allow', 'deny', or 'warn'.
G-GP-01: When THGENT_OPA_URL is set, delegates to OPA first; falls back to Python logic on failure.

---

---

## ProviderScorer

WP-Y8/11008: Continuous scoring and learning loop with policy guardrails.

### Methods

#### ProviderScorer.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### ProviderScorer.get_scores

```python
get_scores(self: Any)
```

Return provider scores categorized by prompt characteristics.

---

#### ProviderScorer.update_score

```python
update_score(self: Any, provider: str, characteristic: str, quality_score: float, approved: bool)
```

WP-11008: Update score with policy guardrails (e.g. requires approval for large changes).

---

---

## ReplayManager

WP-4007/9003/9006: Decision replay and rationale snapshots with sandbox and what-if support.

### Methods

#### ReplayManager.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### ReplayManager.enable_sandbox

```python
enable_sandbox(self: Any)
```

WP-9003: Enable read-only sandbox mode for replay.

---

#### ReplayManager.get_replay_chain

```python
get_replay_chain(self: Any, run_id: str)
```

Fetch the sequence of events for a run from the registry.

---

#### ReplayManager.simulate_policy_change

```python
simulate_policy_change(self: Any, run_meta: RunMeta, new_settings: Any)
```

WP-4007: Pre-flight simulation of a different policy.

---

#### ReplayManager.what_if_branch

```python
what_if_branch(self: Any, run_id: str, branch_point_index: int, new_params: dict[(str, Any)], approved: bool)
```

WP-9006/12004: Simulate an alternate outcome with branch governance.

---

---

## RunMeta

Metadata for a single agent/droid execution run.

**Inherits from**: `BaseModel`

---

## RunRegistry

Manages persistence and retrieval of execution runs.

OPT-019: Uses bloom filter for fast negative lookups on session_id (O(1) session existence checks).

### Methods

#### RunRegistry.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### RunRegistry.get_latest_run_id

```python
get_latest_run_id(self: Any)
```

Return the run_id of the most recent run.

---

#### RunRegistry.get_latest_session_id

```python
get_latest_session_id(self: Any)
```

Return the correlation_id (or run_id) of the most recent started run.

---

#### RunRegistry.get_run_state

```python
get_run_state(self: Any, run_id: str)
```

Return current run state from registry events (G-KD-03).

---

#### RunRegistry.list_runs

```python
list_runs(self: Any, limit: int)
```

List recent runs by parsing the registry.

---

#### RunRegistry.register_end

```python
register_end(self: Any, run_id: str, exit_code: int, status: str, ended_at_utc: str, duration_s: float, error_class: Any, cost_usd: Any)
```

Update a run with completion metadata and hash chaining. G-GP-06: cost_usd optional.

---

#### RunRegistry.register_feedback

```python
register_feedback(self: Any, run_id: str, score: float, note: Any)
```

Record operator feedback for a run with hash chaining.

---

#### RunRegistry.register_pause

```python
register_pause(self: Any, run_id: str, reason: str, continuity_snapshot: Any)
```

Record run pause for state-aware orchestration (G-KD-03).

---

#### RunRegistry.register_resume

```python
register_resume(self: Any, run_id: str)
```

Record run resume for state-aware orchestration (G-KD-03).

---

#### RunRegistry.register_start

```python
register_start(self: Any, run: RunMeta)
```

Record the start of a run with hash chaining.

---

#### RunRegistry.session_exists

```python
session_exists(self: Any, session_id: str)
```

OPT-019: Fast negative lookup using bloom filter (O(1) session existence checks).

Returns False if session definitely doesn't exist (bloom filter negative).
Returns True if session might exist (requires full registry scan for confirmation).

---

---

## RunState

Run lifecycle state for state-aware orchestration (G-KD-03).

**Inherits from**: `StrEnum`

---

## TrustBoundaryValidator

WP-3007: Validates environment transitions (e.g. staging→production).

### Methods

#### TrustBoundaryValidator.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### TrustBoundaryValidator.get_last_environment

```python
get_last_environment(self: Any)
```

Return the last recorded environment from a run.

---

#### TrustBoundaryValidator.record_environment

```python
record_environment(self: Any, env: str)
```

Record current environment after successful run.

---

#### TrustBoundaryValidator.validate_transition

```python
validate_transition(self: Any, from_env: Any, to_env: str)
```

Validate transition from from_env to to_env.

Returns (allowed, reason). Promotions (dev→staging→prod) may require audit.

---

---

## acquire

```python
acquire(self: Any, lane: str, harness_type: Any)
```

Acquire a concurrency slot using advanced resource-based limits.

Uses:

- Extended resource monitoring (CPU, memory, FD, network, disk, etc.)
- Prediction engine for forecasting
- Harness card modeling for harness-specific limits
- Bottleneck detection
- 5% minimum buffer (hard limit, prevents crashes)
- 15% discretionary buffer (soft limit, allows scaling)

---

## add

```python
add(self: Any, run_id: str, reason: str, sla_minutes: int, owner: Any, agent: Any, lane: Any, priority: int)
```

Add a blocked run to the escalation queue.

---

## append

```python
append(self: Any, entry: ChatEntry)
```

Append a new chat entry to the session log.

---

## check_and_escalate_stale_critical

```python
check_and_escalate_stale_critical(self: Any, max_idle_s: int)
```

ROB-012: Check for stale critical tasks and escalate if needed.

Returns list of escalated sessions.

---

## check_and_record

```python
check_and_record(self: Any, registry: RunRegistry, key: str)
```

Check if key exists in registry; return True if already executed.

---

## check_capacity

```python
check_capacity(self: Any, lane: str)
```

Check if a lane has capacity to run (starvation prevention).

---

## confirm_handoff

```python
confirm_handoff(self: Any, snapshot_id: str, incoming_owner: str, confidence: float)
```

WP-9004/12005: Incoming owner confirms handoff completeness with confidence.

---

## create_checkpoint

```python
create_checkpoint(self: Any, reason: str, dag_content: str, owner: str)
```

Record a new checkpoint.

---

## create_snapshot

```python
create_snapshot(self: Any, owner: str, run_ids: list[str])
```

Create a continuity snapshot for a handoff.

---

## defer

```python
defer(self: Any, run_id: str, reason: str, eta_s: int)
```

Defer a task with an estimated time to resume.

---

## enable_sandbox

```python
enable_sandbox(self: Any)
```

WP-9003: Enable read-only sandbox mode for replay.

---

## enqueue

```python
enqueue(self: Any, run_meta: RunMeta, error: str)
```

Add a failing run to the DLQ.

---

## evaluate

```python
evaluate(self: Any, run: RunMeta, registry: Any)
```

Evaluate a run against active policies.

Returns (result, reason) where result is 'allow', 'deny', or 'warn'.
G-GP-01: When THGENT_OPA_URL is set, delegates to OPA first; falls back to Python logic on failure.

---

## find_by_token

```python
find_by_token(self: Any, token: str)
```

Find the most recent run with a given idempotency token.

---

## generate_key

```python
generate_key(self: Any, run_id: str, step_index: int, action_type: str, content: str)
```

Generate a 4-tuple idempotency key (run_id, step, action, hash).

---

## generate_maif_artifact

```python
generate_maif_artifact(self: Any, run: RunMeta, output: Any)
```

Generate a signed MAIF artifact for a run (WP-3002).

---

## get_bottlenecks

```python
get_bottlenecks(self: Any)
```

Get current bottlenecks and slow points.

---

## get_calibration_factor

```python
get_calibration_factor(self: Any, agent: str)
```

Calculate calibration factor (avg feedback / avg confidence) for an agent.

G-GP-09: Checks CalibrationRegistry first for persisted factor.

---

## get_checkpoint

```python
get_checkpoint(self: Any, checkpoint_id: str)
```

Retrieve a specific checkpoint.

---

## get_factor

```python
get_factor(self: Any, agent: str)
```

Return the persisted calibration factor for an agent.

---

## get_fatigue_score

```python
get_fatigue_score(self: Any, window_s: int)
```

Calculate fatigue score based on recent interruptions (0.0-1.0).

---

## get_kpis

```python
get_kpis(self: Any)
```

Calculate the 10 core KPIs for the dashboard.

---

## get_lane_priority

```python
get_lane_priority(self: Any, lane: str)
```

Return numeric priority for a lane (lower is higher priority).

---

## get_last_environment

```python
get_last_environment(self: Any)
```

Return the last recorded environment from a run.

---

## get_latest_run_id

```python
get_latest_run_id(self: Any)
```

Return the run_id of the most recent run.

---

## get_latest_session_id

```python
get_latest_session_id(self: Any)
```

Return the correlation_id (or run_id) of the most recent started run.

---

## get_load_level

```python
get_load_level(self: Any)
```

Return current load level: normal, high, burst.

Uses resource-based thresholds when load-based limits are enabled:

- Normal: Below 70% of resource-based limit
- High: 70-95% of resource-based limit (15% discretionary buffer)
- Burst: Above 95% of resource-based limit (5% minimum buffer)

---

## get_replay_chain

```python
get_replay_chain(self: Any, run_id: str)
```

Fetch the sequence of events for a run from the registry.

---

## get_run_state

```python
get_run_state(self: Any, run_id: str)
```

Return current run state from registry events (G-KD-03).

---

## get_scores

```python
get_scores(self: Any)
```

Return provider scores categorized by prompt characteristics.

---

## has_unexpired

```python
has_unexpired(self: Any, owner: str)
```

True if owner has an override that has not yet expired.

---

## is_handoff_enforced

```python
is_handoff_enforced(self: Any, run_id: str)
```

WP-9004: Check if a run is blocked by a pending handoff confirmation.

---

## is_open

```python
is_open(self: Any, target: str, category: str)
```

Check if the circuit for a target in a category is open (blocked).

---

## is_stale

```python
is_stale(self: Any, path: Path, max_age_s: int)
```

Check if a file or registry is stale.

---

## lint

```python
lint(self: Any, csm: Any)
```

Verify CSM evidence is complete based on phase.

---

## list_checkpoints

```python
list_checkpoints(self: Any, limit: int)
```

List recent checkpoints.

---

## list_items

```python
list_items(self: Any, status: Any, run_id: Any)
```

List items in the DLQ with optional filtering.

---

## list_pending

```python
list_pending(self: Any, past_sla_only: bool, limit: int)
```

List escalation items. If past_sla_only, return only items past escalate_by.

---

## list_runs

```python
list_runs(self: Any, limit: int)
```

List recent runs by parsing the registry.

---

## load

```python
load(self: Any, limit: Any)
```

Load chat history from the session log.

---

## mark_processed

```python
mark_processed(self: Any, msg_id: str, status: str)
```

Mark a message as processed (appends an update event).

---

## persist_maif_artifact

```python
persist_maif_artifact(self: Any, session_dir: Path, artifact: MAIFArtifact)
```

Persist a MAIF artifact to the artifacts directory (WP-3002).

---

## poll_session_messages

```python
poll_session_messages(session_id: Any)
```

Poll for pending messages for the current session (WP-9004).

If session_id is None, tries to read from THGENT_SESSION_ID.

---

## purge_expired

```python
purge_expired(self: Any, default_days: int, by_domain: dict[(str, int)], dry_run: bool)
```

WP-3006: Tiered retention purge (G-GP-07).

Removes records exceeding retention period. Returns counts of kept/purged.

---

## push

```python
push(self: Any, entry: MessageEntry)
```

Add a message to the queue.

---

## record

```python
record(self: Any, owner: str, reason: str, ttl_seconds: int)
```

Record an override; valid until now + ttl_seconds.

---

## record_environment

```python
record_environment(self: Any, env: str)
```

Record current environment after successful run.

---

## record_failure

```python
record_failure(self: Any, target: str, category: str, error_message: Any)
```

Record a failure for a target in a specific category.

ROB-003: Detects poison pills (repeated identical failures) and prevents infinite retry loops.

---

## record_interruption

```python
record_interruption(self: Any, run_id: str, severity: str)
```

Record an agent interruption event.

---

## register_end

```python
register_end(self: Any, run_id: str, exit_code: int, status: str, ended_at_utc: str, duration_s: float, error_class: Any, cost_usd: Any)
```

Update a run with completion metadata and hash chaining. G-GP-06: cost_usd optional.

---

## register_feedback

```python
register_feedback(self: Any, run_id: str, score: float, note: Any)
```

Record operator feedback for a run with hash chaining.

---

## register_pause

```python
register_pause(self: Any, run_id: str, reason: str, continuity_snapshot: Any)
```

Record run pause for state-aware orchestration (G-KD-03).

---

## register_resume

```python
register_resume(self: Any, run_id: str)
```

Record run resume for state-aware orchestration (G-KD-03).

---

## register_start

```python
register_start(self: Any, run: RunMeta)
```

Record the start of a run with hash chaining.

---

## resolve

```python
resolve(self: Any, run_id: str, resolution: str)
```

Mark an escalation item as resolved. Returns True if found and updated.

---

## scan_stale_sessions

```python
scan_stale_sessions(self: Any, max_idle_s: int)
```

Scan for sessions with no activity for max_idle_s.

---

## session_exists

```python
session_exists(self: Any, session_id: str)
```

OPT-019: Fast negative lookup using bloom filter (O(1) session existence checks).

Returns False if session definitely doesn't exist (bloom filter negative).
Returns True if session might exist (requires full registry scan for confirmation).

---

## sign_run

```python
sign_run(self: Any, run: RunMeta)
```

Generate a cryptographic signature for a run record.

---

## simulate_policy_change

```python
simulate_policy_change(self: Any, run_meta: RunMeta, new_settings: Any)
```

WP-4007: Pre-flight simulation of a different policy.

---

## sort_tasks

```python
sort_tasks(self: Any, tasks: list[dict[(str, Any)]])
```

Sort tasks by lane priority and then by creation time.

---

## trigger_auto_handoff

```python
trigger_auto_handoff(self: Any, session_id: str, _backup_owner: str)
```

Automatically trigger a handoff for a stale session (WP-5006).

---

## update_agent

```python
update_agent(self: Any, agent: str, factor: float, sample_size: int)
```

Persist a new calibration factor for an agent.

---

## update_score

```python
update_score(self: Any, provider: str, characteristic: str, quality_score: float, approved: bool)
```

WP-11008: Update score with policy guardrails (e.g. requires approval for large changes).

---

## validate_action

```python
validate_action(self: Any, run_id: str, context_files: list[Path])
```

Validate if the action is safe to perform based on context freshness.

---

## validate_transition

```python
validate_transition(self: Any, from_env: Any, to_env: str)
```

Validate transition from from_env to to_env.

Returns (allowed, reason). Promotions (dev→staging→prod) may require audit.

---

## verify_integrity

```python
verify_integrity(self: Any, snapshot_id: str)
```

Verify the integrity of a handoff snapshot.

---

## verify_registry

```python
verify_registry(self: Any)
```

Verify the integrity of all records in the registry, including the hash chain.

ROB-006: Hash chain integrity verification on audit read - Detect tampered audit logs.

---

## what_if_branch

```python
what_if_branch(self: Any, run_id: str, branch_point_index: int, new_params: dict[(str, Any)], approved: bool)
```

WP-9006/12004: Simulate an alternate outcome with branch governance.

---
