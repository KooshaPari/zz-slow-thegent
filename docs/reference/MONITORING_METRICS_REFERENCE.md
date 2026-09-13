# Monitoring Metrics Reference

## Overview

This document defines all metrics used in the routing system dashboards. Each metric includes:

- Definition (what it measures)
- Calculation formula
- Data source
- Typical range / baseline
- Alert threshold
- Refresh frequency

**Total Metrics Defined:** 25+ across 5 categories

---

## Category 1: Cost Metrics

### daily_cost_by_category

**Definition:** Sum of actual costs incurred for each task category on a given day.

**Formula:**

```
daily_cost_by_category[category][date] =
  SUM(actual_cost_usd) WHERE task_category = category AND DATE(ended_at_utc) = date AND event = 'finish'
```

**Data Source:** `run_registry.jsonl`, field `actual_cost_usd`

**Typical Range:** $5-20 per category per day (varies by usage)

**Refresh Frequency:** Real-time (5-minute batches)

**Alert Threshold:** None (informational only)

**Example:**

```
date       | fast  | normal | complex | high_complex | total
-----------|-------|--------|---------|--------------|-------
2025-02-14 | 12.50 | 45.30  | 38.20   | 15.00        | 111.00
```

---

### mtd_cost

**Definition:** Month-to-date total cost across all categories.

**Formula:**

```
mtd_cost = SUM(actual_cost_usd)
  WHERE STRFTIME('%Y-%m', ended_at_utc) = STRFTIME('%Y-%m', NOW())
  AND event = 'finish'
```

**Data Source:** `run_registry.jsonl`, field `actual_cost_usd`

**Typical Range:** $0-450 (bounded by monthly budget)

**Refresh Frequency:** Hourly

**Alert Threshold:** Warn at $360 (80% of $450), Critical at $450 (100%)

**Example:** $111.00 (as of Feb 14)

---

### category_budget_remaining

**Definition:** Budget remaining for a category after subtracting month-to-date spend.

**Formula:**

```
category_budget_remaining[category] =
  category_budget[category] - SUM(actual_cost_usd) WHERE task_category = category AND STRFTIME('%Y-%m', ended_at_utc) = STRFTIME('%Y-%m', NOW())
```

**Category Budgets:**

- FAST: $50
- NORMAL: $200
- COMPLEX: $150
- HIGH_COMPLEX: $50

**Data Source:** `run_registry.jsonl`, field `actual_cost_usd`

**Typical Range:** $0-{budget} for each category

**Refresh Frequency:** Hourly

**Alert Threshold:** Warn if < 20% of budget remaining

**Example:**

```
category     | budget | mtd_cost | remaining
-------------|--------|----------|----------
fast         | 50.00  | 12.50    | 37.50
normal       | 200.00 | 45.30    | 154.70
complex      | 150.00 | 38.20    | 111.80
high_complex | 50.00  | 15.00    | 35.00
```

---

### budget_utilization_pct

**Definition:** Percentage of category monthly budget consumed.

**Formula:**

```
budget_utilization_pct[category] =
  (category_mtd_cost[category] / category_budget[category]) * 100
```

**Data Source:** `run_registry.jsonl`

**Typical Range:** 0-100% (or >100% if overspent)

**Refresh Frequency:** Hourly

**Alert Threshold:**

- WARNING: >= 80%
- CRITICAL: >= 100%

**Example:**

```
category     | utilization_pct | status
-------------|-----------------|----------
fast         | 25.0%           | OK
normal       | 22.7%           | OK
complex      | 25.5%           | OK
high_complex | 30.0%           | WARNING
```

---

### cost_per_task

**Definition:** Average cost per task, calculated per category.

**Formula:**

```
cost_per_task[category] =
  SUM(actual_cost_usd) / COUNT(*)
  WHERE task_category = category AND event = 'finish' AND DATE(ended_at_utc) >= DATE('now', '-30 days')
```

**Data Source:** `run_registry.jsonl`

**Typical Range:**

- FAST: $0.008-0.015 per task
- NORMAL: $0.14-0.20 per task
- COMPLEX: $0.40-0.50 per task
- HIGH_COMPLEX: $1.00-1.20 per task

**Refresh Frequency:** Daily

**Alert Threshold:** Deviation > 20% from baseline indicates anomaly

**Example:**

```
category     | cost_per_task | trend
-------------|---------------|-------
fast         | 0.0089        | → stable
normal       | 0.1500        | → stable
complex      | 0.4375        | → stable
high_complex | 1.0667        | ↑ +5%
```

---

### cost_forecast_mtd

**Definition:** Linear projection of month-end cost based on daily burn rate.

**Formula:**

```
daily_burn_rate = mtd_cost / days_elapsed
cost_forecast_mtd = daily_burn_rate * 30
```

**Data Source:** Calculated from `run_registry.jsonl`

**Typical Range:** $0-450+ (can exceed budget)

**Refresh Frequency:** Daily (updated end of business day)

**Alert Threshold:** Warn if forecast >= $360, Critical if forecast > $450

**Example:**

- MTD Cost: $111.00
- Days Elapsed: 14
- Daily Burn: $7.93
- Forecast EOY: $223.60

---

## Category 2: Performance Metrics

### avg_quality_by_category

**Definition:** Average quality score achieved by models selected for a category.

**Formula:**

```
avg_quality_by_category[category] =
  AVG(quality_score)
  WHERE task_category = category AND event = 'finish' AND DATE(ended_at_utc) >= DATE('now', '-7 days')
```

**Data Source:** `run_registry.jsonl`, field `routing_constraint.quality`

**Typical Range:** 0.60-0.90 (normalized 0.0-1.0)

**Refresh Frequency:** Hourly

**Alert Threshold:** Regression > 5% below baseline per category

**Quality Baseline by Category:**

- FAST: 0.60 (minimum acceptable)
- NORMAL: 0.70
- COMPLEX: 0.75
- HIGH_COMPLEX: 0.80

**Example:**

```
category     | avg_quality | baseline | status
-------------|------------|----------|--------
fast         | 0.68       | 0.60     | OK (+13%)
normal       | 0.73       | 0.70     | OK (+4%)
complex      | 0.78       | 0.75     | OK (+4%)
high_complex | 0.85       | 0.80     | OK (+6%)
```

---

### quality_threshold_attainment

**Definition:** Percentage of tasks in a category that meet the quality threshold.

**Formula:**

```
quality_threshold_attainment[category] =
  (COUNT(tasks WHERE quality >= threshold[category]) / COUNT(*)) * 100
```

**Data Source:** `run_registry.jsonl`

**Typical Range:** 90-100% (should be consistently high)

**Refresh Frequency:** Hourly

**Alert Threshold:** < 95% for any category indicates quality regression

**Example:**

```
category     | meets_threshold_pct | status
-------------|---------------------|--------
fast         | 95.1%               | OK
normal       | 97.2%               | OK
complex      | 98.4%               | OK
high_complex | 100.0%              | OK
```

---

### model_selection_distribution

**Definition:** Percentage of tasks routed to each model, by category.

**Formula:**

```
model_selection_distribution[category][model] =
  (COUNT(tasks WHERE selected_model = model AND task_category = category) / COUNT(tasks WHERE task_category = category)) * 100
```

**Data Source:** `run_registry.jsonl`, field `selected_model`

**Typical Range:** Varies by category:

- FAST/NORMAL/COMPLEX: ~98% minimax-m2.5, ~2% fallback (claude-sonnet)
- HIGH_COMPLEX: 100% claude-opus

**Refresh Frequency:** Daily

**Alert Threshold:** Deviation > 10% from expected distribution indicates routing anomaly

**Example:**

```
category     | model              | percentage | trend
-------------|-------------------|------------|------
fast         | minimax-m2.5       | 99.7%      | → stable
normal       | minimax-m2.5       | 98.3%      | → stable
complex      | minimax-m2.5       | 87.5%      | → stable
complex      | claude-sonnet-4.5  | 12.5%      | ↑ fallback usage
high_complex | claude-opus-4.6    | 100.0%     | → stable
```

---

### fallback_rate

**Definition:** Percentage of tasks that used a fallback model (not the primary choice for their category).

**Formula:**

```
fallback_rate[category] =
  (COUNT(tasks WHERE used_fallback_model = true AND task_category = category) / COUNT(tasks WHERE task_category = category)) * 100
```

**Data Source:** `run_registry.jsonl`, field `used_fallback_model`

**Typical Range:**

- FAST: 0.5-2% (rare, primary is cost-optimized)
- NORMAL: 1-2%
- COMPLEX: 5-15% (higher due to quality variability)
- HIGH_COMPLEX: 0% (no fallback defined)

**Refresh Frequency:** Daily

**Alert Threshold:** > 20% for any category indicates constraint issues

**Example:**

```
category     | total_tasks | fallback_tasks | fallback_rate_pct
-------------|------------|----------------|------------------
fast         | 4500       | 50             | 1.1%
normal       | 1200       | 18             | 1.5%
complex      | 320        | 40             | 12.5%
high_complex | 45         | 0              | 0.0%
```

---

### constraint_violation_rate

**Definition:** Percentage of tasks that failed at least one constraint.

**Formula:**

```
constraint_violation_rate[category] =
  (COUNT(tasks WHERE constraint_violations IS NOT EMPTY) / COUNT(*)) * 100
```

**Data Source:** `run_registry.jsonl`, field `constraint_violations` (JSON array)

**Typical Range:** 2-5% (baseline acceptable)

**Refresh Frequency:** Hourly

**Alert Threshold:** > 10% for any category indicates routing problems

**Violation Types:**

- `performance`: Quality score below category threshold
- `instantaneous_cost`: Single task cost exceeds per-task budget
- `cumulative_cost`: Monthly cost would exceed budget
- `speed`: Estimated execution time exceeds SLA

**Example:**

```
category     | total_tasks | violations | rate_pct | top_violation
-------------|------------|-----------|----------|------------------
fast         | 4500       | 40        | 0.9%     | speed (15 tasks)
normal       | 1200       | 30        | 2.5%     | instantaneous_cost (8)
complex      | 320        | 12        | 3.8%     | instantaneous_cost (5)
high_complex | 45         | 2         | 4.4%     | performance (2)
```

---

## Category 3: Speed Metrics

### p50_latency_ms

**Definition:** 50th percentile (median) task completion time in milliseconds.

**Formula:**

```
p50_latency_ms[category] =
  PERCENTILE(duration_s * 1000, 0.5)
  WHERE task_category = category AND event = 'finish' AND DATE(ended_at_utc) >= DATE('now', '-7 days')
```

**Data Source:** `run_registry.jsonl`, field `duration_s`

**Typical Range:**

- FAST: 300-600ms
- NORMAL: 2000-4000ms
- COMPLEX: 10000-15000ms
- HIGH_COMPLEX: 30000-40000ms

**Refresh Frequency:** Hourly

**Alert Threshold:** > 1.5x category SLA (e.g., >1500ms for FAST) indicates degradation

**SLA Targets:**

- FAST: 1000ms (1s)
- NORMAL: 5000ms (5s)
- COMPLEX: 20000ms (20s)
- HIGH_COMPLEX: 60000ms (60s)

**Example:**

```
category     | p50_ms | sla_ms | utilization
-------------|--------|--------|------------
fast         | 450    | 1000   | 45%
normal       | 2800   | 5000   | 56%
complex      | 12000  | 20000  | 60%
high_complex | 35000  | 60000  | 58%
```

---

### p99_latency_ms

**Definition:** 99th percentile task completion time in milliseconds (worst-case latency).

**Formula:**

```
p99_latency_ms[category] =
  PERCENTILE(duration_s * 1000, 0.99)
  WHERE task_category = category AND event = 'finish' AND DATE(ended_at_utc) >= DATE('now', '-7 days')
```

**Data Source:** `run_registry.jsonl`, field `duration_s`

**Typical Range:**

- FAST: 700-1200ms
- NORMAL: 4000-6000ms
- COMPLEX: 15000-25000ms
- HIGH_COMPLEX: 45000-70000ms

**Refresh Frequency:** Hourly

**Alert Threshold:** > SLA target (e.g., >1000ms for FAST p99)

**Example:**

```
category     | p99_ms | sla_ms | breach_pct
-------------|--------|--------|----------
fast         | 850    | 1000   | 0.9%
normal       | 4500   | 5000   | 2.8%
complex      | 18500  | 20000  | 3.7%
high_complex | 55000  | 60000  | 5.2%
```

---

### sla_attainment_pct

**Definition:** Percentage of tasks completing within their category's SLA target.

**Formula:**

```
sla_attainment_pct[category] =
  (COUNT(tasks WHERE duration_s * 1000 <= sla[category]) / COUNT(*)) * 100
  WHERE task_category = category AND event = 'finish' AND DATE(ended_at_utc) >= DATE('now', '-7 days')
```

**Data Source:** `run_registry.jsonl`

**Typical Range:** 94-99% (target: ≥95%)

**Refresh Frequency:** Hourly

**Alert Threshold:** < 95% for any category

**Example:**

```
category     | sla_met | sla_missed | total | attainment_pct
-------------|---------|-----------|-------|---------------
fast         | 4461    | 39        | 4500  | 99.1%
normal       | 1166    | 34        | 1200  | 97.2%
complex      | 308     | 12        | 320   | 96.3%
high_complex | 43      | 2         | 45    | 95.6%
```

---

### avg_classification_time_ms

**Definition:** Average time taken by TaskRouter.classify() to categorize a task.

**Formula:**

```
avg_classification_time_ms =
  AVG(routing_time_ms)
  WHERE routing_stage = 'classification' AND DATE(started_at_utc) >= DATE('now', '-7 days')
```

**Data Source:** `run_registry.jsonl`, field `routing_time_ms`

**Typical Range:** 10-50ms

**Refresh Frequency:** Daily

**Alert Threshold:** > 100ms indicates classification overhead

**Note:** This is the time to analyze the prompt and determine category/complexity, NOT the full routing time.

**Example:** 28ms average

---

### total_duration_s

**Definition:** End-to-end execution time from task start to finish.

**Formula:**

```
total_duration_s =
  (ended_at_utc - started_at_utc) in seconds
```

**Data Source:** `run_registry.jsonl`, fields `started_at_utc`, `ended_at_utc`

**Typical Range:** Varies by category (see p50/p99 latencies)

**Refresh Frequency:** Real-time (updated as tasks complete)

**Alert Threshold:** > category SLA

---

## Category 4: Operational Metrics

### task_volume

**Definition:** Total number of tasks processed, by category and in aggregate.

**Formula:**

```
task_volume[category][date] =
  COUNT(*)
  WHERE task_category = category AND event = 'finish' AND DATE(ended_at_utc) = date

task_volume[date] = COUNT(*) WHERE event = 'finish' AND DATE(ended_at_utc) = date
```

**Data Source:** `run_registry.jsonl`

**Typical Range:** 300-700 tasks/day (varies by usage)

**Refresh Frequency:** Real-time

**Alert Threshold:** None (informational only)

**Example:**

```
date       | fast  | normal | complex | high_complex | total
-----------|-------|--------|---------|--------------|-------
2025-02-14 | 450   | 120    | 32      | 4            | 606
7-day avg  | 425   | 115    | 30      | 5            | 575
```

---

### error_rate_pct

**Definition:** Percentage of tasks with non-zero exit code (failures/errors).

**Formula:**

```
error_rate_pct[category] =
  (COUNT(tasks WHERE exit_code != 0) / COUNT(*)) * 100
  WHERE task_category = category AND event = 'finish' AND DATE(ended_at_utc) >= DATE('now', '-7 days')
```

**Data Source:** `run_registry.jsonl`, field `exit_code`

**Typical Range:** 0.5-3% (baseline acceptable)

**Refresh Frequency:** Hourly

**Alert Threshold:** > 5% for any category

**Example:**

```
category     | total_tasks | errors | error_rate_pct | status
-------------|------------|--------|--------------|--------
fast         | 4500       | 40     | 0.9%         | OK
normal       | 1200       | 30     | 2.5%         | WARNING
complex      | 320        | 12     | 3.8%         | WARNING
high_complex | 45         | 2      | 4.4%         | OK
```

---

### escalation_queue_depth

**Definition:** Number of tasks currently pending escalation review.

**Formula:**

```
escalation_queue_depth =
  COUNT(*) WHERE event = 'escalate' AND escalation_status IN ('pending', 'in_progress')
```

**Data Source:** `run_registry.jsonl`, field `escalation_status`

**Typical Range:** 0-5 (should be small)

**Refresh Frequency:** Real-time

**Alert Threshold:** > 10 pending escalations

**Example:** 3 pending, 1 in progress

---

### escalation_age_hours

**Definition:** Age of oldest escalation in the queue, and average age.

**Formula:**

```
escalation_age_hours_max =
  MAX((NOW() - started_at_utc) in hours)
  WHERE event = 'escalate' AND escalation_status = 'pending'

escalation_age_hours_avg =
  AVG((NOW() - started_at_utc) in hours)
  WHERE event = 'escalate' AND escalation_status = 'pending'
```

**Data Source:** `run_registry.jsonl`

**Typical Range:** 0-2 hours average (< 4 hours max)

**Refresh Frequency:** Real-time

**Alert Threshold:** max > 4 hours OR avg > 2 hours

**Example:**

```
status      | count | min_age_h | max_age_h | avg_age_h
------------|-------|-----------|-----------|----------
pending     | 3     | 0.5       | 3.2       | 1.8
in_progress | 1     | 0.1       | 0.1       | 0.1
```

---

### most_common_violation

**Definition:** Constraint violation type that occurs most frequently.

**Formula:**

```
most_common_violation =
  MODE(constraint_violations[0])
  WHERE constraint_violations IS NOT EMPTY AND event = 'finish' AND DATE(ended_at_utc) >= DATE('now', '-7 days')
```

**Data Source:** `run_registry.jsonl`, field `constraint_violations`

**Typical Range:** One of: performance, instantaneous_cost, cumulative_cost, speed

**Refresh Frequency:** Daily

**Alert Threshold:** Change in most common violation type

**Example:**

```
violation_type      | count | trend
--------------------|-------|-------
instantaneous_cost  | 20    | ↑ +3
performance         | 12    | → 0
speed               | 10    | ↓ -2
cumulative_cost     | 2     | ↓ -1
```

---

## Category 5: Budget & Spend Metrics

### fast_mtd_cost

**Definition:** Month-to-date cost for FAST category only.

**Formula:**

```
fast_mtd_cost =
  SUM(actual_cost_usd)
  WHERE task_category = 'fast'
  AND STRFTIME('%Y-%m', ended_at_utc) = STRFTIME('%Y-%m', NOW())
  AND event = 'finish'
```

**Data Source:** `run_registry.jsonl`

**Budget:** $50/month

**Typical Range:** $0-50

**Refresh Frequency:** Hourly

**Alert Threshold:** Warn at $40 (80%), Critical at $50 (100%)

---

### normal_mtd_cost

**Definition:** Month-to-date cost for NORMAL category only.

**Formula:**

```
normal_mtd_cost =
  SUM(actual_cost_usd)
  WHERE task_category = 'normal'
  AND STRFTIME('%Y-%m', ended_at_utc) = STRFTIME('%Y-%m', NOW())
  AND event = 'finish'
```

**Data Source:** `run_registry.jsonl`

**Budget:** $200/month

**Typical Range:** $0-200

**Refresh Frequency:** Hourly

**Alert Threshold:** Warn at $160 (80%), Critical at $200 (100%)

---

### complex_mtd_cost

**Definition:** Month-to-date cost for COMPLEX category only.

**Formula:**

```
complex_mtd_cost =
  SUM(actual_cost_usd)
  WHERE task_category = 'complex'
  AND STRFTIME('%Y-%m', ended_at_utc) = STRFTIME('%Y-%m', NOW())
  AND event = 'finish'
```

**Data Source:** `run_registry.jsonl`

**Budget:** $150/month

**Typical Range:** $0-150

**Refresh Frequency:** Hourly

**Alert Threshold:** Warn at $120 (80%), Critical at $150 (100%)

---

### high_complex_mtd_cost

**Definition:** Month-to-date cost for HIGH_COMPLEX category only.

**Formula:**

```
high_complex_mtd_cost =
  SUM(actual_cost_usd)
  WHERE task_category = 'high_complex'
  AND STRFTIME('%Y-%m', ended_at_utc) = STRFTIME('%Y-%m', NOW())
  AND event = 'finish'
```

**Data Source:** `run_registry.jsonl`

**Budget:** $50/month

**Typical Range:** $0-50

**Refresh Frequency:** Hourly

**Alert Threshold:** Warn at $40 (80%), Critical at $50 (100%)

---

### total_monthly_budget

**Definition:** Total budget across all categories for the month.

**Formula:**

```
total_monthly_budget =
  fast_budget + normal_budget + complex_budget + high_complex_budget
  = 50 + 200 + 150 + 50 = $450
```

**Data Source:** Hard-coded category budgets

**Value:** $450 (fixed)

**Refresh Frequency:** Static (changes only on budget policy updates)

---

### days_until_budget_exhausted

**Definition:** Projected days until monthly budget is fully consumed at current burn rate.

**Formula:**

```
daily_burn_rate = mtd_cost / days_elapsed
days_until_budget_exhausted = (total_monthly_budget - mtd_cost) / daily_burn_rate

If daily_burn_rate <= 0: days_until_budget_exhausted = infinite (or capped at 30)
```

**Data Source:** Calculated from `run_registry.jsonl`

**Typical Range:** 10-30 days (or "safe" if > 30 days remaining)

**Refresh Frequency:** Daily

**Alert Threshold:** < 3 days (critical shortage)

**Example:**

- Days Elapsed: 14
- MTD Cost: $111
- Daily Burn: $7.93
- Days Remaining: 14
- Days at Budget: 48 days (safe)

---

## Metric Summary Table

| Metric                       | Category | Type    | Range       | Refresh | Alert                |
| ---------------------------- | -------- | ------- | ----------- | ------- | -------------------- |
| daily_cost_by_category       | Cost     | USD     | $5-20/day   | 5min    | None                 |
| mtd_cost                     | Cost     | USD     | $0-450      | 1h      | Warn@$360, Crit@$450 |
| category_budget_remaining    | Cost     | USD     | $0-{budget} | 1h      | Warn@<20%            |
| budget_utilization_pct       | Cost     | %       | 0-100%+     | 1h      | Warn@80%, Crit@100%  |
| cost_per_task                | Cost     | USD     | Varies      | 1d      | Deviation>20%        |
| cost_forecast_mtd            | Cost     | USD     | $0-600      | 1d      | Warn@$360, Crit>$450 |
| avg_quality_by_category      | Perf     | 0.0-1.0 | 0.6-0.9     | 1h      | Regression>5%        |
| quality_threshold_attainment | Perf     | %       | 90-100%     | 1h      | <95%                 |
| model_selection_distribution | Perf     | %       | Varies      | 1d      | Deviation>10%        |
| fallback_rate                | Perf     | %       | 0-20%       | 1d      | >20%                 |
| constraint_violation_rate    | Perf     | %       | 2-5%        | 1h      | >10%                 |
| p50_latency_ms               | Speed    | ms      | Varies      | 1h      | >1.5xSLA             |
| p99_latency_ms               | Speed    | ms      | Varies      | 1h      | >SLA                 |
| sla_attainment_pct           | Speed    | %       | 94-99%      | 1h      | <95%                 |
| avg_classification_time_ms   | Speed    | ms      | 10-50       | 1d      | >100                 |
| total_duration_s             | Speed    | s       | Varies      | RT      | >SLA                 |
| task_volume                  | Ops      | count   | 300-700/d   | RT      | None                 |
| error_rate_pct               | Ops      | %       | 0.5-3%      | 1h      | >5%                  |
| escalation_queue_depth       | Ops      | count   | 0-5         | RT      | >10                  |
| escalation_age_hours         | Ops      | hours   | 0-2 avg     | RT      | Max>4h, Avg>2h       |
| most_common_violation        | Ops      | type    | 1 of 4      | 1d      | Change               |
| \*\_mtd_cost (by category)   | Budget   | USD     | Varies      | 1h      | Warn@80%             |
| total_monthly_budget         | Budget   | USD     | 450         | Static  | N/A                  |
| days_until_budget_exhausted  | Budget   | days    | 10-30       | 1d      | <3                   |

---

## Baseline Values by Category

### FAST Category

- Budget: $50/month
- Quality Threshold: 0.60
- SLA: 1000ms
- Per-task Budget: $0.002
- Monthly Budget: $50
- Expected Tasks: 4000-5000/month
- Expected Cost/Task: $0.009

### NORMAL Category

- Budget: $200/month
- Quality Threshold: 0.70
- SLA: 5000ms
- Per-task Budget: $0.05
- Monthly Budget: $200
- Expected Tasks: 1000-1500/month
- Expected Cost/Task: $0.15

### COMPLEX Category

- Budget: $150/month
- Quality Threshold: 0.75
- SLA: 20000ms
- Per-task Budget: $0.15
- Monthly Budget: $150
- Expected Tasks: 300-400/month
- Expected Cost/Task: $0.44

### HIGH_COMPLEX Category

- Budget: $50/month
- Quality Threshold: 0.80
- SLA: 60000ms
- Per-task Budget: $0.85
- Monthly Budget: $50
- Expected Tasks: 40-60/month
- Expected Cost/Task: $1.07

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
