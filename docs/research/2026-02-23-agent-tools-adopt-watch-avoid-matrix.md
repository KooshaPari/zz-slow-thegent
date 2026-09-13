<DONE>
# Agent Tools Matrix (Child-Wave Synthesis)

Date: 2026-02-23
Basis: synthesized strictly from Wave 74 child-agent lane outputs (`A`..`F`), 30 total researched items.

## Adopt Now

- Claude Code workflow hardening (review gates, CI checks, traceability)
  - Why: repeatedly tied to reliable delivery in lane A/B/E.
  - Links:
    - https://docs.anthropic.com/en/docs/claude-code/github-actions
    - https://docs.anthropic.com/en/docs/claude-code/overview
- MCP as primary integration layer
  - Why: strongest repeated interoperability signal across lanes B/C/F.
  - Links:
    - https://modelcontextprotocol.io/
    - https://github.com/modelcontextprotocol/specification
- Eval + observability stack (LangSmith + OTel GenAI)
  - Why: central to post-notebook reliability in lanes A/E.
  - Links:
    - https://docs.langchain.com/langsmith/home
    - https://opentelemetry.io/docs/specs/semconv/gen-ai/
- Memory/context governance for long-running agents
  - Why: context bloat and drift repeatedly flagged in lanes C/F.
  - Links:
    - https://langchain-ai.github.io/langgraph/concepts/memory/
    - https://python.langchain.com/docs/how_to/trim_messages/
- Cost/quota telemetry tools and API reconciliation
  - Why: operational stability and spend control signal in lane D.
  - Links:
    - https://docs.anthropic.com/en/docs/claude-code/costs
    - https://docs.anthropic.com/en/api/data-usage-cost-api

## Watch

- Multi-agent orchestration wrappers and integrations
  - Why: high upside, but fragility without strict decomposition/handoff.
  - Links:
    - https://www.langchain.com/langgraph
    - https://opencode.ai/docs/
- MCP router/proxy compositions
  - Why: promising pattern, uneven maturity and validation depth.
  - Links:
    - https://gofastmcp.com/servers/proxies
    - https://modelcontextprotocol.io/docs/getting-started/intro
- One-click deployment platforms for agent systems
  - Why: helpful ergonomics but claims vary by workload and safety posture.
  - Links:
    - https://vercel.com/docs
    - https://docs.e2b.dev/

## Avoid Hype

- Skill-catalog marketing and "autonomous" claims without production evidence
  - Why: lane A/E repeatedly flagged evidence gaps and overclaim risk.
  - Links:
    - https://www.nist.gov/itl/ai-risk-management-framework
    - https://oecd.ai/en/ai-principles
- Security by prompting alone
  - Why: tool boundaries and memory persistence require explicit controls.
  - Links:
    - https://owasp.org/www-project-top-10-for-large-language-model-applications/
    - https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html

## Short Adoption Order

1. Adopt baseline reliability stack first (`MCP + eval + telemetry + memory controls`).
2. Expand with orchestration/deployment add-ons after reliability SLOs are met.
3. Reject claims that do not include reproducible evaluation and security evidence.
