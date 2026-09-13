# Specification: NATS Agentic Event Mesh (Z-Bus)

## 1. Objective

To provide a low-latency, event-driven communication layer for agents and system hooks. This replaces slow file-based locking and enables real-time observability across the "Ultra-Parity" stack.

## 2. Subjects & Topics

### `shell.events.<session_id>.<event_type>`

- **Events**: `started`, `executed`, `finished`, `resized`.
- **Payload**: JSON containing command line, exit code, and timing data.

### `agent.intents.<agent_id>.<task_id>`

- **Description**: High-level intent broadcast.
- **Payload**: `{ action: "editing", files: ["..."], summary: "..." }`.

### `system.alerts.panic`

- **Description**: Emergency broadcast when resource limits are reached.
- **Payload**: `{ reason: "fork_bomb", pids: [...] }`.

## 3. Architecture

- **Transport**: NATS Core (Pub/Sub) and NATS JetStream (Persistence).
- **Endpoint**: `nats://localhost:4222`.
- **Latency Target**: < 1ms for event delivery.

## 4. Integration

- **Zsh Shims**: The `ultra-shim` binary (Go) will publish events to NATS before and after tool execution.
- **Harness**: The ShareCLI Harness will use NATS for distributed locking and fair-share queueing.
- **Temporal**: NATS events can trigger Temporal workflows for long-running recovery tasks.

## 5. Benefits

- **Sub-millisecond Coordination**: Multiple agents can signal each other instantly.
- **Observability**: A central `harness dash` can subscribe to all subjects to show a real-time "system pulse".
- **Decoupling**: The shell doesn't need to know about Neo4j or Postgres; it just emits to NATS, and dedicated workers handle ingestion.
