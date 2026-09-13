# Composite Actions — Phenotype consumers

GitHub **composite** actions are defined with `runs:` / `using: composite` in `action.yml` under `.github/actions/<name>/`. This page lists **in-repo** definitions and **who calls them** so checkouts are not orphaned and refactors stay coordinated.

## Definitions (local)

| Repository     | Path                                      | Purpose (short)                                                                                                                                              |
| -------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **helios-cli** | `.github/actions/policy-gate`             | PR / policy checks                                                                                                                                           |
| **helios-cli** | `.github/actions/linux-code-sign`         | Release signing                                                                                                                                              |
| **helios-cli** | `.github/actions/macos-code-sign`         | Release signing                                                                                                                                              |
| **helios-cli** | `.github/actions/windows-code-sign`       | Release signing                                                                                                                                              |
| **heliosCLI**  | Same four paths under canonical repo root | Mirror of the above in the **heliosCLI** tree (avoid duplicating edits; treat **helios-cli** as primary for CLI ship paths unless your lane says otherwise). |

Kittify template copies under `heliosCLI/worktrees/.../kittify-templates/` may duplicate these for scaffolding — prefer aligning with canonical **heliosCLI** / **helios-cli** before editing templates.

## Consumers (workflows referencing `./.github/actions/...`)

| Repository     | Workflow(s)                       | Action(s) used                                                                               |
| -------------- | --------------------------------- | -------------------------------------------------------------------------------------------- |
| **helios-cli** | `rust-release.yml`                | `linux-code-sign`, `macos-code-sign`                                                         |
| **helios-cli** | `rust-release-windows.yml`        | `windows-code-sign`                                                                          |
| **heliosApp**  | `gca.yml` (and `.github/gca.yml`) | `gca-with-retry` (path `./.github/actions/gca-with-retry` — verify present in full checkout) |

If your sparse checkout omits `.github/actions`, workflows that reference local actions will fail in CI until those paths are present.

## Cross-repo `uses:`

Many workflows use **marketplace** actions (`actions/checkout@v4`, `oven-sh/setup-bun@v2`, and so on). Those are **not** composite actions in this repo; pin versions per each repo’s CI policy.

If a workflow later uses `uses: org/repo/.github/actions/name@ref`, add a row here and link the **provider** PR / release policy.

## Maintenance

- After adding or renaming an action under `.github/actions/`, update this table and grep consumers:  
  `rg "uses: \\./\\.github/actions" --glob "*.yml" .github`
- **Ship:** doc-only PR in **thegent** is acceptable; mirror a one-line pointer in primary repos if reviewers expect it next to `AGENTS.md`.
