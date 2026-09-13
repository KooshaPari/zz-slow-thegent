<DONE>
# Zero Interpretation: Rust Migration Strategy

## Goal

Eliminate all interpreted runtimes (Bash, Python, Node.js, Java) from the performance-critical path by migrating to Rust-native implementations or optimized shims.

## Phase 1: Hook & Tool Acceleration (IN PROGRESS)

- **Target**: High-frequency Git hooks and CLI utilities.
- **Mechanism**: `thegent-hooks` and `thegent-shims`.
- **Status**:
  - [x] Parallel hook dispatcher (`thegent-hooks dispatch`)
  - [x] Native secret scanner
  - [x] Native complexity ratchet
  - [x] Native AgilePlus cycle
  - [x] Native QA artifact gates
  - [x] Native task completion verifier
  - [x] Shims for `grep`, `find`, `sed`, `git` (routing to `rg`, `fd`, `ast-grep`, `thegent-git`).

## Phase 2: Core Library Porting (UPCOMING)

- **Target**: Shared logic in `lib/common.sh` and Python `thegent.config`.
- **Objective**: Create a unified Rust library crate `thegent-core` that can be shared by all binary crates.
- **Tasks**:
  - Port circuit breaker logic from Bash to Rust.
  - Port cache management from Bash/Python to Rust.
  - Port configuration loading (Pydantic-like) to Rust (`serde`).

## Phase 3: CLI Migration (thegent-cli)

- **Target**: The main Python CLI (`thegent`).
- **Objective**: Replace `src/thegent/main.py` with a Rust binary using `clap` and `ratatui`.
- **Priority Commands**:
  1.  `doctor`: Low complexity, high utility.
  2.  `git` subcommands: High frequency.
  3.  `concurrency`: Configuration-heavy.
  4.  `status`/`stats`: Summary-heavy.

## Phase 4: Agent Orchestration Migration (plangent)

- **Target**: `plangent` (TypeScript/Node.js).
- **Objective**: Port the multi-agent orchestration logic to Rust using `tokio` for concurrency.
- **Status**: Audit required to identify core loops.

## Blackbox Optimizations

- **Node.js**: Shadow `npm`/`pnpm`/`bun` via `thegent-hooks` to enforce tenant isolation and caching.
- **Java**: Shadow `java`/`mvn`/`gradle` if detected.
- **Python**: Shadow `uv`/`pip`/`pytest` to enforce security policies and acceleration.
