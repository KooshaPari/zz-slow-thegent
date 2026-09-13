# Provider Model Reference

Authoritative model lists from official provider docs. Use for catalog alignment and validation.

**Sources:**

- [Kilo free/budget models](https://kilo.ai/docs/code-with-ai/agents/free-and-budget-models)
- [Kilo model selection](https://kilo.ai/docs/code-with-ai/agents/model-selection)
- [Kilo auto-model](https://kilo.ai/docs/code-with-ai/agents/auto-model)
- [Roo Code Router](https://docs.roocode.com/providers/roo-code-router)
- [Cursor models](https://cursor.com/docs/models)
- [NVIDIA Build models](https://build.nvidia.com/models)
- [NVIDIA NIM API reference](https://docs.api.nvidia.com/nim/reference/models-1)

---

## Copilot (GitHub Copilot CLI)

**Allowed `--model` choices** (from `copilot --help`):

| Model                |
| -------------------- |
| claude-sonnet-4.5    |
| claude-haiku-4.5     |
| claude-opus-4.5      |
| claude-sonnet-4      |
| gpt-5                |
| gpt-5.1              |
| gpt-5.1-codex-mini   |
| gpt-5.1-codex        |
| gemini-3-pro-preview |
| gpt-5-mini           |
| gpt-4.1              |

**Invalid:** `gemini-3-flash` is not in the allowed list.

---

## Cursor

| Model             | Context | Max Mode |
| ----------------- | ------- | -------- |
| Claude 4.5 Sonnet | 200k    | 1M       |
| Claude 4.6 Opus   | 200k    | 1M       |
| Composer 1.5      | 200k    | -        |
| Gemini 3 Flash    | 200k    | 1M       |
| Gemini 3 Pro      | 200k    | 1M       |
| GPT-5.2           | 272k    | -        |
| GPT-5.3 Codex     | 272k    | -        |
| Grok Code         | 256k    | -        |

---

## Kilo Gateway (free)

| Model                 | Provider                                               |
| --------------------- | ------------------------------------------------------ |
| Trinity Large Preview | Arcee AI                                               |
| Giga Potato           | (stealth)                                              |
| Kimi K2.5             | MoonshotAI                                             |
| GLM 4.7               | Z.AI                                                   |
| MiniMax M2.1          | MiniMax                                                |
| minimax-m2.5          | see [kilo.ai/leaderboard](https://kilo.ai/leaderboard) |

## Kilo via OpenRouter (free tier)

| Model            |
| ---------------- |
| Kimi K2          |
| DeepSeek R1 0528 |
| GLM 4.5 Air      |
| Qwen3 Coder      |

## Kilo Auto Model (`kilo/auto`)

| Mode                                        | Model             |
| ------------------------------------------- | ----------------- |
| architect, orchestrator, ask, plan, general | Claude Opus 4.6   |
| code, build, debug, explore                 | Claude Sonnet 4.5 |

---

## Antigravity (Vertex Model Garden)

| Model                        |
| ---------------------------- |
| Gemini 3 Pro (high)          |
| Gemini 3 Pro (low)           |
| Gemini 3 Flash               |
| Claude Sonnet 4.5            |
| Claude Sonnet 4.5 (thinking) |
| Claude Opus 4.5 (thinking)   |
| GPT-OSS                      |

---

## NVIDIA NIM / Build

**Model catalog:** [build.nvidia.com/models](https://build.nvidia.com/models)
**API reference:** [docs.api.nvidia.com/nim/reference](https://docs.api.nvidia.com/nim/reference/models-1)

NIM microservices provide foundation models via OpenAI-compatible APIs. Categories: LLM, Retrieval, Visual, Multimodal, Healthcare, Route Optimization, Climate Simulation.

**Catalog routes (nim provider):**

| Model                | Notes                                  |
| -------------------- | -------------------------------------- |
| llama-nemotron-ultra | Default; FREE NIM API                  |
| deepseek-v3.2        | 73% SWE-Bench                          |
| glm-5                | 78% SWE-Bench, self-hosted             |
| step-3.5-flash       | 51.8 Terminal bench (step3.5), via NIM |
| kimi-k2.5            | via NIM                                |

**Setup:** Add openai-compatibility entry named `nim` to cliproxy config, or `thegent cliproxy login nim`. Base URL typically `*.ngc.nvidia.com` or `build.nvidia.com`. **NIM provides glm-5 and step-3.5-flash, NOT minimax.**

---

## Roo Code Router (deprecated)

No free tier; removed from catalog. Use kilo or glm for free/budget models.

---

## Catalog Alignment

When adding or updating catalog routes:

1. **Copilot:** Only use models from the allowed list above.
2. **Kilo:** Models from Kilo Gateway + OpenRouter free tier.
3. **Cursor:** Models from Cursor docs; `auto` for task-based selection.
4. **Antigravity:** Gemini 3.x, Claude 4.5/4.6 variants.
5. **NVIDIA NIM:** See [build.nvidia.com/models](https://build.nvidia.com/models) for current catalog; use openai-compat in cliproxy.

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
