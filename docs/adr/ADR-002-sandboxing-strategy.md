# ADR-002: Sandboxing Tier Strategy

**Date**: 2026-04-02  
**Status**: Accepted  
**Deciders**: Agent

## Context

thegent executes user-provided dotfiles scripts across diverse environments. These scripts range from trusted user configurations to unknown third-party templates. A tiered sandboxing approach is required to balance security with performance.

## Decision Drivers

- **Security**: Isolation strength for untrusted code
- **Performance**: Startup latency and runtime overhead
- **Compatibility**: Cross-platform support (macOS, Linux, WSL)
- **User experience**: Transparent operation without surprises
- **Resource efficiency**: Memory and CPU overhead

## Options Considered

### Single Tier vs Multi-Tier

| Approach                         | Pros                                 | Cons                                         |
| -------------------------------- | ------------------------------------ | -------------------------------------------- |
| **Single tier (gVisor for all)** | Simple, consistent                   | Overkill for trusted scripts, 100ms overhead |
| **Multi-tier**                   | Right security for right trust level | More complex to implement and explain        |

**Decision**: Multi-tier with automatic selection based on trust level

### Tier Definitions

| Tier             | Technology  | Startup | Overhead | Security  | Use Case                  |
| ---------------- | ----------- | ------- | -------- | --------- | ------------------------- |
| **1 (Fast)**     | bubblewrap  | ~10ms   | +5MB     | Medium    | Trusted user scripts      |
| **2 (Balanced)** | gVisor      | ~100ms  | +50MB    | High      | Community templates       |
| **3 (Maximum)**  | Firecracker | ~125ms  | +5MB\*   | Very High | Unknown/untrusted scripts |
| **Plugins**      | WASM        | ~1ms    | +1MB     | High      | User extensions           |

\*Firecracker overhead is per-VM memory, not including guest

## Decision

**Adopt 4-tier sandboxing architecture with automatic tier selection**:

### Tier 1: bubblewrap (Trusted)

**Use case**: User's own dotfiles, verified sources

```rust
pub struct BubblewrapSandbox {
    read_only_dirs: Vec<PathBuf>,
    write_dirs: Vec<PathBuf>,
    tmpfs_dirs: Vec<PathBuf>,
    unshare_all: bool,
}

impl Sandbox for BubblewrapSandbox {
    fn execute(&self, command: &str) -> Result<()> {
        // bwrap --ro-bind /home/user/.dotfiles /dotfiles \
        //       --tmpfs /tmp \
        //       --unshare-all \
        //       /dotfiles/install.sh
    }
}
```

**Security properties**:

- User namespace isolation
- Read-only bind mounts
- No network (by default)
- Tmpfs for /tmp

### Tier 2: gVisor (Community)

**Use case**: Community templates, GitHub-stars-based trust

```rust
pub struct GVisorSandbox {
    container_image: String,
    network: bool,
    privileged: bool,
}

// Uses runsc (gVisor OCI runtime)
// docker run --runtime=runsc ...
```

**Security properties**:

- Userspace kernel (Go)
- Syscall filtering
- Container-level isolation
- Sentry process overhead

### Tier 3: Firecracker (Maximum)

**Use case**: Unknown scripts, complex dependencies, "agent desktop" use case

```rust
pub struct FirecrackerSandbox {
    vm_config: VMConfig,
    rootfs: PathBuf,
    kernel: PathBuf,
}

pub struct VMConfig {
    vcpus: u8,
    memory_mb: u32,
    network: bool,
}
```

**Security properties**:

- Hardware virtualization (KVM)
- Minimal attack surface
- MicroVM boundaries
- <5MB memory overhead

### Tier 4: WASM (Plugins)

**Use case**: User extensions, custom logic

```rust
pub struct WasmSandbox {
    module: wasmtime::Module,
    store: wasmtime::Store,
    capabilities: Capabilities,
}

pub struct Capabilities {
    filesystem: Vec<PathBuf>,
    network: bool,
    env_vars: Vec<String>,
}
```

**Security properties**:

- Capability-based
- Memory-safe
- Explicit permission grants
- Near-native speed

## Automatic Tier Selection

```rust
pub enum TrustLevel {
    Trusted,      // User's own files
    Community,    // Verified community templates
    Untrusted,    // Unknown sources
}

pub fn select_sandbox(
    trust_level: TrustLevel,
    requirements: &ExecutionRequirements,
) -> Box<dyn Sandbox> {
    match trust_level {
        TrustLevel::Trusted if !requirements.needs_root => {
            Box::new(BubblewrapSandbox::default())
        }
        TrustLevel::Community => {
            Box::new(GVisorSandbox::default())
        }
        TrustLevel::Untrusted | _ => {
            Box::new(FirecrackerSandbox::default())
        }
    }
}
```

## Platform Support

| Platform  | Tier 1        | Tier 2        | Tier 3         | Tier 4    |
| --------- | ------------- | ------------- | -------------- | --------- |
| **Linux** | ✅ bubblewrap | ✅ gVisor     | ✅ Firecracker | ✅ WASM   |
| **macOS** | ✅ (via Lima) | ✅ (via Lima) | ✅ (via Lima)  | ✅ Native |
| **WSL2**  | ✅            | ✅            | ❌ (no KVM)    | ✅        |

**Lima integration for macOS**:

```yaml
# lima.yaml
vmType: vz
rosetta:
  enabled: true
mounts:
  - location: "~/.dotfiles"
    writable: false
```

## Consequences

### Positive

- **Right security for right trust level**: No over-sandboxing trusted scripts
- **Performance where it matters**: 10ms startup for daily use
- **Maximum security available**: When needed, VM-level isolation
- **Plugin extensibility**: WASM for safe extensions

### Negative

- **Implementation complexity**: 4 sandbox implementations
- **User education**: Must explain tier selection
- **Platform variance**: macOS requires Lima for most tiers

### Neutral

- **Resource trade-offs**: Higher tiers use more resources (acceptable for security)

## References

- bubblewrap: https://github.com/containers/bubblewrap
- gVisor: https://gvisor.dev/
- Firecracker: https://firecracker-microvm.github.io/
- Wasmtime: https://wasmtime.dev/
- thegent SOTA Research: `docs/research/SANDBOXING_TECHNOLOGIES_SOTA.md`

---

_This ADR will be updated as implementation progresses_
