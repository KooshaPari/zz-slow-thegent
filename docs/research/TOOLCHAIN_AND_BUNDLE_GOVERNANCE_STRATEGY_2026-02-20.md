<DONE>
# Toolchain and Bundle Governance Strategy (2026-02-20)

## Context

thegent is used for user, developer, and agent environment setup across devices and platforms.
Current docs had partial overlap between `uv`, `mise`, `brew`, and optional `nix`, plus unclear policy for third-party bundle files vs worktrees.

## Decision

Adopt a hybrid, formal model:

1. Toolchain manager roles are explicit and non-overlapping.
2. First-party install assets are git-tracked in the repo.
3. Third-party/community assets are installed from a manifest and governed externally.
4. Worktrees and nested repos are not canonical config sources.

## Canonical Manager Roles

- `mise`: runtime/version pinning and activation surface.
- `uv`: Python environment/dependency manager and Python CLI installer.
- `brew` (`Brewfile`): macOS host package manager for system tools.
- `nix`: optional strict/declarative mode for teams that require stronger reproducibility and policy control.

## Bundle Governance Model

### First-party (repo-owned)

- Stored in the repo and installed via `thegent install`.
- Includes shell/config/hook/skill assets owned by thegent.

### Third-party (external)

- Declared in bundle manifest (`~/.config/thegent/third_party_bundles.json` by default).
- Installed via bundle manifest flow in installer.
- Governance should require immutable refs (`commit`/`tag`) and integrity metadata (`checksum`), even where enforcement is currently process-based.

### Worktrees and nested repos

- Treated as operational workspaces.
- Not used as long-term canonical storage for install assets.
- Must not be the source of truth for cross-device bootstrap.

## Why this is the best long-term strategy

- Preserves git-native reviewability for first-party assets.
- Supports extensibility without polluting core repo with external/vendor content.
- Avoids accidental drift from local-only worktrees.
- Keeps onboarding practical (`task setup`, bootstrap) while allowing stronger reproducibility mode (`nix`) when needed.

## Documentation Alignment Completed

- `docs/guides/INSTALLATION.md`: canonical manager roles + bundle/worktree policy.
- `docs/tasks/setup.md`: setup semantics aligned with manager roles.
- `docs/tasks/doctor.md`: manager-drift diagnostics added.
- `docs/guides/DOTFILES_INTEGRATION.md`: cross-device manifest governance guidance.

## Next Implementation Follow-ups (separate execution track)

1. Extend bundle manifest schema and validation to include explicit source pin + checksum fields.
2. Add `thegent doctor --deps` checks for manager-role drift and missing governance metadata.
3. Provide an example tracked manifest template for multi-device rollout.

<!-- PHENOTYPE_GOVERNANCE_OVERLAY_V1 -->

## Phenotype Governance Overlay v1

- Enforce `TDD + BDD + SDD` for all feature and workflow changes.
- Enforce `Hexagonal + Clean + SOLID` boundaries by default.
- Favor explicit failures over silent degradation; required dependencies must fail clearly when unavailable.
- Keep local hot paths deterministic and low-latency; place distributed workflow logic behind durable orchestration boundaries.
- Require policy gating, auditability, and traceable correlation IDs for agent and workflow actions.
- Document architectural and protocol decisions before broad rollout changes.
