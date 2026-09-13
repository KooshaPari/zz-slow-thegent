<DONE>
# Agent Hierarchy MVP Design

> **Date**: 2026-02-19
> **Status**: MVP Design Complete
> **Purpose**: Minimal viable product for multi-level agent coordination via SmolGents + Manager

---

## Executive Summary

The **Agent Hierarchy MVP** enables lightweight, specialized agents (SmolGents) coordinated by a manager agent with a minimal but complete coordination protocol. This is a **pragmatic simplification** of the full hierarchy system documented in `AGENT_HIERARCHY_AND_TEAM_STRUCTURE.md`, focused on MVP completeness rather than maximum features.

**Key Design Principles**:

1. **Minimal Viable**: MVP covers manager + 4-6 SmolGent types; excludes advanced features until Phase 2
2. **File-Based IPC**: Simple, atomic, cross-process using JSON files and Maildir pattern (atomic `mv`)
3. **Opt-In Harnesses**: Core MVP works standalone; Codex/CC/Droid harnesses bolt on as Phase 3
4. **No Breaking Changes**: Extends existing `teammates.py` and agent runners; preserves API

**MVP Scope**:

- Manager agent that routes work to SmolGents
- 4-6 focused SmolGent types (code-search, code-gen, test-gen, doc-gen, refactor, review)
- File-based work queues and result delivery
- Atomic handoff protocol (no race conditions)
- Basic result aggregation
- Error handling and retry

**Out of Scope for MVP** (Phase 2+):

- Advanced routing algorithms
- Team-level coordination
- Cross-team collaboration
- Dynamic team creation
- Hierarchical teams (go straight to swarms in Phase 2)
- Advanced harnesses (Phase 3)

---

## 1. Architecture Overview

### 1.1 MVP Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│ User / CLI                                                    │
│  thegent free --do-next                                      │
│  thegent orchestrate loop                                    │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  Manager Agent                        │
        │  - Parse user prompt                 │
        │  - Route to SmolGents               │
        │  - Aggregate results                │
        │  - Retry on failure                 │
        │  (gemini-3-flash or similar)        │
        └───────┬───────────────┬──────────────┘
                │               │
        ┌───────┴──────┐     ┌──┴──────────┐
        ▼              ▼     ▼             ▼
    ┌────────┐    ┌────────┐ ┌────────┐ ┌────────┐
    │SmolGent│    │SmolGent│ │SmolGent│ │SmolGent│
    │Search  │    │CodeGen │ │TestGen │ │DocGen  │
    └────────┘    └────────┘ └────────┘ └────────┘
        │              │         │           │
        └──────────────┴─────────┴───────────┘
                      │
                      ▼
        ┌───────────────────────────────────┐
        │  Atomic File-Based IPC            │
        │  - .mgmt/inbox/ (new tasks)      │
        │  - .mgmt/active/ (in-progress)   │
        │  - .mgmt/results/ (completed)    │
        │  (Maildir pattern + atomic mv)   │
        └───────────────────────────────────┘
```

### 1.2 Data Flow: Manager → SmolGent → Results

```
1. Manager receives prompt
   └─> Route analysis: "needs code search + review"

2. Manager writes work items to .mgmt/inbox/
   └─> Task: search-codebase-for-patterns
   └─> Task: review-search-results

3. SmolGents (parallel):
   - CodeSearch SmolGent: reads from inbox, atomically mv to active/
   - Review SmolGent: waits for search results in results/

4. SmolGent executes (via subagent or direct)
   └─> CodeSearch: grep/ripgrep, format results
   └─> Review: analyze patterns, generate findings

5. SmolGent atomically writes result to .mgmt/results/
   └─> mv .mgmt/active/{task-id} .mgmt/results/{task-id}

6. Manager aggregates results from .mgmt/results/
   └─> Collects all completed tasks
   └─> Formats output for user
   └─> Cleans up .mgmt/ (optional)
```

---

## 2. SmolGent Type Specifications

### 2.1 Core SmolGent Types (MVP)

| Type            | Purpose                         | Input                         | Output                    | Execution                     |
| --------------- | ------------------------------- | ----------------------------- | ------------------------- | ----------------------------- |
| **code-search** | Find patterns/files in codebase | Query (glob, regex, keywords) | Matching files + context  | Native tools (rg, fd, ag)     |
| **code-gen**    | Generate code snippets/modules  | Spec (requirements, template) | Generated code + tests    | Codex (Phase 3) or direct LLM |
| **test-gen**    | Generate test cases             | Code + coverage gaps          | Test file + assertions    | Direct LLM or droid           |
| **doc-gen**     | Generate documentation          | Codebase context              | Markdown docs             | Direct LLM                    |
| **refactor**    | Apply code transformations      | Pattern + replacement rules   | Refactored code + changes | CodeMod or AST tools          |
| **review**      | Code review & validation        | Code + criteria               | Findings + scores         | Direct LLM                    |

### 2.2 SmolGent Interface

```python
@dataclass
class SmolGentTask:
    """Task routed to a SmolGent."""

    task_id: str  # Unique task ID
    smolgent_type: str  # "code-search", "code-gen", etc.
    prompt: str  # Task description
    context: dict[str, Any]  # Execution context
    timeout: int = 300  # Task timeout (seconds)
    retries: int = 3  # Retry attempts
    priority: int = 5  # 1=highest, 10=lowest


@dataclass
class SmolGentResult:
    """Result from a SmolGent execution."""

    task_id: str  # Original task ID
    smolgent_type: str  # Type that executed
    status: Literal["success", "failure", "timeout"]
    output: str  # Task output
    metadata: dict[str, Any]  # Execution metadata
    duration_secs: float  # Execution time
    error_msg: str | None = None  # Error if failed
    try_count: int = 1  # Number of attempts


class SmolGentBase(AgentRunner):
    """Base class for all SmolGents."""

    def run(
        self,
        task: SmolGentTask,
        *,
        on_stdout: Callable[[str], None] | None = None,
        on_stderr: Callable[[str], None] | None = None,
    ) -> SmolGentResult:
        """Execute a task. Returns SmolGentResult."""
        raise NotImplementedError

    @classmethod
    def route_candidates(cls) -> list[str]:
        """What task types can this SmolGent handle?"""
        raise NotImplementedError
```

### 2.3 SmolGent Implementations (MVP)

#### CodeSearchSmolGent

```python
class CodeSearchSmolGent(SmolGentBase):
    """Search codebase for patterns, files, or text."""

    def run(self, task: SmolGentTask, **kwargs) -> SmolGentResult:
        """
        Context keys:
        - glob_pattern: e.g. "**/*.py"
        - search_term: e.g. "error_handler"
        - regex: optional regex pattern
        - exclude: paths to exclude
        - max_results: max files to return

        Output: JSON with files + line context
        """
        # Use ripgrep (rg) or fd for speed
        # Return structured JSON with file paths and context
        pass

    @classmethod
    def route_candidates(cls):
        return ["code-search", "find-files", "search-patterns"]
```

#### CodeGenSmolGent

```python
class CodeGenSmolGent(SmolGentBase):
    """Generate code from specification."""

    def run(self, task: SmolGentTask, **kwargs) -> SmolGentResult:
        """
        Context keys:
        - language: "python", "typescript", etc.
        - spec: implementation spec
        - template: optional code template
        - tests: optional test spec
        - style_guide: optional conventions

        Output: Generated code file + optional tests
        """
        # Call direct LLM or Codex harness (Phase 3)
        # Return code + metadata (loc, functions, etc.)
        pass

    @classmethod
    def route_candidates(cls):
        return ["code-gen", "generate-code", "stub-implementation"]
```

#### TestGenSmolGent

```python
class TestGenSmolGent(SmolGentBase):
    """Generate test cases for code."""

    def run(self, task: SmolGentTask, **kwargs) -> SmolGentResult:
        """
        Context keys:
        - code: source code to test
        - framework: "pytest", "vitest", etc.
        - coverage_target: e.g. 0.8 (80%)
        - test_type: "unit", "integration", "e2e"

        Output: Test file + coverage estimates
        """
        pass

    @classmethod
    def route_candidates(cls):
        return ["test-gen", "generate-tests", "write-tests"]
```

#### DocGenSmolGent

```python
class DocGenSmolGent(SmolGentBase):
    """Generate documentation from code."""

    def run(self, task: SmolGentTask, **kwargs) -> SmolGentResult:
        """
        Context keys:
        - code: source code to document
        - format: "markdown", "rst", "html"
        - style: "comprehensive", "minimal", "api-only"
        - include_examples: bool

        Output: Formatted documentation
        """
        pass

    @classmethod
    def route_candidates(cls):
        return ["doc-gen", "generate-docs", "write-documentation"]
```

#### RefactorSmolGent

```python
class RefactorSmolGent(SmolGentBase):
    """Apply code refactoring transformations."""

    def run(self, task: SmolGentTask, **kwargs) -> SmolGentResult:
        """
        Context keys:
        - code: source code
        - refactoring_rules: list of transformations
        - check_only: bool (don't apply, just report)
        - preserve_behavior: bool (ensure semantics preserved)

        Output: Refactored code + change summary
        """
        pass

    @classmethod
    def route_candidates(cls):
        return ["refactor", "code-refactor", "simplify"]
```

#### ReviewSmolGent

```python
class ReviewSmolGent(SmolGentBase):
    """Code review and validation."""

    def run(self, task: SmolGentTask, **kwargs) -> SmolGentResult:
        """
        Context keys:
        - code: source code to review
        - criteria: review criteria (style, security, perf)
        - level: "lint", "functional", "security"
        - framework: optional linter/tool to use

        Output: Findings (issues + scores)
        """
        pass

    @classmethod
    def route_candidates(cls):
        return ["review", "code-review", "validate"]
```

---

## 3. Coordination Protocol

### 3.1 File-Based IPC: Maildir Pattern

**Directory Structure** (under `.mgmt/`):

```
.mgmt/
├── inbox/              # New tasks (not yet claimed)
│   ├── {task-id}.new   # Atomic writes (written to tmp, then mv)
│   └── {task-id}.new
├── active/             # Tasks in progress
│   ├── {task-id}.run   # Claimed by SmolGent
│   └── {task-id}.run
├── results/            # Completed tasks
│   ├── {task-id}.ok    # Succeeded
│   ├── {task-id}.fail  # Failed (retryable)
│   └── {task-id}.fail
└── metadata/
    └── manager-state.json  # Manager state tracking
```

**Atomic Operations** (using `mv` for atomicity):

```python
def write_task_atomically(task: SmolGentTask) -> Path:
    """Write task to inbox atomically."""
    inbox = Path(".mgmt/inbox")
    inbox.mkdir(parents=True, exist_ok=True)

    # Write to tmp file
    tmp_file = inbox / f".{task.task_id}.tmp"
    tmp_file.write_text(json.dumps(asdict(task)))

    # Atomic move to inbox
    final_file = inbox / f"{task.task_id}.new"
    tmp_file.replace(final_file)  # Atomic on POSIX
    return final_file


def claim_task_atomically(task_id: str) -> SmolGentTask | None:
    """Atomically claim a task from inbox."""
    inbox_file = Path(".mgmt/inbox") / f"{task_id}.new"
    active_file = Path(".mgmt/active") / f"{task_id}.run"

    if not inbox_file.exists():
        return None

    # Atomic move (claim)
    try:
        inbox_file.replace(active_file)
        return SmolGentTask(**json.loads(active_file.read_text()))
    except FileExistsError:
        # Already claimed by another process
        return None


def write_result_atomically(result: SmolGentResult) -> Path:
    """Write result to results/ atomically."""
    results_dir = Path(".mgmt/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    # Write to tmp
    status_ext = "ok" if result.status == "success" else "fail"
    tmp_file = results_dir / f".{result.task_id}.tmp"
    tmp_file.write_text(json.dumps(asdict(result)))

    # Atomic move
    final_file = results_dir / f"{result.task_id}.{status_ext}"
    tmp_file.replace(final_file)

    # Remove from active/
    active_file = Path(".mgmt/active") / f"{result.task_id}.run"
    if active_file.exists():
        active_file.unlink()

    return final_file
```

### 3.2 Manager → SmolGent Handoff

**Manager Perspective**:

```python
class ManagerAgent:
    """Routes work to SmolGents."""

    def run(self, prompt: str, cwd: Path | None) -> RunResult:
        """Main manager loop."""
        # 1. Parse prompt to identify tasks
        tasks = self.route_tasks(prompt)  # -> list[SmolGentTask]

        # 2. Write tasks to inbox
        task_ids = []
        for task in tasks:
            self.write_task_to_inbox(task)
            task_ids.append(task.task_id)

        # 3. Wait for SmolGents to complete (polling)
        results = self.poll_for_results(task_ids, timeout=300)

        # 4. Aggregate results
        aggregated = self.aggregate_results(results)

        # 5. Return to user
        return RunResult(
            exit_code=0 if all(r.status == "success" for r in results) else 1,
            stdout=aggregated,
            stderr="",
        )

    def route_tasks(self, prompt: str) -> list[SmolGentTask]:
        """Parse prompt → SmolGent task list."""
        # Simple routing: ask LLM what SmolGents are needed
        # Return structured task list
        pass

    def poll_for_results(
        self,
        task_ids: list[str],
        timeout: int = 300,
    ) -> list[SmolGentResult]:
        """Poll .mgmt/results/ until all tasks complete or timeout."""
        results = []
        start = time.time()

        while time.time() - start < timeout:
            # Check for completed tasks
            results_dir = Path(".mgmt/results")
            for task_id in task_ids:
                ok_file = results_dir / f"{task_id}.ok"
                fail_file = results_dir / f"{task_id}.fail"

                if ok_file.exists():
                    result = SmolGentResult(**json.loads(ok_file.read_text()))
                    results.append(result)
                elif fail_file.exists():
                    result = SmolGentResult(**json.loads(fail_file.read_text()))
                    # Retry if retries left
                    if result.try_count < result.retries:
                        self.retry_task(task_id, result)
                    else:
                        results.append(result)

            if len(results) == len(task_ids):
                break
            time.sleep(1)

        return results
```

**SmolGent Perspective**:

```python
class SmolGentRunner:
    """Executes SmolGent tasks from the work queue."""

    def main_loop(self):
        """Main SmolGent loop."""
        while True:
            # 1. Look for tasks in inbox/
            task = self.claim_next_task()
            if not task:
                time.sleep(1)
                continue

            # 2. Execute task
            result = self.execute_task(task)

            # 3. Write result back atomically
            self.write_result_atomically(result)

    def claim_next_task(self) -> SmolGentTask | None:
        """Atomically claim next task from inbox."""
        inbox = Path(".mgmt/inbox")
        if not inbox.exists():
            return None

        for task_file in sorted(inbox.glob("*.new")):
            task_data = json.loads(task_file.read_text())
            task = SmolGentTask(**task_data)

            # Try to claim atomically
            claimed = self.claim_task_atomically(task.task_id)
            if claimed:
                return claimed

        return None

    def execute_task(self, task: SmolGentTask) -> SmolGentResult:
        """Execute a single task."""
        start = time.time()
        try:
            # Find matching SmolGent implementation
            smolgent_class = self.find_smolgent_class(task.smolgent_type)
            if not smolgent_class:
                return SmolGentResult(
                    task_id=task.task_id,
                    smolgent_type=task.smolgent_type,
                    status="failure",
                    output="",
                    error_msg=f"No SmolGent for type: {task.smolgent_type}",
                    metadata={},
                    duration_secs=0,
                )

            # Execute SmolGent
            smolgent = smolgent_class()
            result = smolgent.run(task)
            result.duration_secs = time.time() - start
            return result

        except TimeoutError:
            return SmolGentResult(
                task_id=task.task_id,
                smolgent_type=task.smolgent_type,
                status="timeout",
                output="",
                metadata={},
                duration_secs=time.time() - start,
                error_msg=f"Timeout after {task.timeout}s",
            )
        except Exception as e:
            return SmolGentResult(
                task_id=task.task_id,
                smolgent_type=task.smolgent_type,
                status="failure",
                output="",
                metadata={},
                duration_secs=time.time() - start,
                error_msg=str(e),
            )
```

---

## 4. Execution Modes

### 4.1 MVP Execution Modes

| Mode                        | Setup                   | Execution                             | Harness |
| --------------------------- | ----------------------- | ------------------------------------- | ------- |
| **Local (MVP)**             | Direct Python classes   | Subagent (thegent free/bg) or threads | None    |
| **Distributed (Phase 2)**   | Multiple processes      | Pool of SmolGent workers              | None    |
| **Codex Harness (Phase 3)** | Codex + Python sandbox  | Codex for code-gen, code-search       | Yes     |
| **CC Harness (Phase 3)**    | Claude Code integration | CC for code generation/review         | Yes     |
| **Droid Harness (Phase 3)** | Factory droid exec      | Droids for long-running tasks         | Yes     |

### 4.2 MVP Local Execution (Threads)

```python
class LocalSmolGentPool:
    """Local thread pool for executing SmolGents."""

    def __init__(self, num_workers: int = 4):
        self.pool = ThreadPoolExecutor(max_workers=num_workers)

    def start(self):
        """Start worker threads."""
        for i in range(self.pool._max_workers):
            self.pool.submit(SmolGentRunner().main_loop)

    def stop(self):
        """Stop worker pool."""
        self.pool.shutdown(wait=True)
```

### 4.3 MVP with Subagents (Phase 1.5)

Each SmolGent can optionally spawn a subagent:

```python
class CodeGenSmolGent(SmolGentBase):
    """Generate code - can use subagent."""

    def run(self, task: SmolGentTask, **kwargs) -> SmolGentResult:
        if use_subagent := task.context.get("use_subagent", False):
            # Spawn subagent for code generation
            from thegent.cli_impl import run_impl

            result = run_impl(
                agent="free",  # or "claude"
                prompt=task.prompt,
                mode="write",
                timeout=task.timeout,
            )
            # Parse result
            return SmolGentResult(
                task_id=task.task_id,
                smolgent_type="code-gen",
                status="success" if result.get("exit_code") == 0 else "failure",
                output=result.get("stdout", ""),
                metadata={"subagent": "free"},
                duration_secs=0,
            )
        else:
            # Direct LLM call (hardcoded or configurable)
            pass
```

---

## 5. Error Handling & Retry Strategy

### 5.1 Error Classification

```python
class SmolGentError(Exception):
    """Base SmolGent error."""

    pass


class TransientSmolGentError(SmolGentError):
    """Retryable error (timeout, rate limit, transient crash)."""

    pass


class PermanentSmolGentError(SmolGentError):
    """Non-retryable error (bad input, unsupported task type)."""

    pass


def classify_error(error: Exception) -> type[SmolGentError]:
    """Classify error as transient or permanent."""
    msg = str(error).lower()
    if any(kw in msg for kw in ["timeout", "rate limit", "503", "502", "transient"]):
        return TransientSmolGentError
    return PermanentSmolGentError
```

### 5.2 Retry Logic

```python
@dataclass
class SmolGentResult:
    """Result includes retry metadata."""

    task_id: str
    smolgent_type: str
    status: Literal["success", "failure", "timeout"]
    output: str
    metadata: dict[str, Any]
    duration_secs: float
    error_msg: str | None = None
    try_count: int = 1  # How many times was this attempted?


class ManagerRetryLogic:
    """Handles retry for failed tasks."""

    def should_retry(self, result: SmolGentResult) -> bool:
        """Determine if task should be retried."""
        if result.try_count >= 3:
            return False  # Max retries exceeded
        if result.status == "success":
            return False  # No retry needed
        if "permanent" in result.error_msg.lower():
            return False  # Permanent error
        return True  # Retry transient errors

    def retry_task(self, result: SmolGentResult) -> SmolGentTask:
        """Create retry task from failed result."""
        # Re-submit to inbox with incremented try_count
        task = SmolGentTask(
            task_id=f"{result.task_id}-retry-{result.try_count}",
            smolgent_type=result.smolgent_type,
            prompt=result.metadata.get("prompt", ""),
            context=result.metadata.get("context", {}),
            retries=result.retries,
            # ... other fields
        )
        return task
```

---

## 6. Performance Model

### 6.1 Latency Breakdown

| Component                    | Latency   | Notes                          |
| ---------------------------- | --------- | ------------------------------ |
| Manager routing              | 100-500ms | LLM call to identify SmolGents |
| Task write (atomicity)       | <1ms      | File write + atomic move       |
| SmolGent startup             | 100-200ms | Process/thread spawn           |
| Task execution               | 1-30s     | Actual work (varies by type)   |
| Result write                 | <1ms      | Atomic move                    |
| Result polling (1 iteration) | 10ms      | Check .mgmt/results/           |
| Aggregation                  | 100-500ms | LLM call to combine results    |
| **Total (best case)**        | **2-10s** | Sequential, no parallelism     |
| **Total (with parallelism)** | **1-5s**  | Multiple SmolGents in parallel |

### 6.2 Throughput Model

```
With N SmolGents in parallel:
- Single task: 2-10s (latency-bound)
- 4 tasks parallel: 2-10s (parallelism hides sequential cost)
- 10 tasks: 2-10s (throughput-bound, depends on pool size)

Estimated throughput:
- 4 workers: ~2 tasks/s
- 8 workers: ~4 tasks/s
- 16 workers: ~8 tasks/s
```

### 6.3 Resource Model

| Resource | Per SmolGent                   | Notes                                         |
| -------- | ------------------------------ | --------------------------------------------- |
| Memory   | 10-50MB                        | Varies by type (code-search uses rg, minimal) |
| CPU      | 1 core active during execution | Mostly idle (I/O bound)                       |
| Storage  | .mgmt/ dir: <100MB             | Task files + results (gc periodically)        |
| Network  | 0-1MB/s                        | Optional LLM calls (code-gen, review)         |

---

## 7. Integration Points

### 7.1 Integration with Existing Systems

```python
# Extend existing TeammateManager (from teams.py)
class TeammateManager:
    """Existing: delegates to teammates."""

    def __init__(self, settings: ThegentSettings) -> None:
        self.settings = settings
        self.teammates: list[TeammateAgent] = []
        # NEW: Initialize SmolGent coordinator
        self.smolgent_coordinator = SmolGentCoordinator(settings)


# Extend existing AgentRunner interface
class SmolGentBase(AgentRunner):
    """SmolGents implement AgentRunner interface."""

    def run(
        self,
        prompt: str,
        cwd: Path | None,
        mode: str,
        timeout: int,
        # ... existing params
    ) -> RunResult:
        """SmolGent runs as a normal agent runner."""
        pass


# New: coordinator that ties it together
class SmolGentCoordinator:
    """Coordinates SmolGent execution."""

    def __init__(self, settings: ThegentSettings):
        self.settings = settings
        self.manager = ManagerAgent()
        self.pool = LocalSmolGentPool(num_workers=4)

    def run(self, prompt: str) -> RunResult:
        """Run manager + SmolGents."""
        return self.manager.run(prompt)
```

### 7.2 CLI Integration

```bash
# Phase 1: Direct manager invocation
thegent free "Search for all error handlers in the codebase"
# Manager detects: code-search + review
# Routes to code-search and review SmolGents

# Phase 1.5: Explicit SmolGent selection
thegent smolgent code-search "error_handler" --glob "**/*.py"
thegent smolgent code-gen --spec "Create a retry decorator"

# Phase 2: Team-based execution
thegent teams create --name "ml-team" --type functional
thegent teams delegate ml-team "Train model on dataset"
```

### 7.3 Configuration

```python
# .claude/smolgent-config.json
{
    "enabled": true,
    "num_workers": 4,
    "execution_mode": "local",  # or "distributed", "codex", "cc", "droid"
    "smolgent_types": ["code-search", "code-gen", "test-gen", "doc-gen", "refactor", "review"],
    "retry_policy": {"max_retries": 3, "initial_backoff_ms": 100, "max_backoff_ms": 5000},
    "timeouts": {"code-search": 60, "code-gen": 300, "test-gen": 300, "doc-gen": 120, "refactor": 180, "review": 180},
}
```

---

## 8. Phase Progression

### Phase 1: MVP Core (Weeks 1-2)

**Deliverables**:

- SmolGentBase interface + 2 implementations (code-search, review)
- ManagerAgent with routing
- File-based IPC (Maildir pattern)
- Basic result aggregation
- Local thread pool executor

**Success Criteria**:

- Manager can route simple prompts to SmolGents
- Code search and review work end-to-end
- Results aggregate correctly
- No race conditions in file IPC

### Phase 2: Extended SmolGents (Weeks 3-4)

**Deliverables**:

- Remaining SmolGent types (code-gen, test-gen, doc-gen, refactor)
- Distributed execution (process pool)
- Advanced routing (LLM-based task decomposition)
- Enhanced error handling + retry

**Success Criteria**:

- All 6 SmolGent types working
- Multi-process execution stable
- Retry logic functioning
- Performance meets latency targets

### Phase 3: Harness Integration (Weeks 5-6)

**Deliverables**:

- Codex harness for code-gen/search
- Claude Code harness for review/gen
- Droid harness for long-running tasks
- Harness auto-selection logic

**Success Criteria**:

- Harnesses properly isolate (no resource leaks)
- Fallback to direct LLM working
- Harness-specific performance gains measured

---

## 9. File Structure

```
src/thegent/smolgents/
├── __init__.py
├── base.py                    # SmolGentBase + interfaces
├── types.py                   # SmolGentTask, SmolGentResult
├── manager.py                 # ManagerAgent
├── coordinator.py             # SmolGentCoordinator
├── pool.py                    # LocalSmolGentPool
├── ipc/
│   ├── __init__.py
│   ├── maildir.py             # Maildir pattern utilities
│   └── atomic_fs.py           # Atomic file operations
├── implementations/
│   ├── __init__.py
│   ├── code_search.py         # CodeSearchSmolGent
│   ├── code_gen.py            # CodeGenSmolGent
│   ├── test_gen.py            # TestGenSmolGent
│   ├── doc_gen.py             # DocGenSmolGent
│   ├── refactor.py            # RefactorSmolGent
│   └── review.py              # ReviewSmolGent
├── harness/
│   ├── __init__.py
│   ├── base_harness.py        # HarnessBase (Phase 3)
│   ├── codex_harness.py       # CodexHarness (Phase 3)
│   ├── cc_harness.py          # ClaudeCodeHarness (Phase 3)
│   └── droid_harness.py       # DroidHarness (Phase 3)
└── __main__.py                # SmolGent CLI entry point
```

---

## 10. Comparison: MVP vs Full Hierarchy

| Aspect                    | MVP                     | Full Hierarchy           |
| ------------------------- | ----------------------- | ------------------------ |
| **Scope**                 | Manager + 6 SmolGents   | Multi-level teams        |
| **Coordination**          | File-based IPC          | Structured messages + DB |
| **Team Support**          | No teams (flat)         | Hierarchical teams       |
| **Execution**             | Local threads (Phase 1) | Distributed + harnesses  |
| **Routing**               | Simple LLM-based        | Advanced algorithm       |
| **Result Aggregation**    | Basic concatenation     | Structured synthesis     |
| **Implementation Effort** | ~2 weeks                | ~8 weeks                 |
| **Complexity**            | Low                     | High                     |

**Why MVP First?**

- Delivers value quickly (weeks vs months)
- Foundation for full hierarchy
- Validates file-based IPC approach
- Easy to extend with team support
- Allows harness experiments

**Path to Full Hierarchy**:

1. MVP works → Promote SmolGents to team members
2. Create TeamLead agent type
3. Extend coordinator → HierarchyManager
4. Add cross-team collaboration protocol
5. Implement team-aware routing

---

## 11. Open Questions & Trade-Offs

### 11.1 Execution Model Options

**Option A: Thread Pool (MVP Choice)**

- ✅ Simple, no process overhead
- ❌ Python GIL limits parallelism for CPU-bound tasks
- ❌ Shared memory can cause bugs

**Option B: Process Pool**

- ✅ True parallelism
- ✅ Isolation (good for sandboxing)
- ❌ Higher overhead, IPC complexity
- ✅ Better for Phase 2

**Option C: Async/Await**

- ✅ High concurrency
- ❌ Requires async SmolGents
- ❌ More complex error handling

**Decision**: Start with Thread Pool (MVP), add Process Pool in Phase 2.

### 11.2 Harness Integration

**Option A: SmolGents invoke harness directly**

- ✅ Simple, no extra layer
- ❌ Harness logic spread across SmolGents
- ❌ Harder to swap harnesses

**Option B: Harness layer between Manager & SmolGents**

- ✅ Centralized harness logic
- ✅ Easy to swap/extend
- ❌ Extra indirection

**Decision**: Use Option B (harness layer) in Phase 3 for cleanliness.

### 11.3 Result Aggregation

**Option A: Manager aggregates all results**

- ✅ Simple, no data loss
- ❌ Manager becomes a bottleneck for large result sets
- ❌ Aggregation logic tightly coupled

**Option B: SmolGents self-aggregate**

- ✅ Distributed aggregation
- ❌ Harder to debug
- ❌ Race conditions possible

**Decision**: Use Option A (MVP), move to Option B in Phase 2 if needed.

---

## 12. Success Criteria for MVP

### 12.1 Functional Criteria

- [ ] Manager can parse prompts and route to SmolGents
- [ ] Code-search SmolGent finds files/patterns correctly
- [ ] Review SmolGent analyzes code
- [ ] File-based IPC is atomic (no data loss or corruption)
- [ ] Results aggregate correctly
- [ ] Retry logic handles transient failures
- [ ] All 6 SmolGent types working by end of Phase 2

### 12.2 Performance Criteria

- [ ] End-to-end latency: 2-10 seconds (simple tasks)
- [ ] Throughput: 2+ tasks/second with 4 workers
- [ ] File IPC overhead: <1% of task execution time
- [ ] Memory per SmolGent: <50MB

### 12.3 Quality Criteria

- [ ] Zero race conditions in file IPC
- [ ] 95%+ success rate (retries included)
- [ ] Proper error messages and stack traces
- [ ] Unit test coverage: >80%
- [ ] Integration tests for full manager→SmolGent→result flow

### 12.4 Integration Criteria

- [ ] Extends existing `TeammateManager` without breaking changes
- [ ] Implements `AgentRunner` interface
- [ ] Works with existing CLI (thegent free, thegent bg)
- [ ] Configuration via .claude/smolgent-config.json

---

## 13. Risk Mitigation

| Risk                                     | Probability | Impact | Mitigation                                    |
| ---------------------------------------- | ----------- | ------ | --------------------------------------------- |
| File IPC race conditions                 | Medium      | High   | Use atomic `mv`, extensive testing            |
| SmolGent timeout during execution        | Medium      | Medium | Configurable timeouts, graceful degradation   |
| Manager bottleneck with many tasks       | Low         | Medium | Move to distributed in Phase 2                |
| Harness integration complexity (Phase 3) | Low         | Medium | Design harness layer carefully in MVP         |
| Result data loss on crash                | Low         | High   | Persistent .mgmt/ directory, cleanup policies |

---

## Appendix A: Quick Start Example

### User Perspective

```bash
$ thegent free "Find all error handlers and review them"

Manager: Parsing prompt...
Manager: Detected tasks:
  - code-search (find error handlers)
  - review (analyze patterns)

Manager: Writing 2 tasks to .mgmt/inbox/

SmolGent[code-search]: Executing... (claimed task-001)
SmolGent[review]: Waiting for code-search results...

SmolGent[code-search]: Done! Found 15 error handlers
SmolGent[review]: Analyzing patterns...
SmolGent[review]: Done! Found 3 issues

Manager: Aggregating results...
Output:
  Found 15 error handlers across the codebase
  - Issue 1: Uncaught exceptions in database layer
  - Issue 2: Silent failures in API handlers
  - Issue 3: Inconsistent logging format

Total time: 4.2s
```

### File Structure (Behind the Scenes)

```
.mgmt/
├── inbox/
│   ├── task-001.new        # code-search task
│   └── task-002.new        # review task
├── active/
│   └── task-001.run        # code-search in progress
├── results/
│   └── task-001.ok         # code-search result
└── metadata/
    └── manager-state.json  # Manager tracking
```

---

## Appendix B: Implementation Checklist

### Phase 1: Core (2 weeks)

- [ ] SmolGentTask & SmolGentResult dataclasses
- [ ] SmolGentBase abstract class
- [ ] Maildir pattern utilities (atomic writes, claiming)
- [ ] ManagerAgent (basic routing)
- [ ] CodeSearchSmolGent implementation
- [ ] ReviewSmolGent implementation
- [ ] LocalSmolGentPool (thread executor)
- [ ] SmolGentCoordinator (orchestrator)
- [ ] CLI: `thegent smolgent code-search`
- [ ] Tests: 80%+ coverage
- [ ] Docs: README, examples, API docs

### Phase 2: Extended (2 weeks)

- [ ] CodeGenSmolGent
- [ ] TestGenSmolGent
- [ ] DocGenSmolGent
- [ ] RefactorSmolGent
- [ ] ProcessPool (distributed execution)
- [ ] Advanced routing (LLM-based decomposition)
- [ ] Enhanced error handling & retry
- [ ] CLI: `thegent smolgent *` for all types
- [ ] Benchmarks: latency & throughput
- [ ] Integration tests

### Phase 3: Harnesses (2 weeks)

- [ ] HarnessBase abstraction
- [ ] CodexHarness (code-search, code-gen via Codex sandbox)
- [ ] ClaudeCodeHarness (review, code-gen via CC)
- [ ] DroidHarness (long-running tasks)
- [ ] Harness auto-selection
- [ ] Fallback logic (harness unavailable)
- [ ] Tests for harness isolation
- [ ] Docs: harness architecture, extension guide

---

## References

- [AGENT_HIERARCHY_AND_TEAM_STRUCTURE.md](./AGENT_HIERARCHY_AND_TEAM_STRUCTURE.md) - Full hierarchy design
- [TEAMMATES_RESEARCH_AND_PLAN.md](./TEAMMATES_RESEARCH_AND_PLAN.md) - Teammate coordination patterns
- `src/thegent/agents/teammates.py` - Existing teammate manager
- `src/thegent/agents/base.py` - AgentRunner interface
- `src/thegent/agents/loop_controller.py` - Coordination patterns

---

**Next Step**: Create detailed implementation plan in `docs/plans/AGENT_HIERARCHY_IMPLEMENTATION_PLAN.md`
