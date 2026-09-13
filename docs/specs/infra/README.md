# Infrastructure Domain Technical Specification

## Overview

Core infrastructure: process management, I/O, security sandboxing.

## Components

### Process Management

| Component          | Purpose            | Files                         |
| ------------------ | ------------------ | ----------------------------- |
| Runtime dispatcher | Process allocation | `infra/runtime_dispatcher.py` |
| Subprocess manager | Spawn/control      | `infra/subprocess_manager.py` |
| Shell detection    | Environment        | `infra/shell_detection.py`    |

### Fast I/O

| Component      | Purpose        | Files                       |
| -------------- | -------------- | --------------------------- |
| Fast file ops  | Async I/O      | `infra/fast_file_ops.py`    |
| Fast HTTP      | HTTP client    | `infra/fast_http_client.py` |
| Fast websocket | Real-time      | `infra/fast_websocket.py`   |
| Compression    | Data reduction | `infra/fast_compression.py` |

### Security

| Component   | Purpose   | Files                  |
| ----------- | --------- | ---------------------- |
| Sandbox     | Isolation | `infra/sandbox.py`     |
| Cage        | Container | `infra/cage.py`        |
| Wasm plugin | Extension | `infra/wasm_plugin.py` |

### Resource Management

| Component        | Purpose   | Files                       |
| ---------------- | --------- | --------------------------- |
| Resource monitor | Metrics   | `infra/resource_monitor.py` |
| Resource limits  | Quotas    | `infra/resource_limits.py`  |
| Memory           | In-memory | `infra/memory.py`           |

## Performance

| Metric         | Target |
| -------------- | ------ |
| File ops       | <1ms   |
| HTTP request   | <10ms  |
| Process spawn  | <50ms  |
| Sandbox launch | <100ms |
