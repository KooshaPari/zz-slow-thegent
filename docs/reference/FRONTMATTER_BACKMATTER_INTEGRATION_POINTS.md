# Frontmatter/Backmatter Integration Points

> **Status**: Reference | **Version**: 1.0 | **Last Updated**: 2026-02-16
> **Purpose**: Complete mapping of all integration points between Python frontmatter and Rust backmatter

---

## 1. Completed Integrations (Phase 1)

### 1.1 BKM-01: Resource Sampling

**Python Module**: `src/thegent/orchestration/load_based_limits.py`

**Integration Point**:

```python
def sample_resources() -> ResourceSnapshot:
    """Sample system resources with native fallback."""
    native = _sample_resources_native()
    if native is not None:
        return native
    return _sample_resources_python()  # Fallback
```

**Rust Crate**: `crates/thegent-resources/`

- **Binary**: `src/bin.rs` (standalone JSON output)
- **Library**: `src/lib.rs` (PyO3-ready, not yet exposed)

**Environment Variable**: `THGENT_USE_NATIVE_RESOURCES=1`

**Binary Path**: Auto-detected from `crates/target/release/thegent-resources` or `THGENT_RESOURCES_BIN`

**Call Pattern**: Subprocess JSON (infrequent calls, acceptable overhead)

---

### 1.2 BKM-02: XML/JSONL Parsing

**Python Modules**:

- `src/thegent/contracts/parser.py` → `extract_tags()`
- `src/thegent/output_parser.py` → `strip_noise()`, `strip_think_blocks()`

**Integration Points**:

```python
# contracts/parser.py
def extract_tags(text: str, tags: list[str] | None = None) -> dict[str, str]:
    native = _get_native_parser()
    if native is not None:
        return native.extract_xml_tags(text, allowed_tags=tags, case_sensitive=False)
    # Fallback to Python IncrementalXMLParser


# output_parser.py
def _strip_think_blocks(text: str) -> str:
    native = _get_native_parser()
    if native is not None:
        return native.strip_think_blocks(text)
    return _THINK_RE.sub("", text).strip()  # Fallback
```

**Rust Crate**: `crates/thegent-parser/`

- **PyO3 Module**: `thegent_parser.thegent_parser`
- **Functions**: `extract_xml_tags()`, `strip_noise()`, `strip_think_blocks()`

**Environment Variable**: `THGENT_USE_NATIVE_PARSER=1`

**Call Pattern**: PyO3 (in-process, hot path)

---

### 1.3 BKM-03: Cryptographic Operations

**Python Module**: `src/thegent/governance/signatures.py`

**Integration Points**:

```python
def generate_artifact_hash(artifact: dict) -> str:
    native = _get_native_crypto()
    if native is not None:
        canonical_json = orjson.dumps(artifact, option=orjson.OPT_SORT_KEYS).decode()
        return native.artifact_hash_bytes(canonical_json.encode())
    # Fallback to Python hashlib


def sign_artifact(artifact: dict, secret_key: str) -> str:
    native = _get_native_crypto()
    if native is not None:
        canonical_json = orjson.dumps(artifact, option=orjson.OPT_SORT_KEYS).decode()
        return native.sign_artifact_bytes(canonical_json.encode(), secret_key)
    # Fallback to Python hmac


def verify_signature(artifact: dict, signature: str, secret_key: str) -> bool:
    native = _get_native_crypto()
    if native is not None:
        canonical_json = orjson.dumps(artifact, option=orjson.OPT_SORT_KEYS).decode()
        return native.verify_signature_bytes(canonical_json.encode(), signature, secret_key)
    # Fallback to Python hmac.compare_digest
```

**Rust Crate**: `crates/thegent-crypto/`

- **PyO3 Module**: `thegent_crypto.thegent_crypto`
- **Functions**: `artifact_hash_bytes()`, `sign_artifact_bytes()`, `verify_signature_bytes()`

**Environment Variable**: `THGENT_USE_NATIVE_CRYPTO=1`

**Call Pattern**: PyO3 (in-process, hot path)

**Security Note**: Uses `subtle` crate for constant-time comparison in `verify_signature_bytes()`

---

## 2. Pending Integrations (Phase 2)

### 2.1 BKM-05: State-SHM (Shared Memory)

**Python Module**: `src/thegent/orchestration/circuit_breaker.py`

**Integration Point** (Planned):

```python
class CircuitBreakerRegistry:
    def __init__(self):
        native = _get_native_shm()
        if native is not None:
            self._shm_id = native.create_shm_region("circuit_breaker", 4096)
            self._native = native
        else:
            self._state: dict[str, CircuitBreakerState] = {}  # Fallback
```

**Rust Crate**: `crates/thegent-shm/` (to be created)

- **PyO3 Module**: `thegent_shm.thegent_shm`
- **Functions**: `create_shm_region()`, `read_circuit_breaker()`, `write_circuit_breaker()`

**Environment Variable**: `THGENT_USE_NATIVE_SHM=1`

**Call Pattern**: PyO3 (in-process, cross-process atomicity)

---

### 2.2 BKM-06: Git Operations

**Python Module**: `src/thegent/forensics/snapshot.py`

**Integration Points** (Planned):

```python
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


def _get_git_status(self, root: Path) -> str:
    native = _get_native_git()
    if native is not None:
        try:
            metadata = native.get_git_metadata(str(root))
            return "\n".join(metadata.status)
        except Exception:
            pass
    # Fallback to subprocess
    try:
        return subprocess.check_output(["git", "status", "--short"], cwd=root).decode().strip()
    except Exception:
        return "n/a"


def _get_git_diff(self, root: Path) -> str:
    native = _get_native_git()
    if native is not None:
        try:
            metadata = native.get_git_metadata(str(root))
            return metadata.diff_text
        except Exception:
            pass
    # Fallback to subprocess
    try:
        return subprocess.check_output(["git", "diff", "HEAD"], cwd=root).decode().strip()
    except Exception:
        return "n/a"
```

**Rust Crate**: `crates/thegent-git/` (to be created)

- **PyO3 Module**: `thegent_git.thegent_git`
- **Functions**: `get_git_metadata()`
- **Dependencies**: `gix` (gitoxide)

**Environment Variable**: `THGENT_USE_NATIVE_GIT=1`

**Call Pattern**: PyO3 (in-process, eliminates git subprocesses)

---

### 2.3 BKM-08: Discovery

**Python Module**: `src/thegent/discovery.py`

**Integration Point** (Planned):

```python
def discover_agents() -> list[DiscoveredAgent]:
    """Discover external agents with native fallback."""
    native = _discover_agents_native()
    if native:
        return native
    # Fallback to Python subprocess (ps, git, npx)
    return _discover_agents_python()
```

**Rust Crate**: `crates/thegent-discovery/` (to be created)

- **Binary**: `src/bin.rs` (standalone JSON output)
- **Dependencies**: `sysinfo` for process enumeration

**Environment Variable**: `THGENT_USE_NATIVE_DISCOVERY=1`

**Binary Path**: Auto-detected from `crates/target/release/thegent-discovery` or `THGENT_DISCOVERY_BIN`

**Call Pattern**: Subprocess JSON (infrequent calls)

---

## 3. Architectural Patterns

### 3.1 Lazy Loading Pattern

All native modules use lazy loading to avoid import-time failures:

```python
_native_module = None


def _get_native_module():
    global _native_module
    if _native_module is not None:
        return _native_module
    if not os.environ.get("THGENT_USE_NATIVE_*"):
        return None
    spec = importlib.util.find_spec("module_name.submodule")
    if spec is not None and spec.loader is not None:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _native_module = mod
        return mod
    return None
```

**Benefits**:

- No import-time failures if Rust toolchain unavailable
- Graceful degradation to Python fallback
- Environment flag controls opt-in behavior

---

### 3.2 Fallback Pattern

Every native integration follows this pattern:

```python
def operation(...):
    """Operation with native backmatter fallback."""
    native = _get_native_module()
    if native is not None:
        try:
            return native.operation(...)
        except Exception as e:
            _log.debug("Native operation failed: %s", e)
            # Fall through to Python
    # Python fallback
    return python_implementation(...)
```

**Benefits**:

- Always works (Python fallback guaranteed)
- Easy A/B testing (toggle environment variable)
- Gradual migration path

---

### 3.3 Error Handling

**PyO3 Errors**:

- Rust panics → PyO3 converts to Python exceptions
- Python exceptions → Rust `PyResult<T>` propagates
- Always catch and fallback to Python on exception

**Subprocess Errors**:

- Binary exit code != 0 → Python fallback
- JSON parse error → Python fallback
- Timeout → Python fallback

---

## 4. Environment Variables Reference

| Variable                      | Purpose                        | Default      | Crate                        |
| ----------------------------- | ------------------------------ | ------------ | ---------------------------- |
| `THGENT_USE_NATIVE_RESOURCES` | Use Rust resource sampling     | `0` (Python) | `thegent-resources`          |
| `THGENT_USE_NATIVE_CRYPTO`    | Use Rust crypto                | `0` (Python) | `thegent-crypto`             |
| `THGENT_USE_NATIVE_PARSER`    | Use Rust parser                | `0` (Python) | `thegent-parser`             |
| `THGENT_USE_NATIVE_SHM`       | Use Rust shared memory         | `0` (Python) | `thegent-shm` (future)       |
| `THGENT_USE_NATIVE_GIT`       | Use Rust git operations        | `0` (Python) | `thegent-git` (future)       |
| `THGENT_USE_NATIVE_DISCOVERY` | Use Rust discovery             | `0` (Python) | `thegent-discovery` (future) |
| `THGENT_RESOURCES_BIN`        | Override resources binary path | Auto-detect  | `thegent-resources`          |
| `THGENT_DISCOVERY_BIN`        | Override discovery binary path | Auto-detect  | `thegent-discovery` (future) |

---

## 5. Build Integration

### 5.1 Taskfile.yml

```yaml
build:rust:
  desc: "Build BKM Rust crates"
  cmds:
    - cargo build --release -p thegent-resources --manifest-path crates/Cargo.toml
    - uv pip install crates/thegent-crypto
    - uv pip install crates/thegent-parser
```

### 5.2 CI/CD (Planned)

```yaml
- name: Build Rust crates
  run: |
    cargo build --release --manifest-path crates/Cargo.toml

- name: Install PyO3 extensions
  run: |
    uv pip install crates/thegent-crypto
    uv pip install crates/thegent-parser

- name: Test native backmatter
  env:
    THGENT_USE_NATIVE_RESOURCES: 1
    THGENT_USE_NATIVE_CRYPTO: 1
    THGENT_USE_NATIVE_PARSER: 1
  run: |
    uv run pytest tests/test_native_backmatter.py
```

---

## 6. Testing Strategy

### 6.1 Unit Tests (Rust)

Each crate has unit tests:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_functionality() {
        // Test Rust implementation
    }
}
```

### 6.2 Integration Tests (Python)

Test native + fallback:

```python
def test_native_fallback():
    """Test Python fallback when native unavailable."""
    import os

    old = os.environ.get("THGENT_USE_NATIVE_PARSER")
    os.environ.pop("THGENT_USE_NATIVE_PARSER", None)
    try:
        result = operation(...)  # Should use Python fallback
        assert result is not None
    finally:
        if old:
            os.environ["THGENT_USE_NATIVE_PARSER"] = old
```

### 6.3 Performance Tests

Benchmark native vs Python:

```python
def test_performance():
    """Benchmark native vs Python implementation."""
    # Measure Python baseline
    # Measure native implementation
    # Assert native is faster
```

---

## 7. Migration Checklist

For each new integration:

- [ ] Create Rust crate in `crates/`
- [ ] Implement core logic in `src/lib.rs` or `src/bin.rs`
- [ ] Add PyO3 bindings (if in-process) or JSON output (if binary)
- [ ] Create Python wrapper function with lazy loading
- [ ] Add fallback to Python implementation
- [ ] Add environment variable (`THGENT_USE_NATIVE_*`)
- [ ] Update `Taskfile.yml` build task
- [ ] Add unit tests (Rust)
- [ ] Add integration tests (Python)
- [ ] Add performance benchmarks
- [ ] Update documentation
- [ ] Update this integration points document

---

## 8. References

- [Architecture Document](../architecture/FRONTMATTER_BACKMATTER_ARCHITECTURE.md)
- [Implementation Guides](../guides/BKM_IMPLEMENTATION_GUIDES.md)
- [Research Plan](../research/PYTHON_FRONTMATTER_NATIVE_BACKMATTER_AUDIT_PLAN.md)

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
