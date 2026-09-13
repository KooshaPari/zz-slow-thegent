# 01_RESEARCH

Operational queue conventions (24-item turns, carry-forwards, slice names) live in `04_QUEUE_CADENCE.md`.

## Blocker Matrix (Family Breakdown)

### Control: `thegent`

- **Canonical Root**: Dirty but conflict-free.
- **Detached Lane**: `thegent--lane-split-modules-bootstrap-v2` is dirty/detached (Non-Migratable).
- **Legacy Path**: `thegent-wtrees` is a non-git directory (Blocked).

### Drifting: `cliproxy`

- **Parallel Roots**: `cliproxyapi++` and `cliproxyapi-plusplus` (Dirty).
- **Typo Forest**: `cliproxy-wtress` is a duplicate of `cliproxy-wtrees` (67 lanes each).
- **Detached Surface**: Multiple detached lanes found under the `cliproxy-wtress` forest.

### Critical: `helios` Family

- **`heliosApp`**: Largest dirty root (353 paths); child lanes are all repair-bound (No-Prune).
- **`heliosCLI`**: Heavily dirty; `heliosCLI-composite-actions` is detached.
- **Mixed Forests**: `heliosApp-*` and `heliosCLI-*` containers represent legacy layout drift.
- **Adjacent Slices**: `colab` (dirty, ahead of main) and `helMo` (dirty) require stabilization.

### Mixed-Layout: `AgilePlus` / `phenotype*`

- **`AgilePlus`**: Heavily dirty (535 paths); complex mixed canonical/legacy layouts.
- **`phenotype-shared`**: Forest contains dirty descendants (Cleanup-Required).
- **Clean Containers**: `phenotype-config-wtrees`, `phenotype-design-wtrees`, `phenotype-go-kit-wtrees`, `phenotypeActions-wtrees`.

### Operational Noise: `portage` / `trace` / `trash-cli`

- **`portage`**: Prunable stale lanes in `/private/tmp`; 5+ detached legacy lanes.
- **`trace`**: Multiple locked initializing lanes; widespread dirtiness in forest.
- **`trash-cli`**: Detached `PROJECT-wtrees` lane (`pr1-rust-put-fix`).
- **`ralph-codex-loop`**: Unborn/Initializing state (`HEAD` is zeroed).

### Stable: `template-*`

- Structurally cleanest slice.
- **`template-commons`**: Contains a stale prunable lane; root files are dirty.

## Baseline Counts

- Local standalone roots: `55`
- Local worktree-family top-level roots: `45`
- Local forest roots including nested variants: `65`
- GitHub account-visible repos: `131`

## Wave B verification snapshot (2026-03-24 resume)

Read-only checks against `08_NEXT_WAVE_B.md`. **No destructive** `git worktree` / prune executed.

### heliosApp (`repos/worktrees/heliosApp/*`)

| Lane                                         | Branch / notes                                               | Dirty                              |
| -------------------------------------------- | ------------------------------------------------------------ | ---------------------------------- |
| `ci-workflow-fix`                            | `fix/ci-workflow-billing...upstream/fix/ci-workflow-billing` | 1 path (`AGENTS.md`)               |
| `claude-md-standardize`                      | ahead 591 / behind 57 vs `origin/main`                       | 413 paths                          |
| `parity-debt-wave-20260303`                  | `codex/parity-debt-wave-20260303`                            | 6 paths                            |
| `phase2-decompose`                           | `cleanup/local-work...upstream/main` (ahead 7 / behind 642)  | 2 paths                            |
| `sync-main-upstream-20260305`                | `sync/main-upstream-20260305`                                | 4 paths                            |
| `heliosApp/heliosApp-wtrees/decomp-20260314` | `decomp/20260314-heliosapp`                                  | large WIP; `.tmp/` in `.gitignore` |

### heliosCLI (`repos/heliosCLI-wtrees/*` alt layout)

| Lane                     | Notes                                                         |
| ------------------------ | ------------------------------------------------------------- |
| `code-reduction`         | `feat/code-reduction-helioscli`; `?? .serena/`                |
| `review-orchestrator`    | `codex/review-orchestrator` **ahead 4038** vs `upstream/main` |
| `spec-docs-pr`           | tracking `upstream/codex/tui-renderer-spec-docs-with-core`    |
| `oxc-migration-20260303` | deleted `.md` + `?? .md.zst` swap artifact                    |
| `bazel-llvm-modules-fix` | `MODULE.bazel` modified; **untracked** LLVM patch             |

### colab / helMo / helios-cli

- **`colab`**: `main` **ahead 20**; modified workflows + `AGENTS.md`; `?? .github/hooks/`.
- **`helMo`**: `main`; all-untracked infra files (`.github`, `.pre-commit-config.yaml`, etc.).
- **`helios-cli`**: feature branch; `?? docs/sessions/`, `?? repos/`.
- **`colab-wtrees/helios-integration`**: **symlink** → `repos/worktrees/colab/helios-integration` (alias lane; document policy: real tree is under `worktrees/colab/...`).

### AgilePlus / phenotype\*

- **`AgilePlus`**: **534** short status lines; ahead 2 / behind 2.
- **`phenotype-shared`**: feature branch; `?? crates/`.
- **`phenotypeActions`**: `git status` **fails**: `expected submodule path 'PROJECT-wtrees/add-lint-test-action' not to be a symbolic link` — **structural blocker** until submodule/symlink repaired.
- **`phenodocs`**: `main` ahead 3; `?? .github/` (from partial output).
- **`phench`**: `main` ahead 1 vs `myfork/main`; `M README.md`; `?? .github/`, `?? .pre-commit-config.yaml`.

### Governance / template / thegent

- **`./scripts/worktree_governance.sh list`** (from `repos` hub): emitted registered worktrees (14+ legacy `*-wtrees` → `worktrees/...` pairs shown).
- **`migrate-legacy --dry-run`**: lists **MIGRATE** pairs (e.g. `portage-wtrees/fix-build-blocker` → `worktrees/portage/fix-build-blocker`); **execute only with policy approval**.
- **`template-commons`**: on `agentops/policy-federation-onboard`; `AGENTS.md` dirty.
- **`template-commons-wtrees`**: **not a git repository** (container or empty hub — confirm intent).

### trace / trash / portage / ralph

- **`trace`**: multiple **locked** `codex-required-gates*` lanes; `trace-wtrees/decomp-20260314` registered.
- **`trash-cli`**: `PROJECT-wtrees/pr1-rust-put-fix` still **detached HEAD**.
- **`ralph-codex-loop`**: **no checkout** at `repos/ralph-codex-loop` — treat as **missing / unborn** until path restored or archived.
- **`portage`**: tmp prunable lanes under `/private/tmp/portage-*`; non-tmp lanes under `Phenotype/portage-wtrees/*` and `repos/portage-*` (policy-federation, oxc-migration, etc.) — **owner decision** before prune.

### Re-verify tests (decomp)

- `bun test` on `apps/runtime/src/secrets/__tests__` + `pty/__tests__` — **213 pass, 0 fail** (2026-03-24).
