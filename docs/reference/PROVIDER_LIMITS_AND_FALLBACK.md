# Provider Limits and Auto-Fallback

## Rate Limit vs Usage Limit

| Kind            | Meaning                                                                         | Handling                                                |
| --------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------- |
| **Rate limit**  | Too many requests per minute (429, "rate limit", "too many requests")           | Retry same provider with exponential backoff (tenacity) |
| **Transient**   | Gateway/network issues (502, 503, 504, "reconnecting")                          | Retry same provider with exponential backoff            |
| **Usage limit** | Subscription/quota exhausted ("quota exceeded", "usage limit", "monthly limit") | Fallback to different provider (no retry same)          |

## Auto-Fallback Chains

When a provider hits a **usage limit**, thegent automatically tries the next provider in its fallback chain:

- **glm** → minimax → antigravity → gemini
- **minimax** → glm → antigravity → gemini
- **antigravity** → minimax → glm → gemini
- **gemini** → codex → copilot → claude
- **codex** → gemini → copilot → claude
- **copilot** → gemini → codex → claude
- **claude** → gemini → codex → copilot
- **cursor-agent** → gemini → codex → claude

Fallback only triggers on usage-limit errors. Other failures (config, unknown provider) do not trigger fallback.

## Implementation

- `src/thegent/agents/resilience.py`: `classify_failure()`, `is_retryable()`, `is_usage_limit()`
- `src/thegent/agents/registry.py`: `get_fallback_agents()`, `_PROVIDER_FALLBACK_CHAIN`
- Retry: tenacity with exponential backoff (2–60s, 4 attempts)
- Fallback: CLI and `run_impl` expand routes when usage limit detected

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
