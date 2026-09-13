# Comprehensive Benchmarking Strategy

## Overview

This document outlines a comprehensive benchmarking strategy for measuring and validating performance improvements in thegent's migration from shell scripts to Rust/Go implementations.

---

## Benchmarking Tools

### 1. Hyperfine (Command-Line Benchmarking)

**Installation**:
```bash
cargo install hyperfine
# or
brew install hyperfine
```

**Usage**:
```bash
hyperfine \
  --warmup 3 \
  --runs 10 \
  --export-json results.json \
  'bash -c "source hooks/lib/common.sh; detect_tools_bash"' \
  'thegent-tool-detect --json'
```

**Features**:
- Statistical analysis across multiple runs
- Warmup runs to account for caching
- Outlier detection
- Export to JSON/CSV/Markdown

### 2. Criterion.rs (Rust Micro-Benchmarking)

**Setup** (`Cargo.toml`):
```toml
[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }

[[bench]]
name = "tool_detection"
harness = false
```

**Benchmark** (`benches/tool_detection.rs`):
```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use thegent_tool_detect::ToolDetector;

fn bench_tool_detection(c: &mut Criterion) {
    let detector = ToolDetector::new();

    c.bench_function("detect_all_tools", |b| {
        b.iter(|| {
            black_box(detector.detect_all());
        });
    });

    c.bench_function("detect_cached", |b| {
        detector.detect_all(); // Warm cache
        b.iter(|| {
            black_box(detector.detect_all());
        });
    });
}

criterion_group!(benches, bench_tool_detection);
criterion_main!(benches);
```

**Run**:
```bash
cargo bench --bench tool_detection
```

### 3. Custom Benchmark Suite

**Implementation** (`thegent-benchmark` crate):
- End-to-end benchmarks
- Real-world workload simulation
- Performance regression detection
- Comparative analysis

---

## Benchmark Scenarios

### Scenario 1: Tool Detection

**Bash Implementation**:
```bash
time (
  JQ_CMD="$(command -v jaq 2>/dev/null || command -v jq 2>/dev/null || echo jq)"
  RG_CMD="$(command -v rg 2>/dev/null || true)"
  FD_CMD="$(command -v fd 2>/dev/null || command -v fdfind 2>/dev/null || true)"
  TIMEOUT_CMD="$(command -v gtimeout 2>/dev/null || command -v timeout 2>/dev/null || echo "")"
)
```

**Rust Implementation**:
```bash
time thegent-tool-detect --json
```

**Expected Results**:
- Bash: 60ms average
- Rust: 1ms average (cached), 10ms (uncached)
- Improvement: 60x (cached), 6x (uncached)

### Scenario 2: PATH Resolution

**Bash Implementation**:
```bash
time (
  for dir in $(echo $PATH | tr ':' ' '); do
    if [ -f "$dir/codex" ]; then
      echo "$dir/codex"
      break
    fi
  done
)
```

**Rust Implementation**:
```bash
time thegent-path-resolve codex
```

**Expected Results**:
- Bash: 20ms average
- Rust: 0.5ms average
- Improvement: 40x

### Scenario 3: Process Scanning

**Python Implementation**:
```python
import subprocess
import time

start = time.time()
result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
duration = time.time() - start
print(f"Duration: {duration * 1000:.2f}ms")
```

**Rust Implementation**:
```rust
use sysinfo::System;

let start = Instant::now();
let mut sys = System::new_all();
sys.refresh_all();
let duration = start.elapsed();
println!("Duration: {:?}", duration);
```

**Expected Results**:
- Python: 50ms average
- Rust: 0.5ms average
- Improvement: 100x

### Scenario 4: Hook Execution

**Bash Implementation**:
```bash
time (
  source hooks/lib/common.sh
  detect_tools
  resolve_binary codex
  execute_hook pretool "$(cat event.json)"
)
```

**Rust Implementation**:
```bash
time thegent-hook-dispatcher pretool event.json
```

**Expected Results**:
- Bash: 200ms average
- Rust: 20ms average
- Improvement: 10x

---

## Benchmarking Workflow

### 1. Baseline Measurement

```bash
# Measure current performance
hyperfine \
  --warmup 3 \
  --runs 50 \
  --export-json baseline.json \
  'bash -c "source hooks/lib/common.sh; detect_tools"'
```

### 2. Implementation

Implement Rust version with same functionality.

### 3. Comparative Benchmarking

```bash
hyperfine \
  --warmup 3 \
  --runs 50 \
  --export-json comparison.json \
  'bash -c "source hooks/lib/common.sh; detect_tools"' \
  'thegent-tool-detect --json'
```

### 4. Analysis

```bash
# Compare results
python3 scripts/analyze_benchmarks.py baseline.json comparison.json
```

### 5. Regression Testing

```bash
# Run benchmarks in CI
cargo bench --bench tool_detection
# Fail if performance regresses by >10%
```

---

## Performance Targets

| Operation | Current (bash) | Target (Rust) | Status |
|-----------|---------------|---------------|--------|
| Tool detection | 60ms | 1ms (cached) | ✅ |
| PATH resolution | 20ms | 0.5ms | ✅ |
| Process scanning | 50ms | 0.5ms | ✅ |
| File discovery | 30ms | 2ms | 🔄 |
| Git operations | 100ms | 10ms | 🔄 |
| Hook dispatch | 200ms | 20ms | 🔄 |
| JSON parsing | 5ms | 0.1ms | ✅ |

---

## Continuous Benchmarking

### CI Integration

```yaml
# .github/workflows/benchmark.yml
name: Benchmark

on: [push, pull_request]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      - run: cargo bench --bench tool_detection
      - run: cargo bench --bench path_resolution
      - uses: benchmark-action/github-action@v1
        with:
          tool: 'cargo'
          output-file-path: 'benchmark-results.json'
```

### Performance Regression Detection

```rust
pub fn check_regression(current: Duration, baseline: Duration) -> bool {
    let ratio = current.as_secs_f64() / baseline.as_secs_f64();
    if ratio > 1.1 {
        eprintln!("Performance regression: {:.2}x slower", ratio);
        return true;
    }
    false
}
```

---

## Benchmarking Best Practices

1. **Warmup Runs**: Always include warmup runs to account for caching
2. **Multiple Runs**: Run benchmarks multiple times for statistical significance
3. **Outlier Detection**: Identify and handle outliers
4. **Consistent Environment**: Use same machine/environment for comparisons
5. **Real-World Workloads**: Benchmark with realistic data sizes
6. **Documentation**: Document benchmark methodology and results
7. **Automation**: Automate benchmarking in CI/CD
8. **Visualization**: Create charts and graphs for easy comparison

---

## Tools & Resources

- [Hyperfine](https://github.com/sharkdp/hyperfine) - Command-line benchmarking
- [Criterion.rs](https://github.com/bheisler/criterion.rs) - Rust micro-benchmarking
- [Flamegraph](https://github.com/flamegraph-rs/flamegraph) - Performance profiling
- [perf](https://perf.wiki.kernel.org/) - Linux performance analysis
- [Instruments](https://developer.apple.com/instruments/) - macOS performance analysis


---
## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index
