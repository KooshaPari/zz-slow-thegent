# Merged Fragmented Markdown

## Source: docs/development

## Source: research-protocol.md

# Deep Research Protocol (DRP)

This protocol is designed to circumvent bot-blocking and ensure comprehensive, high-quality research from diverse sources.

## Core Rules

1.  **Bypass Blocking**: NEVER use the default search tool or `WebFetch` for Reddit, Google, or other sites that block automated scrapers.
2.  **Preferred Tooling**: Use `curl` with a browser-like User-Agent.
3.  **Source Prioritization**:
    - **Search**: Use `https://html.duckduckgo.com/html/?q=[query]` for search results.
    - **Reddit**: Use `https://www.reddit.com/r/[subreddit]/[query].json` or search via DDG.
    - **Academic**: Use `https://export.arxiv.org/api/query?search_query=[query]`.
    - **Code/Dev**: Use GitHub's Search API or specialized dev portals.

## Implementation Steps

### Phase 1: Expansion & Discovery

- Generate 3-5 variations of the research query to cover different perspectives.
- Perform searches across multiple engines (DDG, Reddit, Arxiv).
- Collect at least 15-20 potential URLs.

### Phase 2: Filtering & Triage

- Analyze titles and snippets from collected URLs.
- Select 3-5 "Primary Sources" for deep reading.
- Select 5-10 "Secondary Sources" for quick cross-referencing.

### Phase 3: Deep Extraction

- For each Primary Source, fetch the full content using `curl`.
- Extract key arguments, technical details, and unique insights.
- Identify citations or links to other relevant papers/repositories.

### Phase 4: Synthesis & Verification

- Synthesize findings into a structured report.
- Cross-reference claims across at least two independent sources.
- Highlight consensus vs. conflicting views.

## Shell Helpers

Use these commands for fetching:

```bash
# General fetch
curl -L -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" -s "[URL]"

# Reddit JSON API
curl -L -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" -s "https://www.reddit.com/r/[subreddit]/search.json?q=[query]&restrict_sr=1&sort=relevance" | jaq .

# DuckDuckGo HTML Search
curl -L -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" -s "https://html.duckduckgo.com/html/?q=[query]"
```

---

Copied count: 1
