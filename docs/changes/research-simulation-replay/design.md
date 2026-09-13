# Deterministic Replay System — Design Document

## System Overview

### Architecture Goals

1. **Non-invasive**: Trace recording doesn't impact normal execution
2. **Deterministic**: Same inputs → same outputs (with mocked LLM calls)
3. **Efficient**: Low-cost replay (80%+ cheaper than live re-execution)
4. **Debuggable**: Clear diffs, easy to identify root causes
5. **Scalable**: Handle 1000+ tool calls per trace

### Design Principles

- **Immutable traces**: Records are append-only, never modified
- **Async recording**: Non-blocking capture, no impact on execution latency
- **Privacy-first**: Sensitive data redacted by default
- **Compression**: Traces compressed to <50% original size
- **Streaming**: JSONL format supports streaming, line-by-line processing

---

## Core Components

### 1. TraceRecorder

**Purpose**: Capture execution metadata during normal operation.

**Implementation**:

```python
# thegent/trace/recorder.py
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
from datetime import datetime
import json
import asyncio
from pathlib import Path
import zstd


@dataclass
class ToolCallRecord:
    type: str = "tool_call"
    tool_name: str = ""
    tool_id: str = ""
    session_id: str = ""
    call_index: int = 0
    inputs: Dict[str, Any] = None
    result: Any = None
    duration_ms: float = 0.0
    tokens_used: int = 0
    cost: float = 0.0
    status: str = "success"  # success | error | timeout
    error_msg: Optional[str] = None
    timestamp: str = ""

    def to_json_line(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class DecisionRecord:
    type: str = "decision"
    decision_type: str = ""  # routing | classification | override
    reasoning: str = ""
    choice: str = ""
    session_id: str = ""
    timestamp: str = ""


@dataclass
class SessionRecord:
    type: str = "session"
    session_id: str = ""
    task_id: str = ""
    model: str = ""
    provider: str = ""
    config: Dict[str, Any] = None
    status: str = "started"  # started | completed | failed
    start_time: str = ""
    end_time: Optional[str] = None
    total_cost: float = 0.0
    total_tokens: int = 0


class TraceRecorder:
    """Records execution traces to JSONL format."""

    def __init__(self, session_id: str, trace_dir: Optional[Path] = None):
        self.session_id = session_id
        self.trace_dir = trace_dir or Path.home() / ".thegent" / "traces"
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.trace_file = self.trace_dir / f"trace-{session_id}.jsonl"
        self.call_index = 0
        self._write_queue = asyncio.Queue()
        self._running = False
        self._compression = zstd.ZstdCompressor()

    async def start(self):
        """Start async recording."""
        self._running = True
        asyncio.create_task(self._write_worker())

    async def stop(self):
        """Stop recording and flush."""
        self._running = False
        await self._write_queue.join()
        await self._compress_trace()

    async def record_tool_call(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        result: Any,
        duration_ms: float,
        tokens_used: int,
        cost: float,
        status: str = "success",
        error_msg: Optional[str] = None,
    ):
        """Record tool invocation."""
        record = ToolCallRecord(
            tool_name=tool_name,
            tool_id=f"{tool_name}-{self.call_index}",
            session_id=self.session_id,
            call_index=self.call_index,
            inputs=self._redact(tool_name, inputs),
            result=self._truncate(result),
            duration_ms=duration_ms,
            tokens_used=tokens_used,
            cost=cost,
            status=status,
            error_msg=error_msg,
            timestamp=datetime.utcnow().isoformat(),
        )
        self.call_index += 1
        await self._write_queue.put(record.to_json_line())

    async def record_decision(
        self,
        decision_type: str,
        reasoning: str,
        choice: str,
    ):
        """Record decision point."""
        record = DecisionRecord(
            decision_type=decision_type,
            reasoning=reasoning,
            choice=choice,
            session_id=self.session_id,
            timestamp=datetime.utcnow().isoformat(),
        )
        await self._write_queue.put(json.dumps(asdict(record)))

    async def record_session(self, task_id: str, model: str, provider: str, config: Dict):
        """Record session start."""
        record = SessionRecord(
            session_id=self.session_id,
            task_id=task_id,
            model=model,
            provider=provider,
            config=config,
            status="started",
            start_time=datetime.utcnow().isoformat(),
        )
        await self._write_queue.put(json.dumps(asdict(record)))

    def _redact(self, tool_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive data from inputs."""
        redacted = inputs.copy()
        # Redact patterns: api_key, password, token, secret, auth
        sensitive_keys = ["api_key", "password", "token", "secret", "auth", "key"]
        for key in sensitive_keys:
            if key in redacted:
                redacted[key] = "***REDACTED***"
        return redacted

    def _truncate(self, result: Any, max_size: int = 10_000) -> Any:
        """Truncate large results."""
        result_str = json.dumps(result)[:max_size]
        return json.loads(result_str)

    async def _write_worker(self):
        """Async writer worker."""
        with open(self.trace_file, "a") as f:
            while self._running:
                try:
                    line = await asyncio.wait_for(self._write_queue.get(), timeout=1.0)
                    f.write(line + "\n")
                    self._write_queue.task_done()
                except asyncio.TimeoutError:
                    continue

    async def _compress_trace(self):
        """Compress trace file after recording."""
        # Gzip for now; can upgrade to zstd for better compression
        import gzip

        if self.trace_file.exists():
            with open(self.trace_file, "rb") as f_in:
                with gzip.open(f"{self.trace_file}.gz", "wb") as f_out:
                    f_out.writelines(f_in)
```

**Usage**:

```python
# In agent execution pipeline
recorder = TraceRecorder(session_id="s-123")
await recorder.start()
try:
    result = await execute_tool(tool_name, inputs)
    await recorder.record_tool_call(tool_name, inputs, result, duration, tokens, cost)
finally:
    await recorder.stop()
```

---

### 2. ReplayEngine

**Purpose**: Re-execute workflows with mocked LLM calls from traces.

**Implementation**:

```python
# thegent/trace/replay.py
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from dataclasses import dataclass


@dataclass
class ExecutionContext:
    trace_records: List[Dict[str, Any]]
    record_index: int = 0

    def next_record(self) -> Optional[Dict[str, Any]]:
        if self.record_index < len(self.trace_records):
            record = self.trace_records[self.record_index]
            self.record_index += 1
            return record
        return None


class ReplayEngine:
    """Re-executes workflows with mocked tool calls."""

    def __init__(self, trace_file: Path, fallback_mode: str = "mock"):
        """
        Args:
            trace_file: Path to trace JSONL file
            fallback_mode: "mock" | "live" | "error"
        """
        self.trace_file = trace_file
        self.fallback_mode = fallback_mode
        self.context = self._load_trace(trace_file)

    def _load_trace(self, trace_file: Path) -> ExecutionContext:
        """Load trace from JSONL file."""
        records = []
        with open(trace_file, "r") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return ExecutionContext(trace_records=records)

    async def replay(self, workflow_fn, *args, **kwargs) -> Dict[str, Any]:
        """Re-execute workflow with mocked tool calls."""
        # Inject mocks into execution context
        original_tool_executor = self._get_tool_executor()
        mocked_executor = self._create_mock_executor()
        self._set_tool_executor(mocked_executor)

        try:
            result = await workflow_fn(*args, **kwargs)
            return {
                "status": "success",
                "result": result,
                "context": self.context,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "context": self.context,
            }
        finally:
            self._set_tool_executor(original_tool_executor)

    def _create_mock_executor(self):
        """Create mock tool executor that returns traced results."""

        def mock_executor(tool_name: str, inputs: Dict[str, Any]) -> Any:
            record = self.context.next_record()
            if record and record.get("type") == "tool_call":
                if record.get("tool_name") == tool_name:
                    return record.get("result")

            # Fallback behavior
            if self.fallback_mode == "mock":
                return self._get_default_result(tool_name)
            elif self.fallback_mode == "live":
                # Execute live (expensive)
                import warnings

                warnings.warn(f"Trace mismatch for {tool_name}, falling back to live execution")
                return self._execute_live(tool_name, inputs)
            else:  # error
                raise RuntimeError(f"Trace mismatch for {tool_name}")

        return mock_executor

    def _get_default_result(self, tool_name: str) -> Any:
        """Return sensible default based on tool type."""
        defaults = {
            "read_file": "",
            "write_file": "success",
            "bash": {"stdout": "", "stderr": "", "returncode": 0},
            "llm_call": "Mock response",
        }
        return defaults.get(tool_name, None)

    def _execute_live(self, tool_name: str, inputs: Dict[str, Any]) -> Any:
        """Execute tool live (fallback)."""
        # Delegate to real tool execution
        pass
```

---

### 3. LLMCallMocker

**Purpose**: Intercept and mock LLM calls during replay.

**Implementation**:

```python
# thegent/trace/llm_mocker.py
from typing import Dict, Any, Optional
import hashlib


class LLMCallMocker:
    """Mocks LLM calls from trace data."""

    def __init__(self, trace_context):
        self.trace_context = trace_context
        self.call_cache = {}

    def mock_llm_call(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Mock LLM call by returning traced response."""
        # Hash the call signature for lookup
        call_hash = self._hash_call(model, prompt, temperature)

        # Look up in trace
        record = self._find_trace_record(model, prompt)
        if record:
            return record.get("result", "")

        # Fallback
        return f"[MOCK] Model={model}, Tokens={max_tokens}"

    def _hash_call(self, model: str, prompt: str, temperature: float) -> str:
        """Hash LLM call for matching."""
        key = f"{model}:{prompt}:{temperature}"
        return hashlib.sha256(key.encode()).hexdigest()[:8]

    def _find_trace_record(self, model: str, prompt_prefix: str) -> Optional[Dict]:
        """Find matching trace record for LLM call."""
        for record in self.trace_context.trace_records:
            if record.get("type") == "tool_call" and record.get("tool_name") in ["llm_call", "claude", "gpt"]:
                # Match by model and prompt similarity
                if record.get("model") == model:
                    return record
        return None
```

---

### 4. DiffAnalyzer

**Purpose**: Compare original vs. replayed execution and classify differences.

**Implementation**:

```python
# thegent/trace/diff_analyzer.py
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum


class ChangeType(Enum):
    DETERMINISTIC = "deterministic"
    NON_DETERMINISTIC = "non_deterministic"


@dataclass
class Difference:
    tool_name: str
    call_index: int
    original: str
    replayed: str
    change_type: ChangeType
    reason: str = ""


class DiffAnalyzer:
    """Compares original and replayed executions."""

    def __init__(self, original_trace_file: str, replayed_trace_file: str):
        self.original_records = self._load_trace(original_trace_file)
        self.replayed_records = self._load_trace(replayed_trace_file)

    def analyze(self) -> Dict[str, Any]:
        """Analyze differences."""
        differences = []
        matching = 0

        for i, (orig, repl) in enumerate(zip(self.original_records, self.replayed_records)):
            if self._records_equal(orig, repl):
                matching += 1
            else:
                diff = self._classify_difference(orig, repl, i)
                differences.append(diff)

        return {
            "total_calls": len(self.original_records),
            "matching": matching,
            "divergent": len(differences),
            "differences": differences,
            "summary": self._generate_summary(differences),
        }

    def _records_equal(self, rec1: Dict, rec2: Dict) -> bool:
        """Check if records are equal."""
        # Compare results, ignoring metadata
        return rec1.get("tool_name") == rec2.get("tool_name") and rec1.get("result") == rec2.get("result")

    def _classify_difference(self, orig: Dict, repl: Dict, index: int) -> Difference:
        """Classify difference as deterministic or non-deterministic."""
        tool_name = orig.get("tool_name", "unknown")

        # Deterministic changes: model upgrade, config change
        if self._is_config_change(orig, repl):
            change_type = ChangeType.DETERMINISTIC
            reason = "Config or model parameter changed"
        # Non-deterministic: unexpected changes in same config
        else:
            change_type = ChangeType.NON_DETERMINISTIC
            reason = "Unexpected output divergence (logic bug or flaky code)"

        return Difference(
            tool_name=tool_name,
            call_index=index,
            original=str(orig.get("result"))[:100],
            replayed=str(repl.get("result"))[:100],
            change_type=change_type,
            reason=reason,
        )

    def _is_config_change(self, orig: Dict, repl: Dict) -> bool:
        """Detect if difference is due to config change."""
        # Check for model, provider, or routing changes
        model_changed = orig.get("model") != repl.get("model")
        provider_changed = orig.get("provider") != repl.get("provider")
        return model_changed or provider_changed

    def _generate_summary(self, differences: List[Difference]) -> str:
        """Generate human-readable summary."""
        if not differences:
            return "100% match - no divergences"

        deterministic = sum(1 for d in differences if d.change_type == ChangeType.DETERMINISTIC)
        non_deterministic = len(differences) - deterministic

        if non_deterministic == 0:
            return f"All {deterministic} divergences are deterministic (expected)"
        else:
            return f"{non_deterministic} non-deterministic divergences detected - review needed"

    def _load_trace(self, trace_file: str) -> List[Dict]:
        """Load trace from file."""
        records = []
        with open(trace_file, "r") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records
```

---

### 5. TraceVariator

**Purpose**: Modify traces parametrically for simulation.

**Implementation**:

```python
# thegent/trace/variator.py
from typing import List, Dict, Any
from pathlib import Path
import copy


class TraceVariator:
    """Modifies traces parametrically for simulation."""

    def __init__(self, base_trace_file: Path):
        self.base_trace = self._load_trace(base_trace_file)

    def vary_model(self, new_model: str) -> List[Dict]:
        """Create variation with different model."""
        varied = copy.deepcopy(self.base_trace)
        for record in varied:
            if record.get("type") == "tool_call":
                # Update model reference in record
                record["model"] = new_model
                # Simulate different token counts for new model
                record["tokens_used"] = int(record.get("tokens_used", 0) * 0.8)
        return varied

    def vary_routing(self, new_policy: str) -> List[Dict]:
        """Create variation with different routing policy."""
        varied = copy.deepcopy(self.base_trace)
        for record in varied:
            if record.get("type") == "decision" and "routing" in record.get("decision_type", ""):
                record["choice"] = new_policy
                record["reasoning"] = f"Routing policy changed to: {new_policy}"
        return varied

    def vary_config(self, config_changes: Dict[str, Any]) -> List[Dict]:
        """Create variation with config changes."""
        varied = copy.deepcopy(self.base_trace)
        for record in varied:
            if record.get("type") == "session":
                record["config"].update(config_changes)
        return varied

    def batch_vary(self, parameter_grid: Dict[str, List[Any]]) -> List[tuple[str, List[Dict]]]:
        """Create multiple variations from parameter grid."""
        variations = []

        # Example: vary over models and routing policies
        for model in parameter_grid.get("models", []):
            for policy in parameter_grid.get("routing_policies", []):
                trace = self.vary_model(model)
                trace = self._apply_routing(trace, policy)

                variant_name = f"model={model}_routing={policy}"
                variations.append((variant_name, trace))

        return variations

    def _load_trace(self, trace_file: Path) -> List[Dict]:
        """Load trace from file."""
        records = []
        with open(trace_file, "r") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records
```

---

## Data Flow

### Recording Flow

```
Agent Execution
    ↓
Tool Invocation
    ↓
TraceRecorder.record_tool_call(tool, inputs, result, ...)
    ↓
Async Queue
    ↓
TraceRecorder._write_worker()
    ↓
trace-<session_id>.jsonl (append)
```

### Replay Flow

```
ReplayEngine.replay(workflow)
    ↓
Load Trace (JSONL)
    ↓
Mock Tool Executor
    ├─ LLMCallMocker (return traced response)
    ├─ FileIOStubber (read from snapshots)
    ├─ BashStubber (return traced output)
    └─ APIMocker (return traced response)
    ↓
Execute Workflow (mocked)
    ↓
Return Result
```

### Diff Flow

```
Original Trace + Replayed Trace
    ↓
DiffAnalyzer.analyze()
    ↓
Compare Records (tool-by-tool)
    ↓
Classify Differences
    ├─ Config Changed? → Deterministic
    └─ Same Config? → Non-Deterministic
    ↓
DiffReport (summary + details)
```

---

## Integration Points

### 1. Agent Execution Pipeline

Inject TraceRecorder at execution layer:

```python
# In agent runner
async def execute_with_trace(workflow_fn, session_id):
    recorder = TraceRecorder(session_id)
    await recorder.start()

    try:
        result = await workflow_fn()
        return result
    finally:
        await recorder.stop()
```

### 2. Tool Execution Layer

Wrap tool calls with recorder:

```python
# In tool executor
async def execute_tool(tool_name, inputs):
    start_time = time.time()
    try:
        result = await tool_impl(tool_name, inputs)
        duration = time.time() - start_time

        await recorder.record_tool_call(
            tool_name=tool_name,
            inputs=inputs,
            result=result,
            duration_ms=duration * 1000,
            tokens_used=estimate_tokens(result),
            cost=estimate_cost(tokens_used),
        )
        return result
    except Exception as e:
        await recorder.record_tool_call(..., status="error", error_msg=str(e))
        raise
```

### 3. Quality Gate

Integrate DiffAnalyzer for regression detection:

```python
# In quality gate
if model_upgrade_detected():
    original_trace = get_baseline_trace()
    replayed_trace = replay_with_new_model()

    diff_report = DiffAnalyzer(original_trace, replayed_trace).analyze()
    if diff_report["non_deterministic"] > 0:
        raise QualityGateFailure(f"Regressions detected: {diff_report['summary']}")
```

### 4. MCP Tool Interface

Expose replay as MCP tool:

```python
# In MCP server
@mcp_tool
def thegent_replay_trace(trace_file: str, mode: str = "mock") -> Dict:
    """Replay a trace with mocked LLM calls."""
    engine = ReplayEngine(Path(trace_file), fallback_mode=mode)
    result = await engine.replay(execute_workflow)
    return result
```

---

## Configuration

### Trace Configuration (YAML)

```yaml
# ~/.thegent/trace-config.yaml
trace:
  enabled: true
  async_recording: true
  trace_dir: ~/.thegent/traces

  # Redaction policy
  redact:
    - api_key
    - password
    - token
    - secret
    - user_email

  # Retention
  ttl_days: 7
  max_storage_gb: 10
  compression: zstd # zstd | gzip

  # Sampling (record 1 in N traces)
  sample_rate: 1.0

replay:
  fallback_mode: mock # mock | live | error
  validate_traces: true

variator:
  models:
    - claude-opus-4.6
    - claude-sonnet-4.5
    - gemini-3-flash
  routing_policies:
    - prefer_direct
    - prefer_proxy
    - cheapest
```

---

## Testing Strategy

### Unit Tests

1. **TraceRecorder**: Test record creation, serialization, compression
2. **ReplayEngine**: Test trace loading, mock execution, fallback modes
3. **LLMCallMocker**: Test call matching, fallback behavior
4. **DiffAnalyzer**: Test record comparison, classification accuracy
5. **TraceVariator**: Test parametric variations, batch generation

### Integration Tests

1. **End-to-End Replay**: Record real workflow, replay with mocks, validate output
2. **Regression Detection**: Record baseline, replay with model change, verify classification
3. **Simulation**: Generate variations, batch replay, compare costs

### Performance Tests

1. **Recording Overhead**: Measure execution time with/without recording (<10%)
2. **Replay Latency**: Measure replay time for 100, 1000 tool calls
3. **Compression Ratio**: Verify >50% compression

---

## Deployment Checklist

- [ ] TraceRecorder async writer handles errors gracefully
- [ ] TTL cleanup runs daily, respects quota
- [ ] Sensitive data redaction covers all patterns
- [ ] Trace file validation (checksum, corruption detection)
- [ ] CLI commands (`thegent replay`, `thegent vary`) tested end-to-end
- [ ] Monitoring: trace storage, recording overhead, replay latency
- [ ] Documentation: trace format spec, CLI guide, troubleshooting
- [ ] Canary deployment to 5% of traffic
- [ ] Production monitoring (1 week) before 100% rollout

---

**Document Version**: 1.0
**Last Updated**: 2026-02-18
**Status**: Ready for implementation
