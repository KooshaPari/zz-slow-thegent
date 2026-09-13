# Worklog Wave 74 - Lane C

Date: 2026-02-23

## Item 1

Thread: Hidden gems: MCP servers that deserve more love (`r/mcp`)
Core claim: MCP server discovery is still fragmented; practical adoption is being driven by community-curated directories and repo lists more than a single canonical marketplace.
Evidence quality: B
Verdict: Watch
Corroborating non-Reddit links:

- https://modelcontextprotocol.io/
- https://github.com/modelcontextprotocol/servers
- https://github.com/punkpeye/awesome-mcp-servers

## Item 2

Thread: Any MCP server you cannot live without? (`r/mcp`)
Core claim: Day-to-day "must-have" MCP usage concentrates around filesystem, source-control, and browser automation capabilities that reduce context-switching inside agent workflows.
Evidence quality: B
Verdict: Adopt Now
Corroborating non-Reddit links:

- https://docs.anthropic.com/en/docs/claude-code/mcp
- https://github.com/modelcontextprotocol/servers
- https://github.com/microsoft/playwright-mcp

## Item 3

Thread: mcp-glootie Is released (`r/mcp`)
Core claim: Router/proxy-style MCP composition is emerging as a serious pattern for scaling toolchains, not just standalone single-purpose servers.
Evidence quality: C
Verdict: Watch
Corroborating non-Reddit links:

- https://gofastmcp.com/servers/proxies
- https://modelcontextprotocol.io/docs/getting-started/intro
- https://github.com/modelcontextprotocol/specification

## Item 4

Thread: The 11 most useful MCP servers, after browsing hundreds of documents (`r/mcp`)
Core claim: Curated shortlists accelerate MCP adoption but are vulnerable to novelty and recency bias, so teams still need standardized evaluation criteria.
Evidence quality: B
Verdict: Watch
Corroborating non-Reddit links:

- https://github.com/modelcontextprotocol/servers
- https://github.com/modelcontextprotocol/specification
- https://opentelemetry.io/docs/specs/semconv/gen-ai/

## Item 5

Thread: MCP Context Bloat (`r/mcp`)
Core claim: Unbounded context accumulation is a primary reliability and cost failure mode for agent systems; explicit context trimming/caching policies should be baseline.
Evidence quality: A
Verdict: Adopt Now
Corroborating non-Reddit links:

- https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
- https://python.langchain.com/docs/how_to/trim_messages/
- https://langchain-ai.github.io/langgraph/concepts/memory/
- https://docs.llamaindex.ai/en/stable/module_guides/deploying/agents/memory/
