# 15_NEXT_WAVE_I — next 25 items (Waves 1-8 sequence)

**Follows** `07`–`14`. **Snapshot:** 2026-03-24. **Intent:** DX & Dependency Health.

## Slice 1 — Monorepo Hygiene (8)

1. **PNPM**: Audit `pnpm-workspace.yaml` in `agentapi-plusplus`.
2. **Turborepo**: Verify `turbo.json` caching for `heliosApp`.
3. **Internal Packages**: Standardize `exports` in `package.json` for shared libs.
4. **Symlinks**: Convert relative symlinks to project-root-relative.
5. **Git LFS**: Audit large files and migrate to LFS where appropriate.
6. **Attributes**: Standardize `.gitattributes` for binary vs text.
7. **Hooks**: Ensure `lefthook` or `husky` is consistent across monorepos.
8. **Engines**: Pin `node`, `bun`, `go`, `rust` versions in `package.json`.

## Slice 2 — Dependency Depth (8)

9. **Duplicate Deps**: Run `pnpm why` / `bun pm ls` to find version skew.
10. **PeerDeps**: Resolve all peer dependency warnings in `heliosApp`.
11. **Shrinkwrap**: Verify integrity of all lockfiles.
12. **License Check**: Run `license-checker` to find non-compliant OSS.
13. **Unused Deps**: Run `depcheck` on all `apps/` and `libs/`.
14. **Local Deps**: Migrate `file:` or `link:` to workspace protocols.
15. **Pre-releases**: Audit any `alpha`, `beta`, `rc` dependencies.
16. **Vendored**: Document any `third_party/` or `vendor/` inclusions.

## Slice 3 — Developer Experience (8)

17. **VS Code**: Standardize `.vscode/settings.json` and `extensions.json`.
18. **Dev Container**: Create `devcontainer.json` for `heliosApp`.
19. **Nix**: Audit `flake.nix` or `shell.nix` in `portage`.
20. **Scripts**: Create `setup` script for zero-to-dev onboarding.
21. **Docs**: Verify `README.md` has clear 'Quick Start' section.
22. **Example**: Add `examples/` directory to all shared libraries.
23. **CLI**: Add `--version` and `--help` to all internal tools.
24. **Lint-staged**: Ensure only changed files are linted on commit.

## Slice 4 — Meta (1)

25. **Task Inventory**: Re-audit `ACTIVE_BACKLOG.md` for stale items.
