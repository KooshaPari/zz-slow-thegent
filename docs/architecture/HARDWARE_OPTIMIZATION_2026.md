# Thegent 2026 Hardware Optimization Matrix (Multi-Node / Hybrid)

This document specifies the hardware-specific optimizations for the `thegent` polyglot deployment across your 2026 fleet.

---

## 1. Node A: macOS (M1 / Sequoia 15.x / 16.x)

**Role**: Primary Orchestrator, UI Host, and Developer UX.
**Connectivity**: Wi-Fi (802.11ax/be).

| Layer       | Optimization Strategy                                             | Target Technology          |
| :---------- | :---------------------------------------------------------------- | :------------------------- |
| **Compute** | **AMX (Apple Matrix Extensions)** via Mojo/Accelerate.            | Mojo MLIR, NumPy/MPS       |
| **Memory**  | **Unified Memory Architecture (UMA)** optimization.               | `thegent-shm` (Mach ports) |
| **Runtime** | **PyPy 3.11 (AArch64)** with Rosetta 2 disabled for native logic. | `uv` / PyPy                |
| **Power**   | **Caffeinate / PMSET** logic in `fast_subprocess.py`.             | Zsh / `caffeinate`         |

**Action Item [N1.1-Mac]**: Implement `thegent-shm` using macOS-native `shm_open` with `O_EXCL` for UMA efficiency.

---

## 2. Node B: Windows 11 / WSL2 (Ryzen 7 5800X / NVIDIA 3090 Ti)

**Role**: Heavy Compute, GPU-Accelerated Routing, and Large Model Inference (Local).
**Connectivity**: Ethernet (1Gbps/2.5Gbps).

### Windows 11 / WSL2 Core (Ryzen 7 5800X)

- **ID: W1.1** | **SMT (Simultaneous Multithreading)** Awareness: Pin high-priority Rust/Go threads to physical cores using `taskset` or `cpuset` in WSL2.
- **ID: W1.2** | **IO threading**: Optimize WSL2 VHDX overhead by using the 9P protocol bypass for the `/tmp/thegent-bridge` mesh.
- **ID: W1.3** | **Linux Kernel Tuning**: Custom `.wslconfig` with `kernelCommandLine = elevator=noop` for NVMe optimization.

### GPU Acceleration (NVIDIA 3090 Ti / 24GB VRAM)

- **ID: G1.1** | **CUDA 12.x / 13.x**: Direct GPU-accelerated routing scoring via `thegent-router-cuda` (Rust + `cudarc`).
- **ID: G1.2** | **Triton / Mojo GPU**: Port expensive Python heuristics to Mojo kernels running on the 3090 Ti Tensor Cores.
- **ID: G1.3** | **vLLM / FasterTransformer**: Use the 3090 Ti as a local inference worker for the `cliproxyapi-plusplus` proxy.

---

## 3. Node C: Linux Distro Optimizations (Generic/Variety)

**Role**: Specialized Workers (e.g., Arch for latest kernel, Ubuntu/Debian for stability).

| Distro            | Optimization Strategy                                        | Target Tech       |
| :---------------- | :----------------------------------------------------------- | :---------------- |
| **Arch/Gentoo**   | **LTO (Link Time Optimization)** and `-march=native` builds. | Rust / C++ / Mojo |
| **Ubuntu/Debian** | **io_uring** for high-throughput disk/net IPC.               | Go / Rust `tokio` |
| **CentOS/RHEL**   | **SELinux / AppArmor** profiles for Wasm sandboxing.         | Zig / Extism      |

---

## 4. Cross-Hardware IPC (The "Bridge")

Since you have a mixed fleet (macOS on Wi-Fi, Windows 11/WSL2 on Ethernet), the `MultiRuntimeBridge` must be **Network-Robust** to account for asymmetric latency and jitter.

- **ID: B1.1 | Local Optimization**: Use **Shared Memory (SHM)** for intra-node logic (e.g., Python <-> Rust on Mac). No network overhead.
- **ID: B1.2 | NNG / ZeroMQ (Mesh)**: Use **SP (Scalability Protocols)** over TCP for inter-node (Mac <-> Windows). NNG's `SURVEY` and `BUS` patterns are ideal for unreliable Wi-Fi links.
- **ID: B1.3 | Tailscale / WireGuard**: Recommended for consistent peer-to-peer (P2P) addressing between the Mac and PC, bypassing NAT/mDNS issues common on mixed Wi-Fi/Ethernet networks.
- **ID: B1.4 | Asymmetric Buffering**: Implement larger IPC buffers on the Mac side to handle Wi-Fi burstiness, while keeping the Windows Ethernet side low-latency.
- **ID: B1.5 | Heartbeat / Timeout Tuning**: Increase heartbeat intervals to 5s (from 1s) for the Mac-to-PC link to prevent false "worker down" triggers during Wi-Fi interference.

---

## 5. Deployment Strategy (Taskfile)

```yaml
tasks:
  setup:mac:
    desc: "Optimize for Apple Silicon"
    cmds:
      - brew install mojo
      - uv python install pypy-3.11

  setup:wsl:
    desc: "Optimize for Ryzen/NVIDIA"
    cmds:
      - wsl --update
      - docker-compose -f docker-compose.cuda.yml up -d
      - cargo build --features cuda --release
```
