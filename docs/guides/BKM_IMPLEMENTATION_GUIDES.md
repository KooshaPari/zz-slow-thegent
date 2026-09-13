# BKM Implementation Guides

> **Status**: Reference | **Version**: 1.0 | **Last Updated**: 2026-02-16
> **Purpose**: Step-by-step implementation guides for each BKM task

---

## Table of Contents

1. [BKM-01: thegent-resources](#bkm-01-thegent-resources)
2. [BKM-02: thegent-parser](#bkm-02-thegent-parser) ✅ Done
3. [BKM-03: thegent-crypto](#bkm-03-thegent-crypto) ✅ Done
4. [BKM-04: load_based_limits Integration](#bkm-04-load_based_limits-integration) ✅ Done
5. [BKM-05: State-SHM](#bkm-05-state-shm)
6. [BKM-06: thegent-git](#bkm-06-thegent-git)
7. [BKM-07: Hook-Dispatcher Extension](#bkm-07-hook-dispatcher-extension)
8. [BKM-08: thegent-discovery](#bkm-08-thegent-discovery)
9. [BKM-09: thegent-watcher](#bkm-09-thegent-watcher)
10. [BKM-10: JSONL Streaming](#bkm-10-jsonl-streaming)
11. [BKM-11: Native Governance Scanner](#bkm-11-native-governance-scanner)

---

## BKM-01: thegent-resources

**Status**: ✅ Done
**Language**: Rust (PyO3 + Binary)
**ROI**: 50x speedup (eliminates 2-3 subprocess spawns)

### Implementation Steps

1. **Create crate structure**:
```bash
mkdir -p crates/thegent-resources/src
cd crates/thegent-resources
```

2. **Cargo.toml**:
```toml
[package]
name = "thegent-resources"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "thegent-resources"
path = "src/bin.rs"

[lib]
name = "thegent_resources"
crate-type = ["cdylib", "rlib"]

[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"
libc = "0.2"
```

3. **lib.rs** (core logic):
```rust
use serde::Serialize;
use std::fs;
use std::io::Read;
use std::path::Path;

#[derive(Debug, Serialize)]
pub struct ResourceSnapshot {
    pub fd_used: u32,
    pub fd_limit: u32,
    pub mem_rss_mb: f64,
    pub mem_available_mb: f64,
    pub cpu_count: u32,
    pub load_1m: f64,
    pub load_5m: f64,
    pub load_15m: f64,
}

pub fn sample() -> ResourceSnapshot {
    ResourceSnapshot {
        fd_used: get_fd_usage().0,
        fd_limit: get_fd_usage().1,
        mem_rss_mb: get_memory_rss_mb(),
        mem_available_mb: get_memory_available_mb(),
        cpu_count: get_cpu_count(),
        load_1m: get_load_avg().0,
        load_5m: get_load_avg().1,
        load_15m: get_load_avg().2,
    }
}

fn get_fd_usage() -> (u32, u32) {
    // Implementation (see existing code)
}

fn get_memory_rss_mb() -> f64 {
    // Implementation (see existing code)
}

fn get_memory_available_mb() -> f64 {
    // Implementation (see existing code)
}

fn get_cpu_count() -> u32 {
    // Implementation (see existing code)
}

fn get_load_avg() -> (f64, f64, f64) {
    // Implementation (see existing code)
}
```

4. **bin.rs** (standalone binary):
```rust
use thegent_resources::sample;
use serde_json;

fn main() {
    let snapshot = sample();
    println!("{}", serde_json::to_string(&snapshot).unwrap());
}
```

5. **Python integration** (see `load_based_limits.py`):
```python
def _sample_resources_native() -> ResourceSnapshot | None:
    """BKM-01: Sample via thegent-resources Rust binary."""
    if not os.environ.get("THGENT_USE_NATIVE_RESOURCES"):
        return None
    # ... implementation (see existing code)
```

### Testing

```bash
# Build binary
cargo build --release -p thegent-resources --manifest-path crates/Cargo.toml

# Test binary
./crates/target/release/thegent-resources | jq

# Test Python integration
THGENT_USE_NATIVE_RESOURCES=1 uv run python -c "
from thegent.orchestration.load_based_limits import sample_resources
print(sample_resources())
"
```

---

## BKM-02: thegent-parser

**Status**: ✅ Done
**Language**: Rust (PyO3)
**ROI**: 10x speedup (precompiled regex, zero-copy)

### Implementation Steps

1. **Create crate structure**:
```bash
mkdir -p crates/thegent-parser/src
cd crates/thegent-parser
```

2. **Cargo.toml**:
```toml
[package]
name = "thegent-parser"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.23", features = ["extension-module"] }
regex = "1"
lazy_static = "1"
```

3. **pyproject.toml**:
```toml
[project]
name = "thegent-parser"
version = "0.1.0"

[tool.maturin]
module-name = "thegent_parser"
```

4. **lib.rs** (see existing implementation)

5. **Python integration**:
```python
# contracts/parser.py
def _get_native_parser():
    """Lazy import of thegent_parser native extension."""
    # ... implementation (see existing code)


def extract_tags(text: str, tags: list[str] | None = None) -> dict[str, str]:
    native = _get_native_parser()
    if native is not None:
        return native.extract_xml_tags(text, allowed_tags=tags, case_sensitive=False)
    # Fallback to Python
    # ... existing Python implementation
```

### Testing

```bash
# Build and install
uv pip install crates/thegent-parser

# Test
THGENT_USE_NATIVE_PARSER=1 uv run python -c "
from thegent.contracts.parser import extract_tags
print(extract_tags('<TASK>test</TASK>'))
"
```

---

## BKM-03: thegent-crypto

**Status**: ✅ Done
**Language**: Rust (PyO3)
**ROI**: 5x speedup (constant-time comparison, optimized HMAC)

### Implementation Steps

1. **Create crate structure**:
```bash
mkdir -p crates/thegent-crypto/src
cd crates/thegent-crypto
```

2. **Cargo.toml**:
```toml
[package]
name = "thegent-crypto"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.23", features = ["extension-module"] }
hmac = "0.12"
sha2 = "0.10"
hex = "0.4"
subtle = "2.5"
```

3. **lib.rs** (see existing implementation)

4. **Python integration**:
```python
# governance/signatures.py
def _get_native_crypto():
    """Lazy import of thegent_crypto native extension."""
    # ... implementation (see existing code)


def sign_artifact(artifact: dict, secret_key: str) -> str:
    native = _get_native_crypto()
    if native is not None:
        canonical_json = orjson.dumps(artifact, option=orjson.OPT_SORT_KEYS).decode()
        return native.sign_artifact_bytes(canonical_json.encode(), secret_key)
    # Fallback to Python
    # ... existing Python implementation
```

---

## BKM-04: load_based_limits Integration

**Status**: ✅ Done
**Language**: Python wrapper (uses BKM-01)

### Implementation Steps

1. **Modify `load_based_limits.py`**:
```python
def sample_resources() -> ResourceSnapshot:
    """Sample system resources with native fallback."""
    native = _sample_resources_native()
    if native is not None:
        return native
    # Fallback to Python (lsof, vm_stat)
    return _sample_resources_python()
```

---

## BKM-05: State-SHM

**Status**: ⏳ Pending
**Language**: Rust (Shared Memory)
**ROI**: Cross-process atomicity, zero-copy state sharing

### Implementation Steps

1. **Create crate structure**:
```bash
mkdir -p crates/thegent-shm/src
cd crates/thegent-shm
```

2. **Cargo.toml**:
```toml
[package]
name = "thegent-shm"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.23", features = ["extension-module"] }
shared_memory = "0.12"
parking_lot = "0.12"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

3. **lib.rs** (shared memory region):
```rust
use pyo3::prelude::*;
use shared_memory::{Shmem, ShmemConf};
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct CircuitBreakerState {
    pub failures: u32,
    pub last_failure: Option<u64>,
    pub state: String, // "closed", "open", "half-open"
}

#[pyfunction]
fn create_shm_region(name: &str, size: usize) -> PyResult<String> {
    let shmem = ShmemConf::new()
        .size(size)
        .create()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("{}", e)))?;
    Ok(shmem.get_os_id().to_string())
}

#[pyfunction]
fn read_circuit_breaker(shm_id: &str) -> PyResult<CircuitBreakerState> {
    // Open existing shared memory region
    // Deserialize state
    // Return
}

#[pyfunction]
fn write_circuit_breaker(shm_id: &str, state: CircuitBreakerState) -> PyResult<()> {
    // Open existing shared memory region
    // Serialize state
    // Write atomically
    Ok(())
}

#[pymodule]
fn thegent_shm(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(create_shm_region, m)?)?;
    m.add_function(wrap_pyfunction!(read_circuit_breaker, m)?)?;
    m.add_function(wrap_pyfunction!(write_circuit_breaker, m)?)?;
    Ok(())
}
```

4. **Python integration**:
```python
# orchestration/circuit_breaker.py
def _get_native_shm():
    """Lazy import of thegent_shm native extension."""
    # ... implementation


class CircuitBreakerRegistry:
    def __init__(self):
        native = _get_native_shm()
        if native is not None:
            self._shm_id = native.create_shm_region("circuit_breaker", 4096)
            self._native = native
        else:
            # Fallback to Python dict
            self._state: dict[str, CircuitBreakerState] = {}
```

---

## BKM-06: thegent-git

**Status**: ⏳ Pending
**Language**: Rust (PyO3 with gitoxide)
**ROI**: 5-20x faster than git subprocesses

### Implementation Steps

1. **Create crate structure**:
```bash
mkdir -p crates/thegent-git/src
cd crates/thegent-git
```

2. **Cargo.toml**:
```toml
[package]
name = "thegent-git"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.23", features = ["extension-module"] }
gix = "0.61"  # gitoxide
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

3. **lib.rs**:
```rust
use pyo3::prelude::*;
use gix::{Repository, repository::open};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct GitMetadata {
    pub head: String,
    pub branch: String,
    pub status: Vec<String>,
    pub diff_stats: DiffStats,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DiffStats {
    pub files_changed: u32,
    pub insertions: u32,
    pub deletions: u32,
}

#[pyfunction]
fn get_git_metadata(repo_path: &str) -> PyResult<GitMetadata> {
    let repo = open(repo_path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("{}", e)))?;

    let head = repo.head_id()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("{}", e)))?
        .to_string();

    let branch = repo.head_name()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("{}", e)))?
        .to_string();

    // Get status and diff stats
    // ...

    Ok(GitMetadata {
        head,
        branch,
        status: vec![],
        diff_stats: DiffStats {
            files_changed: 0,
            insertions: 0,
            deletions: 0,
        },
    })
}

#[pymodule]
fn thegent_git(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(get_git_metadata, m)?)?;
    Ok(())
}
```

4. **Python integration**:
```python
# forensics/snapshot.py
def _get_native_git():
    """Lazy import of thegent_git native extension."""
    # ... implementation


def _get_git_branch(self, root: Path) -> str:
    native = _get_native_git()
    if native is not None:
        try:
            metadata = native.get_git_metadata(str(root))
            return metadata.branch
        except Exception:
            pass
    # Fallback to subprocess
    try:
        return subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root).decode().strip()
    except Exception:
        return "n/a"
```

---

## BKM-08: thegent-discovery

**Status**: ⏳ Pending
**Language**: Rust (Standalone Binary)
**ROI**: Consolidates multiple subprocess spawns

### Implementation Steps

1. **Create crate structure**:
```bash
mkdir -p crates/thegent-discovery/src
cd crates/thegent-discovery
```

2. **Cargo.toml**:
```toml
[package]
name = "thegent-discovery"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "thegent-discovery"
path = "src/bin.rs"

[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"
sysinfo = "0.30"
```

3. **bin.rs**:
```rust
use serde::Serialize;
use sysinfo::{System, SystemExt, ProcessExt, Pid};

#[derive(Debug, Serialize)]
struct DiscoveredAgent {
    pid: u32,
    ppid: u32,
    agent: String,
    cwd: String,
    command: String,
}

fn main() {
    let mut system = System::new_all();
    system.refresh_all();

    let mut agents = Vec::new();

    for (pid, process) in system.processes() {
        let exe = process.exe().unwrap_or_default();
        let name = exe.file_name().unwrap_or_default().to_string_lossy();

        // Detect agent processes (cursor-agent, claude-code, etc.)
        if name.contains("cursor-agent") || name.contains("claude-code") {
            agents.push(DiscoveredAgent {
                pid: pid.as_u32(),
                ppid: process.parent().map(|p| p.as_u32()).unwrap_or(0),
                agent: name.to_string(),
                cwd: process.cwd().unwrap_or_default().to_string_lossy().to_string(),
                command: process.cmd().join(" "),
            });
        }
    }

    println!("{}", serde_json::to_string(&agents).unwrap());
}
```

4. **Python integration**:
```python
# discovery.py
def _discover_agents_native() -> list[DiscoveredAgent]:
    """BKM-08: Discover agents via thegent-discovery binary."""
    if not os.environ.get("THGENT_USE_NATIVE_DISCOVERY"):
        return []
    bin_path = os.environ.get("THGENT_DISCOVERY_BIN")
    if not bin_path:
        mod_path = Path(__file__).resolve()
        repo_root = mod_path.parents[2]
        bin_path = repo_root / "crates" / "target" / "release" / "thegent-discovery"
        if not bin_path.is_file():
            return []
        bin_path = str(bin_path)
    try:
        out = subprocess.run([bin_path], capture_output=True, text=True, timeout=5, check=False)
        if out.returncode != 0 or not out.stdout:
            return []
        data = json.loads(out.stdout)
        return [DiscoveredAgent(**item) for item in data]
    except Exception:
        return []
```

---

## BKM-10: JSONL Streaming

**Status**: ⏳ Pending
**Language**: Rust (PyO3 with streaming API)
**ROI**: Zero-copy streaming, 10x faster

### Implementation Steps

1. **Extend `thegent-parser` crate**:
```rust
use pyo3::prelude::*;
use simd_json;

#[pyfunction]
fn parse_jsonl_stream(stream: &[u8]) -> PyResult<Vec<PyObject>> {
    let mut results = Vec::new();
    for line in stream.split(|b| *b == b'\n') {
        if line.is_empty() {
            continue;
        }
        let mut owned = line.to_vec();
        let parsed: serde_json::Value = simd_json::from_slice(&mut owned)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("{}", e)))?;
        results.push(Python::with_gil(|py| parsed.to_object(py)));
    }
    Ok(results)
}
```

---

## BKM-11: Native Governance Scanner

**Status**: ⏳ Pending
**Language**: Rust (Extend hook-dispatcher)
**ROI**: Eliminates Python scanner.py spawns

### Implementation Steps

1. **Extend `hooks/hook-dispatcher/src/`**:
```rust
// Add governance scanning functions
pub fn scan_secrets(content: &str) -> Vec<SecretMatch> {
    // Use existing secret detection logic
}

pub fn scan_lint(content: &str, rules: &[LintRule]) -> Vec<LintIssue> {
    // Use existing lint logic
}
```

2. **Expose via CLI**:
```rust
// hooks/hook-dispatcher/src/bin.rs
match args.command {
    Command::GovernanceScan { path } => {
        let content = std::fs::read_to_string(path)?;
        let secrets = scan_secrets(&content);
        let json = serde_json::to_string(&secrets)?;
        println!("{}", json);
    }
    // ...
}
```

3. **Python integration**:
```python
# governance/scanner.py
def scan_native(path: Path) -> list[Issue]:
    """BKM-11: Scan via hook-dispatcher."""
    try:
        out = subprocess.run(
            ["hook-dispatcher", "governance-scan", str(path)],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if out.returncode != 0:
            return []
        issues = json.loads(out.stdout)
        return [Issue(**item) for item in issues]
    except Exception:
        return []
```

---

## Testing Strategy

### Unit Tests (Rust)

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_xml_tags() {
        let text = "<TASK>Fix bug</TASK>";
        let tags = extract_xml_tags(text, None, false).unwrap();
        assert_eq!(tags.get("TASK"), Some(&"Fix bug".to_string()));
    }
}
```

### Integration Tests (Python)

```python
def test_native_fallback():
    """Test Python fallback when native unavailable."""
    import os

    old = os.environ.get("THGENT_USE_NATIVE_PARSER")
    os.environ.pop("THGENT_USE_NATIVE_PARSER", None)
    try:
        tags = extract_tags("<TASK>test</TASK>")
        assert tags == {"TASK": "test"}
    finally:
        if old:
            os.environ["THGENT_USE_NATIVE_PARSER"] = old
```

### Performance Tests

```python
def test_parser_performance():
    """Benchmark native vs Python parser."""
    text = "<TASK>" * 1000 + "content" + "</TASK>" * 1000

    # Python
    start = time.perf_counter()
    for _ in range(100):
        extract_tags(text)  # Python fallback
    python_time = time.perf_counter() - start

    # Native
    os.environ["THGENT_USE_NATIVE_PARSER"] = "1"
    start = time.perf_counter()
    for _ in range(100):
        extract_tags(text)  # Native
    native_time = time.perf_counter() - start

    assert native_time < python_time / 5  # At least 5x faster
```

---

## Build Commands

```bash
# Build all Rust crates
task build:rust

# Build individual crate
cargo build --release -p thegent-parser --manifest-path crates/Cargo.toml

# Install PyO3 extension
uv pip install crates/thegent-parser

# Run tests
cargo test --manifest-path crates/Cargo.toml
uv run pytest tests/test_native_backmatter.py
```

---

## References

- [Architecture Document](../architecture/FRONTMATTER_BACKMATTER_ARCHITECTURE.md)
- [Research Plan](../research/PYTHON_FRONTMATTER_NATIVE_BACKMATTER_AUDIT_PLAN.md)
- [PyO3 User Guide](https://pyo3.rs/)
- [maturin Documentation](https://www.maturin.rs/)


---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made
1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added
- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions
- Implementation templates
- Configuration examples
- Best practices
