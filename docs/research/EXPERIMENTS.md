# Experiments Log — thegent

**Purpose:** Research experiments, prototypes, and validation  
**Last Updated:** 2026-04-02  
**Status:** Active research (multiple in-flight)

---

## Experiment Registry

| ID      | Experiment               | Date    | Status         | Result                      | Location                                     |
| ------- | ------------------------ | ------- | -------------- | --------------------------- | -------------------------------------------- |
| EXP-001 | TUI Compositor Research  | 2026-Q1 | 🔄 In Progress | Cross-platform TUI patterns | `tasks/research-tui-compositor.md`           |
| EXP-002 | Compute Offload Patterns | 2026-Q1 | 🔄 In Progress | Remote execution models     | `tasks/research-compute-offload.md`          |
| EXP-003 | Cross-Platform Isolation | 2026-Q1 | 🔄 In Progress | Sandbox patterns            | `tasks/research-cross-platform-isolation.md` |
| EXP-004 | MAIF Artifacts           | 2026-Q1 | 🔄 In Progress | AI-friendly metadata        | `tasks/research-maif-artifacts.md`           |
| EXP-005 | Hook System (Rust)       | 2026-Q1 | 🔄 In Progress | Event hooks in Rust         | `tasks/research-hook-rust-phase1.md`         |
| EXP-006 | Idea Seed System         | 2026-Q1 | 🔄 In Progress | Knowledge capture           | `tasks/research-idea-seed-system.md`         |
| EXP-007 | Pareto Routing           | 2026-Q1 | 🔄 In Progress | Intelligent routing         | `tasks/research-pareto-routing.md`           |
| EXP-008 | Simulation Replay        | 2026-Q1 | 🔄 In Progress | Deterministic replay        | `tasks/research-simulation-replay.md`        |
| EXP-009 | Supermemory Integration  | 2026-Q1 | 🔄 In Progress | Memory systems              | `tasks/research-supermemory-integration.md`  |
| EXP-010 | Economic Governance      | 2026-Q1 | 🔄 In Progress | Token/credit systems        | `tasks/research-economic-governance.md`      |

---

## Research Methodology

thegent uses a **parallel research model**: multiple research tasks in flight simultaneously, each exploring a different dimension of the dotfiles/configuration management problem space.

**Research Pattern:**

```
tasks/research-{topic}.md
├── Research question
├── SOTA alternatives
├── Hypothesis
├── Evidence gathering
└── Recommendation
```

---

## Active Experiments

### EXP-001: TUI Compositor Research

**Research Question:** How can thegent provide a unified TUI across macOS, Linux, and WSL?

**Hypothesis:** A compositor abstraction enables consistent TUI behavior across platforms.

**Methodology:**

1. Survey TUI frameworks (bubbletea, ratatui, cursive)
2. Analyze terminal capabilities detection
3. Prototype compositor layer
4. Test cross-platform rendering

**Evidence Gathered:**

- TUI frameworks evaluated: 5+
- Terminal capability tests: 20+
- Platform combinations: 3 (macOS, Linux, WSL)

**Status:** 🔄 Phase 2 — Framework selection

**Artifacts:**

- `tasks/research-tui-compositor.md`
- `DESKTOP_AGENT_CURSOR_PLAN.md`

---

### EXP-002: Compute Offload Patterns

**Research Question:** Can heavy configuration tasks be offloaded to remote builders?

**Hypothesis:** Remote builders reduce local setup time for complex Nix builds.

**Methodology:**

1. Benchmark local vs. remote Nix builds
2. Evaluate security models (SSH, mTLS, tokens)
3. Design offload protocol
4. Prototype with thegent-cache

**Evidence Gathered:**

- Build time comparisons: In progress
- Security model analysis: Draft

**Status:** 🔄 Phase 1 — Benchmarking

**Artifacts:**

- `tasks/research-compute-offload.md`

---

### EXP-003: Cross-Platform Isolation

**Research Question:** How to achieve consistent sandboxing across macOS, Linux, WSL?

**Hypothesis:** Platform-specific isolation backends unified by trait interface.

**Methodology:**

1. Research macOS sandbox (seatbelt), Linux (seccomp, gvisor), WSL (limitation analysis)
2. Design unified isolation trait
3. Prototype per-platform implementation
4. Security audit

**Evidence Gathered:**

- Platform sandbox capabilities: Mapped
- Trait design: Draft

**Status:** 🔄 Phase 2 — Trait design

**Artifacts:**

- `tasks/research-cross-platform-isolation.md`

---

### EXP-004: MAIF Artifacts

**Research Question:** Can configuration artifacts include AI-friendly metadata?

**Hypothesis:** MAIF (Machine-Artifact Interaction Format) improves agent understanding of configs.

**Methodology:**

1. Research existing metadata formats
2. Design MAIF schema for dotfiles
3. Prototype generator
4. Test with agent consumption

**Evidence Gathered:**

- Format survey: Complete
- Schema draft: v0.1

**Status:** 🔄 Phase 3 — Prototype

**Artifacts:**

- `tasks/research-maif-artifacts.md`

---

### EXP-005: Hook System (Rust)

**Research Question:** How to implement a safe, performant hook system in Rust?

**Hypothesis:** Type-safe hooks via traits + async execution.

**Methodology:**

1. Research existing hook systems (git hooks, npm scripts)
2. Design Rust trait-based hooks
3. Prototype with thegent events
4. Performance benchmarks

**Evidence Gathered:**

- Hook system survey: 10+ implementations
- Trait design: Draft

**Status:** 🔄 Phase 2 — Design

**Artifacts:**

- `tasks/research-hook-rust-phase1.md`

---

### EXP-006: Idea Seed System

**Research Question:** How to capture and evolve configuration ideas?

**Hypothesis:** Structured seed files enable idea tracking and evolution.

**Methodology:**

1. Research knowledge management systems
2. Design seed file format
3. Prototype CLI for seed management
4. Integration with factory seeds

**Evidence Gathered:**

- KM systems surveyed: 5
- Format iterations: 3

**Status:** 🔄 Phase 3 — Integration

**Artifacts:**

- `tasks/research-idea-seed-system.md`

---

### EXP-007: Pareto Routing

**Research Question:** Can we route configuration tasks based on Pareto-optimal resource usage?

**Hypothesis:** Pareto routing balances speed, cost, and quality.

**Methodology:**

1. Research multi-objective optimization
2. Design Pareto frontier for config tasks
3. Prototype router
4. A/B test with real workloads

**Evidence Gathered:**

- Optimization literature review: In progress

**Status:** 🔄 Phase 1 — Literature review

**Artifacts:**

- `tasks/research-pareto-routing.md`

---

### EXP-008: Simulation Replay

**Research Question:** Can configuration changes be deterministically replayed?

**Hypothesis:** Event sourcing + time-travel enables replay.

**Methodology:**

1. Research event sourcing patterns
2. Design config event schema
3. Prototype event log
4. Replay validation

**Evidence Gathered:**

- Event sourcing systems: 3+ reviewed

**Status:** 🔄 Phase 2 — Schema design

**Artifacts:**

- `tasks/research-simulation-replay.md`

---

### EXP-009: Supermemory Integration

**Research Question:** How to integrate external memory systems?

**Hypothesis:** Supermemory pattern enables long-term config learning.

**Methodology:**

1. Research memory systems (vector DBs, knowledge graphs)
2. Design integration points
3. Prototype with thegent-skills
4. User evaluation

**Evidence Gathered:**

- Memory systems surveyed: 5+

**Status:** 🔄 Phase 2 — Design

**Artifacts:**

- `tasks/research-supermemory-integration.md`

---

### EXP-010: Economic Governance

**Research Question:** Can token/credit systems govern config resource usage?

**Hypothesis:** Economic incentives prevent config bloat.

**Methodology:**

1. Research token economics
2. Design credit system for configs
3. Prototype policy gate
4. Simulation

**Evidence Gathered:**

- Tokenomics literature: Review started

**Status:** 🔄 Phase 1 — Research

**Artifacts:**

- `tasks/research-economic-governance.md`

---

## Experiment Templates

### Starting a New Experiment

```markdown
# Research: [Topic]

## Research Question

[Clear question]

## Hypothesis

[What we expect to find]

## SOTA Alternatives

| Solution | Approach   | Gap   |
| -------- | ---------- | ----- |
| [Name]   | [Approach] | [Gap] |

## Evidence Gathering

- [ ] Step 1
- [ ] Step 2

## Recommendation

[When complete]

## Status

- Phase: [1-3]
- Confidence: [Low/Medium/High]
- Next Action: [Specific task]
```

---

## Research Debt

| Experiment              | Blocker              | Priority | ETA   |
| ----------------------- | -------------------- | -------- | ----- |
| WASM executor           | No use case          | P3       | TBD   |
| GPU acceleration        | No config task needs | P3       | TBD   |
| Blockchain verification | Overkill             | P4       | Never |

---

**Update Cadence:** Weekly during active phase, bi-weekly otherwise
