# Visual Atlas / Matrix by File + Functional Reasoning (2026-02-21)

## Scope

This is a high-impact atlas (not every file in repo) focused on runtime, governance, and largest LOC drivers by language.

## 1) Visual Tree (Code-Weighted)

```text
thegent/
├── src/                         (145,842 code)
│   └── thegent/
│       ├── cli/                (17,098)
│       ├── agents/             (10,132)
│       ├── governance/         (9,263)
│       ├── infra/              (8,786)
│       ├── routing/            (7,831)
│       ├── mcp/                (7,114)
│       ├── orchestration/      (6,754)
│       ├── tui/                (4,137)
│       ├── utils/              (3,791)
│       ├── ui/                 (3,628)
│       └── ... (remaining modules)
├── tests/                       (108,874)
├── crates/                      (26,978)
├── docs/                        (15,265 TS code mostly generated stubs)
├── scripts/                     (12,935)
├── hooks/                       (6,745)
└── governance/                  (5,659)
```

## 2) Language Maturity Matrix

| Language   | Code LOC | Maturity                | Primary Role                                       | Diagnosis                                  | Action                                          |
| ---------- | -------: | ----------------------- | -------------------------------------------------- | ------------------------------------------ | ----------------------------------------------- |
| Python     |  272,910 | High usage / overloaded | Frontmatter + too much core runtime                | Monolith concentration + scope creep       | Split core monoliths, offload hot paths to Rust |
| Rust       |   29,494 | Medium-high             | Backmatter (hooks/runtime/shm/router)              | Healthy direction; several oversized mains | Module-split large files + dep cleanup          |
| TypeScript |   15,560 | Medium (docs-heavy)     | API stubs/docs tooling                             | Mostly generated docs artifacts            | Keep out core runtime KPIs                      |
| Shell      |    8,652 | Medium                  | Orchestration wrappers + legacy governance scripts | One major governance monolith              | Move policy/scanning execution to Rust          |
| Zig        |      161 | Low (POC)               | Utility + ABI experiments                          | Not integrated as production runtime       | Promote ABI contracts + first production kernel |
| Mojo       |        6 | Very low (scaffold)     | Intended numeric kernels                           | Placeholder-only implementation            | Define kernel contracts + benchmark gate        |

## 3) File Matrix (Top Drivers + Functional Reasoning)

### Python

| File                               | Code LOC | Functional Category             | Why It Exists                               | Risk                             | Refactor Direction                        |
| ---------------------------------- | -------: | ------------------------------- | ------------------------------------------- | -------------------------------- | ----------------------------------------- |
| `src/thegent/cli/commands/cli.py`  |     6843 | Command surface / UX API        | Central CLI entrypoint accumulated features | Very high coupling               | Split by command domain modules           |
| `src/thegent/cli/commands/impl.py` |     5786 | Command implementation services | Shared implementation sink                  | Change blast radius              | Extract service layers per domain         |
| `src/thegent/mcp/server.py`        |     4250 | MCP transport + routing + tools | Unified MCP server integration              | Protocol complexity in one file  | Split auth/transport/router/tool adapters |
| `src/thegent/execution.py`         |     2165 | Execution orchestration         | Core run lifecycle engine                   | Hard to reason/test in isolation | Decompose by lifecycle stages             |
| `src/thegent/doctor.py`            |     2016 | Diagnostics/health checks       | Runtime verification entrypoint             | Mixed concerns                   | Split checks into pluggable providers     |
| `src/thegent/install.py`           |     1899 | Installer/bootstrap             | Cross-platform setup logic                  | Operational drift risk           | Isolate platform-specific installers      |

### Rust

| File                                 | Code LOC | Functional Category   | Why It Exists                            | Risk                            | Refactor Direction                   |
| ------------------------------------ | -------: | --------------------- | ---------------------------------------- | ------------------------------- | ------------------------------------ |
| `crates/thegent-hooks/src/main.rs`   |     4109 | Hook runtime engine   | Consolidated governance scanner pipeline | Monolith main                   | Split scanners/evaluators/reporters  |
| `hooks/hook-dispatcher/src/main.rs`  |     2585 | Hook dispatch control | High-speed hook runner                   | Large execution hub             | Extract contract-specific modules    |
| `crates/thegent-shm/src/lib.rs`      |     1025 | Shared memory/state   | Fast in-process state exchange           | Medium complexity concentration | Separate state models from ops       |
| `crates/thegent-runtime/src/main.rs` |      683 | Runtime host          | Runtime process coordination             | Growing orchestration logic     | Extract runtime subcommands/services |

### Shell

| File                            | Code LOC | Functional Category          | Why It Exists                | Risk                       | Refactor Direction                     |
| ------------------------------- | -------: | ---------------------------- | ---------------------------- | -------------------------- | -------------------------------------- |
| `hooks/governance-gates.sh`     |     1983 | Governance gate orchestrator | Legacy+current policy runner | Very high maintenance risk | Move logic to Rust; keep shell wrapper |
| `hooks/lib/common.sh`           |      431 | Shared hook primitives       | Cross-hook helper layer      | Drift + hidden coupling    | Replace heavy logic with binary calls  |
| `scripts/benchmark-extended.sh` |      360 | Benchmark orchestration      | Batch perf checks            | Moderate complexity        | Keep as wrapper to typed runner        |

### TypeScript

| File                                          | Code LOC | Functional Category    | Why It Exists              | Risk             | Refactor Direction                    |
| --------------------------------------------- | -------: | ---------------------- | -------------------------- | ---------------- | ------------------------------------- |
| `docs/reference/api/ts-stubs/cli-examples.ts` |      164 | Generated examples     | API docs generation output | Low runtime risk | Treat as generated artifact only      |
| `docs/reference/api/ts-stubs/cli.d.ts`        |      164 | Generated declarations | API contract docs          | Low runtime risk | Keep generated + non-manual edits     |
| `templates/vitepress/config.ts`               |       86 | Docs site config       | VitePress behavior config  | Low risk         | Maintain separately from runtime KPIs |

### Zig

| File                                    | Code LOC | Functional Category | Why It Exists     | Risk                         | Refactor Direction                     |
| --------------------------------------- | -------: | ------------------- | ----------------- | ---------------------------- | -------------------------------------- |
| `scripts/max_lines_gate.zig`            |      107 | Utility gate runner | Fast gate helper  | Not core runtime integration | Decide keep-as-tool or replace by Rust |
| `src/thegent/abi/zig_rust_poc/main.zig` |       10 | ABI POC             | Interop prototype | Not production-ready         | Promote to versioned ABI contract      |

### Mojo

| File                               | Code LOC | Functional Category | Why It Exists                           | Risk                    | Refactor Direction                   |
| ---------------------------------- | -------: | ------------------- | --------------------------------------- | ----------------------- | ------------------------------------ |
| `src/thegent/infra/mojo/math.mojo` |        6 | Kernel scaffold     | Future numeric acceleration placeholder | No production value yet | Implement real deterministic kernels |

## 4) Categorical Understanding (Why these files grew)

1. **Feature Accretion in Python Frontmatter**

- New capabilities were repeatedly added to existing command/server files instead of creating bounded modules.

2. **Operational Logic Stayed in Shell Too Long**

- Governance and orchestration scripts retained business logic that should be typed/runtime-tested in Rust.

3. **Docs/Stub Surfaces Inflate Non-Runtime Language Counts**

- TypeScript volume is mostly generated docs contracts, not runtime product code.

4. **Zig/Mojo Are Strategic but Not Yet Productized**

- Present as scaffolds/POCs with little production workload ownership.

## 5) Immediate Refactor Sequence

1. Split Python monolith trio (`cli.py`, `impl.py`, `mcp/server.py`).
2. Decompose Rust hook mains and complete legacy dep cleanup.
3. Move shell governance execution paths to Rust binaries.
4. Productize Zig (ABI contract) and Mojo (deterministic kernels) only behind benchmark+contract gates.
