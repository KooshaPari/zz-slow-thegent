<DONE>
# Starred Set Outward Deep Research

Date: February 23, 2026

## Scope

This dossier repeats and extends the prior methodology for your newly provided starred-item set.

Goals:

1. Triage the full set into practical adoption buckets.
2. Separate hype/public-signal from engineering evidence.
3. Identify pilot candidates with strongest ROI and lowest integration risk.
4. Flag high-risk/high-noise projects for sandbox-only exploration.

## Executive Summary

1. The highest-value immediate adoptions in this set are governance and infra fundamentals, not agent hype repos.
2. Top practical picks for your stack:

- `errata-ai/vale`
- `doorstop-dev/doorstop`
- `ory/kratos`
- `nats-io/nats-server`
- `pocketbase/pocketbase`
- `searxng/searxng`
- `gitleaks`/`CodeQL`/`Semgrep` class tools from adjacent ecosystem (recommended via outward expansion)

3. Most fast-rising agent orchestration repos should be treated as pilot-only until reproducibility, security, and maintenance thresholds are met.

## Bucketed Triage of Provided Set

### A. Strong Immediate Utility (production-friendly)

- `errata-ai/vale` (docs linting baseline)
- `doorstop-dev/doorstop` (requirements management in VCS)
- `ory/kratos` (identity/auth)
- `nats-io/nats-server` (messaging/eventing)
- `pocketbase/pocketbase` (lightweight backend)
- `searxng/searxng` (privacy-preserving search)
- `boyter/scc` (codebase metrics)

Why:

- Clear problem/solution fit.
- Mature OSS signals and broad external usage.
- Lower governance risk compared to fast-hype agent frameworks.

### B. High Potential, Needs Strict Pilot Gate

- `anomalyco/opencode`
- `stravu/crystal`
- `BloopAI/vibe-kanban`
- `stakpak/agent`
- `badlogic/pi-mono`
- `virattt/dexter`
- `steveyegge/beads`
- `obra/superpowers`
- `bmad-code-org/BMAD-METHOD`
- `shareAI-lab/learn-claude-code`
- `router-for-me/CLIProxyAPI`

Why:

- Valuable direction (parallel sessions, memory, orchestration, agent ops).
- Often high star velocity and strong social momentum.
- Engineering stability and security posture vary significantly; require internal validation.

### C. Curated Lists / Discovery Inputs (not dependencies)

- `testthedocs/awesome-docs`
- `golangci/awesome-go-linters`
- `avelino/awesome-go`
- `vinta/awesome-python`
- `awesome-selfhosted/awesome-selfhosted`
- `ComposioHQ/awesome-claude-skills`
- `VoltAgent/awesome-claude-code-subagents`
- `trimstray/the-book-of-secret-knowledge`

Use these as sourcing catalogs, not direct adoption targets.

### D. Research/Spec/Signal Heavy (prototype-only until proven)

- `lorelang/lore`
- `stef-k/spec`
- `andrei-shtanakov/open-prose`
- `kase1111-hash/Code_Cobra`
- `Piebald-AI/claude-code-system-prompts`
- `asgeirtj/system_prompts_leaks`
- `ArthurClune/claude-md-examples`
- `luml-ai/AGENTS.lock`

Useful for ideas and experimentation; evidence quality and governance maturity vary widely.

### E. Niche/Domain-Specific (evaluate only with direct need)

- `agentic-ops/real-estate-mcp`
- `IgorWarzocha/Opencode-Google-AI-Search-Plugin`
- `kunal123thakur/LangGraph_Task_multiagent`
- `puran-water/autocad-mcp`
- `project-talan/tln-pm`
- `william-xue/port-checker`
- `Sivachow/mcp-learning-adapter`

## Public-Signal vs Engineering-Signal Model

### Public-Signal (good for discovery, weak for trust)

- LinkedIn amplification.
- Star growth bursts.
- Marketplace listings and reposts.

### Engineering-Signal (required for trust)

- Reproducible test/benchmark evidence.
- CI quality and release hygiene.
- Security posture and dependency risk.
- Issue closure quality and governance docs.

Rule:

- Do not treat public-signal as production readiness.

## Priority Shortlist (Next 30 Days)

### Tier 1: Adopt Immediately

1. `errata-ai/vale`
2. `doorstop-dev/doorstop`
3. `ory/kratos` (if identity stack alignment needed)
4. `nats-io/nats-server` (if eventing fits architecture)

### Tier 2: Sandbox Pilots

1. `anomalyco/opencode`
2. `steveyegge/beads`
3. `obra/superpowers`
4. `stravu/crystal`
5. `BloopAI/vibe-kanban`

### Tier 3: Watchlist

1. `lorelang/lore`
2. `open-prose`
3. `AGENTS.lock`
4. selected MCP niche repos

## Suggested Evaluation Rubric (for all Tier 2+)

- `Reproducibility` (0-5)
- `Security posture` (0-5)
- `Maintenance cadence` (0-5)
- `Integration cost` (0-5, inverse)
- `Operational risk` (0-5, inverse)
- `Net score` (weighted)

Hard gates before production:

1. deterministic install/build/tests on your hardware.
2. no critical security findings.
3. acceptable maintenance signal over 30+ days.
4. rollback path proven.

## Repo-Specific Notes from this batch

- `remotion-dev/remotion`: mature and high-signal for programmatic media workflows.
- `VectifyAI/PageIndex`: interesting vectorless-RAG direction; strong claims require independent benchmark replication before trust.
- `steveyegge/beads`: high momentum; verify architecture/runtime constraints and operational burden in your own workflow.
- `anomalyco/opencode`: very high momentum; prioritize governance/security/testing checks before deep integration.

## Expanded Reference Links

(Seed + outward references used in this pass)

- https://github.com/errata-ai/vale
- https://github.com/testthedocs/awesome-docs
- https://github.com/Piebald-AI/claude-code-system-prompts
- https://github.com/asgeirtj/system_prompts_leaks
- https://github.com/remotion-dev/remotion
- https://github.com/steveyegge/beads
- https://github.com/obra/superpowers
- https://github.com/virattt/dexter
- https://github.com/badlogic/pi-mono
- https://github.com/ComposioHQ/awesome-claude-skills
- https://github.com/shareAI-lab/learn-claude-code
- https://github.com/vinta/awesome-python
- https://github.com/avelino/awesome-go
- https://github.com/awesome-selfhosted/awesome-selfhosted
- https://github.com/doorstop-dev/doorstop
- https://github.com/microsoft/magentic-ui
- https://github.com/ory/kratos
- https://github.com/pocketbase/pocketbase
- https://github.com/nats-io/nats-server
- https://github.com/searxng/searxng
- https://github.com/anomalyco/opencode
- https://github.com/stravu/crystal
- https://github.com/BloopAI/vibe-kanban
- https://github.com/VectifyAI/PageIndex
- https://github.com/bmadcode/BMAD-METHOD
- https://github.com/ruvnet/claude-flow
- https://github.com/bar181
- https://github.com/luml-ai/AGENTS.lock
- https://github.com/lorelang/lore
- https://github.com/ggwicz/skills

## Operational Recommendation

- Start with a conservative core stack and strict gates.
- Use hype-heavy agent frameworks only behind sandbox boundaries and scorecards.
- Keep adoption decisions evidence-first, not feed-first.
