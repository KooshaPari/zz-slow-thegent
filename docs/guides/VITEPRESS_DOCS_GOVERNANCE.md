# VitePress Documentation Governance

## Current State Audit

### Excluded from Build (srcExclude)

| Directory                  | Files       | Why Excluded                                        |
| -------------------------- | ----------- | --------------------------------------------------- |
| `fragemented/**`           | ~72 dirs    | Typo - should be "fragmented" - CONTAINS DUPLICATES |
| `docset/**`                | ~76 dirs    | Excluded but `docsets/` (with 's') is built         |
| `plans/**`                 | ~175 dirs   | Work-in-progress plans                              |
| `research/**`              | ~545 dirs   | Research documents                                  |
| `reports/**`               | ~854 dirs   | Worklog reports                                     |
| `context/**`               | ~31 dirs    | Context docs (P0-P2 priority)                       |
| `reference/api/**`         | ~600+ files | Auto-generated API references                       |
| `reference/WORK_STREAM.md` | 1 file      | Active work stream                                  |

### Actually Built (What Users See)

| Directory      | Status   | Issues                             |
| -------------- | -------- | ---------------------------------- |
| `guides/`      | 103 dirs | OK but many orphaned files         |
| `reference/`   | 169 dirs | OK                                 |
| `governance/`  | 34 dirs  | OK                                 |
| `api/`         | Built    | OK                                 |
| `tutorials/`   | 6 files  | Empty index.md FIXED               |
| `how-to/`      | 3 files  | Empty index.md FIXED               |
| `explanation/` | 3 files  | Empty index.md FIXED               |
| `operations/`  | 3 files  | Empty index.md FIXED               |
| `site/`        | ?        | Likely duplicate of root structure |
| `docsets/`     | 6 dirs   | Some content                       |

### Critical Issues

1. **`fragemented` typo** - 72 directories of duplicates (should be deleted)
2. **`docset` vs `docsets`** - Missing 's' causes confusion
3. **Massive sidebar** - Was 6000+ entries, now simplified to ~50
4. **Empty index pages** - Fixed: how-to, explanation, operations
5. **Duplicate structure** - `site/` directory mirrors root

## Canonical Structure (Based on FastMCP/uv/Terraform)

```
docs/
├── index.md              # Home - hero + highlights
├── start-here.md         # Quick orientation
│
├── getting-started/       # NEW: Quick start guides
│   ├── installation.md
│   ├── quickstart.md
│   └── setup.md
│
├── tutorials/            # Learning-oriented
│   ├── index.md
│   ├── 01-quick-start.md
│   └── 02-configuration.md
│
├── how-to/              # Task-oriented (FIXED)
│   ├── index.md
│   └── ...
│
├── reference/           # Info-oriented
│   ├── index.md
│   ├── configuration.md
│   ├── routing.md
│   └── api/             # If needed
│
├── explanation/          # Understanding-oriented (FIXED)
│   └── index.md
│
├── operations/          # Operator-focused (FIXED)
│   ├── index.md
│   ├── runbooks.md
│   └── troubleshooting.md
│
├── governance/          # Policy & rules
│   ├── index.md
│   ├── tdd-bdd-sdd.md
│   └── test-strategy.md
│
└── guides/             # Deep dives
    ├── index.md
    ├── installation.md
    ├── troubleshooting.md
    └── ...
```

## Migration Tasks

### Phase 1: Cleanup (Immediate)

- [ ] Delete `fragemented/` directory (typo, all duplicates)
- [ ] Verify `docset/` can be removed if `docsets/` covers it
- [ ] Clean stale build artifacts before rebuild

### Phase 2: Structure (This Session)

- [ ] Consolidate `site/` into root or delete
- [ ] Move root-level .md files to appropriate dirs
- [ ] Create `getting-started/` section
- [ ] Populate all index.md files

### Phase 3: Sidebar & Nav (This Session)

- [ ] Finalize sidebar-simple.ts with canonical structure
- [ ] Ensure nav matches FastMCP/uv model
- [ ] Add edit links to all pages

### Phase 4: Governance (Ongoing)

- [ ] Document where new docs go
- [ ] Add pre-write validation for doc location
- [ ] Create doc freshness automation

## Doc Location Rules

| Doc Type  | Put In         | Example                         |
| --------- | -------------- | ------------------------------- |
| Tutorial  | `tutorials/`   | `tutorials/01-quick-start.md`   |
| How-to    | `how-to/`      | `how-to/run-agent.md`           |
| Reference | `reference/`   | `reference/configuration.md`    |
| Concept   | `explanation/` | `explanation/routing.md`        |
| Runbook   | `operations/`  | `operations/troubleshooting.md` |
| Policy    | `governance/`  | `governance/test-strategy.md`   |
| Deep Dive | `guides/`      | `guides/advanced-patterns.md`   |

## Files NOT to Add to Docs

These should NEVER be in docs/:

- Worklog reports → `reports/` (already excluded)
- Research → `research/` (already excluded)
- Plans → `plans/` (already excluded)
- Context docs → `context/` (already excluded)
- Archived docs → `docs/changes/archive/` (create if needed)

<!-- PHENOTYPE_GOVERNANCE_OVERLAY_V1 -->

## Phenotype Governance Overlay v1

- Enforce `TDD + BDD + SDD` for all feature and workflow changes.
- Enforce `Hexagonal + Clean + SOLID` boundaries by default.
- Favor explicit failures over silent degradation; required dependencies must fail clearly when unavailable.
- Keep local hot paths deterministic and low-latency; place distributed workflow logic behind durable orchestration boundaries.
- Require policy gating, auditability, and traceable correlation IDs for agent and workflow actions.
- Document architectural and protocol decisions before broad rollout changes.
