# Monitoring Setup Guide

## Overview

This guide walks through setting up comprehensive monitoring for the thegent routing system. The setup includes:

1. Data collection (logging to run_registry.jsonl)
2. Query infrastructure (SQL database + queries)
3. Dashboard platform (Grafana, Datadog, or custom)
4. Alert rules configuration
5. Notification channels
6. Validation and testing

**Estimated Setup Time:** 2-4 hours (depending on existing infrastructure)

**Required Skills:** SQL, dashboard platform (Grafana or similar), monitoring basics

**Prerequisites:**

- Running thegent application with logging enabled
- SQLite, PostgreSQL, or MySQL database access
- Slack workspace (for alerts)
- Optional: Grafana, Datadog, or custom dashboard platform

---

## Phase 1: Data Collection Setup

### Step 1.1: Verify Run Registry Logging

**Objective:** Ensure run_registry.jsonl is being populated with required fields.

**Check for existing run_registry.jsonl:**

```bash
# Find the session directory
ls -la ~/.thegent/session/run_registry.jsonl
# or
ls -la /path/to/project/run_registry.jsonl
```

**Verify fields are present:**

```bash
# Check the structure of a recent run event
tail -1 ~/.thegent/session/run_registry.jsonl | jq .
```

**Expected output:**

```json
{
  "event": "finish",
  "run_id": "run-abc123",
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
  "used_fallback_model": false
}
```

**If fields are missing:**

Update your RunMeta logging in the execution layer. Add these fields to the "finish" event:

```python
# In execution.py or similar
from thegent.routing.task_router import TaskRouter

# After task execution:
run_meta.task_category = metadata.category  # from TaskRouter.route_task()
run_meta.complexity_score = metadata.complexity_score
run_meta.estimated_cost = metadata.estimated_cost
run_meta.routing_reason = metadata.routing_reason
run_meta.selected_model = metadata.selected_model
run_meta.actual_cost_usd = cost_aggregator.estimate_cost(...)  # actual cost
```

**File Location:** `/src/thegent/execution.py`

---

### Step 1.2: Enable Cost Tracking

**Objective:** Populate actual_cost_usd field for all runs.

**Current Implementation:** Check `src/thegent/governance/cost.py`

**Verify cost aggregator is initialized:**

```python
# In execution context
from thegent.governance.cost import CostAggregator, CostEstimator

cost_estimator = CostEstimator()
cost_aggregator = CostAggregator(session_dir=Path.cwd())

# On task completion:
actual_cost = cost_estimator.estimate(model=selected_model, tokens_in=input_token_count, tokens_out=output_token_count)
```

**Add to RunMeta finish event:**

```python
run_meta.actual_cost_usd = actual_cost
run_meta.ended_at_utc = datetime.now(UTC).isoformat()
```

**Validation Checklist:**

- [ ] All "finish" events have `actual_cost_usd` field
- [ ] Cost values are > 0 and reasonable (0.001 - 2.0 for typical tasks)
- [ ] Timestamp fields are in ISO 8601 UTC format

---

## Phase 2: Database Setup

### Step 2.1: Create Database Schema

**Objective:** Set up SQL database to store run data for querying.

**Option A: SQLite (Recommended for Small/Medium Scale)**

Create a schema file at `monitoring/schema.sqlite.sql`:

```sql
-- Create runs table from run_registry.jsonl data
CREATE TABLE IF NOT EXISTS run_registry (
    run_id TEXT PRIMARY KEY,
    event TEXT NOT NULL,
    task_category TEXT,
    complexity_score INTEGER,
    estimated_cost REAL,
    actual_cost_usd REAL,
    routing_reason TEXT,
    selected_model TEXT,
    status TEXT,
    exit_code INTEGER,
    duration_s REAL,
    started_at_utc TEXT,
    ended_at_utc TEXT,
    constraint_violations TEXT,  -- JSON array as text
    used_fallback_model BOOLEAN,
    escalation_status TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for query performance
CREATE INDEX IF NOT EXISTS idx_run_registry_event ON run_registry(event);
CREATE INDEX IF NOT EXISTS idx_run_registry_category ON run_registry(task_category);
CREATE INDEX IF NOT EXISTS idx_run_registry_ended_date ON run_registry(DATE(ended_at_utc));
CREATE INDEX IF NOT EXISTS idx_run_registry_category_date ON run_registry(task_category, DATE(ended_at_utc));
CREATE INDEX IF NOT EXISTS idx_run_registry_model ON run_registry(selected_model);
CREATE INDEX IF NOT EXISTS idx_run_registry_status ON run_registry(status);
CREATE INDEX IF NOT EXISTS idx_run_registry_finish_cost ON run_registry(event, actual_cost_usd)
    WHERE event = 'finish' AND actual_cost_usd IS NOT NULL;

-- Create daily aggregates table for faster queries
CREATE TABLE IF NOT EXISTS daily_metrics (
    date TEXT PRIMARY KEY,
    fast_cost REAL,
    normal_cost REAL,
    complex_cost REAL,
    high_complex_cost REAL,
    fast_tasks INTEGER,
    normal_tasks INTEGER,
    complex_tasks INTEGER,
    high_complex_tasks INTEGER,
    total_tasks INTEGER,
    error_count INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date);
```

**Initialize database:**

```bash
# Copy schema to project
cp monitoring/schema.sqlite.sql ./

# Create database
sqlite3 monitoring.db < schema.sqlite.sql

# Verify tables created
sqlite3 monitoring.db ".tables"
# Output: daily_metrics run_registry
```

**Option B: PostgreSQL (Recommended for Large Scale)**

```sql
-- Create runs table
CREATE TABLE IF NOT EXISTS run_registry (
    run_id TEXT PRIMARY KEY,
    event TEXT NOT NULL,
    task_category TEXT,
    complexity_score INTEGER,
    estimated_cost NUMERIC(10,6),
    actual_cost_usd NUMERIC(10,6),
    routing_reason TEXT,
    selected_model TEXT,
    status TEXT,
    exit_code INTEGER,
    duration_s NUMERIC(10,3),
    started_at_utc TIMESTAMP WITH TIME ZONE,
    ended_at_utc TIMESTAMP WITH TIME ZONE,
    constraint_violations JSONB,
    used_fallback_model BOOLEAN,
    escalation_status TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indices
CREATE INDEX idx_run_registry_event ON run_registry(event);
CREATE INDEX idx_run_registry_category ON run_registry(task_category);
CREATE INDEX idx_run_registry_category_date ON run_registry(task_category, DATE(ended_at_utc));
CREATE INDEX idx_run_registry_status ON run_registry(status);

-- Partitioning by month (optional, for large-scale)
CREATE TABLE IF NOT EXISTS run_registry_2025_02 PARTITION OF run_registry
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
```

---

### Step 2.2: Load Data from JSONL

**Objective:** Import run_registry.jsonl into database for querying.

**Python Script:** `monitoring/load_jsonl.py`

```python
#!/usr/bin/env python3
"""Load run_registry.jsonl into SQLite/PostgreSQL."""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
import sys


def load_jsonl_to_sqlite(jsonl_path: str, db_path: str = "monitoring.db"):
    """Load JSONL run registry into SQLite."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    loaded = 0
    errors = 0

    with open(jsonl_path, "r") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue

            try:
                data = json.loads(line)

                # Only load "finish" events for now
                if data.get("event") != "finish":
                    continue

                # Extract fields
                run_id = data.get("run_id")
                if not run_id:
                    raise ValueError("Missing run_id")

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO run_registry (
                        run_id, event, task_category, complexity_score,
                        estimated_cost, actual_cost_usd, routing_reason,
                        selected_model, status, exit_code, duration_s,
                        started_at_utc, ended_at_utc, constraint_violations,
                        used_fallback_model, escalation_status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        run_id,
                        data.get("event"),
                        data.get("task_category"),
                        data.get("complexity_score"),
                        data.get("estimated_cost"),
                        data.get("actual_cost_usd"),
                        data.get("routing_reason"),
                        data.get("selected_model"),
                        data.get("status"),
                        data.get("exit_code"),
                        data.get("duration_s"),
                        data.get("started_at_utc"),
                        data.get("ended_at_utc"),
                        json.dumps(data.get("constraint_violations", [])),
                        data.get("used_fallback_model", False),
                        data.get("escalation_status"),
                        datetime.utcnow().isoformat(),
                    ),
                )

                loaded += 1

                if loaded % 100 == 0:
                    print(f"Loaded {loaded} records...", file=sys.stderr)

            except Exception as e:
                errors += 1
                print(f"Error on line {line_num}: {e}", file=sys.stderr)
                if errors > 100:
                    print("Too many errors, aborting", file=sys.stderr)
                    break

    conn.commit()
    conn.close()

    print(f"Loaded {loaded} records, {errors} errors")
    return loaded, errors


if __name__ == "__main__":
    jsonl_path = sys.argv[1] if len(sys.argv) > 1 else "run_registry.jsonl"
    db_path = sys.argv[2] if len(sys.argv) > 2 else "monitoring.db"

    load_jsonl_to_sqlite(jsonl_path, db_path)
```

**Run the loader:**

```bash
# Make executable
chmod +x monitoring/load_jsonl.py

# Load data
python monitoring/load_jsonl.py ~/.thegent/session/run_registry.jsonl monitoring.db

# Verify load
sqlite3 monitoring.db "SELECT COUNT(*) as total_runs FROM run_registry;"
# Output: 1523
```

**Set up incremental sync (optional):**

Create a cron job to sync new records every hour:

```bash
# monitoring/sync_jsonl.sh
#!/bin/bash
JSONL_PATH="${1:-run_registry.jsonl}"
DB_PATH="${2:-monitoring.db}"
LAST_SYNC_FILE=".last_jsonl_sync"

# Find runs newer than last sync
if [ -f "$LAST_SYNC_FILE" ]; then
    LAST_SYNC=$(cat "$LAST_SYNC_FILE")
else
    LAST_SYNC="1970-01-01"
fi

# Run incremental load
python monitoring/load_jsonl.py "$JSONL_PATH" "$DB_PATH"

# Update sync timestamp
date -u +"%Y-%m-%d %H:%M:%S" > "$LAST_SYNC_FILE"
```

Add to crontab:

```bash
# Every hour at :00
0 * * * * /path/to/monitoring/sync_jsonl.sh /path/to/run_registry.jsonl /path/to/monitoring.db
```

---

## Phase 3: Query Validation

### Step 3.1: Test Core Queries

**Objective:** Verify SQL queries execute correctly against loaded data.

**Test Script:** `monitoring/test_queries.sql`

```sql
-- Test 1: Daily cost by category
SELECT
  DATE(ended_at_utc) as date,
  ROUND(COALESCE(SUM(CASE WHEN task_category = 'fast' THEN actual_cost_usd ELSE 0 END), 0), 2) as fast,
  ROUND(COALESCE(SUM(CASE WHEN task_category = 'normal' THEN actual_cost_usd ELSE 0 END), 0), 2) as normal,
  COUNT(*) as total
FROM run_registry
WHERE event = 'finish' AND actual_cost_usd IS NOT NULL
GROUP BY DATE(ended_at_utc)
ORDER BY date DESC
LIMIT 5;

-- Test 2: Budget utilization
SELECT
  task_category as category,
  ROUND(SUM(actual_cost_usd), 2) as mtd_cost,
  CASE
    WHEN task_category = 'fast' THEN 50.00
    WHEN task_category = 'normal' THEN 200.00
    WHEN task_category = 'complex' THEN 150.00
    WHEN task_category = 'high_complex' THEN 50.00
  END as budget
FROM run_registry
WHERE event = 'finish' AND actual_cost_usd IS NOT NULL
GROUP BY task_category;

-- Test 3: Task volume
SELECT
  COUNT(*) as total_tasks,
  COUNT(CASE WHEN task_category = 'fast' THEN 1 END) as fast,
  COUNT(CASE WHEN task_category = 'normal' THEN 1 END) as normal
FROM run_registry
WHERE event = 'finish';

-- Test 4: Error rate
SELECT
  task_category,
  COUNT(*) as total,
  COUNT(CASE WHEN exit_code != 0 THEN 1 END) as errors,
  ROUND((COUNT(CASE WHEN exit_code != 0 THEN 1 END) / COUNT(*)) * 100, 1) as error_rate_pct
FROM run_registry
WHERE event = 'finish'
GROUP BY task_category;
```

**Run tests:**

```bash
# SQLite
sqlite3 monitoring.db < monitoring/test_queries.sql

# PostgreSQL
psql -h localhost -U monitoring -d thegent < monitoring/test_queries.sql
```

**Expected Output:**

```
date       | fast | normal | total
-----------|------|--------|-------
2025-02-14 | 12.5 | 45.3   | 606

category     | mtd_cost | budget
-------------|----------|--------
fast         | 40.0     | 50.0
normal       | 180.0    | 200.0
```

---

### Step 3.2: Query Performance Baseline

**Objective:** Measure query execution times and identify optimization needs.

**Test with timing:**

```bash
# SQLite with timing
sqlite3 monitoring.db
sqlite> .timer ON
sqlite> SELECT COUNT(*) FROM run_registry;
Run Time: real 0.001, user 0.001, sys 0.000

sqlite> SELECT DATE(ended_at_utc), COUNT(*) FROM run_registry GROUP BY DATE(ended_at_utc);
Run Time: real 0.045, user 0.043, sys 0.002
```

**Expected Performance:**

- Simple count: < 10ms
- Grouped queries: 50-200ms (depends on data volume)
- Percentile queries: 100-500ms
- Multi-category aggregates: 50-150ms

**If queries are slow:**

1. Add missing indices (see schema above)
2. Partition data by month (PostgreSQL)
3. Migrate to materialized views for common aggregates

---

## Phase 4: Dashboard Setup

### Step 4.1: Grafana Setup (Recommended)

**Objective:** Create dashboards using Grafana.

**Prerequisites:**

- Grafana running (docker, local install, or SaaS)
- Database connection configured

**Step 1: Add Data Source**

1. Log in to Grafana (http://localhost:3000)
2. Go to: Configuration → Data Sources → Add data source
3. Select: SQLite (for SQLite) or PostgreSQL
4. Configure:
   - **Name:** thegent-monitoring
   - **URL:** `/path/to/monitoring.db` (SQLite) or database connection
   - **Database:** monitoring (PostgreSQL)
   - Click "Save & test"

**Step 2: Create Dashboard**

1. Go to: Dashboards → Create → New Dashboard
2. Add panels:

**Panel 1: Cost Dashboard**

- Query: SQL query from 1.1 (Daily Cost by Category)
- Visualization: Bar Chart or Stacked Bars
- Title: "Daily Cost by Category"
- Y-axis: USD

**Panel 2: Budget Utilization**

- Query: SQL query from 1.2 (Budget Utilization)
- Visualization: Gauge
- Thresholds: 80% (orange), 100% (red)
- Title: "Budget Utilization %"

**Panel 3: Task Volume**

- Query: SQL query from 4.1 (Task Volume)
- Visualization: Time Series
- Title: "Tasks Processed (7d)"

**Panel 4: Error Rate**

- Query: SQL query from 4.2 (Error Rate)
- Visualization: Gauge or Stat
- Title: "Error Rate %"

**Step 3: Configure Variables**

Add dashboard variables for dynamic filtering:

```
Variable: category
├─ Type: Query
├─ Data source: thegent-monitoring
├─ Query: SELECT DISTINCT task_category FROM run_registry WHERE task_category IS NOT NULL ORDER BY task_category
└─ Multi: Yes

Variable: date_range
├─ Type: Date range
├─ Default: Last 7 days
└─ Include: Today, past week
```

Update queries to use variables:

```sql
SELECT ... WHERE DATE(ended_at_utc) >= DATE('now', '-7 days')
  AND (task_category = '${category}' OR '${category}' = 'all')
```

**Step 4: Set Refresh Rate**

- Dashboard default: 1 minute
- Cost queries: 1 hour
- Task volume: 5 minutes
- Error rates: 5 minutes

**Step 5: Add Alerts**

See Phase 5 for alert configuration.

---

### Step 4.2: Alternative: Datadog Setup

**Objective:** Use Datadog for dashboard + alert management.

**Step 1: Connect Database**

1. Log in to Datadog
2. Integrations → Add Database
3. Configure SQL integration:
   - Host: localhost (or Datadog agent)
   - Port: 3306 (MySQL) or 5432 (PostgreSQL)
   - Database: monitoring
   - Username: monitoring
   - Password: \*\*\*\*

**Step 2: Create Custom Metrics**

Via Datadog API or UI, define metrics:

```
routing.cost.daily
├─ Unit: dollar
├─ Type: gauge
└─ Tags: category, date

routing.task.volume
├─ Unit: count
└─ Type: gauge

routing.sla.attainment
├─ Unit: percent
└─ Type: gauge
```

**Step 3: Create Dashboard**

1. Dashboards → Create → New Dashboard
2. Add widgets for each metric
3. Configure time range, refresh rate
4. Add correlations (e.g., cost spike vs. model change)

---

### Step 4.3: Custom Dashboard (Python + Flask/FastAPI)

**Objective:** Build lightweight custom dashboard if external platforms unavailable.

**Minimal example:** `monitoring/dashboard.py`

```python
from flask import Flask, render_template, jsonify
import sqlite3
import json

app = Flask(__name__)
DB_PATH = "monitoring.db"


def query_db(sql):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql)
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


@app.route("/api/daily-costs")
def daily_costs():
    sql = """
    SELECT DATE(ended_at_utc) as date,
      ROUND(SUM(CASE WHEN task_category='fast' THEN actual_cost_usd ELSE 0 END),2) as fast,
      ROUND(SUM(CASE WHEN task_category='normal' THEN actual_cost_usd ELSE 0 END),2) as normal
    FROM run_registry WHERE event='finish'
    GROUP BY DATE(ended_at_utc) ORDER BY date DESC LIMIT 30
    """
    return jsonify(query_db(sql))


@app.route("/api/budget-status")
def budget_status():
    sql = """
    SELECT task_category,
      ROUND(SUM(actual_cost_usd),2) as spent,
      CASE WHEN task_category='fast' THEN 50 ... END as budget
    FROM run_registry WHERE event='finish'
    GROUP BY task_category
    """
    return jsonify(query_db(sql))


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

---

## Phase 5: Alert Configuration

### Step 5.1: Slack Integration

**Objective:** Configure Slack notifications for alerts.

**Step 1: Create Slack Webhook**

1. Go to Slack Workspace Settings
2. Apps → Manage Apps → Create New App → From scratch
3. Name: "thegent-monitoring"
4. Enable Incoming Webhooks
5. Add New Webhook to Channel: #thegent-alerts
6. Copy Webhook URL

**Step 2: Create Alert Script**

`monitoring/alert_engine.py`:

```python
import requests
import json
from datetime import datetime

SLACK_WEBHOOK = "https://hooks.slack.com/services/..."


def send_alert(title, severity, message, data=None):
    """Send alert to Slack."""

    color_map = {"INFO": "#36a64f", "WARNING": "#ff9800", "CRITICAL": "#f44336"}
    emoji_map = {"INFO": "ℹ", "WARNING": "⚠", "CRITICAL": "!"}

    payload = {
        "attachments": [
            {
                "color": color_map.get(severity, "#999"),
                "title": f"{emoji_map.get(severity, '')} {title}",
                "text": message,
                "fields": [
                    {"title": "Severity", "value": severity, "short": True},
                    {"title": "Time", "value": datetime.utcnow().isoformat(), "short": True},
                ]
                + ([{"title": k, "value": str(v), "short": True} for k, v in (data or {}).items()]),
                "footer": "thegent-monitoring",
                "ts": int(datetime.utcnow().timestamp()),
            }
        ]
    }

    response = requests.post(SLACK_WEBHOOK, json=payload)
    return response.status_code == 200


# Example usage:
send_alert(
    "CATEGORY_BUDGET_WARNING",
    "WARNING",
    "Normal category budget at 80%",
    {"Budget": "$160/$200", "Daily Burn": "$11.43", "Days to Exhaustion": "3.5"},
)
```

**Step 3: Run Alert Check (Hourly Cron)**

```bash
# monitoring/check_alerts.sh
#!/bin/bash
HOUR=$(date +%H)
if [ "$HOUR" != "0" ]; then
  # Run every hour except hour 0 (when we do daily summaries)
  python monitoring/alert_engine.py check-all
fi
```

Add to crontab:

```bash
0 * * * * /path/to/monitoring/check_alerts.sh
```

---

### Step 5.2: PagerDuty Integration (Optional)

**For CRITICAL alerts only:**

1. Create PagerDuty service: "thegent-routing"
2. Add integration: Webhooks → get routing key
3. Configure in alert_engine.py:

```python
import pdpyras


def send_pagerduty_alert(summary, severity, details):
    client = pdpyras.APISession(...)
    client.post(
        "/incidents",
        json={
            "incident": {
                "type": "incident",
                "title": summary,
                "severity": severity,  # "critical", "error"
                "service": {"type": "service_reference", "id": "..."},
                "body": {"type": "incident_body", "details": details},
            }
        },
    )
```

---

## Phase 6: Validation and Testing

### Step 6.1: End-to-End Test

**Objective:** Verify entire monitoring pipeline works.

**Test Checklist:**

- [ ] **Data Collection**
  - [ ] Run a task and verify run_registry.jsonl is updated
  - [ ] Check fields: task_category, estimated_cost, actual_cost_usd, status, exit_code

- [ ] **Database Load**
  - [ ] Load JSONL to database
  - [ ] Query table: `SELECT COUNT(*) FROM run_registry WHERE event='finish'`
  - [ ] Expect: > 0 records

- [ ] **Query Execution**
  - [ ] Run test queries (see Phase 3.1)
  - [ ] Verify results are reasonable (costs > $0, counts > 0)

- [ ] **Dashboard Display**
  - [ ] Open dashboard (Grafana / custom)
  - [ ] Verify panels load without errors
  - [ ] Check data values match SQL query results

- [ ] **Alerts**
  - [ ] Create test condition (e.g., manually reduce budget to trigger warning)
  - [ ] Verify Slack message appears in #thegent-alerts
  - [ ] Check message contains expected fields

- [ ] **Performance**
  - [ ] Measure query times: all < 500ms expected
  - [ ] Check database file size: expect 2-10MB for 90 days of data

**Test Commands:**

```bash
# Test 1: Verify data collection
tail -1 ~/.thegent/session/run_registry.jsonl | jq '.task_category, .actual_cost_usd'

# Test 2: Verify database
sqlite3 monitoring.db "SELECT COUNT(*) as finish_events FROM run_registry WHERE event='finish';"

# Test 3: Run sample query
sqlite3 monitoring.db "SELECT DATE(ended_at_utc), ROUND(SUM(actual_cost_usd),2) FROM run_registry WHERE event='finish' GROUP BY DATE(ended_at_utc) LIMIT 5;"

# Test 4: Check dashboard is responsive
curl -s http://localhost:3000/api/health

# Test 5: Send test alert
python -c "from monitoring.alert_engine import send_alert; send_alert('TEST ALERT', 'INFO', 'Testing monitoring setup')"
```

---

### Step 6.2: Load Testing

**Objective:** Verify performance with larger data volumes.

**Simulate 90 days of data:**

```python
# monitoring/generate_test_data.py
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "monitoring.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Generate 50k test records (90 days, ~550 tasks/day)
start_date = datetime.utcnow() - timedelta(days=90)

for i in range(50000):
    days_offset = random.randint(0, 89)
    run_date = start_date + timedelta(days=days_offset)

    category = random.choice(["fast", "normal", "complex", "high_complex"])
    cost = {"fast": 0.01, "normal": 0.15, "complex": 0.44, "high_complex": 1.07}[category]

    cursor.execute(
        """
        INSERT INTO run_registry (
            run_id, event, task_category, complexity_score,
            estimated_cost, actual_cost_usd, selected_model,
            status, exit_code, duration_s, started_at_utc, ended_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            f"test-{i}",
            "finish",
            category,
            random.randint(10, 95),
            cost * 0.95,
            cost,
            "minimax-m2.5",
            random.choice(["success", "timeout", "error"]),
            random.choice([0, 1, 127]) if random.random() < 0.02 else 0,
            random.uniform(0.1, 60.0),
            run_date.isoformat(),
            run_date.isoformat(),
        ),
    )

conn.commit()
conn.close()
print("Generated 50k test records")
```

**Run load test:**

```bash
python monitoring/generate_test_data.py

# Measure query performance
time sqlite3 monitoring.db "SELECT DATE(ended_at_utc), task_category, COUNT(*) FROM run_registry WHERE event='finish' GROUP BY DATE(ended_at_utc), task_category ORDER BY DATE(ended_at_utc) DESC;"

# Expected: < 200ms for 50k records with indices
```

---

### Step 6.3: Alert Testing

**Objective:** Verify alert rules fire correctly.

**Test Scenario 1: Budget Warning**

```bash
# Manually update run_registry to simulate high spending
sqlite3 monitoring.db <<EOF
UPDATE run_registry SET actual_cost_usd = 50.0
  WHERE task_category = 'normal' LIMIT 3;
COMMIT;
EOF

# Run alert check
python monitoring/alert_engine.py check normal

# Expected: Slack message about budget warning
```

**Test Scenario 2: Error Rate Spike**

```bash
# Update exit codes to simulate errors
sqlite3 monitoring.db <<EOF
UPDATE run_registry SET exit_code = 1
  WHERE task_category = 'normal' AND RANDOM() % 20 = 0 LIMIT 50;
COMMIT;
EOF

# Run alert check
python monitoring/alert_engine.py check error_rate

# Expected: Slack message about error rate
```

---

## Phase 7: Operational Procedures

### Step 7.1: Daily Operations

**Morning (Start of Business)**

```bash
# 1. Check overnight alerts
curl http://localhost:5000/api/alerts?severity=CRITICAL

# 2. Review budget status
sqlite3 monitoring.db "SELECT task_category, SUM(actual_cost_usd) FROM run_registry WHERE event='finish' AND STRFTIME('%Y-%m', ended_at_utc) = STRFTIME('%Y-%m', 'now') GROUP BY task_category;"

# 3. Check SLA attainment
sqlite3 monitoring.db "SELECT task_category, ROUND(AVG(duration_s * 1000)) as p50_ms FROM run_registry WHERE event='finish' AND RANDOM() % 2 = 0 GROUP BY task_category;"
```

**End of Day**

```bash
# 1. Generate daily summary report
python monitoring/generate_report.py --date today --output daily_summary.json

# 2. Archive yesterday's logs
tar czf archive/run_registry_$(date -d yesterday +%Y%m%d).jsonl.gz run_registry.jsonl

# 3. Trim local JSONL (keep last 30 days)
python monitoring/trim_jsonl.py --days 30
```

### Step 7.2: Weekly Review

```bash
# 1. Review cost trends
sqlite3 monitoring.db "SELECT strftime('%Y-W%W', ended_at_utc) as week, ROUND(SUM(actual_cost_usd), 2) as cost FROM run_registry WHERE event='finish' GROUP BY week ORDER BY week DESC LIMIT 4;"

# 2. Identify constraint violations
sqlite3 monitoring.db "SELECT constraint_violations, COUNT(*) FROM run_registry WHERE event='finish' AND constraint_violations != '[]' GROUP BY constraint_violations ORDER BY COUNT(*) DESC LIMIT 5;"

# 3. Check model performance regression
python monitoring/analyze_quality_trends.py --window 7 --output quality_report.md
```

### Step 7.3: Monthly Review

```bash
# 1. Generate end-of-month cost report
python monitoring/generate_monthly_report.py --month $(date +%Y-%m)

# 2. Archive old data
find archive -name "*.jsonl.gz" -mtime +90 -delete

# 3. Optimize database (VACUUM in SQLite)
sqlite3 monitoring.db "VACUUM;"

# 4. Review forecast vs actual
sqlite3 monitoring.db << 'EOF'
SELECT
  'FAST' as category,
  50.00 as budget,
  (SELECT ROUND(SUM(actual_cost_usd), 2) FROM run_registry WHERE task_category='fast' AND STRFTIME('%Y-%m', ended_at_utc) = STRFTIME('%Y-%m', 'now') AND event='finish') as actual,
  ROUND((SELECT SUM(actual_cost_usd) FROM run_registry WHERE task_category='fast' AND STRFTIME('%Y-%m', ended_at_utc) = STRFTIME('%Y-%m', 'now') AND event='finish') / CAST(STRFTIME('%d', 'now') AS FLOAT) * 30, 2) as forecast;
EOF
```

---

## Troubleshooting

### Issue: Queries Too Slow

**Diagnosis:**

```bash
# Check index usage
sqlite3 monitoring.db "EXPLAIN QUERY PLAN SELECT * FROM run_registry WHERE task_category='normal' AND DATE(ended_at_utc)='2025-02-14';"
# Look for "SCAN TABLE run_registry" (slow) vs "SEARCH TABLE" (fast)
```

**Fix:**

- Add missing indices (see schema)
- Partition data by month (PostgreSQL)
- Create materialized views for common aggregates

### Issue: Missing Fields in run_registry.jsonl

**Diagnosis:**

```bash
tail -100 run_registry.jsonl | jq '.task_category' | sort | uniq -c
# If many nulls: logging not configured correctly
```

**Fix:**

- Update execution.py to log required fields
- Ensure TaskRouter.route_task() is called
- Verify CostAggregator.estimate_cost() is called

### Issue: Dashboard Not Updating

**Diagnosis:**

```bash
# Check last data load time
ls -la monitoring.db
# Check if recent records in database
sqlite3 monitoring.db "SELECT MAX(DATE(ended_at_utc)) FROM run_registry;"
```

**Fix:**

- Run manual sync: `python monitoring/load_jsonl.py run_registry.jsonl`
- Check cron job: `crontab -l | grep load_jsonl`
- Verify database connection in dashboard config

### Issue: Alerts Not Firing

**Diagnosis:**

```bash
# Check alert log
tail -50 monitoring/alert.log
# Test alert manually
python monitoring/alert_engine.py check all
```

**Fix:**

- Verify Slack webhook URL is valid: `curl -X POST $WEBHOOK_URL ...`
- Check alert query: run manually and verify results
- Check alert threshold logic

---

## Success Criteria

**Monitoring setup is complete when:**

- [ ] All 5 dashboards (Cost, Performance, SLA, Operational, Budget) are accessible and displaying data
- [ ] All 12 alert rules are configured and tested
- [ ] At least 1 week of historical data is in database
- [ ] Query performance is acceptable (< 500ms for all queries)
- [ ] Team has received and acknowledged at least 1 test alert
- [ ] Daily sync process is running on schedule
- [ ] Monthly cost forecast is accurate within 10%
- [ ] SLA attainment is being tracked and reported
- [ ] Budget utilization alerts are working for all categories

**Document Completion:**

- [ ] MONITORING_DASHBOARD_SPEC.md completed
- [ ] MONITORING_METRICS_REFERENCE.md completed
- [ ] MONITORING_ALERT_RULES.md completed
- [ ] This MONITORING_SETUP_GUIDE.md completed
- [ ] Queries tested against real data
- [ ] Dashboard access verified
- [ ] Alert channels tested

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
