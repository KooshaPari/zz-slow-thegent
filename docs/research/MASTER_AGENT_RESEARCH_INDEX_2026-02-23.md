<DONE>
# Master Agent Research Index

<DONE>

Date: February 23, 2026

## Included Research Sets

- `docs/research/VALE_RUVNET_BAR181_OUTWARD_DEEP_RESEARCH_2026-02-23.md`
- `docs/research/STARS_SET_OUTWARD_DEEP_RESEARCH_2026-02-23.md`
- `docs/research/STARS_SET_SECOND_BATCH_OUTWARD_DEEP_RESEARCH_2026-02-23.md`
- `docs/research/STARS_SET_THIRD_BATCH_OUTWARD_DEEP_RESEARCH_2026-02-23.md`

## Consolidated Ranked Roadmap (Deduplicated)

### Tier 1: Adopt Now

1. `errata-ai/vale` (docs quality baseline)
2. `pre-commit` + `actionlint` + `lychee` + `cspell` + `gitleaks` (quality/governance baseline)
3. `pathintegral-institute/mcpm.sh` + `f/mcptools` + `isaacphi/mcp-language-server` (MCP ops baseline)
4. `upstash/context7` (code context documentation channel)
5. `sdi2200262/agentic-project-management` (orchestration backbone)
6. `superagent-ai/vibekit` (sandbox, redaction, observability)
7. `Portkey-AI/gateway` + `aurelio-labs/semantic-router` (routing/gateway layer)
8. `mem0ai/mem0` (memory baseline)

### Tier 2: Pilot With Hard Gates

1. `browser-use/browser-use`
2. `browserbase/stagehand`
3. `block/goose`
4. `testdriverai/testdriverai`
5. `bytedance/UI-TARS-desktop`
6. `opactorai/Claudable`
7. `getzep/graphiti`
8. `LMCache/LMCache`
9. `bgauryy/octocode-mcp` / `Muvon/octocode`
10. `chunkhound/chunkhound`
11. `cvs-health/testaro`
12. `ruvnet/claude-flow` ecosystem (strict validation required)
13. selected `bar181` code repos (`fastapi-agents`, `openai-agents`)

### Tier 3: Reference / Research Inputs

1. `Fission-AI/AgilePlus`
2. `danielmiessler/Fabric`
3. `microsoft/BitNet`
4. `exo-explore/exo`
5. curated lists (`awesome-*`, docs/tooling catalogs)

### Tier 4: Avoid or Delay

1. Archived or stale core dependencies for production control planes.
2. Repos with unclear license/security posture.
3. Marketing-heavy projects lacking reproducible benchmarks or governance proof.

## Added Item: Augment Code Context Engine + Intent

### Augment (Code Context Engine)

- Classification: `Pilot With Hard Gates`.
- Role: external code-context engine for richer retrieval and intent-aware task grounding in coding workflows.
- Why added: aligns directly with your request to include context engine + intent capabilities in the master roadmap.
- Integration note: place between MCP context providers and orchestration layer; treat as retrieval/control-plane dependency that requires strict benchmarking and privacy review.

### Intent Layer (Cross-Cutting)

- Recommended approach: explicit intent-routing layer above tool dispatch.
- Candidate pattern:

1. `semantic-router` for intent-class dispatch.
2. context providers (`context7`, code context engine such as Augment) for retrieval grounding.
3. policy checks (Rulesets/OPA-Conftest style) before high-risk tool calls.

## Standard Hard Gates (All Tier 2+)

1. Reproducible install/build/test in your environment.
2. Security posture pass (SAST/dependency/secrets checks).
3. License/compliance verification.
4. Operational rollback path validated.
5. Measured quality/latency/cost improvement over baseline.

## Immediate Next Execution Backlog

1. Roll out Tier-1 baseline in CI and local hooks.
2. Start two pilot tracks:

- Track A: `browser-use` vs `stagehand` vs `testdriverai`.
- Track B: `mem0` + `semantic-router` + `Portkey` + `context7` (+ Augment pilot).

3. Run 2-week gated evaluation and promote only passing tools.
