<DONE>
# Exhaustive Line-by-Line Audit Master

Date: February 23, 2026

## Scope Baseline

This master audit consolidates exhaustive passes over all items captured in:

- `docs/research/VALE_RUVNET_BAR181_OUTWARD_DEEP_RESEARCH_2026-02-23.md`
- `docs/research/STARS_SET_OUTWARD_DEEP_RESEARCH_2026-02-23.md`
- `docs/research/STARS_SET_SECOND_BATCH_OUTWARD_DEEP_RESEARCH_2026-02-23.md`
- `docs/research/STARS_SET_THIRD_BATCH_OUTWARD_DEEP_RESEARCH_2026-02-23.md`

## Coverage Summary

- Lane A (`ruvnet`): fully enumerated surfaces from prior dossiers, line-by-line.
- Lane B (`bar181`): fully enumerated repos/gists/public-post/package surfaces from prior dossiers, line-by-line.
- Lane C (starred-set batch 1): all 47 repo/link clusters from dossier scanned and verdict-assigned.
- Lane D (starred-set batch 2): all line-mapped repos from dossier scanned with live metadata and verdicts.
- Lane E (starred-set batch 3): all line-mapped repos/links scanned and verdict-assigned.

## Final Verdict Key

- `Adopt`: ready for baseline integration.
- `Pilot`: use with hard gates only.
- `Reference`: informational input, not runtime dependency.
- `Watchlist`: unresolved risk/license/stability concerns.
- `Avoid/Defer`: do not onboard now.

## Lane A: ruvnet (line-by-line)

| Item                                                                   | Verdict                          |
| ---------------------------------------------------------------------- | -------------------------------- |
| `ruvnet/claude-flow`                                                   | Pilot                            |
| `ruvnet/claude-flow` releases/issues/discussions/actions/wiki surfaces | Pilot/Reference mix              |
| `ruvnet/agentic-flow`                                                  | Reference                        |
| `ruvnet/agentic-security`                                              | Reference                        |
| npm/package/marketplace/public-post signal links                       | Reference or Avoid (signal-only) |

## Lane B: bar181 (line-by-line)

| Item                                        | Verdict             |
| ------------------------------------------- | ------------------- |
| `bar181/fastapi-agents`                     | Pilot               |
| `bar181/openai-agents`                      | Pilot               |
| `bar181/ai-toolkit`                         | Pilot               |
| `bar181/aisp-open-core`                     | Reference           |
| `bar181/savant-ai-results`                  | Reference           |
| `bar181/agentic-professor`                  | Reference           |
| `bar181` gist/profile/post/package surfaces | Reference/Watchlist |

## Lane C: Starred Set Batch 1 (all clusters)

Coverage result from lane: `47/47` clusters covered.

High-confidence `Adopt` candidates:

- `errata-ai/vale`
- `doorstop-dev/doorstop`
- `ory/kratos` (with architecture fit)
- `nats-io/nats-server` (with ops fit)

High-value `Pilot` candidates:

- `anomalyco/opencode`
- `steveyegge/beads`
- `obra/superpowers`
- `stravu/crystal`
- `BloopAI/vibe-kanban`
- `VectifyAI/PageIndex`
- `chunkhound/chunkhound`
- `bgauryy/octocode-mcp`

## Lane D: Starred Set Batch 2 (line-mapped exhaustive)

`Adopt`:

- `browser-use/browser-use`
- `browserbase/stagehand`
- `block/goose`
- `mem0ai/mem0`
- `aurelio-labs/semantic-router`
- `Portkey-AI/gateway`
- `pathintegral-institute/mcpm.sh`
- `f/mcptools`
- `isaacphi/mcp-language-server`

`Pilot`:

- `AgilePlus`, `claude-task-master`, `humanlayer`, `cua`, `OmniParser`, `self-operating-computer`
- `cognee`, `graphiti`, `bifrost`, `LMCache`, `octocode-mcp`, `muster`, `claude-context`
- `exo`, `BitNet`, `Fabric`, `vanna`, `RAGMeUp`, `PageIndex`

`Watchlist`:

- `memU`, `WilmerAI`, `tool4ai`, `awesome-ai-model-routing`
- `mcp-router`, `dynamic-fastmcp`, `magg`, `mcp-sqlalchemy-server`
- `iai-group/nordlys`, `Nordlys-Labs/nordlys`

## Lane E: Starred Set Batch 3 (line-by-line)

`Adopt`:

- `upstash/context7`
- `mcp-use/mcp-use`
- `evalstate/fast-agent`
- `testdriverai/testdriverai`
- `bytedance/UI-TARS-desktop` (pilot-to-adopt path)
- `sdi2200262/agentic-project-management` (pilot-to-adopt path)
- `superagent-ai/vibekit`

`Pilot`:

- `opactorai/Claudable`
- `vanzan01/claude-code-sub-agent-collective`
- `Helmi/claude-simone`
- `moonshinelabs-ai/skipper-tool`
- `Quickchart/Office-Visio/HITL MCP utilities`

`Watchlist/Avoid`:

- `textcortex/claude-code-sandbox` (archived)
- protocol-ambiguous bridge repos without clear standards mapping
- stale/unclear-license repos in this batch

## Explicit Ambiguities / Unverifiable Items

- `QueryHandler` name-collision set (exact canonical repo unresolved without explicit URL pin).
- Some social/profile surfaces are signal-only and not engineering evidence.
- Private/deleted or inaccessible repos cannot be fully audited without direct access.

## Hard Gates Applied Uniformly

1. Reproducibility of setup/tests.
2. Security posture and secrets discipline.
3. License/compliance clarity.
4. Maintainer cadence and issue hygiene.
5. Integration/rollback readiness in your environment.

## Current Recommendation

- Use `MASTER_AGENT_RESEARCH_INDEX_2026-02-23.md` as strategic roadmap.
- Use this file as exhaustive audit ledger against that roadmap.
- Promote only projects that pass hard gates in your own pilot harness.
