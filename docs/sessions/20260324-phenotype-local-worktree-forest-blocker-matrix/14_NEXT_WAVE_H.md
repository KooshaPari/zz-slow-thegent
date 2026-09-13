# 14_NEXT_WAVE_H — next 26 items (50 total with G)

**Follows** `07`–`13`. **Snapshot:** 2026-03-24. **Intent:** Final cleanup and long-term stabilization.

## Slice 1 — GitHub / Repo Policy (8)

1.  **Protections**: Verify required reviewers for `main` in all major repos.
2.  **CODEOWNERS**: Create/Update for `thegent` repository.
3.  **Dependabot**: Group all minor/patch updates to reduce noise.
4.  **Workflow Pins**: Ensure all GitHub Actions use commit SHAs.
5.  **Audit Log**: Review recent repository access (GitHub Admin).
6.  **Secret Scanning**: Enable/Verify for all private repositories.
7.  **Labels**: Standardize issue labels across the Phenotype org.
8.  **Templates**: Sync Issue/PR templates from `template-commons`.

## Slice 2 — Reproducibility & Builds (8)

9.  **Bun**: Lock version to `1.3.10` in all `.tool-versions`.
10. **Frozen Locks**: Ensure `bun install --frozen-lockfile` in all CI.
11. **Cache**: Optimize `node_modules` caching in GHA.
12. **Build Artifacts**: Standardize output directories (`dist/`, `build/`).
13. **Scripts**: Standardize `dev`, `build`, `test` script names.
14. **Types**: Verify `tsc --noEmit` on all projects.
15. **Lint**: Standardize `oxlint` rules across the monorepo.
16. **Pre-commit**: Verify hooks (lint, typecheck) are mandatory.

## Slice 3 — Security & Compliance (8)

17. **SBOM**: Generate SBOM using `syft` for `heliosApp`.
18. **Audit**: Run `bun audit` and fix all critical vulnerabilities.
19. **Licenses**: Review `LICENSE` headers in all new source files.
20. **PII**: Verify no secrets or PII are logged in CI output.
21. **Vendoring**: Audit any existing vendored code for updates.
22. **Docker**: Verify base image pinning (SHA or tag).
23. **Signing**: Ensure all commits are GPG/SSH signed.
24. **Scan**: Run `gitleaks` on local repositories.

## Slice 4 — Feature Safety & Rollout (2)

25. **Kill Switch**: Document the runtime kill process for `heliosApp`.
26. **Rollback**: Test the rollback procedure in a staging environment.

---

**Total Tasks (G+H):** 50.
