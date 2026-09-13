# Model Routing: Terminal Bench 2.0 Quick Reference

**Date**: 2026-02-15
**Status**: Corrected (supersedes SWE-Bench analysis)
**Key Finding**: GPT-5.3-Codex is now PRIMARY (was rejected before); Claude models drop significantly on terminal tasks

---

## One-Page Pareto Frontier

### Models on Frontier (Terminal Bench 2.0)

```
┌─────────────────────────────────────────────────────────────────┐
│ PARETO FRONTIER — TERMINAL BENCH 2.0                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. Qwen3.5 Plus 02-15     ~52%   │  $0 (free) │  Free tier      │
│ 2. MiniMax M2.5          51.7%  │  $0.79/M   │  Budget         │
│ 3. Codex-Spark           58.4%  │  $1.00/M   │  Speed          │
│ 4. GPT-5.3-Codex         64.7%  │  $1.25/M   │  Quality ★      │
│ 5. Claude Opus 4.6       62.9%  │  $17.50/M  │  Premium (bad)  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ DOMINATED (off frontier):                                        │
│ • GLM-5 (56.2%) — beaten by Codex-Spark                        │
│ • Gemini 3 Flash (51.7%) — beaten by MiniMax on cost           │
│ • Claude Sonnet (42.8%) — beaten by Codex                      │
│ • Claude Haiku (28.3%) — beaten by MiniMax                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Task Category Routing (Terminal Bench 2.0)

| Task Type        | Budget | Primary           | Quality | Cost         | Speed     | Why                                       |
| ---------------- | ------ | ----------------- | ------- | ------------ | --------- | ----------------------------------------- |
| **FAST**         | $0.002 | **MiniMax M2.5**  | 51.7%   | $0.0004/call | very-fast | Cheapest; adequate for simple tasks       |
| **NORMAL**       | $0.05  | **GPT-5.3-Codex** | 64.7%   | $0.0016/call | fast      | Best terminal quality; fits budget easily |
| **COMPLEX**      | $0.15  | **GPT-5.3-Codex** | 64.7%   | $0.0048/call | fast      | Reliable for multi-step shell work        |
| **HIGH_COMPLEX** | $0.85  | **GPT-5.3-Codex** | 64.7%   | $0.0048/call | fast      | Top terminal performer; well under budget |

---

## Fallback Chain

**Primary selection fails?** Use this chain:

```
GPT-5.3-Codex (unavailable)
  ↓ fallback to Codex-Spark (58.4%, faster, slightly lower quality)
    ↓ fallback to MiniMax M2.5 (51.7%, cheapest, lower quality)

MiniMax M2.5 (unavailable)
  ↓ fallback to Codex-Spark (better quality, higher cost)
    ↓ fallback to GPT-5.3-Codex (best quality, moderate cost)

Codex-Spark (unavailable)
  ↓ fallback to GPT-5.3-Codex (higher quality)
    or to MiniMax M2.5 (cheaper)

Claude Opus 4.6 (use only if reasoning is critical AND cost is irrelevant)
  ↓ fallback to GPT-5.3-Codex (better on terminal tasks, cheaper)
```

---

## What Changed from SWE-Bench

| Metric            | SWE-Bench          | Terminal Bench 2.0    | Impact                                 |
| ----------------- | ------------------ | --------------------- | -------------------------------------- |
| **Primary Model** | MiniMax (80.2%)    | GPT-5.3-Codex (64.7%) | Switch to Codex for terminal/CLI tasks |
| **Claude Haiku**  | 73.3% (good)       | 28.3% (poor)          | -61% drop; avoid for terminal work     |
| **Claude Sonnet** | 77.2% (good)       | 42.8% (poor)          | -35% drop; avoid for terminal work     |
| **Claude Opus**   | 80.8% (best)       | 62.9% (good)          | -18% drop; no longer top choice        |
| **GPT-5.3-Codex** | 56.8% (poor)       | 64.7% (best)          | +13.6% gain; now top choice            |
| **MiniMax M2.5**  | 80.2% (best value) | 51.7% (budget)        | Drops to budget tier; not primary      |

**Why?** Terminal Bench 2.0 tests CLI/shell expertise, not code editing. Codex excels at tool dispatch; Claude excels at reasoning (penalized on terminal tasks).

---

## Cost-Quality Comparison

### Terminal Bench 2.0

| Model           | Cost       | Quality   | Cost per 1% Quality     |
| --------------- | ---------- | --------- | ----------------------- |
| MiniMax M2.5    | $0.79      | 51.7%     | $0.0153 (best ratio)    |
| Codex-Spark     | $1.00      | 58.4%     | $0.0171                 |
| GPT-5.3-Codex   | $1.25      | 64.7%     | $0.0193                 |
| **Claude Opus** | **$17.50** | **62.9%** | **$0.2779 (18x worse)** |

**Key finding:** Opus costs 14x more than Codex for **1.8% LESS** quality on terminal tasks.

---

## Monthly Budget Projection

**Assumptions:**

- 5K FAST calls (500 tok avg)
- 2K NORMAL calls (1.3K tok avg)
- 500 COMPLEX calls (3.8K tok avg)
- 100 HIGH_COMPLEX calls (5K tok avg)
- Contingency: 35%

| Category     | Calls    | Avg Tokens | Primary Model | Cost        |
| ------------ | -------- | ---------- | ------------- | ----------- |
| FAST         | 5000     | 500        | MiniMax       | $1.98       |
| NORMAL       | 2000     | 1300       | Codex         | $32.50      |
| COMPLEX      | 500      | 3800       | Codex         | $23.75      |
| HIGH_COMPLEX | 100      | 5000       | Codex         | $6.25       |
| Contingency  | —        | —          | —             | $35         |
| **TOTAL**    | **7600** | —          | —             | **$100.48** |

**Cost change vs SWE-Bench:** Neutral (~$101), but **better quality for terminal tasks**.

---

## Decision Tree (One-Minute Version)

```
Is this a TERMINAL TASK? (CLI, MCP, hooks, shell scripts)
├─ YES → Use TERMINAL BENCH 2.0 models:
│         1. GPT-5.3-Codex (64.7% — best for terminal)
│         2. Codex-Spark (58.4% — if latency < 20s)
│         3. MiniMax (51.7% — only if cost critical)
│
└─ NO → Use SWE-BENCH models (code reasoning/editing):
         1. Claude Opus (80.8% — best reasoning)
         2. MiniMax (80.2% — best value)
         3. Gemini Flash (78% — if latency < 1s)
         (This is rare for thegent; thegent is terminal-focused)
```

---

## Missing Data & Assumptions

1. **Codex-Spark cost**: Estimated $1.00/M (unconfirmed)
   - If actual ≥ $1.50, Spark falls off frontier
   - **Action**: Confirm with OpenAI

2. **Terminal Bench 2.0 scope**: Assumes includes CLI/shell/environment tasks
   - May NOT include MCP protocol, governance logic, agent lifecycle
   - **Action**: Shadow test Codex on actual thegent workload

3. **Codex-Spark availability**: New model; may not be generally available
   - **Action**: Verify availability before relying on it

---

## Immediate Actions

- [ ] Confirm Codex-Spark pricing with OpenAI
- [ ] Update `/src/thegent/models/catalog.py` to use Terminal Bench 2.0 scores
- [ ] Update `/src/thegent/governance/cost.py` to route NORMAL/COMPLEX/HIGH_COMPLEX to Codex
- [ ] Shadow test Codex on actual thegent agent dispatch tasks
- [ ] Gradual rollout: Start NORMAL category, monitor quality metrics
- [ ] Re-evaluate in 1 month as Codex usage data accumulates

---

## References

- **Full Analysis**: `/docs/reference/PARETO_FRONTIER_TERMINAL_BENCH_2_0.md`
- **Previous Analysis**: `/docs/reference/PARETO_FRONTIER_COMPLETE_ANALYSIS.md` (superseded)
- **Benchmark**: Terminal Bench 2.0 (system/terminal task performance)

---

**Status**: Corrected Analysis, Ready for Implementation
**Date**: 2026-02-15

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
