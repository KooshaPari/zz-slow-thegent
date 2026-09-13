# Worklog Wave 75 - Lane D Research (2026-02-23)

Scope: actionable quality/documentation patterns extracted from `Best-README-Template`, `kwality`, `KodeVibe-Go`, plus relevant KooshaPari public repos.

## 1) Standardize README information architecture

- Source: Best-README-Template README and BLANK_README (`About`, `Getting Started`, `Usage`, `Roadmap`, `Contributing`, `License`, `Contact`, `Acknowledgments`)
- Core claim: A consistent section order reduces onboarding friction and makes maintenance predictable across projects.
- Evidence quality (A/B/C): A
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://github.com/othneildrew/Best-README-Template, https://raw.githubusercontent.com/othneildrew/Best-README-Template/master/BLANK_README.md, https://github.com/KooshaPari/cliproxyapi-plusplus
- Adaptation note for thegent: Add a `README section contract` to `docs/reference/` and enforce via `task quality` doc-check so `README.md` keeps mandatory section headers in fixed order.

## 2) Put a copy-paste quick start in the first screenful

- Source: kwality README (`One-Command Installation`, `Quick Validation Test`), KodeVibe-Go README (`Quick Install`, immediate command examples)
- Core claim: Early executable commands reduce time-to-first-success and lower abandon rate.
- Evidence quality (A/B/C): B
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://github.com/KooshaPari/kwality, https://github.com/KooshaPari/KodeVibe-Go, https://github.com/KooshaPari/cliproxyapi-plusplus
- Adaptation note for thegent: Insert a `60-second quickstart` block near top of `README.md` with exact install + `thegent --help` + one smoke command, all validated in CI.

## 3) Expose prerequisites as explicit machine/environment contracts

- Source: kwality README (`System Requirements`), KodeVibe deployment guide (`Prerequisites`, `Dependencies`)
- Core claim: Declared minimum versions and resource envelopes prevent support churn caused by implicit assumptions.
- Evidence quality (A/B/C): A
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://raw.githubusercontent.com/KooshaPari/kwality/main/README.md, https://raw.githubusercontent.com/KooshaPari/KodeVibe-Go/main/DEPLOYMENT.md, https://github.com/KooshaPari/opencode-openai-codex-auth
- Adaptation note for thegent: Add a `Compatibility Matrix` table (OS, shell, Python, Node/Bun, task, optional Docker) and fail preflight when versions are out of contract.

## 4) Pair architecture narrative with one canonical system diagram

- Source: kwality README + `ARCHITECTURE.md` (layered architecture + workflow diagrams)
- Core claim: A single canonical architecture diagram aligns contributors faster than prose-only docs.
- Evidence quality (A/B/C): B
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://raw.githubusercontent.com/KooshaPari/kwality/main/ARCHITECTURE.md, https://github.com/KooshaPari/kwality, https://github.com/KooshaPari/cliproxyapi-plusplus
- Adaptation note for thegent: Maintain one source-of-truth architecture diagram in `docs/reference/` and link it from `README.md`, `ADR.md`, and onboarding docs.

## 5) Separate functional API docs from operational runbooks

- Source: cliproxyapi++ README (`Provider Usage`, `Provider Operations Runbook`, routing reference), KodeVibe README/API section
- Core claim: Splitting usage reference from operations runbook improves both day-1 adoption and day-2 reliability.
- Evidence quality (A/B/C): B
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://github.com/KooshaPari/cliproxyapi-plusplus, https://github.com/KooshaPari/KodeVibe-Go, https://github.com/KooshaPari/kwality
- Adaptation note for thegent: Keep command/API reference in `docs/reference/` and production/operator procedures in `docs/guides/operations/`, then cross-link them from a short docs index.

## 6) Treat security policy as user-facing SLA, not boilerplate

- Source: KodeVibe-Go `SECURITY.md` (reporting channel, acknowledgment and triage windows)
- Core claim: Concrete vulnerability disclosure timelines and channels increase trust and improve inbound report quality.
- Evidence quality (A/B/C): A
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://raw.githubusercontent.com/KooshaPari/KodeVibe-Go/main/SECURITY.md, https://github.com/KooshaPari/KodeVibe-Go, https://github.com/KooshaPari/cliproxyapi-plusplus
- Adaptation note for thegent: Expand `SECURITY.md` with explicit response SLA windows, required report fields, and disclosure lifecycle states.

## 7) Back production-readiness claims with checklists and named artifacts

- Source: kwality `PRODUCTION-READINESS-SUMMARY.md` (checklists + referenced files + deployment paths)
- Core claim: Readiness claims are credible only when tied to verifiable artifact lists and procedural checklists.
- Evidence quality (A/B/C): B
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://raw.githubusercontent.com/KooshaPari/kwality/main/PRODUCTION-READINESS-SUMMARY.md, https://raw.githubusercontent.com/KooshaPari/KodeVibe-Go/main/DEPLOYMENT.md, https://github.com/KooshaPari/kwality
- Adaptation note for thegent: Create `docs/checklists/release-readiness.md` that links to concrete files/commands and require completion before release tagging.

## 8) Publish one-command quality gates and keep them deterministic

- Source: kwality `Makefile` (`check`, `security`, `test`, `lint`), cliproxyapi++ `Taskfile.yml` (`quality`, `quality:quick`, `preflight`)
- Core claim: A canonical quality command reduces local/CI drift and makes contributor expectations explicit.
- Evidence quality (A/B/C): A
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://raw.githubusercontent.com/KooshaPari/kwality/main/Makefile, https://raw.githubusercontent.com/KooshaPari/cliproxyapi-plusplus/main/Taskfile.yml, https://raw.githubusercontent.com/KooshaPari/KodeVibe-Go/main/Makefile
- Adaptation note for thegent: Keep `task quality` as the sole mandatory gate, document sub-target semantics in `docs/reference/quality-contract.md`, and ensure CI calls the same entrypoint.

## 9) Make roadmap and issue surface externally visible

- Source: Best-README-Template (`Roadmap` + open issues link), cliproxyapi++ (planning index + execution board links)
- Core claim: Public roadmap + issue linkage reduces duplicate asks and turns docs into an execution interface.
- Evidence quality (A/B/C): B
- Verdict (Adopt Now/Watch/Avoid): Watch
- Corroborating links: https://github.com/othneildrew/Best-README-Template, https://github.com/KooshaPari/cliproxyapi-plusplus, https://github.com/KooshaPari/KodeVibe-Go/issues
- Adaptation note for thegent: Add a concise `Roadmap` section in `README.md` that links to active board/docs; avoid speculative items without issue IDs.

## 10) Keep legal/usage constraints near install/auth instructions

- Source: opencode-openai-codex-auth README (`Terms of Service & Usage Notice` before setup/auth flow)
- Core claim: Prominent policy constraints reduce misuse risk more effectively than buried legal text.
- Evidence quality (A/B/C): B
- Verdict (Adopt Now/Watch/Avoid): Adopt Now
- Corroborating links: https://github.com/KooshaPari/opencode-openai-codex-auth, https://github.com/KooshaPari/KodeVibe-Go/blob/main/SECURITY.md, https://github.com/othneildrew/Best-README-Template
- Adaptation note for thegent: Add a short `Usage Boundaries` block above install/auth in `README.md` covering supported use, prohibited use, and where to find full policy docs.

## Notes on evidence grading

- A: backed by mature/common structure and corroborated across multiple repositories or executable artifacts (Taskfile/Makefile/SECURITY policy).
- B: supported by multiple repos but partly presentation-oriented or claims not independently benchmarked here.
- C: weak/uncorroborated; not used for Adopt Now in this report.
