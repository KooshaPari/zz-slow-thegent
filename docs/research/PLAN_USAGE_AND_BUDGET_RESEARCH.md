<DONE>
# Plan Usage and Budget Research

**Date:** 2026-02-16
**Scope:** Gauging plan usage across providers; provider-specific APIs; Tokscale; session file locations.

---

## Executive Summary

| Approach                                        | Providers                                                         | Data Source   | thegent Integration                                  |
| ----------------------------------------------- | ----------------------------------------------------------------- | ------------- | ---------------------------------------------------- |
| **CLIProxyAPIPlus** `GET /v1/metrics/providers` | All proxy-backed                                                  | Proxy metrics | ✅ `thegent_provider_usage`, `thegent observe usage` |
| **Tokscale** `bunx tokscale`                    | OpenCode, Claude, Codex, Gemini, Cursor, Amp, Droid, OpenClaw, Pi | Session files | Recommended external tool                            |
| **Z.ai glm-plan-usage**                         | GLM Coding Plan only                                              | Z.ai API      | Claude Code plugin; Node.js                          |
| **Provider dashboards**                         | Anthropic, OpenAI, Google, MiniMax, Z.ai                          | Web consoles  | Manual                                               |
| **Provider usage APIs**                         | Anthropic, OpenAI                                                 | REST APIs     | Future integration                                   |

---

## 1. CLIProxyAPIPlus Metrics

**Endpoint:** `GET http://127.0.0.1:{cliproxy_port}/v1/metrics/providers`

**Response shape:**

```json
{
  "nim": {"latency_p50_ms": 1200, "tps_1m": 45, "cost_per_1k": 0.22, "success_rate": 0.98},
  "kilo": {...},
  "minimax": {...}
}
```

**thegent usage:**

- `thegent observe usage` — CLI table + cost status
- `thegent_provider_usage` — MCP tool
- `clode --policy cheapest` — uses metrics for GLM backend selection

---

## 2. Tokscale (Cross-Provider Session Parsing)

**Repo:** [junhoyeo/tokscale](https://github.com/junhoyeo/tokscale)
**Install:** `bunx tokscale@latest`

**Supported clients and data locations:**

| Client          | Data Location                                               |
| --------------- | ----------------------------------------------------------- |
| OpenCode        | `~/.local/share/opencode/opencode.db` or `storage/message/` |
| Claude Code     | `~/.claude/projects/`                                       |
| OpenClaw        | `~/.openclaw/agents/` (+ legacy `.clawdbot`, `.moltbot`)    |
| Codex CLI       | `~/.codex/sessions/`                                        |
| Gemini CLI      | `~/.gemini/tmp/*/chats/`                                    |
| Cursor IDE      | API sync → `~/.config/tokscale/cursor-cache/`               |
| Amp (AmpCode)   | `~/.local/share/amp/threads/`                               |
| Droid (Factory) | `~/.factory/sessions/`                                      |
| Pi              | `~/.pi/agent/sessions/`                                     |

**Pricing:** LiteLLM pricing data; tiered pricing; cache token discounts.

**Commands:**

```bash
tokscale                    # TUI
tokscale --light            # Table
tokscale --json             # JSON for scripting
tokscale models --json      # Per-model breakdown
tokscale monthly --json     # Monthly breakdown
tokscale --opencode --claude # Filter by platform
tokscale --week --month     # Date filters
tokscale pricing "claude-3-5-sonnet"  # Lookup pricing
```

**Recommendation:** Document `bunx tokscale` as the recommended cross-provider usage tool for users who want session-level token/cost aggregation.

---

## 3. Z.ai GLM Plan Usage Plugin

**Repo:** [zai-org/zai-coding-plugins](https://github.com/zai-org/zai-coding-plugins) — `plugins/glm-plan-usage`

**Scope:** GLM Coding Plan only (Claude Code with Z.ai).

**Usage:** In Claude Code, run `/glm-plan-usage:usage-query`

**Implementation:**

- Command triggers `usage-query-agent` → `usage-query-skill`
- Skill runs `node scripts/query-usage.mjs`
- Returns usage payload or error

**Constraint:** Requires Node.js; GLM-specific.

---

## 4. Provider-Specific Usage APIs

### Anthropic

- **Docs:** [docs.anthropic.com/en/api/usage](https://docs.anthropic.com/en/api/usage)
- **Scope:** Organization usage; token counts; billing.
- **Auth:** API key.

### OpenAI

- **Endpoint:** `GET /v1/organization/usage/completions` (and variants)
- **Params:** `start_time`, `end_time`, `bucket_width`, `group_by`, etc.
- **Returns:** Bucketed usage (input_tokens, output_tokens, num_model_requests, costs).
- **Auth:** `Authorization: Bearer $OPENAI_API_KEY`

### Google AI / Gemini

- **Docs:** [ai.google.dev/gemini-api/docs/usage](https://ai.google.dev/gemini-api/docs/usage)
- **Scope:** Quota, usage limits, billing.

### MiniMax

- **Docs:** [platform.minimax.io](https://platform.minimax.io) — rate limits, quotas.
- **Note:** No public usage API documented in standard docs.

### Z.ai / GLM

- **Docs:** [docs.z.ai/api-reference/rate-limit](https://docs.z.ai/api-reference/rate-limit)
- **Scope:** Rate limits, concurrency; GLM Coding users refer to package benefits.

---

## 5. Session File Locations (for Parsing)

| Tool            | Location                                         |
| --------------- | ------------------------------------------------ |
| **Codex**       | `~/.codex/sessions/*.jsonl` (token_count events) |
| **Claude Code** | `~/.claude/projects/{path}/*.jsonl`              |
| **Gemini CLI**  | `~/.gemini/tmp/*/chats/session-*.json`           |

**Session retention:**

- Claude Code: 30 days default; set `cleanupPeriodDays: 9999999999` in `~/.claude/settings.json` to disable.
- Gemini CLI: Disabled by default.
- Codex: No cleanup.

---

## 6. thegent Existing Usage/Budget Support

| Component         | Location             | Purpose                                           |
| ----------------- | -------------------- | ------------------------------------------------- |
| `CostAggregator`  | `governance/cost.py` | MTD total, by category, daily total, budget check |
| `CostEstimator`   | `governance/cost.py` | Per-run cost estimate from pricing table          |
| `cost_status_cmd` | `cli.py`             | `thegent observe cost-status`                     |
| `govern_cost_cmd` | `cli.py`             | `thegent govern cost` — daily aggregation         |
| `usage_cmd`       | `cli.py`             | `thegent observe usage` — provider metrics + cost |
| Config            | `config.py`          | `cost_budget_mtd`, `cost_tracking_enabled`        |

---

## 7. Unification Roadmap

1. **Done:** Proxy metrics via `thegent_provider_usage` and `thegent observe usage`
2. **Done:** Cost status via `thegent_cost_status` MCP tool
3. **Optional:** Feed proxy metrics into `CostAggregator` for unified view
4. **Optional:** Call Tokscale subprocess for session-derived usage when available
5. **Future:** Direct provider usage API integration (Anthropic, OpenAI) for org-level quotas

---

## References

- [OPENROUTER_STYLE_ROUTING_AND_CLIPROXY.md](../plans/OPENROUTER_STYLE_ROUTING_AND_CLIPROXY.md)
- [Tokscale README](https://github.com/junhoyeo/tokscale)
- [zai-coding-plugins glm-plan-usage](https://github.com/zai-org/zai-coding-plugins/tree/main/plugins/glm-plan-usage)
- [OpenAI Usage API](https://platform.openai.com/docs/api-reference/usage)

---

## 6. IMPLEMENTATION: Usage Monitoring

### 6.1 CLIProxy Metrics Collector

```python
#!/usr/bin/env python3
# scripts/usage_collector.py

import httpx
import json
from datetime import datetime
from pathlib import Path


class UsageCollector:
    """Collect usage metrics from CLIProxyAPIPlus."""

    def __init__(self, proxy_url: str = "http://127.0.0.1:8318"):
        self.proxy_url = proxy_url

    def get_provider_metrics(self) -> dict:
        """Get provider metrics from proxy."""
        try:
            response = httpx.get(f"{self.proxy_url}/v1/metrics/providers")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            print(f"❌ Failed to get metrics: {e}")
            return {}

    def format_cost_report(self, metrics: dict) -> str:
        """Format metrics as cost report."""
        lines = [f"\n📊 Usage Report - {datetime.now().isoformat()}\n"]
        lines.append("-" * 50)

        for provider, data in metrics.items():
            latency = data.get("latency_p50_ms", 0)
            tps = data.get("tps_1m", 0)
            cost = data.get("cost_per_1k", 0)
            success = data.get("success_rate", 0)

            lines.append(f"\n🔹 {provider}:")
            lines.append(f"   Latency (P50): {latency}ms")
            lines.append(f"   Throughput: {tps} req/s")
            lines.append(f"   Cost: ${cost}/1K tokens")
            lines.append(f"   Success Rate: {success * 100:.1f}%")

        lines.append("\n" + "-" * 50)
        return "\n".join(lines)


if __name__ == "__main__":
    collector = UsageCollector()
    metrics = collector.get_provider_metrics()
    if metrics:
        print(collector.format_cost_report(metrics))
```

### 6.2 Tokscale Integration

```bash
#!/usr/bin/env bash
# scripts/tokscale_usage.sh

# Install and run Tokscale for session analysis
bunx tokscale@latest analyze --client claude \
    --format table \
    --output ~/.thegent/usage/tokscale_report.md

echo "📊 Tokscale report saved to ~/.thegent/usage/tokscale_report.md"
```

---

## 7. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. **Added §6:** Implementation of Usage Monitoring
   - CLIProxy metrics collector
   - Cost report formatting
   - Tokscale integration script

### Cross-References Added

- CLIProxyAPIPlus metrics endpoint
- Tokscale repository (external)

### Practical Additions

- Python usage collector with cost formatting
- Bash script for Tokscale integration

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
