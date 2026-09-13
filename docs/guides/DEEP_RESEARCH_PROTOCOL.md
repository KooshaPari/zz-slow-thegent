# Deep Research Protocol (DRP)

**Version:** 1.0
**Status:** Implementation Ready
**Scope:** Systematic research across Reddit, Google, GitHub, ArXiv, and other domains.

---

## 1. Core Principles

1.  **Exploration First**: Broad exploration before targeted scraping.
2.  **Domain-Specific Search**: Use tailored queries for specialized sources.
3.  **Resilience**: Bypass site-level blocking (Reddit, Google) using stealth tools (Playwright) and API aggregators (Exa, Tavily).
4.  **No Duplicate Effort**: Cache results and synthesis to avoid re-scraping.
5.  **Multi-Level Synthesis**: Consolidate findings at each stage.

---

## 2. Protocol Phases

### Phase 1: Broad Exploration (Search)

- **Tool**: `thegent_ddg_search` or `thegent_exa_search`.
- **Method**: Broad queries across multiple search engines.
- **Goal**: Identify key sources, subreddits, and repositories.

### Phase 2: Domain-Specific Deep Dive

- **Reddit**: Use `thegent_reddit_search` or `site:reddit.com` queries via a resilient search tool.
- **GitHub**: Search for code patterns, READMEs, and discussions.
- **ArXiv**: Search for academic papers and latest research.
- **StackOverflow**: Search for technical implementation details.

### Phase 3: Targeted Scrape (Stealth)

- **Tool**: `thegent_scrape_url` (Playwright-backed).
- **Method**: Use a real browser locally to bypass anti-bot measures.
- **Goal**: Extract content from links identified in Phase 2.

### Phase 4: Synthesis & Mapping

- **Tool**: Agent synthesis.
- **Method**: Map findings back to the original query. Identify gaps and iterate if needed.
- **Output**: Research summary in `docs/research/RESEARCH_YYYY_MM_DD.md`.

---

## 3. Tool Implementation (Roadmap)

| Tool                    | Engine                 | Status         | Purpose                           |
| ----------------------- | ---------------------- | -------------- | --------------------------------- |
| `thegent_ddg_search`    | duckduckgo-search      | ✅ Implemented | Broad web search                  |
| `thegent_reddit_search` | PRAW / site:reddit.com | ✅ Implemented | Dedicated Reddit search           |
| `thegent_scrape_url`    | Playwright (Stealth)   | ✅ Implemented | Bypassing blocks on Reddit/Google |
| `thegent_deep_research` | Orchestrator           | ✅ Implemented | Multi-phase research protocol     |
| `thegent_exa_search`    | Exa.ai API             | ⏳ Future      | Semantic search for AI agents     |

---

## 4. Enforcement Strategy

1.  **Governance**: Added to `CLAUDE.md`. Agents _must_ use this protocol for research.
2.  **Hooks**: `hooks/pre-research-protocol-checker.sh` (Future) to enforce multi-step research.
3.  **Default Agent**: `thegent research` subcommand enforces this protocol by default.

---

## 5. Troubleshooting (Bypassing Blocks)

- **Problem**: Reddit blocks standard scrapers.
- **Fix**: Use `thegent_scrape_url` which uses a local Playwright instance (browser fingerprinting) instead of `WebFetch`.
- **Problem**: Google blocks automated searches.
- **Fix**: Use DuckDuckGo or Exa.ai as primary search engines. Use `thegent_scrape_url` for Google links if necessary.
- **Problem**: Overly narrow scope.
- **Fix**: Always start with broad keywords and use the `exploration_depth` parameter in research tools.
