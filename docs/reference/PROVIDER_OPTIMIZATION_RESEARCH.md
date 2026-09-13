# Provider-Specific Optimization Research

## Overview

Research on rate limits, retry behavior, and best practices for all LLM providers.

## MiniMax M2.5

- Max attempts: 5, Min wait: 2.0s, Max wait: 120.0s, Backoff: 2.0
- Highspeed plan optimized

## GLM-5 / Zhipu

- Max attempts: 4, Min wait: 2.0s, Max wait: 60.0s, Backoff: 1.5

## OpenAI

- Max attempts: 3, Min wait: 1.0s, Max wait: 30.0s, Backoff: 2.0

## Anthropic Claude

- Max attempts: 4, Min wait: 2.0s, Max wait: 60.0s, Backoff: 2.0

## Google Gemini

- Max attempts: 3, Min wait: 1.0s, Max wait: 30.0s, Backoff: 1.5

## DeepSeek

- Max attempts: 3, Min wait: 1.0s, Max wait: 20.0s, Backoff: 1.5

## OpenRouter

- Max attempts: 3, Min wait: 1.0s, Max wait: 30.0s, Backoff: 2.0

## All Providers Configured

| Provider    | Max Attempts | Min Wait | Max Wait | Backoff | Timeout | CB Fail | CB Timeout |
| ----------- | ------------ | -------- | -------- | ------- | ------- | ------- | ---------- |
| minimax     | 5            | 2.0s     | 120.0s   | 2.0     | 300s    | 5       | 60s        |
| glm         | 4            | 2.0s     | 60.0s    | 1.5     | 180s    | 4       | 45s        |
| openai      | 3            | 1.0s     | 30.0s    | 2.0     | 120s    | 5       | 30s        |
| claude      | 4            | 2.0s     | 60.0s    | 2.0     | 180s    | 5       | 45s        |
| gemini      | 3            | 1.0s     | 30.0s    | 1.5     | 120s    | 5       | 30s        |
| deepseek    | 3            | 1.0s     | 20.0s    | 1.5     | 120s    | 5       | 30s        |
| openrouter  | 3            | 1.0s     | 30.0s    | 2.0     | 120s    | 5       | 30s        |
| nim         | 3            | 1.0s     | 30.0s    | 1.5     | 120s    | 4       | 30s        |
| kilo        | 3            | 1.0s     | 30.0s    | 1.5     | 120s    | 4       | 30s        |
| ollama      | 2            | 0.5s     | 5.0s     | 1.5     | 300s    | 3       | 15s        |
| codex       | 3            | 1.0s     | 30.0s    | 2.0     | 120s    | 5       | 30s        |
| cursor      | 3            | 1.0s     | 30.0s    | 2.0     | 120s    | 5       | 30s        |
| antigravity | 3            | 1.0s     | 30.0s    | 2.0     | 120s    | 5       | 30s        |
| kimi        | 4            | 2.0s     | 60.0s    | 1.5     | 180s    | 4       | 45s        |
| qwen        | 3            | 1.0s     | 30.0s    | 1.5     | 120s    | 4       | 30s        |
| meta        | 3            | 1.0s     | 30.0s    | 1.5     | 120s    | 4       | 30s        |
| roo         | 3            | 1.0s     | 30.0s    | 1.5     | 120s    | 4       | 30s        |

## Implementation Status

- [x] Provider-specific retry configs module created
- [x] All 17 providers configured
- [x] Circuit breaker settings per provider

## Files Created

- `src/thegent/utils/provider_retry_config.py`
