# Cheap/Local Agent Stack Playbook

Date: 2026-02-22
Goal: run reliable agent workflows locally with minimal recurring cost, real web interaction, and clear observability.

## Stack (Exact Components)

- Runtime: Python 3.11
- Package/env: uv
- Local model runtime: Ollama
- Main reasoning model: qwen2.5:14b
- Fast routing/planning model: qwen2.5:3b
- Embeddings model: nomic-embed-text
- Orchestration: LangGraph
- Web automation: Playwright (Chromium)
- Discovery search: ddgr (DuckDuckGo CLI)
- Diagnostics: ripgrep, jq
- Observability: local JSONL traces (no paid service required)

## Why This Stack

- Local-first and low recurring cost.
- Deterministic browser automation for reliability.
- Model-tiering controls token/compute cost.
- Simple, auditable trace files for debugging.

## Hardware Guidance

- Minimum practical: 16 GB RAM (works, slower).
- Recommended: 32 GB RAM for smooth local orchestration.
- Better quality/speed if GPU acceleration is available, but not required.

## Install (macOS)

```bash
brew install uv ollama ripgrep jq ddgr
ollama serve
ollama pull qwen2.5:14b
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
```

## Bootstrap Project

```bash
mkdir -p ~/local-agent-stack
cd ~/local-agent-stack
uv init
uv add langgraph langchain langchain-ollama playwright pydantic rich typer duckduckgo-search
uv run playwright install chromium
```

## Environment Config

```bash
cat > .env << 'EOF_ENV'
OLLAMA_BASE_URL=http://127.0.0.1:11434
MAIN_MODEL=qwen2.5:14b
FAST_MODEL=qwen2.5:3b
EMBED_MODEL=nomic-embed-text
TRACE_DIR=./traces
EOF_ENV
mkdir -p traces
```

## Minimal Runtime Pattern

1. Use `FAST_MODEL` for:

- routing
- decomposition
- tool selection

2. Use `MAIN_MODEL` for:

- synthesis
- final outputs
- higher-stakes reasoning

3. Use Playwright for:

- logins
- form submits
- deterministic page interactions

4. Keep traces for each tool call:

- timestamp
- tool name
- arguments (sanitized)
- result summary
- latency

## Reliability Rules

- Do not use unconstrained autonomous browsing for critical paths.
- Prefer deterministic workflows and explicit retries with backoff.
- Fail loudly and visibly when dependencies are unavailable.
- Keep tasks small; parallelize only independent steps.

## Cost Controls

- Tier model usage by task complexity.
- Cache repeated retrieval/context chunks.
- Keep context window lean with task-scoped summaries.
- Use local embeddings and local retrieval first.

## Security Guardrails

- Restrict tool set to only required commands/sites.
- Enforce path allowlists for file operations.
- Require confirmation for destructive actions.
- Redact secrets in logs and traces.

## Fast Verification

```bash
ollama list
uv run python -m playwright --version
uv run python - << 'PY'
import os
print('OLLAMA_BASE_URL=', os.getenv('OLLAMA_BASE_URL'))
PY
```

## Optional Extensions

- Add worktree-based multi-agent isolation.
- Add dashboarding over JSONL traces.
- Add benchmark harness for regression checks.

## Common Failure Modes

- Slow startup: too many plugins/processes competing for RAM.
- Browser automation flakiness: selectors too brittle; use stable locators.
- Over-contexting: large prompts reduce quality and speed.
- Hidden dependency failures: missing model pulls or stale env vars.

## Outcome

This stack gives a practical baseline for cheap/local agent operation with real browser actions, explicit control surfaces, and enough observability to debug failures without paid tooling.
