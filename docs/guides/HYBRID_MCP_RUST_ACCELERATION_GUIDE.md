---
title: Hybrid MCP Server Implementation Guide - FastMCP + Rust Acceleration
date: 2026-02-22
status: active
owner: thegent
tags: [guide, MCP, FastMCP, Rust, PyO3, maturin, performance]
---

# Hybrid MCP Server: FastMCP 3.x + Rust Hot-Path Acceleration

**Objective:** Achieve 70% of full-Rust throughput gains (3,500+ QPS) while maintaining FastMCP's developer experience and Python integration.

**Effort:** 2-3 weeks | **Risk:** Medium | **ROI:** High

---

## Table of Contents

1. [Architecture](#architecture)
2. [Prerequisites](#prerequisites)
3. [Implementation Steps](#implementation-steps)
4. [Performance Testing](#performance-testing)
5. [Troubleshooting](#troubleshooting)
6. [Decision Points](#decision-points)

---

## Architecture

### Hybrid Server Layout

```
┌─────────────────────────────────────────────────┐
│  FastMCP 3.x Server (Python)                    │
│  ├─ Standard tools (I/O-bound)                  │
│  │  ├─ run_tool (agent execution)               │
│  │  ├─ session_list (DB queries)                │
│  │  └─ api_call (REST) → 100-300ms              │
│  │                                              │
│  └─ Accelerated tools (CPU-bound, Rust)         │
│     ├─ diff_tool (Rust impl)                    │
│     ├─ search_codebase (Rust impl)              │
│     ├─ parse_ast (Rust impl)                    │
│     └─ contract_validate (Rust impl) → 1-5ms   │
└────────────────┬────────────────────────────────┘
                 │
         ┌───────┴────────┐
         │                │
         ▼                ▼
    [Python tools]   [Rust tools via PyO3]
    Import directly  Import as .whl package
```

### Tool Categorization

**Stay in FastMCP (Python):**

- I/O-bound: API calls, DB queries, file I/O
- Governance: hooks, escalation, contracts
- Dynamic: introspection, discovery, listing

**Move to Rust (PyO3):**

- CPU-bound: diff, search, parse, validate
- Hot-path: called >100x/sec per server
- Latency-critical: P99 <5ms required

---

## Prerequisites

### Environment

```bash
# Check current setup
python --version          # 3.10+ required
rustc --version          # 1.70+ required
cargo --version          # 1.70+ required

# Verify PyO3 support
pip show pyo3            # Optional, auto-installed by maturin
```

### Tool Stack

| Tool        | Purpose                       | Version        |
| ----------- | ----------------------------- | -------------- |
| **Python**  | FastMCP server, orchestration | 3.10+          |
| **Rust**    | Hot-path implementation       | 1.70+ (stable) |
| **PyO3**    | Rust ↔ Python bindings       | 0.21+          |
| **Maturin** | Build tool for PyO3 wheels    | 1.0+           |
| **Pytest**  | Testing                       | 7.0+           |

### Installation

```bash
# Install maturin (if not already present)
pip install maturin[patchelf]  # patchelf for Linux compatibility

# Verify maturin
maturin --version              # 1.0+
```

---

## Implementation Steps

### Step 1: Profile Current FastMCP Server (Day 1)

**Goal:** Identify which tools are actually bottlenecks.

#### 1.1 Enable OpenTelemetry

FastMCP 3.x has native OTel instrumentation. Enable it:

```python
# In src/thegent/mcp/server.py, at startup:

import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Configure Jaeger exporter (or your collector)
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(jaeger_exporter))

logging.basicConfig(level=logging.INFO)
```

#### 1.2 Run Load Test

Create a load test that simulates 30+ agents calling tools:

```python
# tests/load/test_mcp_load.py

import asyncio
import time
from fastmcp import FastMCP


async def simulate_agent_calls(num_agents: int = 30, calls_per_agent: int = 100):
    """Simulate realistic agent workload."""
    tasks = []

    for agent_id in range(num_agents):
        for call_num in range(calls_per_agent):
            # Mix of tools: 70% I/O, 30% CPU-bound
            if call_num % 10 < 3:
                # CPU-bound: diff, search
                tool_name = "search_codebase"
                args = {"query": "test_query", "limit": 10}
            else:
                # I/O-bound: API calls, DB queries
                tool_name = "run_tool"
                args = {"name": "ls", "timeout": 30}

            tasks.append(call_tool(tool_name, args))

    start = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    elapsed = time.time() - start

    success = sum(1 for r in results if not isinstance(r, Exception))
    qps = len(results) / elapsed

    print(f"Completed {success}/{len(results)} calls in {elapsed:.1f}s ({qps:.0f} QPS)")
    return qps


# Run: pytest tests/load/test_mcp_load.py -v --durations=10
```

**Collect metrics:**

- Tool call latency distribution (p50, p95, p99)
- Throughput (QPS)
- Top 5 slowest tools
- CPU-bound vs I/O-bound breakdown

#### 1.3 Document Baseline

Create `docs/reference/MCP_BASELINE_METRICS.md`:

```markdown
# FastMCP Baseline Metrics (Pre-Hybrid)

## Load Test Results (30 agents, 100 calls/agent = 3,000 total)

| Metric      | Value   |
| ----------- | ------- |
| Total time  | 45.2s   |
| Throughput  | 66 QPS  |
| P50 latency | 200ms   |
| P95 latency | 800ms   |
| P99 latency | 2,500ms |

## Slowest Tools

1. search_codebase: avg 800ms (30% of calls, 25% of total time)
2. diff_tool: avg 500ms (10% of calls, 5% of total time)
3. parse_ast: avg 300ms (5% of calls, 2% of total time)
4. run_tool: avg 150ms (40% of calls, 6% of total time)
5. list_sessions: avg 50ms (15% of calls, 0.8% of total time)

## Recommendation

Accelerate: search_codebase, diff_tool, parse_ast (top 3 = 32% of latency)
Expected gain: 2-3x (300+ QPS target)
```

---

### Step 2: Design Rust Accelerators (Day 2)

**Goal:** Plan the Rust modules without writing code yet.

#### 2.1 Select 3-5 Tools for Acceleration

Criteria:

- Appears in top-5 slowest tools
- CPU-bound (not I/O-limited)
- Stateless (no complex shared state)
- High call volume (>50 calls/min)

**Recommended for thegent (based on research):**

1. **search_codebase** (800ms) - String search in large codebases
2. **diff_tool** (500ms) - Diff two documents
3. **parse_ast** (300ms) - Parse code to AST
4. _(Optional)_ **contract_validate** (150ms) - Complex validation logic
5. _(Optional)_ **format_code** (100ms) - Code formatting

#### 2.2 Define Interface Contract

For each tool, document the interface:

```rust
// src/mcp_accelerators/search.rs

/// Search a codebase for a query string.
///
/// # Arguments
/// * `query` - Search string (regex or literal)
/// * `limit` - Max results to return
/// * `path` - Root directory to search (optional)
///
/// # Returns
/// JSON array of matches: [{"file": "...", "line": 10, "match": "..."}]
///
/// # Performance
/// Expected: <100ms for 1M lines, <5 results
pub fn search_codebase(query: &str, limit: usize, path: Option<&str>) -> Result<String>;
```

#### 2.3 Create Project Structure

```
src/
  thegent/
    mcp/
      server.py         # Existing FastMCP server
      server_*.py       # Existing modules

  mcp_accelerators/     # NEW: Rust accelerators
    Cargo.toml          # Rust package config
    src/
      lib.rs            # Rust library entry point
      search.rs         # search_codebase implementation
      diff.rs           # diff_tool implementation
      parse.rs          # parse_ast implementation
      utils.rs          # Shared utilities
```

---

### Step 3: Implement Rust Accelerators (Days 3-7)

**Goal:** Implement each tool in Rust with PyO3 bindings.

#### 3.1 Initialize Rust Project

```bash
# Create Maturin project
cd src/mcp_accelerators
maturin init --name thegent_mcp_accelerators

# Verify structure
ls -la
# Cargo.toml, src/lib.rs, pyproject.toml
```

#### 3.2 Configure Cargo.toml

```toml
# src/mcp_accelerators/Cargo.toml

[package]
name = "thegent_mcp_accelerators"
version = "0.1.0"
edition = "2021"

[dependencies]
pyo3 = { version = "0.21", features = ["extension-module"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
regex = "1.10"
rayon = "1.7"  # Parallel processing

[lib]
crate-type = ["cdylib"]

[profile.release]
opt-level = 3
lto = true
```

#### 3.3 Implement First Tool: search_codebase

```rust
// src/mcp_accelerators/src/search.rs

use pyo3::prelude::*;
use regex::Regex;
use serde::Serialize;
use std::fs;
use std::path::Path;

#[derive(Serialize)]
pub struct SearchMatch {
    file: String,
    line: usize,
    match_text: String,
}

#[pyfunction]
pub fn search_codebase(
    query: &str,
    limit: usize,
    path: Option<&str>,
) -> PyResult<String> {
    let root = path.unwrap_or(".");
    let regex = Regex::new(query)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

    let mut results = Vec::new();

    // Walk directory
    for entry in walkdir::WalkDir::new(root)
        .into_iter()
        .filter_map(|e| e.ok())
    {
        if results.len() >= limit {
            break;
        }

        let path = entry.path();
        if !path.is_file() {
            continue;
        }

        // Skip binaries, large files
        if let Ok(metadata) = path.metadata() {
            if metadata.len() > 10_000_000 {
                continue; // Skip >10MB files
            }
        }

        if let Ok(content) = fs::read_to_string(path) {
            for (line_num, line) in content.lines().enumerate() {
                if regex.is_match(line) && results.len() < limit {
                    results.push(SearchMatch {
                        file: path.to_string_lossy().to_string(),
                        line: line_num + 1,
                        match_text: line.to_string(),
                    });
                }
            }
        }
    }

    Ok(serde_json::to_string(&results)?)
}
```

Complete `lib.rs`:

```rust
// src/mcp_accelerators/src/lib.rs

mod search;
mod diff;
mod parse;

use pyo3::prelude::*;

#[pymodule]
#[pyo3(name = "thegent_mcp_accelerators")]
fn thegent_mcp_accelerators(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(search::search_codebase, m)?)?;
    m.add_function(wrap_pyfunction!(diff::diff_tool, m)?)?;
    m.add_function(wrap_pyfunction!(parse::parse_ast, m)?)?;
    Ok(())
}
```

#### 3.4 Build the Wheel

```bash
# Build wheel for current platform
maturin develop  # Install in dev mode for testing

# Or build release wheel
maturin build --release

# Verify wheel was created
ls -la target/wheels/
# thegent_mcp_accelerators-0.1.0-cp310-cp310-macosx_10_9_x86_64.whl
```

#### 3.5 Test Rust Implementation

```python
# tests/test_mcp_accelerators.py

import pytest
from thegent_mcp_accelerators import search_codebase, diff_tool, parse_ast


def test_search_codebase():
    """Test search_codebase Rust implementation."""
    # Create test file
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, "w") as f:
            f.write("def foo():\n    pass\ndef bar():\n    pass\n")

        # Call Rust function
        results_json = search_codebase("def", limit=10, path=tmpdir)

        # Verify results
        import json

        results = json.loads(results_json)
        assert len(results) == 2
        assert results[0]["line"] == 1


def test_search_codebase_performance(benchmark):
    """Benchmark search_codebase (Rust vs Python)."""
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create large test file (1M lines)
        test_file = os.path.join(tmpdir, "large.py")
        with open(test_file, "w") as f:
            for i in range(1_000_000):
                f.write(f"line_{i} = {i}\n")

        # Benchmark
        result = benchmark(search_codebase, "500000", limit=10, path=tmpdir)
        assert result is not None


# Run with pytest-benchmark
# pytest tests/test_mcp_accelerators.py --benchmark-only
```

---

### Step 4: Integrate into FastMCP Server (Day 8-9)

**Goal:** Make Rust tools available to FastMCP clients without changing the interface.

#### 4.1 Create Wrapper Module

```python
# src/thegent/mcp/server_accelerators.py

"""
Rust accelerators for hot-path MCP tools.

Attempts to import Rust implementations (PyO3); falls back to Python
implementations if not available (e.g., during development, wheel not built).
"""

import logging
import json
from typing import Optional

_log = logging.getLogger(__name__)

# Attempt to import Rust accelerators
_ACCELERATORS_AVAILABLE = False
try:
    from thegent_mcp_accelerators import (
        search_codebase as _rust_search_codebase,
        diff_tool as _rust_diff_tool,
        parse_ast as _rust_parse_ast,
    )

    _ACCELERATORS_AVAILABLE = True
    _log.info("Rust accelerators loaded successfully")
except ImportError as e:
    _log.warning(f"Rust accelerators not available: {e}. Using Python fallbacks.")


def search_codebase_impl(query: str, limit: int = 10, path: Optional[str] = None) -> str:
    """
    Search codebase using Rust implementation if available, else Python.

    Returns: JSON string of matches
    """
    if _ACCELERATORS_AVAILABLE:
        return _rust_search_codebase(query, limit, path or ".")
    else:
        # Fallback to Python implementation
        from thegent.mcp.server_research_tools import search_codebase as _py_search

        return json.dumps(_py_search(query, limit, path or "."))


def diff_tool_impl(file_a: str, file_b: str) -> str:
    """
    Diff two files using Rust implementation if available, else Python.

    Returns: Unified diff string
    """
    if _ACCELERATORS_AVAILABLE:
        return _rust_diff_tool(file_a, file_b)
    else:
        # Fallback to Python implementation
        from thegent.mcp.server_research_tools import diff_tool as _py_diff

        return _py_diff(file_a, file_b)


def parse_ast_impl(source: str, language: str = "python") -> str:
    """
    Parse source to AST using Rust implementation if available, else Python.

    Returns: JSON string of AST
    """
    if _ACCELERATORS_AVAILABLE:
        return _rust_parse_ast(source, language)
    else:
        # Fallback to Python implementation
        from thegent.mcp.server_research_tools import parse_ast as _py_parse

        return json.dumps(_py_parse(source, language))
```

#### 4.2 Register Tools in FastMCP Server

```python
# In src/thegent/mcp/server.py, update tool registration:

from thegent.mcp.server_accelerators import (
    search_codebase_impl,
    diff_tool_impl,
    parse_ast_impl,
)

# Existing FastMCP server setup...
app = FastMCP()


# Register accelerated tools
@app.tool()
def search_codebase(query: str, limit: int = 10, path: str = ".") -> str:
    """
    Search codebase for a pattern.

    Uses Rust implementation for performance; falls back to Python if not available.
    """
    return search_codebase_impl(query, limit, path)


@app.tool()
def diff_tool(file_a: str, file_b: str) -> str:
    """
    Diff two files using unified format.

    Uses Rust implementation for performance; falls back to Python if not available.
    """
    return diff_tool_impl(file_a, file_b)


@app.tool()
def parse_ast(source: str, language: str = "python") -> str:
    """
    Parse source code to abstract syntax tree (JSON).

    Uses Rust implementation for performance; falls back to Python if not available.
    """
    return parse_ast_impl(source, language)


# Continue with existing tool registrations...
```

#### 4.3 Update pyproject.toml

Add the Rust wheel as a build dependency:

```toml
# pyproject.toml

[build-system]
requires = ["maturin>=1.0,<2.0"]
build-backend = "maturin"

[project]
# ... existing config ...
dependencies = [
    # ... existing deps ...
    "thegent-mcp-accelerators>=0.1.0",  # Rust wheels
]

[project.optional-dependencies]
dev = [
    # ... existing dev deps ...
    "maturin>=1.0",
    "pytest-benchmark>=4.0",
]
```

#### 4.4 Build & Install

```bash
# From project root:

# Build Rust wheels
cd src/mcp_accelerators
maturin build --release
cd ../../

# Install in editable mode (includes Rust wheel)
pip install -e .

# Verify imports work
python -c "from thegent_mcp_accelerators import search_codebase; print('OK')"
```

---

### Step 5: Performance Testing (Days 10-11)

**Goal:** Validate that hybrid approach achieves 70% of full-Rust gains.

#### 5.1 Create Comparative Benchmark

```python
# tests/benchmarks/test_mcp_hybrid_performance.py

import asyncio
import time
import json
import pytest
from thegent.mcp.server import app  # FastMCP app

# Load test configuration
NUM_AGENTS = 30
CALLS_PER_AGENT = 100
TOOL_MIX = {
    "search_codebase": 0.15,  # CPU-bound, will use Rust
    "diff_tool": 0.10,  # CPU-bound, will use Rust
    "parse_ast": 0.05,  # CPU-bound, will use Rust
    "run_tool": 0.40,  # I/O-bound, stays Python
    "list_sessions": 0.15,  # I/O-bound, stays Python
    "get_resource": 0.15,  # I/O-bound, stays Python
}


async def run_hybrid_benchmark():
    """Run comparative benchmark: FastMCP-only vs Hybrid."""

    # Scenario 1: Pure FastMCP (disable Rust)
    import thegent.mcp.server_accelerators as accel

    original_available = accel._ACCELERATORS_AVAILABLE

    # Test Python path
    accel._ACCELERATORS_AVAILABLE = False
    python_qps = await benchmark_server()
    python_latencies = await collect_latencies()

    # Test Rust path
    accel._ACCELERATORS_AVAILABLE = True
    rust_hybrid_qps = await benchmark_server()
    rust_hybrid_latencies = await collect_latencies()

    # Restore
    accel._ACCELERATORS_AVAILABLE = original_available

    return {
        "python_only": {
            "qps": python_qps,
            "p50": python_latencies[0],
            "p95": python_latencies[1],
            "p99": python_latencies[2],
        },
        "hybrid": {
            "qps": rust_hybrid_qps,
            "p50": rust_hybrid_latencies[0],
            "p95": rust_hybrid_latencies[1],
            "p99": rust_hybrid_latencies[2],
        },
        "improvement": {
            "qps_gain": (rust_hybrid_qps / python_qps - 1) * 100,
            "p99_reduction": (1 - rust_hybrid_latencies[2] / python_latencies[2]) * 100,
        },
    }


async def benchmark_server():
    """Run synthetic load test."""

    tasks = []
    start = time.time()

    for agent_id in range(NUM_AGENTS):
        for call_num in range(CALLS_PER_AGENT):
            # Select tool probabilistically
            import random

            tool = random.choices(list(TOOL_MIX.keys()), weights=list(TOOL_MIX.values()), k=1)[0]

            # Prepare args based on tool
            if tool == "search_codebase":
                args = {"query": "test", "limit": 5}
            elif tool == "diff_tool":
                args = {"file_a": "/tmp/a.txt", "file_b": "/tmp/b.txt"}
            elif tool == "parse_ast":
                args = {"source": "def foo(): pass", "language": "python"}
            else:
                args = {}

            # Queue task
            tasks.append(call_tool(tool, **args))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    elapsed = time.time() - start

    success = sum(1 for r in results if not isinstance(r, Exception))
    qps = success / elapsed

    return qps


async def collect_latencies():
    """Collect latency percentiles."""
    # Implementation: collect call times, sort, return p50, p95, p99
    pass


# Run: pytest tests/benchmarks/test_mcp_hybrid_performance.py -v -s
```

#### 5.2 Compare Against Baseline

```python
# tests/reports/generate_hybrid_report.py

import json
from pathlib import Path


def generate_report(baseline_metrics, hybrid_metrics):
    """Generate comparison report."""

    report = {
        "title": "Hybrid MCP Server Performance Report",
        "date": "2026-02-22",
        "baseline": baseline_metrics,
        "hybrid": hybrid_metrics,
        "improvements": {
            "throughput_gain": f"{(hybrid_metrics['qps'] / baseline_metrics['qps'] - 1) * 100:.1f}%",
            "p99_latency_reduction": f"{(1 - hybrid_metrics['p99'] / baseline_metrics['p99']) * 100:.1f}%",
            "memory_overhead": f"+{hybrid_metrics['memory_mb'] - baseline_metrics['memory_mb']:.0f}MB",
        },
        "recommendation": "PROCEED" if hybrid_metrics["qps"] > baseline_metrics["qps"] * 2 else "EVALUATE",
    }

    with open("docs/reference/MCP_HYBRID_PERFORMANCE_REPORT.md", "w") as f:
        f.write("# Hybrid MCP Performance Report\n\n")
        f.write(json.dumps(report, indent=2))
```

#### 5.3 Document Results

Expected outcomes after optimization:

| Metric          | FastMCP-Only | Hybrid      | Target   | Status  |
| --------------- | ------------ | ----------- | -------- | ------- |
| QPS             | 66           | 150-180     | >150     | ✅ Pass |
| P99 latency     | 2,500ms      | 800-1,200ms | <1,200ms | ✅ Pass |
| Memory          | 120MB        | 130-140MB   | <150MB   | ✅ Pass |
| Throughput gain | Baseline     | 2.2-2.7x    | 2.0x+    | ✅ Pass |

---

### Step 6: Production Deployment (Day 12)

**Goal:** Deploy hybrid server with monitoring.

#### 6.1 Build Release Artifacts

```bash
# Build multi-platform wheels
maturin build --release
pip install twine

# (Optional) Publish to PyPI or private repo
twine upload target/wheels/*

# For deployment: include .whl files in Docker image
```

#### 6.2 Docker Deployment

```dockerfile
# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install Rust wheel
COPY src/mcp_accelerators/target/wheels/*.whl /tmp/
RUN pip install /tmp/*.whl

# Install thegent
COPY . .
RUN pip install -e .

# Run FastMCP server
CMD ["python", "-m", "uvicorn", "thegent.mcp.server:app", "--host", "0.0.0.0", "--port", "3847"]
```

#### 6.3 Monitoring & Alerts

Add OpenTelemetry metrics:

```python
# src/thegent/mcp/server_monitoring.py

from opentelemetry import metrics

meter = metrics.get_meter("thegent-mcp")

# Histogram for tool latency
tool_latency_histogram = meter.create_histogram(
    name="mcp.tool.latency_ms",
    description="Tool call latency",
    unit="ms",
)

# Counter for tool calls
tool_call_counter = meter.create_counter(
    name="mcp.tool.calls",
    description="Tool call count",
    unit="1",
)

# Gauge for Rust acceleration usage
rust_usage_gauge = meter.create_observable_gauge(
    name="mcp.accelerators.available",
    description="Whether Rust accelerators are available",
    unit="1",
)


# Update in tool handlers:
def record_tool_call(tool_name: str, latency_ms: float):
    tool_latency_histogram.record(latency_ms, {"tool": tool_name})
    tool_call_counter.add(1, {"tool": tool_name})
```

---

## Performance Testing

### Test 1: Synthetic Load (Realistic Distribution)

```bash
# Run with pytest-benchmark
pytest tests/benchmarks/test_mcp_hybrid_performance.py \
    --benchmark-only \
    --benchmark-json=results.json

# Analyze results
python -m pytest_benchmark compare results.json
```

### Test 2: Real Agent Workload

If possible, run against actual thegent agents:

```bash
# Run 30 agents for 10 minutes
thegent plan loop --max 30 --duration 600

# Collect OTel metrics
# Check Jaeger UI for tool call distribution
```

### Test 3: Stress Test

```bash
# Ramp up to 100 concurrent agents
pytest tests/load/test_mcp_stress.py -v -s --durations=10
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'thegent_mcp_accelerators'"

**Cause:** Rust wheel not built/installed

**Solution:**

```bash
cd src/mcp_accelerators
maturin develop  # Install wheel in dev mode
cd ../../
python -c "import thegent_mcp_accelerators; print('OK')"
```

---

### Issue: "Rust tool slower than Python version"

**Cause:** Possible causes:

1. Serialization overhead (JSON) dominates
2. Algorithm not optimized for Rust
3. Small input size (Rust overhead not amortized)

**Solution:**

```rust
// Optimize serialization
// Use serde_json::to_value() for direct value passing if possible
// Benchmark algorithm in isolation vs with JSON overhead
```

---

### Issue: "Wheel compatibility errors across Python versions"

**Cause:** Built wheel for one Python version; running on another

**Solution:**

```bash
# Build for multiple versions
for version in 3.10 3.11 3.12; do
    maturin build --release -i python$version
done

# Install version-specific wheel
pip install target/wheels/*cp311*.whl  # For Python 3.11
```

---

### Issue: "Performance gain is <10%, not worth it"

**Cause:** Tool not actually CPU-bound; bottleneck elsewhere

**Solution:**

1. Re-profile to confirm (OTel traces)
2. Check if I/O-bound (network latency dominates)
3. Consider different tool for acceleration
4. Keep Rust implementation anyway (minimal downside, option for future)

---

## Decision Points

### Go / No-Go Decision (Day 11)

**Proceed to Production If:**

- ✅ Throughput gain ≥ 2.0x (150+ QPS)
- ✅ P99 latency reduction ≥ 30% (down to <1,800ms)
- ✅ Memory overhead < 20MB
- ✅ No integration friction (wrapper layer works seamlessly)
- ✅ Rust fallback works (Python path still functional)

**Hold / Iterate If:**

- ⚠️ Throughput gain < 1.5x (reconsider tool selection)
- ⚠️ Rust build takes >2 minutes (optimize build config)
- ⚠️ Wheel compatibility issues (consider lighter FFI approach)

---

## Next Steps

### If Hybrid is Successful:

1. Deploy to production
2. Monitor metrics for 4 weeks
3. Document learnings
4. Evaluate full Rust migration if gains justify

### If Hybrid is Insufficient:

1. Keep as proof-of-concept
2. Revisit bottleneck (may not be CPU-bound)
3. Consider full Rust migration only if business need justifies 4-week effort

---

## References

- [FastMCP 3.x Docs](https://gofastmcp.com/)
- [PyO3 User Guide](https://pyo3.rs/)
- [Maturin Book](https://maturin.rs/)
- [Comprehensive MCP Comparison - FASTMCP_VS_RUST_MCP_SDK_COMPARISON_2026.md](./FASTMCP_VS_RUST_MCP_SDK_COMPARISON_2026.md)
- [MCP Framework Selection Matrix - MCP_FRAMEWORK_SELECTION_MATRIX.md](../reference/MCP_FRAMEWORK_SELECTION_MATRIX.md)
