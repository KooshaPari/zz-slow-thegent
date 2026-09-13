# 05_KNOWN_ISSUES

## Resolution criteria (when an item leaves this list)

- **Repair-bound lane**: `git status` clean on that worktree path, branch merged or intentionally parked with no uncommitted product changes needed for migration.
- **Prune candidate**: `git worktree list` no longer references the path, or path removed with `git worktree remove` after confirming no unique commits worth keeping.
- **Detached lane**: either reattached to a registered worktree, or explicitly abandoned and removed per repo policy.
- **Locked initializing**: git/worktree initialization completed or lane removed; re-run `git worktree list` to confirm.

## GitHub / CI (release merges)

- **`thegent` Rust CI lane (2026-03-24 → 2026-03-25):** Prior failure at **`quality:rust:ci`** was due to duplicate **`Cache::is_empty`** in **`thegent-cache-rs`** (E0592) plus flaky parallel **`ThemeRegistry`** tests. **Fix:** remove duplicate method; add **`serial_test`** + **`#[serial]`** on registry tests; commit **`crates/Cargo.lock`** when **`serial_test`** is added. Re-verify: `cargo clippy --workspace --manifest-path crates/Cargo.toml --all-targets --all-features -- -D warnings` and `cargo test --workspace --manifest-path crates/Cargo.toml --all-targets --all-features`. Merge via focused PR to **`main`** (worktree branch per **`AGENTS.md`**), then strike this bullet once **`task quality:rust:ci`** is green on **`main`**.

- **`thegent` [PR #549](https://github.com/KooshaPari/thegent/pull/549)** — **merged** (`feat/migrate-cache` → `main`). Track post-merge CI on **`main`**; if billing blocked checks during merge, note date + **`FULL_TURN_DELIVERY.md`** billing section.
- **Actions billing / quota:** When checks cannot complete because **jobs do not start** (not because tests fail), use the **Billing / Actions quota** procedure in `FULL_TURN_DELIVERY.md` — **`gh pr merge --admin`** only after confirming infrastructure cause and local verification.
- **Hub tracking (resolved 2026-03-24):** [colab#13](https://github.com/KooshaPari/colab/pull/13) merged; [helMo](https://github.com/KooshaPari/helMo) published — [thegent#552](https://github.com/KooshaPari/thegent/issues/552) **closed**.

## Blocked Forest Registry

### Critical: Dirty-Root Blockers

- **`heliosApp`**: 353 dirty paths; all expanded child lanes are dirty/divergent (No-Prune).
- **`heliosCLI`**: 96 dirty paths; heavily divergent root state.
- **`AgilePlus`**: 535 dirty paths; major forest noise.

### Operational: Layout and State Blockers

- **`cliproxy-wtress`**: Typo duplicate of `cliproxy-wtrees` (Must-Normalize).
- **`portage`**: Stale prunable worktrees and detached legacy lanes (Cleanup-Ready).
- **`trace`**: Locked initializing lanes (`codex-required-gates*`) block migration (Unlock-Required).
- **`trash-cli`**: Detached `PROJECT-wtrees` lane (`pr1-rust-put-fix`).
- **`ralph-codex-loop`**: Unborn/Initializing (`HEAD` is all zeros).

### Structural: Mixed-Layout Blockers

- **`AgilePlus`, `phenotype-shared`, `phenotypeActions`**: Mixed canonical + legacy layouts prevent stable forest governance.
- **`phenotypeActions` (2026-03-24):** `git status` fails with **`expected submodule path 'PROJECT-wtrees/add-lint-test-action' not to be a symbolic link`** — repair submodule/symlink layout before any merge or worktree ops.
- **`heliosApp` (2026-03-24):** Extensive type errors (200+) in `apps/desktop` and `apps/runtime` (missing modules/types, `InMemoryLocalBus` vs `LocalBus` mismatches, Bun API `spawnSync/file/Glob` missing).

### Missing / non-repo paths

- **`ralph-codex-loop`:** Decided **archive** (2026-03-24); already in `.archive/ralph-codex-loop`.
- **`template-commons-wtrees`:** Directory present but **not a git repo** — confirm whether it should be a hub, symlink, or removed.
- **`heliosApp`**: Missing `CONTRIBUTING.md` and disk space runbook (2026-03-24).
- **`portage`**: No cron schedule for `/private/tmp` cleanup found.
