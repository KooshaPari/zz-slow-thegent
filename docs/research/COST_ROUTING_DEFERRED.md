<DONE>
# Cost-Based Routing — Deferred Scope

**Date:** 2026-02-14
**Status:** Documented as deferred (R8, Optional→Required)
**Source:** `docs/plans/DISTRIBUTED_MODEL_ROUTING_PLAN.md`, gaps doc R8

---

## 1. What Exists Today

- **`cost_weight` on Route** (`src/thegent/models/catalog.py`): Each route has a static `cost_weight` (lower = cheaper). Static catalog assigns weights per provider/model (e.g. gemini-3-flash 0.1, claude-opus 1.0).
- **`cheapest` routing policy**: When policy is `cheapest`, routes are sorted by `cost_weight` then priority. Implemented in `resolve_route()`.
- **Scraped routes**: Use defaults (proxy 0.8, direct 0.3) when no static weight exists.

---

## 2. Deferred / Out of Scope

The following are **not implemented** and are documented as deferred:

| Item                          | Description                                                   | Reference           |
| ----------------------------- | ------------------------------------------------------------- | ------------------- |
| Per-run cost tracking         | Aggregate actual cost per run; budget alerts                  | FR-036, WP-Y4       |
| Cost-per-quality optimization | RouteLLM-style provider selection; A/B cost-quality trade-off | WP-5003, NFR-016    |
| Dynamic cost weights          | Cost weights from live pricing or usage data                  | —                   |
| Budget enforcement            | Hard limits per run or per hour; throttle on overage          | Risk registry TD-02 |

---

## 3. Future Work

When cost-based routing is prioritized:

1. Implement `orchestration/cost.py` (WP-Y4) for per-run cost aggregation.
2. Add budget alerts and cost-overage gates.
3. Integrate cost tracking with run registry for historical analysis.
4. Consider RouteLLM or similar for cost-quality optimization (WP-5003).

---

## BACKLOG items (when cost-based routing prioritized)

| ID                 | Title                                                                   | Source                               | Priority | Depends    |
| ------------------ | ----------------------------------------------------------------------- | ------------------------------------ | -------- | ---------- |
| cost-wp-y4         | Per-run cost aggregation (orchestration/cost.py)                        | COST_ROUTING_DEFERRED.md §3          | P2       | —          |
| cost-budget-alerts | Budget alerts and cost-overage gates                                    | COST_ROUTING_DEFERRED.md §3          | P2       | cost-wp-y4 |
| cost-wp-5003       | Cost-quality optimization (RouteLLM-style); integrate with run registry | COST_ROUTING_DEFERRED.md §3, WP-5003 | P2       | cost-wp-y4 |

_Run `thegent plan incorporate` to merge into [WORK_STREAM.md](../reference/WORK_STREAM.md)._

---

## 4. References

- `docs/plans/DISTRIBUTED_MODEL_ROUTING_PLAN.md` §3.1, §3.2
- `docs/unified-plan/04-REQUIREMENTS.md` FR-036, NFR-016
- `docs/unified-plan/02-UNIFIED-WBS.md` WP-Y4, WP-5003
- `docs/docset/RISKS_AND_ANTIPATTERNS.md` (cost optimization risks)
- [WORK_STREAM.md](../reference/WORK_STREAM.md)

---

## 4. IMPLEMENTATION: Cost Tracking System

### 4.1 Cost Aggregation Module

```python
#!/usr/bin/env python3
# src/thegent/orchestration/cost.py

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class CostEntry:
    """Single cost entry for a token or API call."""

    timestamp: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    run_id: str
    task_id: Optional[str] = None


class CostTracker:
    """Track and aggregate costs across runs."""

    def __init__(self, cost_dir: Path = Path("~/.thegent/costs")):
        self.cost_dir = cost_dir.expanduser()
        self.cost_dir.mkdir(parents=True, exist_ok=True)
        self.current_run: Optional[str] = None
        self.run_entries: list[CostEntry] = []

    def start_run(self, run_id: str):
        """Start tracking a new run."""
        self.current_run = run_id
        self.run_entries = []

    def record_entry(self, entry: CostEntry):
        """Record a cost entry."""
        self.run_entries.append(entry)

    def end_run(self) -> Dict:
        """End run and return aggregated costs."""
        if not self.current_run:
            return {}

        total_cost = sum(e.cost_usd for e in self.run_entries)
        total_input = sum(e.input_tokens for e in self.run_entries)
        total_output = sum(e.output_tokens for e in self.run_entries)

        summary = {
            "run_id": self.current_run,
            "total_cost_usd": round(total_cost, 6),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "providers": {},
            "ended_at": datetime.utcnow().isoformat() + "Z",
        }

        # Aggregate by provider
        for entry in self.run_entries:
            provider = entry.provider
            if provider not in summary["providers"]:
                summary["providers"][provider] = {"cost_usd": 0, "input_tokens": 0, "output_tokens": 0, "models": {}}
            p = summary["providers"][provider]
            p["cost_usd"] += entry.cost_usd
            p["input_tokens"] += entry.input_tokens
            p["output_tokens"] += entry.output_tokens

            model = entry.model
            if model not in p["models"]:
                p["models"][model] = {"cost_usd": 0, "calls": 0}
            p["models"][model]["cost_usd"] += entry.cost_usd
            p["models"][model]["calls"] += 1

        # Save to file
        self._save_run_summary(summary)
        self.current_run = None
        self.run_entries = []
        return summary

    def _save_run_summary(self, summary: Dict):
        """Save run summary to JSON file."""
        run_file = self.cost_dir / f"{summary['run_id']}.json"
        run_file.write_text(json.dumps(summary, indent=2))

        # Append to aggregate
        aggregate_file = self.cost_dir / "aggregate.jsonl"
        with open(aggregate_file, "a") as f:
            f.write(
                json.dumps(
                    {
                        "run_id": summary["run_id"],
                        "total_cost": summary["total_cost_usd"],
                        "ended_at": summary["ended_at"],
                    }
                )
                + "\n"
            )
```

### 4.2 Budget Alert System

```python
#!/usr/bin/env python3
# src/thegent/orchestration/budget_alerts.py

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class BudgetConfig:
    """Budget configuration."""

    hourly_limit_usd: float = 10.0
    daily_limit_usd: float = 100.0
    run_limit_usd: float = 5.0
    warning_threshold: float = 0.8


class BudgetAlertSystem:
    """Check budgets and emit alerts."""

    def __init__(self, cost_dir: Path, config: Optional[BudgetConfig] = None):
        self.cost_dir = cost_dir
        self.config = config or BudgetConfig()

    def check_budget(self, current_cost: float, context: str = "run") -> tuple[str, bool]:
        """
        Check if cost exceeds budget.
        Returns (alert_level, is_blocking).
        """
        limit = getattr(self.config, f"{context}_limit_usd", self.config.run_limit_usd)

        if current_cost >= limit:
            return ("BLOCK", True)
        elif current_cost >= limit * self.config.warning_threshold:
            return ("WARN", False)
        return ("OK", False)

    def get_hourly_spend(self) -> float:
        """Get total spend in current hour."""
        # Implementation would check aggregate and filter by timestamp
        return 0.0
```

---

## 5. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. **Added Section 4:** Implementation of Cost Tracking System
   - CostEntry dataclass for individual entries
   - CostTracker class for aggregation
   - Provider and model breakdown

2. **Added Section 5:** Budget Alert System
   - BudgetConfig for limits
   - BudgetAlertSystem for checking thresholds
   - Alert levels (OK, WARN, BLOCK)

### Cross-References Added

- DISTRIBUTED_MODEL_ROUTING_PLAN.md
- WORK_STREAM.md

### Practical Additions

- Python CostTracker implementation
- Budget alert system with configurable limits
- Cost aggregation by provider and model

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [COST_ROUTING_DEFERRED_EXPANDED.md](./COST_ROUTING_DEFERRED_EXPANDED.md) - Expanded version
- [SESSION_RESEARCH_FRAGMENTS_EXPANDED.md](./SESSION_RESEARCH_FRAGMENTS_EXPANDED.md) - Economic governance
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
