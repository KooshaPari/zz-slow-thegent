# Monitoring Dashboard Specifications

## Overview

This document defines comprehensive monitoring dashboards for the thegent routing system. All dashboards are powered by SQL queries against the `run_registry.jsonl` event log and optional PostgreSQL/MySQL backend for aggregations.

**Supported Databases:** SQLite, PostgreSQL, MySQL (all queries dialect-agnostic unless noted)

**Data Source:** `run_registry.jsonl` - JSONL event log with run metadata

**Fields Used:**

- `task_category`: FAST, NORMAL, COMPLEX, HIGH_COMPLEX
- `complexity_score`: 0-100 integer
- `estimated_cost`: USD decimal
- `actual_cost_usd`: USD decimal (populated at run end)
- `routing_reason`: Text explanation
- `selected_model`: Model identifier
- `status`: success, timeout, error, escalated
- `duration_s`: Execution time in seconds
- `exit_code`: 0 for success, non-zero for failure
- `started_at_utc`: ISO 8601 timestamp
- `ended_at_utc`: ISO 8601 timestamp
- `constraint_violations`: JSON array of violated constraint names

---

## Dashboard 1: Cost Dashboard

**Purpose:** Track spending against monthly budgets, identify cost spikes, forecast month-end spend.

**Refresh Frequency:** Hourly (budget utilization), Daily (forecasts)

**Alert Thresholds:**

- WARNING: 80% of category budget used
- CRITICAL: 100% of category budget used

### Query 1.1: Daily Cost by Category

**Purpose:** Track daily spending patterns by task category.

**Refresh:** Real-time (every 5 minutes)

**Sample Output:**

```
date       | fast  | normal | complex | high_complex | total
-----------|-------|--------|---------|--------------|-------
2025-02-14 | 12.50 | 45.30  | 38.20   | 15.00        | 111.00
2025-02-13 | 11.20 | 42.10  | 35.80   | 14.50        | 103.60
2025-02-12 | 13.40 | 48.90  | 40.10   | 16.20        | 118.60
```

**SQL Query:**

```sql
SELECT
  DATE(r.ended_at_utc) as date,
  ROUND(COALESCE(SUM(CASE WHEN r.task_category = 'fast' THEN r.actual_cost_usd ELSE 0 END), 0), 2) as fast,
  ROUND(COALESCE(SUM(CASE WHEN r.task_category = 'normal' THEN r.actual_cost_usd ELSE 0 END), 0), 2) as normal,
  ROUND(COALESCE(SUM(CASE WHEN r.task_category = 'complex' THEN r.actual_cost_usd ELSE 0 END), 0), 2) as complex,
  ROUND(COALESCE(SUM(CASE WHEN r.task_category = 'high_complex' THEN r.actual_cost_usd ELSE 0 END), 0), 2) as high_complex,
  ROUND(SUM(r.actual_cost_usd), 2) as total
FROM run_registry r
WHERE r.event = 'finish'
  AND r.actual_cost_usd IS NOT NULL
  AND DATE(r.ended_at_utc) >= DATE('now', '-30 days')
GROUP BY DATE(r.ended_at_utc)
ORDER BY date DESC
LIMIT 30;
```

**Visualization:** Stacked bar chart (x-axis: date, y-axis: cost, stack: category)

**Indices Recommended:**

```sql
CREATE INDEX idx_run_registry_category_date ON run_registry(task_category, DATE(ended_at_utc));
```

---

### Query 1.2: Budget Utilization by Category (Month-to-Date)

**Purpose:** Show % of monthly budget used per category. Alert at 80%, block at 100%.

**Refresh:** Hourly

**Sample Output:**

```
category     | mtd_cost | budget | utilization_pct | status
-------------|----------|--------|-----------------|----------
fast         | 40.00    | 50.00  | 80.0%           | WARNING
normal       | 180.00   | 200.00 | 90.0%           | WARNING
complex      | 140.00   | 150.00 | 93.3%           | WARNING
high_complex | 48.00    | 50.00  | 96.0%           | WARNING
```

**SQL Query:**

```sql
SELECT
  r.task_category as category,
  ROUND(SUM(COALESCE(r.actual_cost_usd, 0)), 2) as mtd_cost,
  CASE
    WHEN r.task_category = 'fast' THEN 50.00
    WHEN r.task_category = 'normal' THEN 200.00
    WHEN r.task_category = 'complex' THEN 150.00
    WHEN r.task_category = 'high_complex' THEN 50.00
    ELSE 0
  END as budget,
  ROUND(
    (SUM(COALESCE(r.actual_cost_usd, 0)) / CASE
      WHEN r.task_category = 'fast' THEN 50.00
      WHEN r.task_category = 'normal' THEN 200.00
      WHEN r.task_category = 'complex' THEN 150.00
      WHEN r.task_category = 'high_complex' THEN 50.00
      ELSE 1
    END) * 100, 1
  ) as utilization_pct,
  CASE
    WHEN (SUM(COALESCE(r.actual_cost_usd, 0)) / CASE
      WHEN r.task_category = 'fast' THEN 50.00
      WHEN r.task_category = 'normal' THEN 200.00
      WHEN r.task_category = 'complex' THEN 150.00
      WHEN r.task_category = 'high_complex' THEN 50.00
      ELSE 1
    END) >= 1.0 THEN 'CRITICAL'
    WHEN (SUM(COALESCE(r.actual_cost_usd, 0)) / CASE
      WHEN r.task_category = 'fast' THEN 50.00
      WHEN r.task_category = 'normal' THEN 200.00
      WHEN r.task_category = 'complex' THEN 150.00
      WHEN r.task_category = 'high_complex' THEN 50.00
      ELSE 1
    END) >= 0.8 THEN 'WARNING'
    ELSE 'OK'
  END as status
FROM run_registry r
WHERE r.event = 'finish'
  AND r.actual_cost_usd IS NOT NULL
  AND STRFTIME('%Y-%m', r.ended_at_utc) = STRFTIME('%Y-%m', 'now')
GROUP BY r.task_category
ORDER BY utilization_pct DESC;
```

**Visualization:** Gauge chart per category (0-100% scale, red zone 80-100%)

**Metrics Definition:**

- `mtd_cost`: Sum of actual_cost_usd for category in current month
- `budget`: Hard-coded category budget limit
- `utilization_pct`: (mtd_cost / budget) \* 100

---

### Query 1.3: Cost Trend (Forecast vs Actual)

**Purpose:** Compare actual spend to linear forecast based on daily burn rate.

**Refresh:** Daily (update at end of day)

**Sample Output:**

```
metric          | value
----------------|----------
days_elapsed    | 14
burn_rate_daily | 7.46
mtd_actual      | 111.00
forecast_mtd    | 223.80
days_remaining  | 16
days_at_budget  | 6.72
```

**SQL Query:**

```sql
WITH mtd_data AS (
  SELECT
    STRFTIME('%Y-%m', 'now') as current_month,
    CAST((STRFTIME('%d', 'now')) AS FLOAT) as days_elapsed,
    ROUND(SUM(COALESCE(r.actual_cost_usd, 0)), 2) as mtd_actual
  FROM run_registry r
  WHERE r.event = 'finish'
    AND r.actual_cost_usd IS NOT NULL
    AND STRFTIME('%Y-%m', r.ended_at_utc) = STRFTIME('%Y-%m', 'now')
)
SELECT
  'days_elapsed' as metric,
  ROUND(mtd_data.days_elapsed, 1) as value
FROM mtd_data
UNION ALL
SELECT
  'burn_rate_daily' as metric,
  ROUND(mtd_data.mtd_actual / mtd_data.days_elapsed, 2) as value
FROM mtd_data
UNION ALL
SELECT
  'mtd_actual' as metric,
  mtd_data.mtd_actual as value
FROM mtd_data
UNION ALL
SELECT
  'forecast_mtd' as metric,
  ROUND((mtd_data.mtd_actual / mtd_data.days_elapsed) * 30, 2) as value
FROM mtd_data
UNION ALL
SELECT
  'days_remaining' as metric,
  ROUND(30 - mtd_data.days_elapsed, 1) as value
FROM mtd_data
UNION ALL
SELECT
  'days_at_budget' as metric,
  ROUND(450 / (mtd_data.mtd_actual / mtd_data.days_elapsed), 2) as value
FROM mtd_data;
```

**Visualization:**

- Line chart: X-axis (day of month), Y-axis (cumulative cost), two lines (actual vs forecast)
- Gauge: Days remaining at current burn rate

**Metrics Definition:**

- `burn_rate_daily`: MTD cost / days elapsed
- `forecast_mtd`: burn_rate_daily \* 30
- `days_at_budget`: total_monthly_budget / burn_rate_daily

**Note:** Total monthly budget = $450 (sum of all categories: 50 + 200 + 150 + 50)

---

### Query 1.4: Cost per Task Type

**Purpose:** Average cost per task by category, identify which categories are most expensive.

**Refresh:** Daily

**Sample Output:**

```
category     | task_count | total_cost | avg_cost | min_cost | max_cost
-------------|------------|-----------|----------|----------|----------
high_complex | 45         | 48.00     | 1.0667   | 0.8000   | 1.2500
complex      | 320        | 140.00    | 0.4375   | 0.1200   | 0.8500
normal       | 1200       | 180.00    | 0.1500   | 0.0200   | 0.5000
fast         | 4500       | 40.00     | 0.0089   | 0.0010   | 0.0150
```

**SQL Query:**

```sql
SELECT
  r.task_category as category,
  COUNT(*) as task_count,
  ROUND(SUM(r.actual_cost_usd), 2) as total_cost,
  ROUND(AVG(r.actual_cost_usd), 4) as avg_cost,
  ROUND(MIN(r.actual_cost_usd), 4) as min_cost,
  ROUND(MAX(r.actual_cost_usd), 4) as max_cost
FROM run_registry r
WHERE r.event = 'finish'
  AND r.actual_cost_usd IS NOT NULL
  AND DATE(r.ended_at_utc) >= DATE('now', '-30 days')
GROUP BY r.task_category
ORDER BY avg_cost DESC;
```

**Visualization:** Bar chart (x-axis: category, y-axis: avg_cost) with count labels

**Metrics Definition:**

- `avg_cost`: SUM(actual_cost_usd) / COUNT(\*)
- `min_cost`: Minimum cost for any task in category
- `max_cost`: Maximum cost for any task in category

---

## Dashboard 2: Performance Dashboard

**Purpose:** Track model quality, selection distribution, and fallback rates.

**Refresh Frequency:** Hourly

**Alert Threshold:** Quality regression > 5% below baseline

### Query 2.1: Quality Scores by Category

**Purpose:** Average quality score achieved per category vs threshold.

**Sample Output:**

```
category     | avg_quality | threshold | meets_threshold_pct | status
-------------|------------|-----------|---------------------|--------
high_complex | 0.85       | 0.80      | 100.0%              | OK
complex      | 0.78       | 0.75      | 98.4%               | OK
normal       | 0.73       | 0.70      | 97.2%               | OK
fast         | 0.68       | 0.60      | 95.1%               | OK
```

**SQL Query:**

```sql
SELECT
  r.task_category as category,
  ROUND(AVG(CAST(JSON_EXTRACT(r.routing_constraint, '$.quality') AS FLOAT)), 2) as avg_quality,
  CASE
    WHEN r.task_category = 'fast' THEN 0.60
    WHEN r.task_category = 'normal' THEN 0.70
    WHEN r.task_category = 'complex' THEN 0.75
    WHEN r.task_category = 'high_complex' THEN 0.80
    ELSE 0
  END as threshold,
  ROUND(
    (COUNT(CASE
      WHEN CAST(JSON_EXTRACT(r.routing_constraint, '$.quality') AS FLOAT) >=
        CASE
          WHEN r.task_category = 'fast' THEN 0.60
          WHEN r.task_category = 'normal' THEN 0.70
          WHEN r.task_category = 'complex' THEN 0.75
          WHEN r.task_category = 'high_complex' THEN 0.80
          ELSE 0
        END THEN 1
      END) / COUNT(*)) * 100, 1
  ) as meets_threshold_pct,
  CASE
    WHEN AVG(CAST(JSON_EXTRACT(r.routing_constraint, '$.quality') AS FLOAT)) <
      (CASE
        WHEN r.task_category = 'fast' THEN 0.60
        WHEN r.task_category = 'normal' THEN 0.70
        WHEN r.task_category = 'complex' THEN 0.75
        WHEN r.task_category = 'high_complex' THEN 0.80
        ELSE 0
      END) - 0.05 THEN 'WARNING'
    ELSE 'OK'
  END as status
FROM run_registry r
WHERE r.event = 'finish'
  AND DATE(r.ended_at_utc) >= DATE('now', '-7 days')
GROUP BY r.task_category
ORDER BY category;
```

**Visualization:** Heatmap (rows: categories, columns: quality metrics)

**Metrics Definition:**

- `avg_quality`: Average quality score (0.0-1.0) for tasks in category
- `threshold`: Minimum acceptable quality for category
- `meets_threshold_pct`: % of tasks meeting or exceeding threshold

---

### Query 2.2: Model Selection Frequency

**Purpose:** Which models are being used most, by category.

**Sample Output:**

```
category     | model              | task_count | percentage | avg_cost
-------------|-------------------|------------|-----------|----------
high_complex | claude-opus-4.6    | 45         | 100.0%    | 1.067
complex      | minimax-m2.5       | 280        | 87.5%     | 0.420
complex      | claude-sonnet-4.5  | 40         | 12.5%     | 0.625
normal       | minimax-m2.5       | 1180       | 98.3%     | 0.145
fast         | minimax-m2.5       | 4485       | 99.7%     | 0.009
```

**SQL Query:**

```sql
SELECT
  r.task_category as category,
  r.selected_model as model,
  COUNT(*) as task_count,
  ROUND((COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY r.task_category)) * 100, 1) as percentage,
  ROUND(AVG(r.actual_cost_usd), 3) as avg_cost
FROM run_registry r
WHERE r.event = 'finish'
  AND DATE(r.ended_at_utc) >= DATE('now', '-30 days')
GROUP BY r.task_category, r.selected_model
ORDER BY r.task_category, task_count DESC;
```

**Visualization:** Pie chart (per category) showing model distribution

**Metrics Definition:**

- `percentage`: (model task_count / category total) \* 100
- `avg_cost`: SUM(actual_cost_usd) / COUNT(\*) for that model in category

---

### Query 2.3: Fallback Rate by Category

**Purpose:** % of tasks that used fallback model (not primary choice).

**Sample Output:**

```
category     | total_tasks | fallback_tasks | fallback_rate_pct | reason_top
-------------|------------|--------------|------------------|------------------
complex      | 320        | 40           | 12.5%            | quality_too_low
normal       | 1200       | 18           | 1.5%             | cost_exceeded
fast         | 4500       | 50           | 1.1%             | speed_sla_miss
high_complex | 45         | 0            | 0.0%             | N/A
```

**SQL Query:**

```sql
SELECT
  r.task_category as category,
  COUNT(*) as total_tasks,
  COUNT(CASE WHEN r.used_fallback_model = true THEN 1 END) as fallback_tasks,
  ROUND(
    (COUNT(CASE WHEN r.used_fallback_model = true THEN 1 END) / COUNT(*)) * 100, 1
  ) as fallback_rate_pct,
  (SELECT constraint_violations FROM run_registry r2
   WHERE r2.task_category = r.task_category
     AND r2.used_fallback_model = true
     AND r2.event = 'finish'
     AND DATE(r2.ended_at_utc) >= DATE('now', '-30 days')
   LIMIT 1) as reason_top
FROM run_registry r
WHERE r.event = 'finish'
  AND DATE(r.ended_at_utc) >= DATE('now', '-30 days')
GROUP BY r.task_category
ORDER BY fallback_rate_pct DESC;
```

**Visualization:** Bar chart (x-axis: category, y-axis: fallback_rate_pct)

**Metrics Definition:**

- `fallback_rate_pct`: (fallback tasks / total tasks) \* 100
- `reason_top`: Most common constraint violation for fallbacks in category

---

### Query 2.4: Constraint Violations

**Purpose:** Track constraint failures and violations by type.

**Sample Output:**

```
violation_type      | category     | count | pct_of_category
--------------------|--------------|-------|----------------
performance         | high_complex | 2     | 4.4%
instantaneous_cost  | normal       | 8     | 0.7%
instantaneous_cost  | complex      | 5     | 1.6%
cumulative_cost     | normal       | 7     | 0.6%
speed               | fast         | 15    | 0.3%
```

**SQL Query:**

```sql
WITH violations AS (
  SELECT
    r.task_category,
    json_each.value as violation_type,
    COUNT(*) as count
  FROM run_registry r,
    json_each(json(r.constraint_violations))
  WHERE r.event = 'finish'
    AND r.constraint_violations IS NOT NULL
    AND DATE(r.ended_at_utc) >= DATE('now', '-30 days')
  GROUP BY r.task_category, json_each.value
)
SELECT
  v.violation_type,
  v.task_category as category,
  v.count,
  ROUND((v.count / (SELECT COUNT(*) FROM run_registry WHERE task_category = v.task_category AND event = 'finish' AND DATE(ended_at_utc) >= DATE('now', '-30 days'))) * 100, 1) as pct_of_category
FROM violations v
ORDER BY count DESC;
```

**Visualization:** Stacked bar chart (x-axis: category, y-axis: violation count, stack: violation_type)

**Metrics Definition:**

- `violation_type`: performance, instantaneous_cost, cumulative_cost, speed
- `pct_of_category`: (violations / total tasks in category) \* 100

---

## Dashboard 3: SLA Dashboard

**Purpose:** Track latency, SLA attainment, and timeout/failure rates.

**Refresh Frequency:** Real-time (for active requests), Hourly (for aggregates)

**Alert Threshold:** SLA attainment < 95% for any category

### Query 3.1: Speed Metrics by Category

**Purpose:** P50, P99 latency and SLA target by category.

**Sample Output:**

```
category     | p50_ms | p99_ms | sla_target_ms | sla_attainment_pct
-------------|--------|--------|---------------|-------------------
fast         | 450    | 850    | 1000          | 99.1%
normal       | 2800   | 4500   | 5000          | 97.2%
complex      | 12000  | 18500  | 20000         | 96.3%
high_complex | 35000  | 55000  | 60000         | 94.8%
```

**SQL Query:**

```sql
WITH latencies AS (
  SELECT
    r.task_category,
    r.duration_s * 1000 as duration_ms,
    ROW_NUMBER() OVER (PARTITION BY r.task_category ORDER BY r.duration_s) as rn,
    COUNT(*) OVER (PARTITION BY r.task_category) as total_count
  FROM run_registry r
  WHERE r.event = 'finish'
    AND r.duration_s IS NOT NULL
    AND DATE(r.ended_at_utc) >= DATE('now', '-7 days')
)
SELECT
  l.task_category as category,
  ROUND(
    (SELECT duration_ms FROM latencies l2
     WHERE l2.task_category = l.task_category
     AND l2.rn = CAST(l.total_count * 0.5 AS INT)
     LIMIT 1), 0
  ) as p50_ms,
  ROUND(
    (SELECT duration_ms FROM latencies l3
     WHERE l3.task_category = l.task_category
     AND l3.rn = CAST(l.total_count * 0.99 AS INT)
     LIMIT 1), 0
  ) as p99_ms,
  CASE
    WHEN l.task_category = 'fast' THEN 1000
    WHEN l.task_category = 'normal' THEN 5000
    WHEN l.task_category = 'complex' THEN 20000
    WHEN l.task_category = 'high_complex' THEN 60000
    ELSE 0
  END as sla_target_ms,
  ROUND(
    (COUNT(CASE WHEN l.duration_ms <= CASE
      WHEN l.task_category = 'fast' THEN 1000
      WHEN l.task_category = 'normal' THEN 5000
      WHEN l.task_category = 'complex' THEN 20000
      WHEN l.task_category = 'high_complex' THEN 60000
      ELSE 999999
    END THEN 1 END) / COUNT(*)) * 100, 1
  ) as sla_attainment_pct
FROM latencies l
GROUP BY l.task_category
ORDER BY l.task_category;
```

**Visualization:**

- Table (latency percentiles by category)
- Line chart overlay (SLA target line + actual p50/p99 over time)

**Metrics Definition:**

- `p50_ms`: 50th percentile (median) of duration_s \* 1000
- `p99_ms`: 99th percentile of duration_s \* 1000
- `sla_target_ms`: Hard-coded target (FAST: 1s, NORMAL: 5s, COMPLEX: 20s, HIGH_COMPLEX: 60s)
- `sla_attainment_pct`: % of tasks finishing within sla_target_ms

---

### Query 3.2: Task Completion Time vs SLA

**Purpose:** Detailed breakdown of tasks meeting vs missing SLA.

**Sample Output:**

```
category     | sla_met | sla_missed | total | attainment_pct
-------------|---------|-----------|-------|---------------
fast         | 4461    | 39        | 4500  | 99.1%
normal       | 1166    | 34        | 1200  | 97.2%
complex      | 308     | 12        | 320   | 96.3%
high_complex | 43      | 2         | 45    | 95.6%
```

**SQL Query:**

```sql
SELECT
  r.task_category as category,
  COUNT(CASE WHEN r.duration_s * 1000 <= CASE
    WHEN r.task_category = 'fast' THEN 1000
    WHEN r.task_category = 'normal' THEN 5000
    WHEN r.task_category = 'complex' THEN 20000
    WHEN r.task_category = 'high_complex' THEN 60000
    ELSE 999999
  END THEN 1 END) as sla_met,
  COUNT(CASE WHEN r.duration_s * 1000 > CASE
    WHEN r.task_category = 'fast' THEN 1000
    WHEN r.task_category = 'normal' THEN 5000
    WHEN r.task_category = 'complex' THEN 20000
    WHEN r.task_category = 'high_complex' THEN 60000
    ELSE 999999
  END THEN 1 END) as sla_missed,
  COUNT(*) as total,
  ROUND((COUNT(CASE WHEN r.duration_s * 1000 <= CASE
    WHEN r.task_category = 'fast' THEN 1000
    WHEN r.task_category = 'normal' THEN 5000
    WHEN r.task_category = 'complex' THEN 20000
    WHEN r.task_category = 'high_complex' THEN 60000
    ELSE 999999
  END THEN 1 END) / COUNT(*)) * 100, 1) as attainment_pct
FROM run_registry r
WHERE r.event = 'finish'
  AND r.duration_s IS NOT NULL
  AND DATE(r.ended_at_utc) >= DATE('now', '-7 days')
GROUP BY r.task_category
ORDER BY attainment_pct ASC;
```

**Visualization:** Progress bars (100% = full SLA attainment) per category

---

### Query 3.3: Timeout/Failed Tasks by Category

**Purpose:** Track hard failures (non-zero exit code, timeout, escalated).

**Sample Output:**

```
category     | total_tasks | successful | timeout | error | escalated | error_rate_pct
-------------|------------|-----------|---------|-------|-----------|---------------
fast         | 4500       | 4461      | 15      | 20    | 4         | 0.9%
normal       | 1200       | 1166      | 18      | 12    | 4         | 2.5%
complex      | 320        | 308       | 7       | 5     | 0         | 3.8%
high_complex | 45         | 43        | 2       | 0     | 0         | 4.4%
```

**SQL Query:**

```sql
SELECT
  r.task_category as category,
  COUNT(*) as total_tasks,
  COUNT(CASE WHEN r.exit_code = 0 THEN 1 END) as successful,
  COUNT(CASE WHEN r.status = 'timeout' THEN 1 END) as timeout,
  COUNT(CASE WHEN r.exit_code != 0 AND r.status != 'timeout' THEN 1 END) as error,
  COUNT(CASE WHEN r.status = 'escalated' THEN 1 END) as escalated,
  ROUND(
    (COUNT(CASE WHEN r.exit_code != 0 OR r.status = 'timeout' OR r.status = 'escalated' THEN 1 END) / COUNT(*)) * 100, 1
  ) as error_rate_pct
FROM run_registry r
WHERE r.event = 'finish'
  AND DATE(r.ended_at_utc) >= DATE('now', '-7 days')
GROUP BY r.task_category
ORDER BY error_rate_pct DESC;
```

**Visualization:** Stacked bar chart (x-axis: category, y-axis: task count, stack: successful/timeout/error/escalated)

**Metrics Definition:**

- `error_rate_pct`: (timeout + error + escalated) / total \* 100

---

## Dashboard 4: Operational Dashboard

**Purpose:** Overall operational health and task flow metrics.

**Refresh Frequency:** Real-time counters (every minute), Daily aggregates

### Query 4.1: Total Tasks Processed

**Purpose:** Daily task volume by category and overall.

**Sample Output:**

```
date       | fast  | normal | complex | high_complex | total | avg_daily
-----------|-------|--------|---------|--------------|-------|----------
2025-02-14 | 450   | 120    | 32      | 4            | 606   | 580
2025-02-13 | 420   | 115    | 30      | 5            | 570   | 580
2025-02-12 | 480   | 130    | 36      | 6            | 652   | 580
```

**SQL Query:**

```sql
SELECT
  DATE(r.ended_at_utc) as date,
  COUNT(CASE WHEN r.task_category = 'fast' THEN 1 END) as fast,
  COUNT(CASE WHEN r.task_category = 'normal' THEN 1 END) as normal,
  COUNT(CASE WHEN r.task_category = 'complex' THEN 1 END) as complex,
  COUNT(CASE WHEN r.task_category = 'high_complex' THEN 1 END) as high_complex,
  COUNT(*) as total,
  ROUND(AVG(COUNT(*)) OVER (ORDER BY DATE(r.ended_at_utc) ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 0) as avg_daily
FROM run_registry r
WHERE r.event = 'finish'
  AND DATE(r.ended_at_utc) >= DATE('now', '-30 days')
GROUP BY DATE(r.ended_at_utc)
ORDER BY date DESC;
```

**Visualization:**

- Line chart (daily volume with 7-day moving average)
- Counter (today's total tasks)

---

### Query 4.2: Error Rate by Category

**Purpose:** Non-zero exit code rate by category.

**Sample Output:**

```
category     | total_tasks | error_count | error_rate_pct | status
-------------|------------|------------|--------------|--------
fast         | 4500       | 40         | 0.9%         | OK
normal       | 1200       | 30         | 2.5%         | WARNING
complex      | 320        | 12         | 3.8%         | WARNING
high_complex | 45         | 2          | 4.4%         | OK
```

**SQL Query:**

```sql
SELECT
  r.task_category as category,
  COUNT(*) as total_tasks,
  COUNT(CASE WHEN r.exit_code != 0 THEN 1 END) as error_count,
  ROUND((COUNT(CASE WHEN r.exit_code != 0 THEN 1 END) / COUNT(*)) * 100, 1) as error_rate_pct,
  CASE
    WHEN (COUNT(CASE WHEN r.exit_code != 0 THEN 1 END) / COUNT(*)) > 0.05 THEN 'WARNING'
    ELSE 'OK'
  END as status
FROM run_registry r
WHERE r.event = 'finish'
  AND DATE(r.ended_at_utc) >= DATE('now', '-7 days')
GROUP BY r.task_category
ORDER BY error_rate_pct DESC;
```

**Visualization:** Gauge charts (0-5% scale, red zone > 5%)

---

### Query 4.3: Most Common Constraint Violations

**Purpose:** Which constraints are violated most frequently.

**Sample Output:**

```
violation_type      | count | pct_of_total | trend
--------------------|-------|-------------|-------
instantaneous_cost  | 20    | 45.5%       | ↑ +3
performance         | 12    | 27.3%       | → 0
speed               | 10    | 22.7%       | ↓ -2
cumulative_cost     | 2     | 4.5%        | ↓ -1
```

**SQL Query:**

```sql
WITH violations AS (
  SELECT json_each.value as violation_type
  FROM run_registry r,
    json_each(json(r.constraint_violations))
  WHERE r.event = 'finish'
    AND r.constraint_violations IS NOT NULL
    AND DATE(r.ended_at_utc) >= DATE('now', '-7 days')
)
SELECT
  v.violation_type,
  COUNT(*) as count,
  ROUND((COUNT(*) / (SELECT COUNT(*) FROM violations)) * 100, 1) as pct_of_total
FROM violations v
GROUP BY v.violation_type
ORDER BY count DESC;
```

**Visualization:** Donut chart or horizontal bar chart

---

### Query 4.4: Escalation Queue

**Purpose:** Track escalations pending review.

**Sample Output:**

```
status      | count | min_age_hours | max_age_hours | avg_age_hours
------------|-------|---------------|---------------|---------------
pending     | 12    | 0.5           | 4.2           | 1.8
in_progress | 3     | 0.1           | 0.7           | 0.4
completed   | 45    | 0.2           | 12.5          | 2.1
```

**SQL Query:**

```sql
SELECT
  r.escalation_status as status,
  COUNT(*) as count,
  ROUND(MIN((JULIANDAY('now') - JULIANDAY(r.started_at_utc)) * 24), 1) as min_age_hours,
  ROUND(MAX((JULIANDAY('now') - JULIANDAY(r.started_at_utc)) * 24), 1) as max_age_hours,
  ROUND(AVG((JULIANDAY('now') - JULIANDAY(r.started_at_utc)) * 24), 1) as avg_age_hours
FROM run_registry r
WHERE r.event = 'escalate'
  AND DATE(r.started_at_utc) >= DATE('now', '-7 days')
GROUP BY r.escalation_status
ORDER BY CASE WHEN r.escalation_status = 'pending' THEN 0 WHEN r.escalation_status = 'in_progress' THEN 1 ELSE 2 END;
```

**Visualization:**

- Counter (pending escalations - alert if > 10)
- Timeline (escalation age distribution)

---

## Dashboard 5: Budget Projection

**Purpose:** Forecast month-end budget position.

**Refresh Frequency:** Daily (end of business day)

### Query 5.1: Monthly Forecast

**Purpose:** Project month-end spend and remaining budget.

**Sample Output:**

```
metric                    | value
--------------------------|----------
current_date              | 2025-02-14
days_in_month             | 28
days_elapsed              | 14
days_remaining            | 14
total_monthly_budget      | 450.00
mtd_cost_actual           | 111.00
mtd_cost_pct_of_budget    | 24.7%
daily_burn_rate           | 7.93
forecast_month_end_spend  | 223.60
projected_budget_remaining| 226.40
burn_out_risk             | LOW
```

**SQL Query:**

```sql
WITH dates AS (
  SELECT
    STRFTIME('%Y-%m', 'now') as current_month,
    CAST(STRFTIME('%d', 'now') AS INT) as day_of_month,
    28 as days_in_month  -- February 2025
),
mtd_costs AS (
  SELECT
    SUM(COALESCE(r.actual_cost_usd, 0)) as mtd_total
  FROM run_registry r
  WHERE r.event = 'finish'
    AND r.actual_cost_usd IS NOT NULL
    AND STRFTIME('%Y-%m', r.ended_at_utc) = STRFTIME('%Y-%m', 'now')
)
SELECT
  'current_date' as metric,
  DATE('now') as value
UNION ALL
SELECT 'days_in_month', 28
UNION ALL
SELECT 'days_elapsed', (SELECT day_of_month FROM dates)
UNION ALL
SELECT 'days_remaining', 28 - (SELECT day_of_month FROM dates)
UNION ALL
SELECT 'total_monthly_budget', 450.00
UNION ALL
SELECT 'mtd_cost_actual', (SELECT ROUND(mtd_total, 2) FROM mtd_costs)
UNION ALL
SELECT 'mtd_cost_pct_of_budget', (SELECT ROUND((mtd_total / 450.00) * 100, 1) FROM mtd_costs)
UNION ALL
SELECT 'daily_burn_rate', (SELECT ROUND(mtd_total / (SELECT day_of_month FROM dates), 2) FROM mtd_costs)
UNION ALL
SELECT 'forecast_month_end_spend', (SELECT ROUND((mtd_total / (SELECT day_of_month FROM dates)) * 28, 2) FROM mtd_costs)
UNION ALL
SELECT 'projected_budget_remaining', (SELECT ROUND(450.00 - ((mtd_total / (SELECT day_of_month FROM dates)) * 28), 2) FROM mtd_costs)
UNION ALL
SELECT 'burn_out_risk', CASE
  WHEN (SELECT mtd_total FROM mtd_costs) / (SELECT day_of_month FROM dates) * 28 >= 450 THEN 'CRITICAL'
  WHEN (SELECT mtd_total FROM mtd_costs) / (SELECT day_of_month FROM dates) * 28 >= 360 THEN 'HIGH'
  WHEN (SELECT mtd_total FROM mtd_costs) / (SELECT day_of_month FROM dates) * 28 >= 270 THEN 'MEDIUM'
  ELSE 'LOW'
END;
```

**Visualization:**

- Gauge chart (projected spend vs 450 budget)
- Counter (days remaining at current burn)
- Risk indicator (color-coded: LOW/MEDIUM/HIGH/CRITICAL)

---

### Query 5.2: Budget by Category Projection

**Purpose:** Forecast spend per category by month end.

**Sample Output:**

```
category     | budget | mtd_cost | pct_used | projected_eom | budget_remaining | status
-------------|--------|----------|----------|--------------|-----------------|--------
fast         | 50.00  | 12.50    | 25.0%    | 25.00        | 25.00            | OK
normal       | 200.00 | 45.30    | 22.7%    | 90.60        | 109.40           | OK
complex      | 150.00 | 38.20    | 25.5%    | 76.40        | 73.60            | OK
high_complex | 50.00  | 15.00    | 30.0%    | 30.00        | 20.00            | WARNING
```

**SQL Query:**

```sql
WITH category_budgets AS (
  SELECT 'fast' as category, 50.00 as budget
  UNION ALL
  SELECT 'normal', 200.00
  UNION ALL
  SELECT 'complex', 150.00
  UNION ALL
  SELECT 'high_complex', 50.00
),
mtd_by_category AS (
  SELECT
    r.task_category,
    SUM(COALESCE(r.actual_cost_usd, 0)) as mtd_cost,
    COUNT(*) as task_count,
    CAST(STRFTIME('%d', 'now') AS INT) as day_of_month
  FROM run_registry r
  WHERE r.event = 'finish'
    AND r.actual_cost_usd IS NOT NULL
    AND STRFTIME('%Y-%m', r.ended_at_utc) = STRFTIME('%Y-%m', 'now')
  GROUP BY r.task_category
)
SELECT
  cb.category,
  cb.budget,
  ROUND(COALESCE(mtd.mtd_cost, 0), 2) as mtd_cost,
  ROUND((COALESCE(mtd.mtd_cost, 0) / cb.budget) * 100, 1) as pct_used,
  ROUND((COALESCE(mtd.mtd_cost, 0) / mtd.day_of_month) * 28, 2) as projected_eom,
  ROUND(cb.budget - ((COALESCE(mtd.mtd_cost, 0) / mtd.day_of_month) * 28), 2) as budget_remaining,
  CASE
    WHEN ((COALESCE(mtd.mtd_cost, 0) / mtd.day_of_month) * 28) >= cb.budget THEN 'CRITICAL'
    WHEN ((COALESCE(mtd.mtd_cost, 0) / mtd.day_of_month) * 28) >= (cb.budget * 0.8) THEN 'WARNING'
    ELSE 'OK'
  END as status
FROM category_budgets cb
LEFT JOIN mtd_by_category mtd ON cb.category = mtd.task_category
ORDER BY budget_remaining DESC;
```

**Visualization:** Stacked bar chart (per category, actual vs remaining budget)

---

## Data Schema Requirements

### Required Fields in `run_registry.jsonl`

```json
{
  "event": "finish",
  "run_id": "unique-run-id",
  "task_category": "normal",
  "complexity_score": 45,
  "estimated_cost": 0.045,
  "actual_cost_usd": 0.038,
  "routing_reason": "Routed to minimax-m2.5 for normal task...",
  "selected_model": "minimax-m2.5",
  "status": "success",
  "exit_code": 0,
  "duration_s": 2.5,
  "started_at_utc": "2025-02-14T10:30:00Z",
  "ended_at_utc": "2025-02-14T10:32:30Z",
  "constraint_violations": ["instantaneous_cost"],
  "used_fallback_model": false,
  "escalation_status": null
}
```

### Recommended Database Indices

For SQLite/PostgreSQL:

```sql
-- Core indices for query performance
CREATE INDEX idx_run_registry_event ON run_registry(event);
CREATE INDEX idx_run_registry_category ON run_registry(task_category);
CREATE INDEX idx_run_registry_ended_date ON run_registry(DATE(ended_at_utc));
CREATE INDEX idx_run_registry_category_date ON run_registry(task_category, DATE(ended_at_utc));
CREATE INDEX idx_run_registry_model ON run_registry(selected_model);
CREATE INDEX idx_run_registry_status ON run_registry(status);

-- Composite indices for common query patterns
CREATE INDEX idx_run_registry_finish_cost ON run_registry(event, actual_cost_usd)
  WHERE event = 'finish' AND actual_cost_usd IS NOT NULL;
CREATE INDEX idx_run_registry_month ON run_registry(STRFTIME('%Y-%m', ended_at_utc));
```

---

## Storage and Retention

**Data Retention:** 90 days of detailed records, 1 year of daily aggregates

**JSONL Storage:**

- ~2MB per day with default volume (~500 tasks/day)
- 90 days = ~180MB raw logs

**Database Optimization:**

- Create materialized views for daily aggregates
- Partition by month for archival
- Archive older data to compressed storage

---

## Query Performance Notes

**Expected Query Execution Time:**

- Daily/category queries: 10-50ms (on indexed data)
- Percentile queries: 100-500ms (requires sorting)
- Trend/forecast queries: 50-200ms

**Optimization Tips:**

1. Index on `task_category` + `DATE(ended_at_utc)` for most queries
2. Use date range filters (WHERE DATE(...) >= DATE('now', '-30 days'))
3. Pre-aggregate hourly summaries for real-time dashboards
4. Cache computed metrics (burn rate, forecast) for 1 hour

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
