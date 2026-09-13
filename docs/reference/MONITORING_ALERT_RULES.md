# Monitoring Alert Rules

## Overview

Alert rules define when to trigger notifications and escalations. Each rule includes:

- Trigger condition (metric + threshold)
- Severity level (INFO, WARNING, CRITICAL)
- Action (notification channels, auto-response)
- Context (data to include in alert)
- Escalation path

**Total Rules:** 12 core rules + 3 anomaly detection rules

**Alert Channels:**

- Slack: `#thegent-alerts` (all severity)
- Email: Team lead (WARNING+), Manager (CRITICAL)
- PagerDuty: CRITICAL only
- Dashboard: Real-time update

---

## Cost Rules

### Rule 1: CATEGORY_BUDGET_WARNING

**Trigger Condition:**

```
category_budget_utilization >= 80%
AND category_budget_utilization < 100%
```

**Severity:** WARNING

**Applicable Categories:**

- FAST: When >= $40 of $50 budget used
- NORMAL: When >= $160 of $200 budget used
- COMPLEX: When >= $120 of $150 budget used
- HIGH_COMPLEX: When >= $40 of $50 budget used

**Action:**

1. Post to Slack `#thegent-alerts` with warning emoji
2. Include current spend, remaining budget, and projection
3. Tag team lead (@channel-owner)
4. Log to monitoring system with severity=WARNING

**Data Included in Alert:**

```
Alert: CATEGORY_BUDGET_WARNING (NORMAL)
├─ Category: normal
├─ Budget: $200.00
├─ MTD Spend: $160.00 (80.0%)
├─ Budget Remaining: $40.00
├─ Daily Burn Rate: $11.43
├─ Projected End-of-Month: $343 (172% of budget) ⚠
├─ Days to Exhaustion: 3.5 days
└─ Action: Review and optimize model selection for normal tasks
```

**Trigger Frequency:** Hourly (re-check every 60 minutes)

**Silence Duration:** 1 hour (don't re-alert if already warned)

**Escalation Path:** If still at 80%+ after 4 hours → escalate to CRITICAL

**Manual Override:**

- Team lead can manually increase budget via config update
- Requires approval and note in audit log

---

### Rule 2: CATEGORY_BUDGET_CRITICAL

**Trigger Condition:**

```
category_budget_utilization >= 100%
```

**Severity:** CRITICAL

**Applicable Categories:** All (FAST, NORMAL, COMPLEX, HIGH_COMPLEX)

**Action:**

1. Post to Slack with critical emoji and thread
2. Page on-call manager via PagerDuty
3. Send email to manager + team lead with context
4. Auto-block new tasks in affected category (optional implementation)
5. Log to error tracking system

**Data Included in Alert:**

```
! CRITICAL: CATEGORY_BUDGET_CRITICAL (COMPLEX)
├─ Category: complex
├─ Budget: $150.00 EXCEEDED ✗
├─ MTD Spend: $152.34 (101.6%)
├─ Overage: $2.34 (1.6%)
├─ Daily Burn Rate: $10.88
├─ Last 24h Spend: $10.88
├─ Projected Monthly Total: $326.40 (217% of budget) ⚠⚠⚠
├─ Status: BUDGET EXHAUSTED - NEW TASKS BLOCKED
├─ Task Backlog Pending: 5 tasks waiting
└─ Required Action: Immediate budget review and approval
```

**Action on Triggered:**

1. Page on-call (within 5 minutes)
2. Log critical event to audit trail
3. Block new tasks in category (set `routing_blocked = true`)
4. Require manager approval to unblock
5. Generate spend breakdown report

**Recovery:**

- Manager approves budget increase OR
- Wait for next calendar month (reset)

**Trigger Frequency:** Immediate (within 1 minute of threshold breach)

**Silence Duration:** No silence - each new overage triggers new alert

---

## Performance Rules

### Rule 3: QUALITY_REGRESSION

**Trigger Condition:**

```
avg_quality_by_category < (baseline[category] - 0.05)
```

**Severity:** WARNING

**Trigger Examples:**

- FAST: avg_quality < 0.55 (baseline 0.60 - 5%)
- NORMAL: avg_quality < 0.65 (baseline 0.70 - 5%)
- COMPLEX: avg_quality < 0.70 (baseline 0.75 - 5%)
- HIGH_COMPLEX: avg_quality < 0.75 (baseline 0.80 - 5%)

**Baseline:** 7-day rolling average

**Action:**

1. Post to Slack with warning: quality regression detected
2. Alert ML/model team
3. Include model breakdown by category
4. Recommend: Review model selection policy or fallback to higher-quality model

**Data Included in Alert:**

```
⚠ WARNING: QUALITY_REGRESSION (COMPLEX)
├─ Category: complex
├─ Current Avg Quality: 0.70 (7d rolling)
├─ Baseline: 0.75
├─ Regression: -5.0%
├─ Tasks Affected: 287 (past 7 days)
├─ Model Breakdown:
│  ├─ minimax-m2.5: 87% (avg quality 0.68)
│  └─ claude-sonnet-4.5: 13% (avg quality 0.78)
├─ Estimated Impact: -0.01 cost savings, -5% quality hit
└─ Recommended Action: Increase claude-sonnet-4.5 usage for complex tasks
```

**Trigger Frequency:** Hourly (measured against 7d rolling average)

**Silence Duration:** 4 hours (don't re-alert same category)

---

### Rule 4: MODEL_SELECTION_ANOMALY

**Trigger Condition:**

```
ABS(model_selection_distribution[model] - expected[model]) > 10%
```

**Severity:** INFO (escalate to WARNING if > 20%)

**Example Trigger:**

- FAST expected: 99.5% minimax, actual: 85% minimax (14.5% deviation)
- COMPLEX expected: 85% minimax, actual: 60% minimax (25% deviation) → WARNING

**Action:**

1. Post to Slack `#thegent-routing` (not critical channel)
2. Include comparison table of expected vs actual
3. Investigate: constraint violations, fallback trigger rate

**Data Included in Alert:**

```
ℹ INFO: MODEL_SELECTION_ANOMALY (COMPLEX)
├─ Category: complex
├─ Model Deviation Analysis (7d):
│  ├─ minimax-m2.5:
│  │  ├─ Expected: 85%
│  │  ├─ Actual: 60%
│  │  ├─ Deviation: -25% ⚠
│  │  └─ Reason: 15% constraint violations (instantaneous_cost)
│  └─ claude-sonnet-4.5:
│     ├─ Expected: 15% (fallback)
│     ├─ Actual: 40%
│     └─ Deviation: +25% ⚠
├─ Tasks Routed: 287
└─ Recommendation: Review cost constraints - primary model failing cost checks
```

**Trigger Frequency:** Daily (compare 7d distribution)

**Silence Duration:** 12 hours (model selection changes gradually)

---

## SLA Rules

### Rule 5: SLA_MISS_THRESHOLD

**Trigger Condition:**

```
sla_attainment_pct < 95%
```

**Severity:** WARNING

**Trigger Examples:**

- FAST: <95% of tasks finish within 1000ms
- NORMAL: <95% of tasks finish within 5000ms
- COMPLEX: <95% of tasks finish within 20000ms
- HIGH_COMPLEX: <95% of tasks finish within 60000ms

**Measurement Window:** Past 7 days

**Action:**

1. Post to Slack with warning
2. Include p50 and p99 latency metrics
3. Alert infrastructure/performance team
4. Recommend: Investigate model performance, retry logic, or system load

**Data Included in Alert:**

```
⚠ WARNING: SLA_MISS_THRESHOLD (NORMAL)
├─ Category: normal
├─ SLA Target: 5000ms
├─ SLA Attainment: 92.5% (target: ≥95%)
├─ Misses: 90 of 1200 tasks
├─ Latency Metrics (7d):
│  ├─ p50: 2800ms (56% of SLA)
│  ├─ p99: 4800ms (96% of SLA) ← near limit
│  └─ max: 7200ms (144% of SLA) ✗
├─ Trend: ↑ degrading (was 97% yesterday)
├─ Suspected Cause: Model latency or system load
└─ Action: Check model performance and system metrics
```

**Trigger Frequency:** Hourly

**Silence Duration:** 2 hours (allow time to investigate)

---

## Operational Rules

### Rule 6: CONSTRAINT_VIOLATION_SPIKE

**Trigger Condition:**

```
constraint_violation_rate[category] > (baseline + 3%)
```

**Severity:** WARNING

**Baseline:** 7-day average (typically 2-3%)

**Example Triggers:**

- NORMAL: violation_rate > 5% (baseline 2%)
- COMPLEX: violation_rate > 6% (baseline 3%)

**Action:**

1. Post to Slack with details on violation type
2. Break down by violation type (performance, cost, speed)
3. Alert routing team to investigate constraint settings

**Data Included in Alert:**

```
⚠ WARNING: CONSTRAINT_VIOLATION_SPIKE (NORMAL)
├─ Category: normal
├─ Violation Rate: 4.8% (7d baseline: 1.5%)
├─ Spike: +3.3% above baseline
├─ Violations (24h):
│  ├─ instantaneous_cost: 32 tasks (67%)
│  ├─ performance: 12 tasks (25%)
│  └─ speed: 4 tasks (8%)
├─ Impact:
│  ├─ Fallback Rate: 4.8% (vs 1.5% normal)
│  └─ Cost Impact: +$0.48 in fallback overhead
├─ Most Recent: instantaneous_cost violation on task XYZ
└─ Recommendation: Review instantaneous cost budget ($0.05) - may be too tight
```

**Trigger Frequency:** Hourly

**Silence Duration:** 2 hours

---

### Rule 7: ESCALATION_QUEUE_AGING

**Trigger Condition:**

```
escalation_queue_depth > 10
OR
MAX(escalation_age_hours) > 4
```

**Severity:** WARNING

**Action:**

1. Post to Slack with escalation queue status
2. Tag review team to process pending escalations
3. Include task IDs and escalation reasons

**Data Included in Alert:**

```
⚠ WARNING: ESCALATION_QUEUE_AGING
├─ Pending Escalations: 12 (threshold: 10)
├─ Queue Age:
│  ├─ Oldest: 5.2 hours (exceeds 4h limit)
│  ├─ Average: 2.1 hours
│  └─ Newest: 0.1 hours
├─ Escalation Breakdown:
│  ├─ constraint_violation: 7 tasks
│  ├─ manual_review: 4 tasks
│  └─ fallback_decision: 1 task
├─ Assigned Reviewers:
│  ├─ alice@company.com: 3 items (in progress)
│  └─ bob@company.com: 2 items (idle)
├─ Unassigned: 7 items (waiting)
└─ Action: Assign unassigned items and process queue
```

**Trigger Frequency:** Real-time (check every 5 minutes)

**Silence Duration:** 1 hour (give reviewers time to process)

---

### Rule 8: ERROR_RATE_SPIKE

**Trigger Condition:**

```
error_rate_pct[category] > (baseline + 2%)
```

**Severity:** WARNING

**Baseline:** 7-day average (typically 1-2%)

**Example Triggers:**

- FAST: error_rate > 3.5% (baseline 1.5%)
- NORMAL: error_rate > 4.5% (baseline 2.5%)

**Action:**

1. Post to Slack with error distribution
2. Include log excerpts or error types
3. Alert engineering team to investigate

**Data Included in Alert:**

```
⚠ WARNING: ERROR_RATE_SPIKE (COMPLEX)
├─ Category: complex
├─ Error Rate: 6.2% (7d baseline: 3.8%)
├─ Spike: +2.4% above baseline
├─ Errors (24h): 18 of 290 tasks
├─ Error Types:
│  ├─ timeout: 10 tasks (55%)
│  ├─ exit_code!=0: 6 tasks (33%)
│  └─ escalated: 2 tasks (12%)
├─ Sample Error: "model inference timeout after 25s"
├─ Correlation: High error rate correlates with model="claude-sonnet-4.5"
└─ Action: Check model availability and system resources
```

**Trigger Frequency:** Hourly

**Silence Duration:** 2 hours

---

## Anomaly Detection Rules

### Rule 9: COST_ANOMALY_DETECTION

**Trigger Condition:**

```
daily_cost > (7d_avg_daily_cost * 1.5)
```

**Severity:** INFO (escalate to WARNING if > 2x)

**Example:**

- Average daily cost: $7.50
- Today's cost: $12.00 (1.6x) → INFO
- Today's cost: $15.00 (2x) → WARNING

**Action:**

1. Post informational message to Slack
2. Include comparison to historical average
3. List top-spending categories/models

**Data Included in Alert:**

```
ℹ INFO: COST_ANOMALY_DETECTION
├─ Today's Cost: $14.20
├─ 7d Average: $8.90
├─ Deviation: +59.5% (threshold: +50%)
├─ Contributing Factors:
│  ├─ high_complex tasks: +$8.50 (100% above normal)
│  ├─ complex tasks: +$2.10 (+25%)
│  └─ model="claude-opus-4.6": +$7.80 (unusual concentration)
├─ Task Volume:
│  ├─ high_complex: 8 tasks (vs 5d average of 3)
│  └─ Reason: Feature development sprint (planned)
└─ Status: Anomaly detected but likely benign (sprint-related)
```

**Trigger Frequency:** Daily (once per day at EOD)

**Silence Duration:** None (informational only)

---

### Rule 10: QUALITY_VARIANCE_ANOMALY

**Trigger Condition:**

```
STDDEV(quality_scores) > (baseline_stddev * 1.5)
```

**Severity:** INFO

**Action:**

1. Post to Slack `#thegent-routing`
2. Show quality distribution across models
3. Recommend: Investigate model consistency

**Data Included in Alert:**

```
ℹ INFO: QUALITY_VARIANCE_ANOMALY (NORMAL)
├─ Category: normal
├─ Quality Variance: High
├─ Standard Deviation: 0.18 (baseline: 0.12)
├─ Quality Distribution:
│  ├─ 0.60-0.70: 12% of tasks (outliers)
│  ├─ 0.70-0.80: 65% of tasks
│  └─ 0.80-1.00: 23% of tasks (high performers)
├─ Contributing Models:
│  ├─ minimax-m2.5: STDDEV=0.15 (consistent)
│  └─ gpt-4o-mini: STDDEV=0.22 (variable)
└─ Recommendation: Investigate gpt-4o-mini performance variance
```

**Trigger Frequency:** Daily

---

### Rule 11: LATENCY_DEGRADATION

**Trigger Condition:**

```
p50_latency_today > (p50_latency_7d_avg * 1.3)
OR
p99_latency_today > (p99_latency_7d_avg * 1.2)
```

**Severity:** WARNING

**Action:**

1. Post to Slack with latency comparison
2. Alert infrastructure team
3. Check system load and model availability

**Data Included in Alert:**

```
⚠ WARNING: LATENCY_DEGRADATION (COMPLEX)
├─ Category: complex
├─ P50 Latency:
│  ├─ Today: 15.8s
│  ├─ 7d Average: 12.0s
│  ├─ Degradation: +31.7% (threshold: +30%)
│  └─ Status: ABOVE THRESHOLD ⚠
├─ P99 Latency:
│  ├─ Today: 21.2s
│  ├─ 7d Average: 18.5s
│  ├─ Degradation: +14.6% (threshold: +20%)
│  └─ Status: OK
├─ Contributing Factors:
│  ├─ System Load: 75% (normal 50%)
│  ├─ Model Queue: High (waiting tasks)
│  └─ Network: Healthy
└─ Recommended Action: Check model availability, increase capacity or reduce load
```

**Trigger Frequency:** Daily (measured end-of-day)

**Silence Duration:** 4 hours

---

## Action Matrix

### By Severity Level

**INFO** (Informational)

- Post to `#thegent-alerts` Slack channel
- Log to dashboard
- No notification/paging
- Example: Cost anomaly, model variance

**WARNING**

- Post to `#thegent-alerts` with @channel mention
- Notify team lead via email
- Log to dashboard with visual indicator
- Set snooze/silence to prevent spam
- Example: Budget at 80%, SLA miss, error spike

**CRITICAL**

- Post to `#thegent-alerts` with @channel and thread
- Page on-call engineer via PagerDuty
- Email manager + team lead
- Log to error tracking system
- Auto-remediation (if applicable): block new tasks
- Example: Budget exhausted, system down

---

## Escalation Paths

### Budget Crisis (CRITICAL)

```
CRITICAL: Budget Exhausted
  ├─ (Immediate) Page on-call
  ├─ (5 min) If not acknowledged: page manager
  ├─ (15 min) If still no response: send email to director
  ├─ (Parallel) Auto-block new tasks in category
  └─ (Parallel) Generate spend report + recommendations
```

### SLA Degradation (WARNING → CRITICAL)

```
WARNING: SLA miss 94% (1 hour)
  ├─ Post alert
  └─ Monitor for 1 hour

If still <95% after 1 hour:
  CRITICAL: SLA Degradation
  ├─ Page on-call
  ├─ Investigate model/system issues
  └─ Consider fallback or capacity increase
```

### Constraint Violations (INFO → WARNING)

```
INFO: Violation rate 2.5% (monitor)
  ├─ Update routing policy to tighten/loosen constraints
  └─ Measure effect over 24 hours

If violations remain > baseline after 24h:
  WARNING: Sustained constraint violations
  ├─ Post alert
  └─ Review constraint thresholds with team
```

---

## Custom Alert Configuration

### Per-Category Budget Thresholds

```yaml
alerts:
  budget_warning:
    fast:
      threshold_pct: 80
      threshold_usd: 40.00
      silence_minutes: 60
    normal:
      threshold_pct: 80
      threshold_usd: 160.00
      silence_minutes: 60
    complex:
      threshold_pct: 80
      threshold_usd: 120.00
      silence_minutes: 60
    high_complex:
      threshold_pct: 80
      threshold_usd: 40.00
      silence_minutes: 60

  budget_critical:
    fast:
      threshold_pct: 100
      threshold_usd: 50.00
    normal:
      threshold_pct: 100
      threshold_usd: 200.00
    complex:
      threshold_pct: 100
      threshold_usd: 150.00
    high_complex:
      threshold_pct: 100
      threshold_usd: 50.00
```

### Notification Channels

```yaml
channels:
  slack:
    warnings:
      channel: "#thegent-alerts"
      mention: "channel"
    critical:
      channel: "#thegent-alerts"
      mention: "channel"
      thread: true

  email:
    warnings:
      to:
        - "team-lead@company.com"
      cc: []
    critical:
      to:
        - "manager@company.com"
        - "team-lead@company.com"
      cc:
        - "director@company.com"

  pagerduty:
    critical:
      service: "thegent-routing"
      severity: "critical"
```

---

## Alert Silence/Snooping

**Default Silence Periods:**

- Budget warning: 60 minutes (don't spam)
- Quality warning: 4 hours (allow time to investigate)
- SLA warning: 2 hours (allow recovery)
- Escalation queue: 1 hour (give time to process)
- Error spike: 2 hours (allow debugging)

**Manual Silence:**

- Team lead can manually silence an alert for up to 8 hours
- Requires reason/comment in audit log
- Auto-unsuppress if condition persists

**Auto-Clear:**

- Alert automatically clears 1 hour after condition resolves
- Notification sent: "Alert resolved: budget_warning[normal] - now at 78%"

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
