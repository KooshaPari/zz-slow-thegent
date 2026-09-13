# Worklog Wave 74 - Lane F

Date: 2026-02-23
Lane focus: memory systems, model/framework, deployment, scraping

## Item 1

- Thread: AI agents need better memory systems, not just bigger context windows (`r/AI_Agents`)
  https://reddit.com/r/AI_Agents/comments/1r0q4qf/ai_agents_need_better_memory_systems_not_just/
- Core claim: Durable, structured memory layers outperform brute-force larger context windows for long-horizon agent work.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating non-Reddit links:
  - https://langchain-ai.github.io/langgraph/concepts/memory/
  - https://github.com/cpacker/MemGPT
  - https://arxiv.org/abs/2310.08560

## Item 2

- Thread: How important is Langchain in building Agents? (`r/AI_Agents`)
  https://www.reddit.com/r/AI_Agents/comments/1lbs0j7/how_important_is_langchain_in_building_agents/
- Core claim: Framework choice (LangChain/LangGraph/AutoGen/CrewAI class) is an accelerator, but architecture and orchestration discipline determine reliability.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating non-Reddit links:
  - https://python.langchain.com/docs/introduction/
  - https://microsoft.github.io/autogen/stable/
  - https://docs.crewai.com/

## Item 3

- Thread: What is the best tool for long-running agentic memory in Claude Code? (`r/ClaudeCode`)
  https://reddit.com/r/ClaudeCode/comments/1q7mqx8/what_is_the_best_tool_for_longrunning_agentic/
- Core claim: Long-running coding agents need explicit external memory services (historian/MCP-backed stores), not chat history alone.
- Evidence quality: B
- Verdict: Adopt Now
- Corroborating non-Reddit links:
  - https://github.com/Vvkmnn/claude-historian
  - https://modelcontextprotocol.io/
  - https://github.com/modelcontextprotocol/servers

## Item 4

- Thread: What are people actually using for web scraping that doesn’t break every few days/weeks? (`r/aiagents`)
  https://reddit.com/r/aiagents/comments/1qjllrs/what_are_people_actually_using_for_web_scraping/
- Core claim: Browser-automation-first scraping stacks are favored for resilience against frequent frontend changes.
- Evidence quality: A
- Verdict: Adopt Now
- Corroborating non-Reddit links:
  - https://playwright.dev/docs/intro
  - https://pptr.dev/
  - https://docs.firecrawl.dev/

## Item 5

- Thread: I built “Vercel for AI agents” — a single click deployment platform for any framework (`r/aiagents`)
  https://reddit.com/r/aiagents/comments/1pd77du/i_built_vercel_for_ai_agents_single_click/
- Core claim: Agent deployment is converging on managed platform patterns (standardized deploy targets + sandboxed execution + operational ergonomics), but product claims still require careful validation.
- Evidence quality: B
- Verdict: Watch
- Corroborating non-Reddit links:
  - https://vercel.com/docs
  - https://docs.e2b.dev/
  - https://modal.com/docs
